# Stabilized Multi-Source Skill Library

## Context

The repository already provides a local on-demand Librarian runtime over 1,952 active registry records. It searches compact metadata, selects one to five skills, applies state/risk/path/hash policy, and reads only the selected `SKILL.md`. The catalog is not installed into Codex and official Superpowers remains separate.

The current runtime has three trust-boundary gaps that must be closed before adding another source:

1. confirmation exit `3` does not provide enough provenance for an informed decision;
2. `refresh` still queries a deleted legacy repository and fails before reporting healthy sources;
3. the verifier does not bind each record's `source_commit` and stable ID to its locked source.

After stabilization, the product must accept additional pinned GitHub repositories without becoming a bulk installer, hosted marketplace, MCP server, or semantic-search service.

## Product Goal

Build a local, source-aware library in which outside repositories provide the books and this repository provides the operating system for those books:

```text
Pinned sources
→ prepare candidates
→ normalize metadata
→ propose classification
→ detect duplicates
→ human review
→ commit registry snapshot
→ Librarian search
→ select and compose 1–5 skills
→ policy-gated on-demand read
```

Completion means a second source can be imported through this flow while existing search/read behavior remains deterministic and the full catalog never enters agent context.

## Scope Decomposition

Work is split into two independently reviewable plans.

### Plan A — Runtime Stabilization

Plan A closes current trust-boundary defects and adds continuous verification. It changes no catalog skill content and adds no source.

### Plan B — Multi-Source Intake

Plan B begins only after Plan A passes. It adds a staged, review-gated intake path for pinned public GitHub repositories and pilots one explicitly selected skill from a pinned source containing no more than 250 candidates.

## Authoritative Data

- `registry/skills.json` is authoritative for identity, state, risk, provenance, path, canonical relationships, and content hash.
- `registry/sources.lock.json` is authoritative for source lifecycle, URL, layout, pinned commit, and refresh behavior.
- `registry/core.json` is the audited allow-list.
- `registry/quarantine.json` is authoritative for blocked catalog bundles.
- `librarian-index.json` contains discovery text and proposed taxonomy only. It is never authoritative for risk, provenance, state, or hash.
- The catalog contains pinned snapshots. It is not an installation target and is never loaded wholesale.

## Plan A Design

### Structured confirmation

`SkillConfirmationRequired` carries a machine-readable payload. For `--format json`, exit `3` writes this object to stderr:

```json
{
  "error": "confirmation_required",
  "skill": {
    "skill_id": "asr_7d7e8d9a0b1c2d3e",
    "load_name": "example-skill",
    "risk": "unknown",
    "risk_reasons": ["initial-review-required"],
    "source_id": "example-source",
    "source_commit": "0123456789abcdef0123456789abcdef01234567",
    "source_path": "skills/example-skill",
    "license": "MIT",
    "content_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    "core": false
  }
}
```

The payload never contains `instructions`. Text mode remains concise but reports source, commit, license, and risk reasons. `--allow-unreviewed` continues to open only `unknown` and `review`; it never overrides dangerous, quarantine, state, path, symlink, or hash failures.

### Source lifecycle and refresh

Every source lock entry has:

```json
{
  "status": "active|retired",
  "refreshable": true,
  "timeout_seconds": 15
}
```

The deleted legacy source remains locked for provenance with `status: retired` and `refreshable: false`. Refresh reports it as `retired` without network access. Active refreshable sources are checked independently. One failed source produces an `error` record but does not suppress other source results. The CLI returns exit `1` when any active source errors and still emits the complete report.

### Provenance verification

For every active and quarantined record, the verifier requires:

- source exists in `sources.lock.json`;
- `record.source_commit == locked_source.commit`;
- `record.skill_id == stable_skill_id(record.source_id, record.source_path)`;
- `(source_id, source_path)` is unique across active and quarantine records;
- source path is relative, normalized, and contains no `..` segment;
- source lifecycle fields are valid.

