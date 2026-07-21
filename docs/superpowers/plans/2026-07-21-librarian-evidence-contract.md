# Librarian Evidence Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Librarian phase names a library skill only after current-phase CLI output proves it was loaded.

**Architecture:** Markdown contract plus static Pytest guards; no new runtime. The integration lock changes only because it hashes the installable Librarian file.

**Tech Stack:** Markdown, PyYAML, Pytest, existing stdlib lock generator.

## Global Constraints

- Python 3.11+; no new dependency.
- No MCP, hook, wrapper, telemetry, database, persona framework, or bulk installer.
- Do not say Markdown technically enforces Codex tool use.
- Status names require current-phase JSON search and each named JSON read exit `0`.
- CLI errors show only exit code plus sanitized first stderr line.
- Quota: 1–8 concurrent domain skills per phase; prefer 1–5.

---

### Task 1: Contract tests and routing scenarios

**Files:**
- Modify: `tests/contracts/test_librarian_skill.py`
- Modify: `docs/evaluations/2026-07-16-librarian-scenarios.md`

**Interfaces:** Consumes `_skill(repo_root)`; produces evidence/fallback and scenario contract coverage.

- [x] **Step 1: Write a failing evidence test**

Add:

```python
def test_librarian_requires_current_phase_cli_evidence(repo_root):
    _, body = _skill(repo_root)
    required = [
        "actual successful output of skill-registry search --format json in the current phase",
        "individual skill-registry read --format json command that exits 0 in the current phase",
        "Evidence: search=exit 0; reads=<skill-id: exit 0, ...>",
        "Librarian: unavailable (CLI exit <code>)",
        "sanitized first stderr line",
        "Never claim to use, select, load, or apply a library skill without those current-phase command results",
    ]
    assert all(item in body for item in required)
```

Add one test that requires scenario headings 8–14: Explicit Librarian request, Specialized file format, Tool name only, Direct edit, Multi-domain task, No match, CLI failure.

- [x] **Step 2: Prove RED**

Run `PYTHONPATH=pipeline uv run --extra dev python -m pytest tests/contracts/test_librarian_skill.py -q`.

Expected: FAIL because evidence wording and scenario headings are absent.

- [x] **Step 3: Append routing scenarios**

Document the seven outcomes: explicit request searches/reads; specialized file format invokes; tool name only skips absent a specialized need; direct edit skips; multi-domain composes per phase; no match retries once then reports no library skill; CLI failure reports unavailable plus sanitized trace.

### Task 2: Evidence and fallback contract

**Files:**
- Modify: `skills/skill-librarian/SKILL.md`
- Modify: `registry/librarian-integration.lock.json` (generated)
- Test: `tests/contracts/test_librarian_skill.py`

**Interfaces:** Consumes JSON `search`/`read` command results; produces truthful status and trace fields.

- [x] **Step 1: Correct frontmatter trigger**

Replace `name a specialized domain/tool/deliverable` with `name a specialized deliverable or non-routine domain guidance need`. Keep the body rule that a tool/service name alone is insufficient.

- [x] **Step 2: Add evidence preconditions**

Add these exact lines after search/read workflow steps:

```markdown
Treat the actual successful output of skill-registry search --format json in the current phase as search evidence. Do not invent candidates or say the registry is unavailable without a command result.

Name a skill in `Librarian P<n>` or `Selected` only after the actual successful output of skill-registry search --format json in the current phase and an individual skill-registry read --format json command that exits 0 in the current phase.
```

- [x] **Step 3: Add fallback and trace rules**

Add:

```markdown
If the search command fails, do not treat it as a no-match. Before task execution report `Librarian: unavailable (CLI exit <code>)`; trace only the sanitized first stderr line and set `Policy: unavailable`.

If every selected read fails, report `Librarian: no library skill used`; set `Policy: blocked` and list only skill IDs plus exit codes in the trace.

Never claim to use, select, load, or apply a library skill without those current-phase command results.
```

Add trace field: `Evidence: search=exit 0; reads=<skill-id: exit 0, ...>`.
For `Policy: unavailable`, use only `Evidence: search=exit <code>;
stderr=<sanitized first stderr line>; reads=none`; never raw tool output.

- [x] **Step 4: Regenerate lock and prove GREEN**

Run:

```bash
PYTHONPATH=pipeline uv run --extra dev python tools/generate_librarian_integration_lock.py --root .
PYTHONPATH=pipeline uv run --extra dev python -m pytest tests/contracts/test_librarian_skill.py -q
```

Expected: focused tests pass and only the SKILL hash changes in the lock.

### Task 3: Public docs, full gates, PR

**Files:**
- Modify: `README.md`
- Modify: `docs/migration-from-agentic-library.md`
- Create: `docs/superpowers/plans/2026-07-21-librarian-evidence-contract.md`

**Interfaces:** Consumes Task 2; produces accurate public docs and reviewed PR.

- [x] **Step 1: Align docs**

Migration guide replaces `1–5 domain playbooks per phase` with `one to eight domain playbooks concurrently per phase, preferring one to five for the main agent`.

README Visible routing gains: `It does not claim a skill was used if the phase has no successful registry search and read results.`

- [x] **Step 2: Run gates**

Run:

```bash
PYTHONPATH=pipeline uv run --extra dev python -m pytest -q
PYTHONPATH=pipeline uv run --extra dev python -m skill_registry.cli verify --strict
git diff --check
```

Expected: full suite passes, verifier says `result=pass failed=0`, and no whitespace errors.

- [ ] **Step 3: Review and publish**

Reject changes adding hook/MCP/dependency, claiming technical enforcement, or exposing unsanitized stderr/instructions. Then:

```bash
git add README.md docs/evaluations/2026-07-16-librarian-scenarios.md docs/migration-from-agentic-library.md docs/superpowers/specs/2026-07-21-librarian-evidence-contract-design.md registry/librarian-integration.lock.json skills/skill-librarian/SKILL.md tests/contracts/test_librarian_skill.py docs/superpowers/plans/2026-07-21-librarian-evidence-contract.md
git commit -m "docs: require librarian evidence traces"
git push -u origin feat/librarian-evidence-contract
gh pr create --draft --base main --head feat/librarian-evidence-contract --title "Require evidence for Librarian routing claims"
```

- [ ] **Step 4: CI and native rollout**

Require `strict-verifier` plus tests on Python 3.11–3.14. After merge, reinstall native Librarian from the merge commit and compare its SHA-256 with `registry/librarian-integration.lock.json`.

## Plan self-review

- Evidence, fallbacks, trigger consistency, seven scenarios, quota docs, gates, CI, and rollout are covered.
- No placeholders or ambiguous status variants remain.
- Statuses are only `Librarian P<n>`, `Librarian: no library skill used`, or `Librarian: unavailable (CLI exit <code>)`; quota is consistently 1–8, prefer 1–5.
