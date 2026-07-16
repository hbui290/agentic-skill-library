import json
import shutil

import pytest

from skill_registry.validator import verify_repository
from skill_registry.identity import stable_skill_id


def clone_repository_fixture(repo_root, tmp_path):
    shutil.copytree(repo_root / "catalog", tmp_path / "catalog")
    shutil.copytree(repo_root / "registry", tmp_path / "registry")
    return tmp_path


def write_json(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def check_ids(root):
    return {finding["check_id"] for finding in verify_repository(root).findings}


def test_complete_repository_passes(repo_root):
    report = verify_repository(repo_root)
    assert report.result == "pass"
    assert report.failed == 0
    assert report.skipped == 0


def test_missing_skill_marker_fails(tmp_path):
    (tmp_path / "registry").mkdir()
    (tmp_path / "catalog/x/y/z").mkdir(parents=True)
    (tmp_path / "registry/skills.json").write_text(json.dumps({"skills": [{
        "skill_id": "asr_0123456789abcdef", "name": "z", "load_name": "z",
        "catalog_path": "catalog/x/y/z", "content_sha256": "0" * 64,
    }]}))
    report = verify_repository(tmp_path)
    assert report.result == "fail"
    assert any(finding["check_id"] == "catalog.skill-root" for finding in report.findings)


def test_strict_contract_rejects_cross_registry_conflicts(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    skills = json.loads((root / "registry/skills.json").read_text())
    quarantine = json.loads((root / "registry/quarantine.json").read_text())
    duplicate = skills["skills"][0]
    quarantine["records"][0]["skill_id"] = duplicate["skill_id"]
    (root / "registry/quarantine.json").write_text(json.dumps(quarantine))
    (root / "registry/aliases.json").write_text(json.dumps({"schema_version": 1, "aliases": [{"alias": duplicate["load_name"], "target_skill_id": duplicate["skill_id"]}]}))
    check_ids = {finding["check_id"] for finding in verify_repository(root).findings}
    assert {"registry.identity-overlap", "registry.alias-shadow"} <= check_ids


def test_strict_contract_rejects_bad_frontmatter_and_source_lock(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    skills = json.loads((root / "registry/skills.json").read_text())["skills"]
    (root / skills[0]["catalog_path"] / "SKILL.md").write_text("---\nname: wrong\ndescription: ''\n---\n")
    lock = json.loads((root / "registry/sources.lock.json").read_text())
    lock["sources"][0]["commit"] = "main"
    (root / "registry/sources.lock.json").write_text(json.dumps(lock))
    check_ids = {finding["check_id"] for finding in verify_repository(root).findings}
    assert {"catalog.frontmatter", "registry.source-lock"} <= check_ids


def test_strict_contract_rejects_expired_exception(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    (root / "registry/exceptions.json").write_text(json.dumps({"schema_version": 1, "exceptions": [{
        "exception_id": "EX-001", "requirement_ids": ["GR-04"], "owner": "hbui290",
        "rationale": "fixture", "created_at": "2026-01-01", "expires_at": "2026-01-02",
    }]}))
    assert any(finding["check_id"] == "governance.exception" for finding in verify_repository(root).findings)


def test_strict_contract_rejects_unknown_schema_version(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    (root / "registry/schema-version.json").write_text(json.dumps({"schema_version": 999}))
    assert any(finding["check_id"] == "registry.schema-version" for finding in verify_repository(root).findings)


def test_strict_contract_rejects_core_record_that_is_not_safe(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    record = json.loads((root / "registry/skills.json").read_text())["skills"][0]
    (root / "registry/core.json").write_text(json.dumps({"schema_version": 1, "skill_ids": [record["skill_id"]]}))
    check_ids = {finding["check_id"] for finding in verify_repository(root).findings}
    assert "registry.core" in check_ids


def test_strict_contract_rejects_malformed_core_members(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    (root / "registry/core.json").write_text(json.dumps({"schema_version": 1, "skill_ids": [[]]}))
    check_ids = {finding["check_id"] for finding in verify_repository(root).findings}
    assert "registry.core" in check_ids


def test_strict_contract_rejects_invalid_upstream_review(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    payload = json.loads((root / "registry/upstream-review.json").read_text())
    payload["records"][0]["disposition"] = "accepted"
    (root / "registry/upstream-review.json").write_text(json.dumps(payload))
    check_ids = {finding["check_id"] for finding in verify_repository(root).findings}
    assert "registry.upstream-review" in check_ids


def test_default_core_contains_only_audited_safe_skill(repo_root):
    core = json.loads((repo_root / "registry/core.json").read_text())["skill_ids"]
    skills = {record["skill_id"]: record for record in json.loads((repo_root / "registry/skills.json").read_text())["skills"]}
    assert core == ["asr_8b273fe4fe068d88"]
    assert skills[core[0]]["risk"] == "safe"
    assert "core-audit" in skills[core[0]]["risk_reasons"]


def test_verify_rejects_record_commit_not_equal_to_source_lock(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    payload = json.loads((root / "registry/skills.json").read_text())
    payload["skills"][0]["source_commit"] = "b" * 40
    write_json(root / "registry/skills.json", payload)
    assert "registry.provenance" in check_ids(root)


def test_verify_rejects_skill_id_not_derived_from_source(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    payload = json.loads((root / "registry/skills.json").read_text())
    payload["skills"][0]["skill_id"] = "asr_0000000000000000"
    write_json(root / "registry/skills.json", payload)
    assert "registry.identity" in check_ids(root)


def test_verify_rejects_duplicate_source_path_across_active_and_quarantine(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    active = json.loads((root / "registry/skills.json").read_text())["skills"][0]
    quarantine = json.loads((root / "registry/quarantine.json").read_text())
    quarantine["records"].append({**active, "disposition": "quarantined"})
    write_json(root / "registry/quarantine.json", quarantine)
    assert "registry.source-path" in check_ids(root)


def test_verify_rejects_invalid_source_lifecycle(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    lock = json.loads((root / "registry/sources.lock.json").read_text())
    lock["sources"][0].update({"status": "retired", "refreshable": True})
    write_json(root / "registry/sources.lock.json", lock)
    assert "registry.source-lock" in check_ids(root)


def test_verify_rejects_boolean_source_timeout(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    lock = json.loads((root / "registry/sources.lock.json").read_text())
    lock["sources"][0]["timeout_seconds"] = True
    write_json(root / "registry/sources.lock.json", lock)
    assert "registry.source-lock" in check_ids(root)


def test_verify_rejects_non_refreshable_active_source(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    lock = json.loads((root / "registry/sources.lock.json").read_text())
    lock["sources"][1]["refreshable"] = False
    write_json(root / "registry/sources.lock.json", lock)
    assert "registry.source-lock" in check_ids(root)


@pytest.mark.parametrize("sources", [None, 1, {}, "invalid"])
def test_verify_reports_malformed_source_collection(repo_root, tmp_path, sources):
    root = clone_repository_fixture(repo_root, tmp_path)
    write_json(
        root / "registry/sources.lock.json",
        {"schema_version": 1, "sources": sources},
    )
    assert "registry.source-lock" in check_ids(root)


def test_quarantine_skill_ids_are_derived_from_source(repo_root):
    records = json.loads((repo_root / "registry/quarantine.json").read_text())["records"]
    assert all(
        record["skill_id"] == stable_skill_id(record["source_id"], record["source_path"])
        for record in records
    )
