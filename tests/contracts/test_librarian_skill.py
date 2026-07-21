from pathlib import Path

import yaml


def _skill(repo_root: Path) -> tuple[dict[str, object], str]:
    path = repo_root / "skills/skill-librarian/SKILL.md"
    content = path.read_text(encoding="utf-8")
    _, frontmatter, body = content.split("---", 2)
    return yaml.safe_load(frontmatter), body


def test_only_librarian_is_native(repo_root):
    skill_dirs = sorted(path.name for path in (repo_root / "skills").iterdir() if path.is_dir())
    assert skill_dirs == ["skill-librarian"]


def test_librarian_contract(repo_root):
    metadata, body = _skill(repo_root)
    normalized_body = " ".join(body.split())
    assert metadata["name"] == "skill-librarian"
    assert "specialized" in metadata["description"].lower()
    for trigger in (
        "complex",
        "unfamiliar",
        "multi-part",
        "explicitly ask for a skill or playbook",
        "specialized domain/tool/deliverable",
        "unfamiliar domain guidance",
        "two or more independent domains",
        "skip routine work",
    ):
        assert trigger in metadata["description"].lower()

    required = [
        "AGENTIC_SKILL_REGISTRY_ROOT",
        "skill-registry search",
        "skill-registry read",
        "2-5 keywords",
        "retry exactly once",
        "1-8 domain skills",
        "Prefer 1-5",
        "primary",
        "supporting",
        "single",
        "sequential",
        "parallel",
        "exit code 1",
        "Do not execute bundled scripts",
        "Apply an applicable Official Superpowers skill for process first",
        "Librarian decision — Phase <n>",
        "Candidates:",
        "Selected:",
        "Composition:",
        "Why:",
        "Policy:",
        "Handoff:",
        "no-match",
        "## Required trigger check",
        "Before planning or execution",
        "User explicitly asks for the Librarian",
        "more than one workstream",
        "Do not invoke it for simple general reasoning",
        "Do not invoke it merely because a request mentions a tool or service",
        "task title sounds clear",
        "then invoke Librarian in the same task phase",
        "Superpowers does not replace domain-skill discovery",
        "Do not add a runtime hook, MCP integration, or automatic router",
    ]
    for phrase in required:
        assert phrase in normalized_body


def test_librarian_forbids_unsafe_shortcuts(repo_root):
    _, body = _skill(repo_root)
    forbidden = ["superpowers-mcp", "list_skills", "mcpServers"]
    assert not any(term in body for term in forbidden)

    required = [
        "Never load the entire catalog",
        "Never load more than 8 domain skills concurrently in one phase",
        "not a limit on the total number of skills used across a multi-phase task",
        "Never bypass quarantine, path, symlink, or hash failures",
        "Do not grant credentials or broad permissions",
        "Risk labels are metadata, not an approval gate.",
    ]
    for phrase in required:
        assert phrase in body


def test_librarian_reports_a_compact_truthful_phase_status(repo_root):
    _, body = _skill(repo_root)
    normalized_body = body.lower()

    required = [
        "Librarian P<n>: <loaded load names> (<composition>)",
        "after every named skill has returned exit code 0",
        "before substantive task execution",
        "Never report a selected or loaded skill without actual search output and a successful read result in the current phase",
        "Librarian: no library skill used",
    ]
    for phrase in required:
        assert phrase.lower() in normalized_body


def test_architecture_docs_keep_catalog_out_of_native_discovery(repo_root):
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    architecture = (repo_root / "docs/architecture.md").read_text(
        encoding="utf-8"
    )
    migration = (repo_root / "docs/migration-from-agentic-library.md").read_text(
        encoding="utf-8"
    )
    assert "docs/architecture.md" in readme
    for layer in ("Process", "Routing", "Trust", "Knowledge"):
        assert layer in architecture
    for text in (readme, architecture, migration):
        assert "native-install the catalog" not in text
        assert "mcpServers" not in text
        assert "list_skills" not in text


def test_readme_documents_search_json_matches_field(repo_root):
    readme = (repo_root / "README.md").read_text(encoding="utf-8")

    assert '"matches"' in readme
