import os
from pathlib import Path

import pytest

from skill_registry.hashing import UnsafeCatalogPath, tree_sha256


def test_hash_changes_with_executable_mode(tmp_path: Path):
    skill = tmp_path / "skill"
    skill.mkdir()
    script = skill / "run.sh"
    script.write_text("#!/bin/sh\nexit 0\n")
    before = tree_sha256(skill)
    script.chmod(0o755)
    assert tree_sha256(skill) != before


def test_hash_rejects_symlink(tmp_path: Path):
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("content")
    os.symlink(skill / "SKILL.md", skill / "copy")
    with pytest.raises(UnsafeCatalogPath, match="symlink"):
        tree_sha256(skill)
