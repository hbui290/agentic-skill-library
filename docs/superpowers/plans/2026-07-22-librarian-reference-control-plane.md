# Librarian Reference Control Plane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` for inline execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the native Librarian into a compact router with integrity-locked, just-in-time reference contracts.

**Architecture:** Keep `SKILL.md` as the always-loaded trigger, routing table, and non-negotiable boundaries. Move detailed operational guidance into six focused Markdown references. Extend the existing integration lock so every regular file in the native skill bundle, including references, is hash-verified by strict validation.

**Tech Stack:** Python 3.11, pytest, Markdown, existing registry integration validator.

## Global Constraints

- Preserve the on-demand contract: no runtime hook, MCP router, or automatic catalog loading.
- Registry CLI remains the only discovery and loading runtime.
- Never auto-execute bundled scripts or grant credentials/permissions.
- Keep `SKILL.md` compact; detailed operational material belongs in `references/`.
- Do not add dependencies or generators solely for this refactor.
- Bump package version to `0.3.0` and native integration version to `1.1.0`.

---

## Task 1: Add failing contracts for reference routing and bundle integrity

**Files:**
- Modify: `tests/contracts/test_librarian_skill.py`
- Modify: `tests/contracts/test_validator.py`

- [ ] Assert the six reference files exist, are regular files, and are named by their operational scope.
- [ ] Assert the main skill contains a compact route table pointing to every reference, but does not embed reference-only detail such as the full decision-trace template.
- [ ] Add strict-verifier mutations for a changed reference, an extra reference file, and a reference symlink; each must fail `registry.librarian-integration`.
- [ ] Run the focused contracts and confirm RED against the current one-file native skill.

**Verify:**

```bash
uv run --extra dev pytest tests/contracts/test_librarian_skill.py tests/contracts/test_validator.py -q
```

## Task 2: Refactor the native skill into a compact router and six references

**Files:**
- Modify: `skills/skill-librarian/SKILL.md`
- Create: `skills/skill-librarian/references/control-plane.md`
- Create: `skills/skill-librarian/references/trust-and-safety.md`
- Create: `skills/skill-librarian/references/composition.md`
- Create: `skills/skill-librarian/references/decision-trace.md`
- Create: `skills/skill-librarian/references/source-intake.md`
- Create: `skills/skill-librarian/references/evaluation.md`

- [ ] Keep the existing frontmatter trigger semantics.
- [ ] Make `SKILL.md` state when to invoke/skip, set `REGISTRY_ROOT`, route the current phase to the minimum reference set, and preserve hard boundaries.
- [ ] Put exact search/retry/select/read behavior in `control-plane.md`.
- [ ] Put safety-profile meanings and scope/confirmation boundary in `trust-and-safety.md`.
- [ ] Put multi-phase composition, 1–8 quota, and subagent boundary in `composition.md`.
- [ ] Put the receipt templates for read, no-match, blocked, and unavailable in `decision-trace.md`.
- [ ] Put reviewed source admission only in `source-intake.md`.
- [ ] Put pressure scenarios and release checks in `evaluation.md`.

**Verify:** focused contracts turn GREEN and `wc -w skills/skill-librarian/SKILL.md` stays below 350 words.

## Task 3: Lock the complete native skill bundle

**Files:**
- Modify: `pipeline/skill_registry/integration.py`
- Modify: `registry/librarian-integration.json`
- Modify: `registry/librarian-integration.lock.json`

- [ ] Change lock construction from one file to every regular, contained file beneath `skills/skill-librarian/`, sorted by POSIX-relative path.
- [ ] Reject symlinks, missing files, non-file lock entries, and any extra/missing bundle file through the existing strict integration check.
- [ ] Preserve the manifest schema and `native_skill_path`; bump only its integration version to `1.1.0`.
- [ ] Regenerate the committed lock from `build_librarian_integration_lock` after all references exist.

**Verify:** changed, missing, symlinked, and unexpected reference files fail strict validation; the pristine repository passes.

## Task 4: Update scenario coverage and release metadata

**Files:**
- Modify: `docs/evaluations/2026-07-16-librarian-scenarios.md`
- Modify: `README.md`
- Modify: `docs/getting-started.md`
- Modify: `docs/trust-model.md`
- Modify: `pyproject.toml`

- [ ] Add scenarios for high-risk signal handling, no-match retry, CLI unavailable, blocked read, multi-phase handoff, and reference selection.
- [ ] Explain that only the router is always loaded; references are read only when the current phase needs them.
- [ ] Keep the distinction between static signal evidence and tool-level enforcement explicit.
- [ ] Bump the package to `0.3.0`.

**Verify:** documentation links resolve; contracts cover every required scenario and exact safety boundary.

## Task 5: Final verification and local native-skill refresh

- [ ] Run focused contracts, runtime tests, strict verification, compilation, and whitespace checks.
- [ ] Reinstall the local native Librarian through its documented path only after strict verification passes.
- [ ] Confirm the installed bundle hash matches the regenerated integration lock.
- [ ] Commit with `feat: add librarian reference control plane`.

**Verify:**

```bash
uv run --extra dev pytest tests/contracts/test_librarian_skill.py tests/contracts/test_validator.py tests/unit/test_runtime.py -q
uv run --extra dev skill-registry verify --root . --strict
uv run --extra dev python -m compileall -q pipeline
git diff --check
```
