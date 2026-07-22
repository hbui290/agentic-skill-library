# Reviewed source admission

Admit a source only through reviewed intake: pin a public GitHub source to an
exact commit, prepare it outside the repository without running source scripts
or installing dependencies, and review every candidate before mutation. Never
use private access, credentials, or credential helpers for intake.

Each reviewed source path needs exactly one non-empty decision: `import`,
`canonical`, `quarantine`, or `reject`. Confirm source path, content hash,
license, taxonomy, duplicate evidence, and risk-sensitive content before
acceptance. Classification and duplicate signals are evidence, not automatic
approval, merging, deletion, or promotion.

Commit only from a clean worktree after validation; the reviewed snapshot must
move together. Roll back a reviewed import with `git revert`, never by manually
editing catalog or registry files.
