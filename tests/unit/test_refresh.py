import json
import subprocess
from pathlib import Path

from skill_registry.refresh import refresh_sources


def write_lock(root: Path, sources: list[dict[str, object]]) -> Path:
    registry = root / "registry"
    registry.mkdir()
    (registry / "sources.lock.json").write_text(
        json.dumps({"sources": sources}), encoding="utf-8"
    )
    return root


def active_source(source_id: str, url: str, commit: str) -> dict[str, object]:
    return {
        "source_id": source_id,
        "url": url,
        "commit": commit,
        "status": "active",
        "refreshable": True,
        "timeout_seconds": 15,
    }


def test_refresh_marks_a_changed_remote_as_behind(tmp_path: Path):
    write_lock(
        tmp_path,
        [active_source("example", "https://example.invalid/source.git", "a" * 40)],
    )

    def runner(*_args, **kwargs):
        assert kwargs["timeout"] == 15
        return f"{'b' * 40}\tHEAD\n"

    report = refresh_sources(tmp_path, runner=runner)

    assert report == {
        "result": "pass",
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
    write_lock(
        tmp_path,
        [active_source("example", "https://example.invalid/source.git", "a" * 40)],
    )

    payload = refresh_sources(tmp_path, runner=lambda *_args, **_kwargs: "")

    assert payload["result"] == "error"
    assert payload["sources"][0]["status"] == "error"


def test_refresh_skips_retired_source(tmp_path: Path):
    root = write_lock(tmp_path, [{
        "source_id": "legacy",
        "url": "https://github.com/deleted/repo.git",
        "commit": "a" * 40,
        "status": "retired",
        "refreshable": False,
        "timeout_seconds": 15,
    }])
    calls = []

    payload = refresh_sources(root, runner=lambda *args, **kwargs: calls.append(args))

    assert calls == []
    assert payload == {
        "result": "pass",
        "sources": [{
            "source_id": "legacy",
            "pinned_commit": "a" * 40,
            "observed_commit": None,
            "status": "retired",
        }],
    }


def test_refresh_reports_error_and_continues(tmp_path: Path):
    root = write_lock(tmp_path, [
        active_source("broken", "https://example.invalid/broken.git", "a" * 40),
        active_source("healthy", "https://example.invalid/healthy.git", "b" * 40),
    ])

    def runner(command, **kwargs):
        if "broken" in command[2]:
            raise subprocess.CalledProcessError(2, command)
        assert kwargs["timeout"] == 15
        return f"{'b' * 40}\tHEAD\n"

    payload = refresh_sources(root, runner=runner)

    assert payload["result"] == "error"
    assert [item["status"] for item in payload["sources"]] == ["error", "current"]