The two existing legacy quarantine records first receive the exact historical
source paths that reproduce their current stable IDs. No ID or catalog path is
rewritten during this reconciliation.

### CI

GitHub Actions runs tests on Python 3.11, 3.12, and 3.13. Python 3.11 also runs strict verification and `git diff --check`. No new runtime dependency is introduced.

## Plan B Design

### Supported source type

Version one intake supports public GitHub repositories pinned to an exact 40-character commit SHA. It does not support private repositories, credentials, floating branches, arbitrary archive URLs, GitLab, or `.well-known` discovery. Those formats can be added only after a real source requires them.

The CLI exposes two explicit phases:

```bash
skill-registry prepare-source --root PATH --source-id SOURCE --url URL --commit SHA --skills-root DIR --license SPDX --license-note NOTE --staging PATH
skill-registry commit-source --root PATH --manifest PATH --review PATH
```

Preparation is read-only with respect to catalog and registry. Commit is impossible until every candidate has a valid human review decision.

### Prepare phase

Preparation:

1. validates a canonical GitHub HTTPS URL, source ID, exact commit, literal safe-segment skills root with no glob/pathspec syntax, and SPDX/license evidence;
2. preflights the selected subtree through GitHub's unauthenticated tree API and rejects truncated trees, more than 10,000 blobs, or more than 250 MiB declared blob bytes;
3. performs a cone-mode sparse exact-commit checkout with Git prompts, credential helpers, system Git config/attributes, and LFS smudge downloads disabled;
4. finds candidate directories containing a root `SKILL.md`;
5. rejects path escape, symlink, and hardlink content;
6. enforces at most 1,000 files and 50 MiB unpacked content per bundle;
7. parses frontmatter and requires non-empty `name` and `description`;
8. computes the existing `tree_sha256` over unmodified upstream content;
9. proposes taxonomy/category from deterministic token overlap with the existing discovery index;
10. detects exact hash duplicates, source/path identity, name collisions, and high textual similarity;
11. writes a deterministic manifest plus a review template containing SHA-256 of the exact manifest bytes.

Preparation does not copy into `catalog/`, mutate registry JSON, run bundled scripts, install dependencies, or mark anything safe.

### Deduplication policy

Deduplication produces evidence, not automatic deletion:

| Signal | Automated result |
| --- | --- |
| Same source ID and source path | Treat as existing identity/update candidate |
| Same tree hash | Mark exact duplicate candidate |
| Same normalized name/load name | Mark collision candidate |
| Textual similarity above threshold | Mark functional-review candidate |
| No duplicate evidence | Mark new candidate |

Only a human review can choose `import`, `canonical`, `quarantine`, or `reject`. `canonical` requires an existing valid canonical skill ID. Similarity never automatically merges, deletes, blocks, or promotes a skill.

### Classification policy

Classification is a proposal. The prepare phase aggregates token overlap against current `librarian-index.json` entries by `(taxonomy, category_fine)`. A zero-score candidate falls back to `uncategorized-and-misc`. The review file must explicitly accept or override taxonomy and category before commit.

### Review contract

Every candidate review contains:

```json
{
  "source_path": "skills/example",
  "decision": "import|canonical|quarantine|reject",
  "taxonomy": "engineering/testing",
  "category_fine": "testing",
  "canonical_skill_id": null,
  "reason": "human-readable decision rationale"
}
```

The review document also contains `manifest_sha256`. Pending, duplicated,
missing, extra, or manifest-digest-mismatched review entries block commit.

### Commit phase

Commit phase:

