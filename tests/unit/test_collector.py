from pathlib import Path

from skill_registry.collector import discover_catalog


def test_discover_catalog_returns_third_level_directories(tmp_path: Path):
    valid = tmp_path / "catalog/engineering/testing/valid"
    valid.mkdir(parents=True)
    (valid / "SKILL.md").write_text("content")
    markerless = tmp_path / "catalog/engineering/testing/bundle"
    markerless.mkdir(parents=True)
    (markerless / "plugin.json").write_text("{}")
    assert discover_catalog(tmp_path) == [markerless, valid]
