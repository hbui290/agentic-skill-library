from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_readme_does_not_expose_legacy_updater():
    readme = (ROOT / "README.md").read_text()
    assert "scripts/update_skills.py" not in readme
    assert "skill-registry verify --strict" in readme
    assert "skill-registry refresh --format json" in readme
    assert "Automatic bulk import" in readme