1. verifies the review's manifest digest before any mutation;
2. requires a clean Git worktree and validates review completeness;
3. repeats the source preflight and sparse exact-commit checkout;
4. re-discovers candidates and recomputes hashes to prevent TOCTOU;
5. aborts if any reviewed candidate changed or disappeared;
6. slugifies new load names and derives the destination exactly as `catalog/<taxonomy-segment-1>/<taxonomy-segment-2>/<load_name>`;
7. rejects catalog-root escape, symlinked parents, duplicate destinations, and existing targets before copying accepted bundles without modifying upstream bytes;
8. stores URL/license evidence once in the source lock while retaining per-skill license fields;
9. updates source lock, skills/quarantine records, and discovery index;
10. preserves registry schema version 1, writes JSON atomically, and rolls back newly created catalog directories on failure;
11. runs strict repository verification before reporting success.

Imported records start with `risk: unknown`, `risk_reasons: ["initial-review-required"]`, and are excluded from Core. Exact duplicates may be retained as canonical-linked provenance records but are excluded from search by existing runtime policy.

## Librarian Boundary

Multi-source intake does not change the Librarian contract:

- search metadata only;
- select at most five skills;
- assign primary/supporting roles;
- choose single, sequential, or parallel composition;
- call policy-gated `read` separately for each selection;
- ask before reading unknown/review skills;
- never run bundled scripts or grant credentials automatically.

## Error Handling

- Invalid source/review/manifest: exit `1`, no mutation.
- Network or pinned-commit failure during prepare: exit `1`, no staging manifest advertised as complete.
- TOCTOU mismatch during commit: exit `1`, no registry mutation.
- Duplicate or similarity evidence: successful prepare with review required.
- Strict verifier failure after tentative commit: rollback created catalog paths and restore original JSON bytes.
- No valid candidates: successful prepare with an empty candidate list; do not create a source record.

## Verification

### Plan A gate

```bash
git diff --check
PYTHONPATH=pipeline python -m pytest -q
PYTHONPATH=pipeline python -m skill_registry.cli verify --strict
PYTHONPATH=pipeline python -m skill_registry.cli refresh --format json
```

Required results:

- tests pass on Python 3.11–3.13;
- strict verifier returns `result=pass failed=0`;
- legacy source reports `retired` without network access;
- healthy active sources still report after another source errors;
- unknown read exits `3` with complete metadata and no instructions.

### Plan B gate

A fixture source plus one pinned public pilot containing at most 250 candidates must prove:

- prepare is deterministic and does not mutate catalog/registry;
- invalid URL/commit/path/symlink/size/license is blocked;
- exact duplicate, collision, similarity, and new candidate paths are covered;
- commit requires complete review;
- re-fetch mismatch blocks commit;
- accepted bundles preserve upstream bytes;
- all imported records remain unknown and outside Core;
- search can discover the new source while read policy remains unchanged;
- full tests and strict verifier pass.

## Completion Criteria

The product goal is complete when:

1. Plan A is merged and its CI is green;
2. Plan B imports one additional pinned source through prepare/review/commit;
3. registry and catalog remain fully reconcilable;
4. Librarian finds at least one imported skill in fixed-query acceptance;
5. only selected skill instructions enter context;
6. no imported skill is silently trusted, installed, or executed.

## Stop Conditions

Stop and do not broaden scope when:

- Plan A tests, CI, or strict verifier fail;
- source lock and registry provenance cannot be reconciled;
- a source is not public, license evidence is missing, or commit is not pinned;
- path, symlink, size, hash, or TOCTOU verification fails;
- review is incomplete or requests an invalid canonical target;
- the first real source cannot be imported without adding credentials or broad permissions;
- Plan B acceptance passes: do not continue into MCP, embeddings, database, marketplace, GUI, telemetry, automatic Core promotion, or background synchronization.

## Explicit Non-Goals

- Bulk installation of catalog skills.
- Automatic execution of scripts or dependencies.
- Automatic safety classification or Core promotion.
- Hosted search, marketplace, accounts, ratings, or monetization.
- MCP server or Superpowers fork.
- Embeddings or vector database.
- Private source authentication.
- Background auto-import or auto-update.
