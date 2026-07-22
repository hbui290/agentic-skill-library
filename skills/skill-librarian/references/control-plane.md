# Control plane

Use the Registry CLI as the only discovery and loading runtime; do not inspect
or load catalog entries directly.

1. Extract 2-5 keywords for task, domain, output, and constraints.
2. Search at most ten candidates:

   ```bash
   skill-registry search --root "$REGISTRY_ROOT" --limit 10 --format json KEYWORDS...
   ```

   The actual successful output of `skill-registry search --format json` in the
   current phase is search evidence. Do not invent candidates or say the registry
   is unavailable without a command result.
3. If no useful candidate appears, retry exactly once with broader domain terms
   or synonyms. If the second search is unhelpful, continue without a library
   skill.
4. Select 1-8 domain skills for the current phase by textual relevance. Prefer
   1-5; use 6-8 only for a genuinely multi-domain phase. Mark each `primary` or
   `supporting`.
5. Read every selected skill separately:

   ```bash
   skill-registry read --root "$REGISTRY_ROOT" --format json SKILL_ID_OR_LOAD_NAME
   ```

6. On exit code 1, discard the candidate. Never suggest or attempt a bypass.

Do not name a skill in `Librarian P<n>` or `Selected` without actual successful
current-phase search output and an individual `skill-registry read --format json` command that exits 0 in the current phase. Never claim to use, select, load, or apply a library skill without those current-phase command results.
