# Composition

Choose one composition: `single` when one skill covers the task, `sequential`
when an output or check feeds the next skill, or `parallel` for independent
workstreams. Never load more than 8 domain skills concurrently in one phase;
this is not a limit on the total number of skills used across a multi-phase task.
Prefer 1-5 and use 6-8 only for a genuinely multi-domain phase. Official
Superpowers process skills are separate from the domain-skill quota. Superpowers
does not replace domain-skill discovery.

For each new phase, start a new search and decision trace. A phase handoff
carries only the output and decision needed by the next phase; do not carry prior
`SKILL.md` instructions forward automatically.

For simple or clearly matched work, perform routing directly. Use a Librarian
subagent only when the task spans multiple domains or several candidates are
similarly relevant. It may search and recommend, but must not execute the user's
task, run bundled scripts, use secrets, or widen permissions.
