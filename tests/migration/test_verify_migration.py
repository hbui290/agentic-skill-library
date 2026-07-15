import json
from pathlib import Path

import pytest

from tools.verify_migration import MigrationError, verify


def test_verify_reconciles_active_and_markerless_records(tmp_path: Path):
    valid = tmp_path / "catalog/engineering/testing/valid"
    valid.mkdir(parents=True)
    (valid / "SKILL.md").write_text("---\nname: valid\ndescription: valid\n---\n")
    markerless = tmp_path / "catalog/engineering/testing/bundle"
    markerless.mkdir(parents=True)
    (markerless / "plugin.json").write_text("{}")
    manifest = tmp_path / "registry/migration/legacy-manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"entries": [
        "catalog/engineering/testing/valid",
        "catalog/engineering/testing/bundle",
    ]}))

    assert verify(tmp_path) == {"legacy": 2, "active_candidates": 1, "markerless": 1}


def test_verify_rejects_missing_path(tmp_path: Path):
    manifest = tmp_path / "registry/migration/legacy-manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"entries": ["catalog/engineering/testing/missing"]}))

    with pytest.raises(MigrationError, match="missing legacy path"):
        verify(tmp_path)
