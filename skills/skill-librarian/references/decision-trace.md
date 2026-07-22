# Decision trace

Before substantive task execution, return one compact phase status and receipt.
Evidence is a receipt summary, never raw tool output; do not repeat search JSON,
read JSON, or skill instructions.

## Read

```text
Librarian P<n>: <loaded load names> (<composition>)

Librarian decision — Phase <n>
Query: <2-5 normalized terms>
Candidates: <top relevant candidates>
Selected: <primary/supporting skills>
Composition: single | sequential | parallel
Why: <one reason per selection>
Policy: read
Evidence: search=exit 0; reads=<skill-id: exit 0, ...>
Handoff: <output passed to the next phase, or none>
```

## No match

After two successful searches with no useful candidate, continue without a
library skill:

```text
Librarian: no library skill used

Librarian decision — Phase <n>
Query: <2-5 normalized terms>
Candidates: none
Selected: none
Composition: single
Why: no useful candidate after one broader retry
Policy: no-match
Evidence: search=exit 0; retry=exit 0; reads=none
Handoff: none
```

## Blocked

If every selected read fails, continue without a library skill and list only
skill IDs plus exit codes:

```text
Librarian: no library skill used

Librarian decision — Phase <n>
Query: <2-5 normalized terms>
Candidates: <top relevant candidates>
Selected: none
Composition: <single | sequential | parallel>
Why: selected reads failed
Policy: blocked
Evidence: search=exit 0; reads=<skill-id: exit <code>, ...>
Handoff: none
```

## Unavailable

If search fails, it is not a no-match. Before task execution report this status,
set `Policy: unavailable`, and trace only the sanitized first stderr line. For
Policy: unavailable, do not use the standard Evidence placeholder.

```text
Librarian: unavailable (CLI exit <code>)

Librarian decision — Phase <n>
Query: <2-5 normalized terms>
Candidates: unavailable
Selected: none
Composition: single
Why: registry search failed
Policy: unavailable
Evidence: search=exit <code>; stderr=<sanitized first stderr line>; reads=none
Handoff: none
```
