import json
import shutil

from skill_registry.validator import verify_repository


def clone_repository_fixture(repo_root, tmp_path):
    shutil.copytree(repo_root / "catalog", tmp_path / "catalog")
    shutil.copytree(repo_root / "registry", tmp_path / "registry")
    return tmp_path


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
