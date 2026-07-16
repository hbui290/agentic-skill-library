# Task 2 Report: Explicit source lifecycle and resilient refresh

## Scope

- Implemented only the assigned refresh behavior in `pipeline/skill_registry/refresh.py` and `pipeline/skill_registry/cli.py`.
- Updated lifecycle fields in `registry/sources.lock.json` without changing source URLs, commits, layouts, metadata paths, or license notes.
- Added the assigned unit and integration coverage.

## TDD evidence

### RED: lifecycle-aware refresh

Command:

```bash
PYTHONPATH=pipeline /tmp/asr-runtime-venv/bin/python -m pytest tests/unit/test_refresh.py -q
```

Result: `4 failed in 0.03s`.

The failures proved the prior behavior did not pass `timeout=15`, raised on an invalid remote response, queried retired sources, and stopped at the first source error.

### GREEN: lifecycle-aware refresh

Command:

```bash
PYTHONPATH=pipeline /tmp/asr-runtime-venv/bin/python -m pytest tests/unit/test_refresh.py -q
```

Result: `4 passed in 0.01s`.

### RED: CLI partial error exit behavior

Command:

```bash
PYTHONPATH=pipeline /tmp/asr-runtime-venv/bin/python -m pytest tests/integration/test_refresh_cli.py -q
```

Result: `1 failed, 1 passed in 0.04s` because `cli.main()` returned `0` after rendering a payload with `result: error`.

### GREEN: focused refresh suite

Command:

```bash
PYTHONPATH=pipeline /tmp/asr-runtime-venv/bin/python -m pytest tests/unit/test_refresh.py tests/integration/test_refresh_cli.py -q
```

Result: `6 passed in 0.04s`.

## Implementation evidence

- Retired or non-refreshable sources yield a `retired` record without running `git ls-remote`.
- Active sources use their lock-provided `timeout_seconds`.
- Per-source remote failures produce an `error` record and refresh continues with later sources.
- The payload sets `result` to `error` when any source fails; the CLI renders it first and exits `1`.
- Invalid source locks still raise `SourceRefreshError`, which the CLI writes to stderr.

## Self-review and checks

- `git diff --check`: passed.
- `PYTHONPATH=pipeline /tmp/asr-runtime-venv/bin/python -m json.tool registry/sources.lock.json >/dev/null`: passed.
- Removed an unused test import found during self-review.
- Worktree status contained only the five assigned implementation/test files plus this requested report; no Task 1 changes were altered.

## Important Task 2 review finding: source-lock lifecycle validation

### Scope

- Modified only `pipeline/skill_registry/refresh.py` and `tests/unit/test_refresh.py` for the fix.
- No CLI integration change was required.

### Root cause

`refresh_sources()` checked only for the presence of lifecycle keys. As a result,
an invalid `status` was accepted, a non-empty string such as
`refreshable: "false"` was truthy and reached the remote runner, and invalid
`timeout_seconds` values were passed to the runner.

### RED

Command:

```bash
PYTHONPATH=pipeline uv run --python 3.11 --with pytest --no-project python -m pytest tests/unit/test_refresh.py -q
```

Output:

```text
...FFFFFFF.                                                              [100%]
7 failed, 4 passed in 0.04s
```

The new tests covered invalid status, non-boolean `refreshable`, string, zero,
over-60, and boolean `timeout_seconds`, plus invalid `retired` plus
`refreshable: true`. The failures showed validation did not raise before the
runner.

### GREEN

Command:

```bash
PYTHONPATH=pipeline uv run --python 3.11 --with pytest --no-project python -m pytest tests/unit/test_refresh.py -q
```

Output:

```text
...........                                                              [100%]
11 passed in 0.02s
```

`refresh_sources()` now rejects source locks before runner/network access when:

- `status` is not `active` or `retired`;
- `refreshable` is not a boolean;
- `timeout_seconds` is not a non-boolean integer in `1..60`; or
- a retired source is marked refreshable.

Additional verification: `git diff --check` exited `0`.

### Commit

Fix commit: `50d1b8dd8670c19acb8e6cb37b2968bc23660efb`
