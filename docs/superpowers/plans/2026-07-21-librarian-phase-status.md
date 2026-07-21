# Librarian Phase Status Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the user one compact, truthful line naming the library skills actually loaded for the current task phase.

**Architecture:** The agent-facing Librarian contract emits `Librarian P<n>: <load names> (<composition>)` only after every named skill has passed a real `skill-registry read` command. The existing detailed decision trace remains available for audit; no CLI, catalog, or runtime-hook behavior changes.

**Tech Stack:** Markdown skill contract, Pytest contract tests, existing Python lock generator.

## Global Constraints

- No MCP, runtime hook, dependencies, catalog mutation, or bulk installation.
- A status never claims a skill was used or loaded without actual `search` and successful `read --format json` results in that phase.
- Status is one line, names at most eight loaded domain skills, and appears before substantive task execution.

---

### Task 1: Add a truthful compact phase-status contract

**Files:**

- Modify: `tests/contracts/test_librarian_skill.py`
- Modify: `skills/skill-librarian/SKILL.md`
- Modify: `README.md`
- Modify: `docs/evaluations/2026-07-16-librarian-scenarios.md`
- Modify: `registry/librarian-integration.lock.json` (generated)

**Interfaces:**

- Consumes: existing `skill-registry search` and `skill-registry read` commands.
- Produces: `Librarian P<n>: <loaded load names> (<composition>)` as the first user-facing status before execution.

- [x] **Step 1: Write the failing contract tests**

Add assertions requiring the exact status template, successful `read --format json` before reporting, no status on failed/no-match routing, and the phrase that it appears before substantive execution.

- [x] **Step 2: Run the focused test to verify it fails**

Run: `PYTHONPATH=pipeline uv run --extra dev python -m pytest tests/contracts/test_librarian_skill.py -q`

Expected: FAIL because the current skill has no phase-status contract.

- [x] **Step 3: Add the minimal contract and docs**

In the Librarian workflow, require the one-line status after each named skill read exits `0` and before execution. Keep the detailed trace after it. Document that no-match or failed reads say no library skill was used, rather than falsely naming a selection.

- [x] **Step 4: Regenerate the integration lock**

Run: `PYTHONPATH=pipeline uv run --extra dev python tools/generate_librarian_integration_lock.py --root .`

- [x] **Step 5: Run focused and full verification**

Run:

```bash
PYTHONPATH=pipeline uv run --extra dev python -m pytest tests/contracts/test_librarian_skill.py -q
PYTHONPATH=pipeline uv run --extra dev python -m pytest -q
PYTHONPATH=pipeline uv run --extra dev python -m skill_registry.cli verify --strict
git diff --check
```

Expected: all commands return `0`; strict verifier reports `result=pass failed=0`.

- [ ] **Step 6: Commit and ship through CI**

Commit message: `docs: show concise librarian phase status`.

Push the feature branch, open a PR, wait for CI, merge only after all required checks succeed, then reinstall the native skill from the merged commit and verify its hash against the integration lock.
