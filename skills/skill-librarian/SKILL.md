---
name: skill-librarian
description: Use when a request is complex, unfamiliar, multi-part, explicitly asks for a skill or playbook, names a specialized deliverable or non-routine domain guidance need, requires unfamiliar domain guidance, or spans two or more independent domains. Skip routine work fully covered by an installed process, project, or domain skill.
---

# Skill Librarian

Apply an applicable Official Superpowers skill for process first; then invoke Librarian in the same task phase when triggered.

## Required trigger check

Before planning or execution, invoke Librarian when:

- specialized/unfamiliar guidance could prevent a wrong approach;
- more than one workstream, deliverable, or domain may need composition; or
- User explicitly asks for the Librarian or to find/select skills.

Do not invoke it for simple general reasoning, direct edits without specialized guidance, or work covered by a native skill. Do not invoke it merely because a request mentions a tool or service; do not skip it because the task title sounds clear.

## Registry

```bash
REGISTRY_ROOT="${AGENTIC_SKILL_REGISTRY_ROOT:-$HOME/.agents/agentic-skill-library}"
```

The registry CLI is the only discovery and loading runtime. Do not inspect or load catalog entries directly.

## Current-phase routing

Read only the minimum reference set for the current phase.

| Phase need | Reference to read |
| --- | --- |
| Every invoked phase: search, retry, select, and read | [control plane](references/control-plane.md) |
| Every invoked phase: user-visible receipt | [decision trace](references/decision-trace.md) |
| Safety metadata, action scope, or owner confirmation | [trust and safety](references/trust-and-safety.md) |
| Multiple skills/phases or a Librarian subagent | [composition](references/composition.md) |
| Admit a reviewed external source | [source intake](references/source-intake.md) |
| Pressure-test routing or release this contract | [evaluation](references/evaluation.md) |

## Hard Rules

- Never load the entire catalog or dump the whole discovery index.
- Do not execute bundled scripts automatically.
- Do not grant credentials or broad permissions to a selected skill.
- Never bypass quarantine, path, symlink, or hash failures.
- Keep official Superpowers unmodified and use it only for process guidance.
- Do not add a runtime hook, MCP integration, or automatic router; this remains an on-demand skill contract.
