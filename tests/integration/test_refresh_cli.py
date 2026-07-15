import json

from skill_registry import cli


def test_refresh_cli_renders_machine_report(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(
        cli,
        "refresh_sources",
        lambda _root: {
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
