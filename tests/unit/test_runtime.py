import json
from pathlib import Path

import pytest

from skill_registry.hashing import tree_sha256
from skill_registry.runtime import RegistryRuntimeError, search_skills


def build_registry(root: Path, specs: list[dict[str, object]]) -> list[dict[str, object]]:
    (root / "registry").mkdir()
    records = []
    entries = []
    core_ids = []
    for number, spec in enumerate(specs, start=1):
        name = str(spec["name"])
        taxonomy = str(spec.get("taxonomy", "engineering/testing"))
        description = str(spec.get("description", name))
        skill_id = f"asr_{number:016x}"
        skill_root = root / "catalog" / taxonomy / name
        skill_root.mkdir(parents=True)
        (skill_root / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\nUse {name}.\n",
            encoding="utf-8",
        )
        record = {
            "skill_id": skill_id,
            "name": name,
            "load_name": name,
            "catalog_path": skill_root.relative_to(root).as_posix(),
            "source_id": "fixture",
            "source_commit": "a" * 40,
            "source_path": f"skills/{name}",
            "content_sha256": tree_sha256(skill_root),
            "license": "MIT",
            "risk": str(spec.get("risk", "unknown")),
            "risk_reasons": ["fixture"],
            "state": str(spec.get("state", "active")),
            "canonical_skill_id": spec.get("canonical_skill_id"),
            "first_seen_version": "1.0.0",
        }
        records.append(record)
        entries.append(
            {
                "name": name,
                "flat_name": name,
                "taxonomy": taxonomy,
                "category_fine": str(spec.get("category", "engineering")),
                "description": description,
            }
        )
        if spec.get("core"):
            core_ids.append(skill_id)
    (root / "registry" / "skills.json").write_text(
        json.dumps({"schema_version": 1, "skills": records}), encoding="utf-8"
    )
    (root / "registry" / "core.json").write_text(
        json.dumps({"schema_version": 1, "skill_ids": core_ids}), encoding="utf-8"
    )
    (root / "registry" / "quarantine.json").write_text(
        json.dumps({"schema_version": 1, "records": []}), encoding="utf-8"
    )
    (root / "librarian-index.json").write_text(
        json.dumps({"schemaVersion": 1, "entries": entries}), encoding="utf-8"
    )
    return records


def test_search_ranks_name_and_taxonomy_before_description(tmp_path):
    build_registry(
        tmp_path,
        [
            {
                "name": "security-audit",
                "taxonomy": "security/auditing",
                "description": "Review a repository.",
            },
            {
                "name": "release-notes",
                "taxonomy": "writing/documentation",
                "description": "Mention security audit results.",
            },
        ],
    )
    matches = search_skills(tmp_path, "security audit")["matches"]
    assert [item["load_name"] for item in matches] == ["security-audit", "release-notes"]


def test_search_adds_safety_bonus_only_after_text_match(tmp_path):
    build_registry(
        tmp_path,
        [
            {"name": "pdf", "description": "Work with PDF documents."},
            {
                "name": "unrelated-safe",
                "description": "Manage calendars.",
                "risk": "safe",
                "core": True,
            },
        ],
    )
    matches = search_skills(tmp_path, "pdf")["matches"]
    assert [item["load_name"] for item in matches] == ["pdf"]


def test_search_excludes_dangerous_inactive_and_canonical_records(tmp_path):
    build_registry(
        tmp_path,
        [
            {"name": "safe-audit", "description": "Security audit", "risk": "safe"},
            {"name": "danger-audit", "description": "Security audit", "risk": "dangerous"},
            {"name": "old-audit", "description": "Security audit", "state": "deprecated"},
            {
                "name": "alias-audit",
                "description": "Security audit",
                "canonical_skill_id": "asr_0000000000000001",
            },
        ],
    )
    matches = search_skills(tmp_path, "security audit")["matches"]
    assert [item["load_name"] for item in matches] == ["safe-audit"]


def test_search_rejects_missing_or_duplicate_discovery_metadata(tmp_path):
    records = build_registry(tmp_path, [{"name": "security-audit"}])
    index = tmp_path / "librarian-index.json"
    index.write_text(json.dumps({"schemaVersion": 1, "entries": []}), encoding="utf-8")
    with pytest.raises(RegistryRuntimeError, match=records[0]["load_name"]):
        search_skills(tmp_path, "security")

    duplicate = {
        "name": "security-audit",
        "flat_name": "security-audit",
        "taxonomy": "security/auditing",
        "category_fine": "security",
        "description": "duplicate",
    }
    index.write_text(
        json.dumps({"schemaVersion": 1, "entries": [duplicate, duplicate]}), encoding="utf-8"
    )
    with pytest.raises(RegistryRuntimeError, match="duplicate discovery metadata"):
        search_skills(tmp_path, "security")


@pytest.mark.parametrize(("query", "limit"), [("", 10), ("---", 10), ("pdf", 0), ("pdf", 51)])
def test_search_rejects_invalid_query_or_limit(tmp_path, query, limit):
    build_registry(tmp_path, [{"name": "pdf"}])
    with pytest.raises(ValueError):
        search_skills(tmp_path, query, limit=limit)


def test_search_ties_are_sorted_by_load_name(tmp_path):
    build_registry(
        tmp_path,
        [
            {"name": "zeta", "description": "shared"},
            {"name": "alpha", "description": "shared"},
        ],
    )
    matches = search_skills(tmp_path, "shared")["matches"]
    assert [item["load_name"] for item in matches] == ["alpha", "zeta"]
