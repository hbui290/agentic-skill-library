---
name: skill-librarian
description: Use when a request is complex, unfamiliar, multi-part, explicitly asks for a skill or playbook, names a specialized deliverable or non-routine domain guidance need, requires unfamiliar domain guidance, or spans two or more independent domains. Skip routine work fully covered by an installed process, project, or domain skill.
---

# Skill Librarian

Use this skill when the right domain skill is unclear, specialized knowledge is useful, or a task may need several skills. Apply an applicable Official Superpowers skill for process first; then invoke Librarian in the same task phase when one of the triggers below applies. Superpowers does not replace domain-skill discovery.

## Required trigger check

Before planning or execution, invoke the Librarian when one or more of these is
true:

- The task needs specialized or unfamiliar guidance for domain-specific
  methods, a file format, platform/tool, external service, research, security,
  or automation.
- The task has more than one workstream, deliverable, or domain and may need a
  composition of skills.
- The task is unfamiliar enough that domain guidance could prevent a wrong
  approach.
- User explicitly asks for the Librarian or asks to find/select skills.

Do not invoke it for simple general reasoning, a direct edit with no specialized
guidance, or when a more specific native skill fully covers the work. Do not
invoke it merely because a request mentions a tool or service. Do not skip it
merely because the task title sounds clear: a clear request can still need
domain guidance. Official Superpowers remains the process layer; invoke the
Librarian after that process check when a domain playbook could help.

## Registry

Use the configured local registry:

```bash
REGISTRY_ROOT="${AGENTIC_SKILL_REGISTRY_ROOT:-$HOME/.agents/agentic-skill-library}"
```

The registry CLI is the only discovery and loading runtime. Do not inspect or load catalog entries directly.

## Workflow

1. Extract 2-5 keywords that describe the task, domain, output, and important constraints.
2. Search for at most ten candidates:

   ```bash
   skill-registry search --root "$REGISTRY_ROOT" --limit 10 --format json KEYWORDS...
   ```

   Treat the actual successful output of `skill-registry search --format json`
   in the current phase as search evidence. Do not invent candidates or say the
   registry is unavailable without a command result.

3. If no useful candidate appears, retry exactly once with broader domain terms or synonyms. If the second search is also unhelpful, continue the task without a library skill.
4. Select 1-8 domain skills for the current phase based on textual relevance. Prefer 1-5; use 6-8 only when the phase is genuinely multi-domain. Mark each as `primary` or `supporting`.
5. Choose one composition:
   - `single`: one skill covers the task.
   - `sequential`: outputs or checks from one skill feed the next.
   - `parallel`: independent workstreams can use different skills.
6. Read every selected skill separately:

   ```bash
   skill-registry read --root "$REGISTRY_ROOT" --format json SKILL_ID_OR_LOAD_NAME
   ```

7. On exit code 1, discard the candidate. Never suggest or attempt a bypass.
8. Name a skill in `Librarian P<n>` or `Selected` only after the actual
   successful output of `skill-registry search --format json` in the current
   phase and an individual `skill-registry read --format json` command that
   exits 0 in the current phase. Before substantive task execution, show one
   compact user-facing line:

   ```text
   Librarian P<n>: <loaded load names> (<composition>)
   ```

   If no skill is loaded after the search and read attempts, show:

   ```text
   Librarian: no library skill used
   ```

   If the search command fails, do not treat it as a no-match. Before task
   execution report `Librarian: unavailable (CLI exit <code>)`; trace only the
   sanitized first stderr line and set `Policy: unavailable`. For `Policy:
   unavailable`, do not use the standard Evidence placeholder. Use:

   ```text
   Evidence: search=exit <code>; stderr=<sanitized first stderr line>; reads=none
   ```

   If every selected read fails, report `Librarian: no library skill used`; set
   `Policy: blocked` and list only skill IDs plus exit codes in the trace.

   Never claim to use, select, load, or apply a library skill without those
   current-phase command results.
9. Return a decision trace and short composition plan to the main agent.

## Decision Trace

Return this concise trace for every search and composition decision:

```text
Librarian decision — Phase <n>

Query: <2-5 normalized terms>
Candidates: <top relevant candidates>
Selected: <primary/supporting skills>
Composition: single | sequential | parallel
Why: <one reason per selection>
Policy: <read | blocked>
Evidence: search=exit 0; reads=<skill-id: exit 0, ...>
Handoff: <output passed to the next phase, or none>
```

Evidence is a receipt summary, never raw tool output. Do not repeat search
JSON, read JSON, or skill instructions in a trace.

If two searches produce no useful candidate, return the same trace with
`Policy: no-match` and `Evidence: search=exit 0; retry=exit 0; reads=none`,
then let the main agent continue without a library skill.

For a multi-phase task, start a new search and trace for each new phase. A
phase handoff carries only the output and decision needed by the next phase;
do not carry prior `SKILL.md` instructions forward automatically. Official
Superpowers process skills are separate from the domain-skill quota.

## Optional Librarian Subagent

For a simple or clearly matched request, perform the workflow directly. A Librarian subagent may be used only when the task spans multiple domains or several candidates are similarly relevant. The subagent may search and recommend; it must not execute the user's task, run bundled scripts, use secrets, or widen permissions.

## Hard Rules

- Never load more than 8 domain skills concurrently in one phase; this is not a limit on the total number of skills used across a multi-phase task. Prefer 1-5 and use 6-8 only for a genuinely multi-domain phase.
- Never load the entire catalog or dump the whole discovery index.
- Do not execute bundled scripts automatically.
- Do not grant credentials or broad permissions to a selected skill.
- Risk labels are metadata, not an approval gate.
- Never bypass quarantine, path, symlink, or hash failures.
- Keep official Superpowers unmodified and use it only for process guidance.
- Do not add a runtime hook, MCP integration, or automatic router; this remains
  an on-demand skill contract.
