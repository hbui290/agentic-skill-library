# Verified On-Demand Skill Library

**Status:** Approved product direction

**Repository:** `hbui290/agentic-skill-registry`

## Context

The registry preserves 1,952 active skill records, two quarantined records, and
one audited Core skill. It verifies provenance, content hashes, risk state,
Core admission, and upstream freshness, but its public CLI currently exposes
only `verify` and `refresh`. It therefore cannot yet perform the useful part of
the original library concept: find a small set of relevant skills and load only
those instructions on demand.

Installing the entire catalog as native Codex skills is not acceptable. It
would crowd the native discovery list, weaken selection quality, and make
unreviewed skills appear more trustworthy than they are. The official Obra or
OpenAI distribution of Superpowers remains stock and is not modified to carry
or route this catalog.

## Product Statement

The product is a local, verified skill library with one installable Librarian
skill. The Librarian searches the registry when the main agent needs specialized
guidance, selects one to five candidates, passes each candidate through a
deterministic policy and integrity gate, and loads only the approved `SKILL.md`
instructions.

Superpowers supplies process skills such as brainstorming, planning, TDD,
debugging, and verification. The registry supplies domain playbooks. They may
be used together, but neither is forked or embedded into the other.

## Architecture

```text
User request
    -> Main agent
    -> Official Superpowers process skill, when applicable
    -> Librarian, when specialized or multi-domain guidance is needed
    -> skill-registry search
    -> 1-10 compact candidates
    -> Librarian selects 1-5
    -> policy + path + content-hash gate per candidate
    -> skill-registry read
    -> main agent executes selected instructions
```

The Librarian performs semantic judgment. Python performs deterministic search,
path containment, risk policy, and hash verification. Full skill instructions
enter context only after selection and approval.

## Runtime Interfaces

Version one adds exactly two commands:

```bash
skill-registry search --root PATH --format json QUERY...
skill-registry read --root PATH --format json SKILL_ID_OR_LOAD_NAME
```

`search` joins `registry/skills.json` with discovery metadata from
`librarian-index.json` by the stable `load_name`/`flat_name` key. Registry risk,
state, path, hash, provenance, and Core membership remain authoritative; legacy
index risk and hash values are never trusted.

`read` returns metadata and the selected `SKILL.md`. It never executes scripts,
installs dependencies, grants tools, or supplies credentials.

## Selection and Composition

The Librarian may select one to five skills and returns one composition mode:

- `single`: one skill is sufficient;
- `sequential`: later skills depend on earlier outputs;
- `parallel`: independent skills may be applied concurrently.

The default path stays in the main agent. A Librarian subagent is optional only
for ambiguous or multi-domain requests; it is not spawned for every task.

## Safety Policy

| Condition | Search | Read |
| --- | --- | --- |
| Active and `safe` | Recommend | Allow |
| Core | Prefer after textual relevance | Allow |
| Active and `unknown` or `review` | Show warning | Require explicit user confirmation |
| `dangerous` | Do not recommend | Block |
| Quarantine | Do not recommend | Block |
| Hash mismatch | N/A | Block |
| Missing registry record | N/A | Block |
| Path outside `catalog/` | N/A | Block |

Search ranking may prefer Core and safe records only after textual relevance is
positive. Safety status must never make an unrelated skill rank as a match.

## Superpowers Boundary

- Use only the official Obra repository or OpenAI-curated Superpowers plugin.
- Do not modify `using-superpowers`.
- Do not install or depend on third-party `superpowers-mcp` packages.
- Keep process skills higher priority than loaded domain playbooks.
- The Librarian is owned and versioned by this repository.

## MCP Decision

MCP is not part of version one. Local Codex and terminal-capable agents can call
the CLI and read its output without another process or protocol.

A first-party MCP adapter may be considered only when a verified client cannot
use local CLI/filesystem access. If added, it must delegate to the same runtime
functions and must not duplicate search or policy logic.

## Version-One Scope

Included:

- deterministic taxonomy/name/description search;
- secure on-demand read;
- one Librarian skill;
- one-to-five skill composition guidance;
- JSON and human-readable CLI output;
- unit, contract, integration, and fixed-query acceptance tests;
- README installation and operating guidance.

Excluded:

- MCP;
- embeddings or a vector database;
- hosted search;
- GUI or marketplace;
- bulk installation;
- automatic script execution;
- automatic upstream import or risk promotion;
- changes to the official Superpowers plugin.

## Completion Criteria

Version one is complete when:

1. `search` returns relevant active candidates without reading every full
   `SKILL.md` into agent context.
2. `read` allows safe records, requires confirmation for unreviewed records,
   and blocks dangerous, quarantined, escaped, missing, or modified records.
3. The Librarian can describe and load one to five skills with `single`,
   `sequential`, or `parallel` composition.
4. The catalog is not installed as native Codex skills.
5. Search and read work offline after the repository is cloned and installed.
6. Existing strict verification and all new tests pass.

## Stop Conditions

- If no suitable candidate is found, return `no suitable verified skill` and
  continue without a library skill.
- If user confirmation is required, stop before loading the instructions.
- If path, state, quarantine, or hash checks fail, block the candidate without
  an override.
- Once version-one completion criteria pass, stop development. Do not add MCP,
  embeddings, a plugin wrapper, or hosted infrastructure without a concrete
  failed client requirement.
