import json
from pathlib import Path

import pytest

from skill_registry.refresh import SourceRefreshError, refresh_sources


def write_lock(root: Path, commit: str = "a" * 40) -> None:
    registry = root / "registry"
    registry.mkdir()
    (registry / "sources.lock.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "example",
                        "url": "https://example.invalid/source.git",
                        "commit": commit,
                    }
                ]
            }
        )
    )


def test_refresh_marks_a_changed_remote_as_behind(tmp_path: Path):
    write_lock(tmp_path)

    report = refresh_sources(tmp_path, runner=lambda *_args, **_kwargs: f"{'b' * 40}\tHEAD\n")

    assert report == {
        "sources": [
            {
                "source_id": "example",
                "pinned_commit": "a" * 40,
                "observed_commit": "b" * 40,
                "status": "behind",
            }
        ]
    }


def test_refresh_rejects_an_unparseable_remote_response(tmp_path: Path):
    write_lock(tmp_path)

    with pytest.raises(SourceRefreshError, match="no commit"):
        refresh_sources(tmp_path, runner=lambda *_args, **_kwargs: "")
