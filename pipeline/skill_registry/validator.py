import json
import re
from datetime import date
from pathlib import Path

import yaml

from skill_registry.collector import discover_catalog
from skill_registry.hashing import UnsafeCatalogPath, tree_sha256
from skill_registry.reporting import VerificationReport


ID = re.compile(r"^asr_[0-9a-f]{16}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
RISK_VALUES = {"safe", "review", "dangerous", "unknown"}
STATE_VALUES = {"active", "deprecated", "quarantined"}
SKILL_FIELDS = {"skill_id", "name", "load_name", "catalog_path", "source_id", "source_commit", "source_path", "content_sha256", "license", "risk", "risk_reasons", "state", "canonical_skill_id", "first_seen_version"}


def add(findings: list[dict[str, object]], check_id: str, requirement_ids: list[str], **context: object) -> None:
    findings.append({"check_id": check_id, "requirement_ids": requirement_ids, "result": "fail", **context})


def read_records(path: Path, key: str) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get(key, []) if isinstance(payload, dict) else []


def frontmatter(path: Path) -> dict[str, object]:
    match = re.match(r"^---\s*\n(.*?)\n---", path.read_text(encoding="utf-8", errors="replace"), re.DOTALL)
    if not match:
        return {}
    try:
        value = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return {}
    return value if isinstance(value, dict) else {}


def verify_repository(root: Path) -> VerificationReport:
    findings: list[dict[str, object]] = []
    registry = root / "registry"
    skills_path = registry / "skills.json"
    if not skills_path.is_file():
        add(findings, "registry.present", ["DR-08"])
        return VerificationReport("fail", 0, 1, 0, 0, tuple(findings))
    required = ("sources.lock.json", "aliases.json", "quarantine.json", "risk-overrides.json", "exceptions.json", "schema-version.json", "core.json", "upstream-review.json")
    missing = [name for name in required if not (registry / name).is_file()]
    if missing:
        add(findings, "registry.present", ["DR-08"], missing=missing)
    elif json.loads((registry / "schema-version.json").read_text(encoding="utf-8")).get("schema_version") != 1:
        add(findings, "registry.schema-version", ["DR-08"])
    skills = read_records(skills_path, "skills")
    quarantine = read_records(registry / "quarantine.json", "records")
    aliases = read_records(registry / "aliases.json", "aliases")
    exceptions = read_records(registry / "exceptions.json", "exceptions")
    core_payload = json.loads((registry / "core.json").read_text()) if (registry / "core.json").is_file() else {}
    core = core_payload.get("skill_ids") if isinstance(core_payload, dict) else None
    known_skills = {record.get("skill_id"): record for record in skills}
    if (
        core_payload.get("schema_version") != 1
        or not isinstance(core, list)
        or not all(isinstance(skill_id, str) for skill_id in core or [])
        or len(core) != len(set(core))
        or any(
            known_skills.get(skill_id, {}).get("state") != "active"
            or known_skills.get(skill_id, {}).get("risk") != "safe"
            for skill_id in core or []
        )
    ):
        add(findings, "registry.core", ["DR-08"])
    lock_payload = json.loads((registry / "sources.lock.json").read_text()) if (registry / "sources.lock.json").is_file() else {"sources": []}
    sources = lock_payload.get("sources", []) if isinstance(lock_payload, dict) else []
    source_ids = {source.get("source_id") for source in sources if isinstance(source, dict)}
    if lock_payload.get("schema_version") != 1 or len(source_ids) != len(sources) or any(
        not all(source.get(field) for field in ("source_id", "url", "layout", "license_note")) or not COMMIT.fullmatch(str(source.get("commit", "")))
        for source in sources if isinstance(source, dict)
    ):
        add(findings, "registry.source-lock", ["DR-04", "UR-01"])
    try:
        review_payload = json.loads((registry / "upstream-review.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        review_payload = {}
    review_records = review_payload.get("records") if isinstance(review_payload, dict) else None
    review_source = next((source for source in sources if isinstance(source, dict) and source.get("source_id") == review_payload.get("source_id")), None)
    review_valid = (
        isinstance(review_records, list)
        and review_payload.get("schema_version") == 1
        and isinstance(review_source, dict)
        and review_payload.get("pinned_commit") == review_source.get("commit")
        and COMMIT.fullmatch(str(review_payload.get("observed_commit", ""))) is not None
        and all(
            isinstance(record, dict)
            and isinstance(record.get("source_path"), str)
            and record["source_path"].startswith("skills/")
            and ".." not in record["source_path"].split("/")
            and record.get("change") in {"added", "modified"}
            and record.get("disposition") in {"review", "quarantined"}
            and isinstance(record.get("reason"), str)
            and bool(record["reason"].strip())
            for record in review_records or []
        )
    )
    if review_valid:
        review_paths = [record["source_path"] for record in review_records]
        review_valid = len(review_paths) == len(set(review_paths))
    if not review_valid:
        add(findings, "registry.upstream-review", ["UR-01"])
    ids: set[str] = set()
    load_names: set[str] = set()
    for record in skills:
        path = root / str(record.get("catalog_path", ""))
        marker = path / "SKILL.md"
        if not marker.is_file():
            add(findings, "catalog.skill-root", ["DR-03"], skill_id=record.get("skill_id"))
        missing_fields = sorted(SKILL_FIELDS - record.keys())
        if missing_fields:
            add(findings, "registry.skill-schema", ["DR-08"], missing=missing_fields)
            continue
        if not marker.is_file():
            continue
        metadata = frontmatter(marker)
        if metadata.get("name") != record["name"] or not str(metadata.get("description", "")).strip():
            add(findings, "catalog.frontmatter", ["DR-03"], skill_id=record["skill_id"])
        if not ID.fullmatch(str(record["skill_id"])) or record["skill_id"] in ids:
            add(findings, "registry.skill-id", ["DR-01"], skill_id=record["skill_id"])
        ids.add(record["skill_id"])
        if not record["load_name"] or record["load_name"] in load_names:
            add(findings, "registry.load-name", ["DR-02"], skill_id=record["skill_id"])
        load_names.add(record["load_name"])
        if record["source_id"] not in source_ids or not COMMIT.fullmatch(str(record["source_commit"])) or not all(record.get(field) for field in ("source_path", "license", "risk", "risk_reasons", "state")):
            add(findings, "registry.provenance", ["DR-04", "DR-06"], skill_id=record["skill_id"])
        if record["risk"] not in RISK_VALUES or record["state"] not in STATE_VALUES:
            add(findings, "registry.state-values", ["DR-06"], skill_id=record["skill_id"])
        try:
            actual = tree_sha256(path)
        except (UnsafeCatalogPath, OSError):
            actual = ""
        if not SHA.fullmatch(str(record["content_sha256"])) or actual != record["content_sha256"]:
            add(findings, "catalog.content-hash", ["DR-05", "UR-06"], skill_id=record["skill_id"])
    quarantine_ids = {record.get("skill_id") for record in quarantine}
    if ids & quarantine_ids or len(quarantine_ids) != len(quarantine):
        add(findings, "registry.identity-overlap", ["DR-01", "DR-07"])
    for record in quarantine:
        if not ID.fullmatch(str(record.get("skill_id", ""))) or not record.get("rule_ids") or not record.get("disposition"):
            add(findings, "registry.quarantine", ["DR-07"], skill_id=record.get("skill_id"))
        path_value = record.get("catalog_path")
        if path_value:
            try:
                actual = tree_sha256(root / str(path_value))
            except (UnsafeCatalogPath, OSError):
                actual = ""
            if actual != record.get("content_sha256"):
                add(findings, "registry.quarantine-hash", ["DR-05", "DR-07"], skill_id=record.get("skill_id"))
    alias_names = {alias.get("alias") for alias in aliases}
    if alias_names & load_names:
        add(findings, "registry.alias-shadow", ["DR-02"])
    active_ids = {record["skill_id"] for record in skills if SKILL_FIELDS <= record.keys() and record.get("state") == "active"}
    if len(alias_names) != len(aliases) or any(alias.get("target_skill_id") not in active_ids for alias in aliases):
        add(findings, "registry.alias-target", ["DR-02"])
    if any(record.get("canonical_skill_id") is not None and (record["canonical_skill_id"] not in active_ids or record["canonical_skill_id"] == record["skill_id"]) for record in skills if SKILL_FIELDS <= record.keys()):
        add(findings, "registry.canonical-target", ["DR-02"])
    catalog_paths = {path.relative_to(root).as_posix() for path in discover_catalog(root)} if (root / "catalog").is_dir() else set()
    registered_paths = {record.get("catalog_path") for record in skills + quarantine if record.get("catalog_path")}
    if catalog_paths != registered_paths:
        add(findings, "registry.reconciliation", ["DR-08"], missing=sorted(catalog_paths - registered_paths), extra=sorted(registered_paths - catalog_paths))
    for exception in exceptions:
        fields = ("exception_id", "requirement_ids", "rationale", "owner", "created_at", "expires_at")
        try:
            expired = date.fromisoformat(str(exception.get("expires_at"))) < date.today()
        except ValueError:
            expired = True
        if not all(exception.get(field) for field in fields) or expired:
            add(findings, "governance.exception", ["GR-04"], exception_id=exception.get("exception_id"))
    failed = len(findings)
    return VerificationReport("pass" if not failed else "fail", 1 if not failed else 0, failed, 0, 0, tuple(findings))
