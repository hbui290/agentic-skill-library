import json

from skill_registry import cli


def test_refresh_cli_renders_machine_report(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(
        cli,
        "refresh_sources",
        lambda _root: {
            "result": "pass",
            "sources": [
                {
                    "source_id": "example",
                    "pinned_commit": "a" * 40,
                    "observed_commit": "b" * 40,
                    "status": "behind",
                }
            ]
        },
    )

    assert cli.main(["refresh", "--root", str(tmp_path), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["sources"][0]["status"] == "behind"


def test_refresh_cli_returns_error_after_rendering_complete_partial_error_report(
    monkeypatch, capsys, tmp_path
):
    monkeypatch.setattr(
        cli,
        "refresh_sources",
        lambda _root: {
            "result": "error",
            "sources": [
                {
                    "source_id": "broken",
                    "pinned_commit": "a" * 40,
                    "observed_commit": None,
                    "status": "error",
                    "error": "CalledProcessError",
                },
                {
                    "source_id": "healthy",
                    "pinned_commit": "b" * 40,
                    "observed_commit": "b" * 40,
                    "status": "current",
                },
            ],
        },
    )

    result = cli.main(["refresh", "--root", str(tmp_path), "--format", "json"])
    captured = capsys.readouterr()

    assert result == 1
    assert json.loads(captured.out)["sources"][1]["status"] == "current"
    assert captured.err == ""
