import json

from skill_registry import cli
from skill_registry.runtime import SkillBlocked, SkillConfirmationRequired


MATCH = {
    "skill_id": "asr_0000000000000001",
    "name": "pdf",
    "load_name": "pdf",
    "risk": "safe",
    "risk_reasons": ["fixture"],
    "core": True,
    "taxonomy": "documents/pdf",
    "category": "documents",
    "description": "Work with PDF files.",
    "score": 10,
}


CONFIRMATION = {
    "error": "confirmation_required",
    "skill": {
        "skill_id": "asr_0000000000000001",
        "load_name": "unknown-skill",
        "risk": "unknown",
        "risk_reasons": ["fixture"],
        "core": False,
        "source_id": "fixture",
        "source_commit": "a" * 40,
        "source_path": "skills/unknown-skill",
        "license": "MIT",
        "content_sha256": "b" * 64,
    },
}


def needs_confirmation(root, identifier, allow):
    raise SkillConfirmationRequired(CONFIRMATION)


def test_search_cli_renders_json(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(
        cli,
        "search_skills",
        lambda root, query, limit: {"query": query, "matches": [MATCH]},
        raising=False,
    )
    result = cli.main(["search", "pdf", "document", "--root", str(tmp_path), "--format", "json"])
    assert result == 0
    assert json.loads(capsys.readouterr().out)["matches"][0]["load_name"] == "pdf"


def test_search_cli_renders_text_and_no_match(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(
        cli,
        "search_skills",
        lambda root, query, limit: {"query": query, "matches": [MATCH]},
        raising=False,
    )
    assert cli.main(["search", "pdf", "--root", str(tmp_path)]) == 0
    assert capsys.readouterr().out == "pdf | safe | documents/pdf | Work with PDF files.\n"

    monkeypatch.setattr(
        cli,
        "search_skills",
        lambda root, query, limit: {"query": query, "matches": []},
        raising=False,
    )
    assert cli.main(["search", "absent", "--root", str(tmp_path)]) == 0
    assert capsys.readouterr().out == "no matches\n"


def test_read_cli_renders_text_and_json(monkeypatch, capsys, tmp_path):
    payload = {"skill": {"load_name": "pdf"}, "instructions": "# Loaded\n"}
    monkeypatch.setattr(cli, "read_skill", lambda root, identifier, allow: payload, raising=False)
    assert cli.main(["read", "pdf", "--root", str(tmp_path)]) == 0
    assert capsys.readouterr().out == "# Loaded\n"

    assert cli.main(["read", "pdf", "--root", str(tmp_path), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out) == payload


def test_read_unknown_json_emits_metadata_without_instructions(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "read_skill", needs_confirmation, raising=False)
    result = cli.main(
        ["read", "unknown-skill", "--root", str(tmp_path), "--format", "json"]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.err)
    assert result == 3
    assert payload["error"] == "confirmation_required"
    assert payload["skill"]["source_commit"] == "a" * 40
    assert "instructions" not in payload
    assert captured.out == ""


def test_read_unknown_text_reports_decision_fields(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "read_skill", needs_confirmation, raising=False)
    result = cli.main(["read", "unknown-skill", "--root", str(tmp_path)])
    captured = capsys.readouterr()
    assert result == 3
    assert "risk=unknown" in captured.err
    assert "source=fixture@" in captured.err
    assert "license=MIT" in captured.err
    assert "fixture" in captured.err


def test_read_cli_returns_one_for_blocked_skill(monkeypatch, capsys, tmp_path):
    def blocked(root, identifier, allow):
        raise SkillBlocked("hash mismatch: pdf")

    monkeypatch.setattr(cli, "read_skill", blocked, raising=False)
    assert cli.main(["read", "pdf", "--root", str(tmp_path)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "hash mismatch" in captured.err
