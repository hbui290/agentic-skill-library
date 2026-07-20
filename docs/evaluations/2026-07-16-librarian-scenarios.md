# Librarian manual scenario review

Reviewed against the local registry on 2026-07-16. These are selection and
policy transcripts, not executions of bundled skill scripts.

## 1. Single skill

- Request: work with a PDF.
- Search: `pdf`.
- Selection: `pdf` as `primary`; composition `single`.
- Read result: exit code `3` because the candidate is `unknown`.
- Outcome: stop before loading instructions and ask for confirmation. No second
  skill is added merely because it has a safer status.

## 2. Sequential skills

- Request: audit a repository, then write technical documentation from the
  findings.
- Search concepts: `security audit` and `technical documentation`.
- Selection: one audit skill as `primary`, then `docs-architect` as
  `supporting`; composition `sequential`.
- Outcome: policy-check each candidate separately. The documentation step only
  receives the audit output after both selected skills pass their read gates.

## 3. Parallel skills

- Request: obtain a YouTube transcript and independently prepare a spreadsheet
  summary layout.
- Search concepts: `youtube transcript` and `spreadsheet`.
- Selection: `youtube-transcript` and one spreadsheet candidate, with one
  `primary` per workstream; composition `parallel`.
- Outcome: both reads require their own policy decision. Neither selected skill
  executes the other skill or receives credentials.

## 4. Unreviewed candidate

- Candidate: `youtube-transcript`.
- Read result: exit code `3`; stdout contains zero bytes and stderr reports
  confirmation required.
- Outcome: instructions stay unloaded. `--allow-unreviewed` is permitted only
  for this candidate after explicit user approval.

## 5. Integrity failure

- Scenario: selected skill tree differs from its registered hash.
- Verified by: `test_read_blocks_symlink_and_hash_mismatch`.
- Outcome: exit code `1`; discard the candidate. The Librarian contract forbids
  suggesting or attempting a bypass.

## 6. No candidate

- Search: `qzxvplmno nonexistentdomain`.
- Result: zero matches with successful search status.
- Outcome: retry once with meaningful broader terms if available, then continue
  without a library skill. Do not dump or scan the entire catalog.

## Review conclusion

## Scenario 7 — Multi-phase task

- Scenario: audit an API, implement a remediation, then document and release it.
- Phase 1 decision: query `api security audit`; select two primary/supporting
  audit skills with `sequential` composition. Handoff: prioritized findings and
  acceptance criteria.
- Phase 2 decision: query `implementation tests remediation`; select three
  primary/supporting implementation skills with `sequential` composition.
  Handoff: tested patch and verification results.
- Phase 3 decision: query `technical documentation release`; select two
  primary/supporting documentation/release skills with `parallel` composition.
  Handoff: published-ready documentation and release checklist.
- Outcome: seven domain skills are used across the task, while every phase loads
  no more than three. Each decision records Query, Candidates, Selected,
  Composition, Why, Policy, and Handoff. No prior `SKILL.md` is automatically
  carried into the next phase.

Every scenario loads no more than five domain skills concurrently in one phase,
assigns a role and composition, loads only through `skill-registry read`, and
never automatically runs bundled scripts. Official Superpowers process guidance
remains higher priority than a selected domain playbook and does not count
against the domain-skill quota.
