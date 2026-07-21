# Librarian Evidence Contract Design

## Decision

Keep the V1 architecture: no MCP server, runtime hook, custom agent runtime,
vector store, persona framework, or catalog bulk installation. Strengthen the
agent-facing Librarian contract so its short status and detailed trace are
truthful only when backed by the current phase's CLI tool results.

## Problem

`skill-registry` verifies state, containment, symlinks, and content hashes when
called. A Markdown skill cannot technically force Codex to call a command,
however. The previous YouTube task claimed to use the Librarian without an
actual `search` or `read` tool call. The current phase-status line improves
visibility but needs a precise evidence and failure contract.

## Alternatives considered

1. **Prompt-only status.** Keep the present one-line status without additional
   evidence rules. Cheap, but permits a false claim. Rejected.
2. **Evidence contract (selected).** Require real current-phase command output
   before any claim; specify no-match and CLI-failure responses; test the
   contract and routing scenarios. It materially reduces false claims while
   preserving the V1 boundary.
3. **Runtime enforcement.** Add a hook, MCP wrapper, or custom agent runtime
   that blocks task execution until a receipt exists. This could enforce calls,
   but is a new product/runtime layer and is explicitly out of scope.

## Contract

### Evidence

- `search` evidence is the actual successful output of
  `skill-registry search --format json` in the current phase.
- A skill may appear in `Librarian P<n>` or `Selected` only after its own
  `skill-registry read --format json` completes with exit `0` in that phase.
- The detailed trace contains receipt summaries only: `Evidence: search=exit 0;
  reads=<skill-id: exit 0, ...>`. Actual tool output exists in the tool
  transcript; it is never copied into the trace.
- An agent must never say it used, selected, loaded, or applied a library skill
  if those command results do not exist. It may say it did not use the library.

### User-visible results

| Situation | Required concise status | Detailed policy |
| --- | --- | --- |
| One or more reads succeed | `Librarian P<n>: <loaded load names> (<composition>)` | `read` |
| Two useful searches find no candidate | `Librarian: no library skill used` | `no-match` |
| Search command fails | `Librarian: unavailable (CLI exit <code>)` | `unavailable`; `Evidence: search=exit <code>; stderr=<sanitized first stderr line>; reads=none` |
| All selected reads fail | `Librarian: no library skill used` | `blocked`; include the failed skill IDs and exit codes in the trace |

The status appears before substantive execution. It never exposes skill
instructions, credentials, or an arbitrary full stderr dump.

### Routing wording

The frontmatter trigger becomes: a request names a **specialized deliverable or
non-routine domain guidance need**. Merely naming a tool or service remains
insufficient. This removes the current contradiction between metadata and the
body rule.

### Quota and scope

The official wording is: **one to eight domain skills concurrently per phase;
prefer one to five**. A task may call the Librarian again for later phases.
Update the stale migration guide. Official Superpowers remains a separate
process layer and does not count toward this quota.

## Test strategy

- Contract tests require the exact statuses, evidence field, successful-read
  precondition, sanitized CLI-failure rule, and no-false-claim rule.
- Scenario fixtures cover: explicit request, specialized file format,
  tool-name-only request, direct edit, multi-domain task, no-match, and CLI
  failure.
- Existing full pytest and `verify --strict` must pass. Tests validate the
  repository contract; they cannot prove future Codex model compliance.

## Non-goals

- No runtime hook or tool wrapper.
- No MCP, telemetry, task database, hosted service, or automatic execution of
  catalog scripts.
- No claim that Markdown alone enforces tool use.

## Acceptance criteria

1. The Librarian never has a permitted wording path to claim a loaded skill
   without a current-phase search result and `read` exit `0`.
2. A CLI failure is distinguishable from no-match and cannot be silently
   replaced by a generic claim that the registry is broken.
3. Trigger wording is internally consistent and all seven routing scenarios
   are documented and contract-tested.
4. The migration guide uses the live 1–8, prefer 1–5 quota.
5. Full tests and strict verifier pass without new runtime dependencies.
