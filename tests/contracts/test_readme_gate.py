from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_readme_does_not_expose_legacy_updater():
    readme = (ROOT / "README.md").read_text()
    assert "scripts/update_skills.py" not in readme
    assert "Migration in progress" in readme
    assert "python3 tools/verify_migration.py" in readme
