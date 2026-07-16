# Runtime Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the confirmation, source-refresh, and provenance-verification gaps so the existing on-demand Librarian runtime has a reliable trust boundary and continuously enforced CI.

**Architecture:** Keep the current Python runtime and JSON registry. Add structured confirmation metadata to the existing read path, add explicit source lifecycle fields to the source lock, make refresh produce a complete per-source report, and make the verifier bind every record to its locked source and stable identity. CI runs the existing package on supported Python versions; no catalog content changes.

**Tech Stack:** Python 3.11+, standard library, PyYAML, pytest, GitHub Actions.

## Global Constraints

- `registry/skills.json` remains authoritative for skill identity, state, risk, provenance, and content hash.
- `librarian-index.json` remains discovery-only.
- Do not modify catalog skill content.
- Do not change search ranking or Librarian composition behavior.
- Do not add runtime dependencies.
- Do not add MCP, embeddings, database, GUI, hosted service, telemetry, or automatic Core promotion.
- Unknown/review confirmation must never expose instructions before approval.
- Dangerous, quarantine, state, path, symlink, and hash blocks remain non-overridable.
- Plan B must not begin until the final gate in this plan passes.

---

## File Map

- Modify `pipeline/skill_registry/runtime.py`: structured confirmation payload and shared skill metadata rendering.
- Modify `pipeline/skill_registry/cli.py`: deterministic JSON/text confirmation and complete refresh exit behavior.
- Modify `pipeline/skill_registry/refresh.py`: retired-source handling, timeout, and per-source errors.
- Modify `pipeline/skill_registry/validator.py`: source lifecycle, commit binding, stable identity, and source-path uniqueness.
- Modify `registry/sources.lock.json`: explicit lifecycle for every pinned source.
- Modify `registry/quarantine.json`: restore two deterministic legacy source paths.
- Modify `tests/unit/test_runtime.py`: confirmation payload contract.
- Modify `tests/unit/test_refresh.py`: retired, timeout, partial failure, and result tests.
- Modify `tests/contracts/test_validator.py`: provenance and source-lock contract tests.
- Modify `tests/integration/test_runtime_cli.py`: read exit `3` JSON/text contract.
- Modify `tests/integration/test_refresh_cli.py`: full report plus non-zero exit on partial errors.
- Create `.github/workflows/ci.yml`: Python matrix and strict verifier gate.
- Modify `README.md`: source lifecycle and confirmation examples.
- Modify `docs/migration-from-agentic-library.md`: retired legacy source behavior.
- Delete `DIRECTORY_TREE.md`: stale generated tree with invalid paths.

## Public Interfaces Produced

```python
class SkillConfirmationRequired(RegistryRuntimeError):
    payload: dict[str, object]

def refresh_sources(
    root: Path,
    runner: Callable = subprocess.check_output,
) -> dict[str, object]:
    """Return a pass/error result with every source record; raise only for an invalid lock."""
```

Source lock entry contract:

```json
{
  "source_id": "example",
  "url": "https://github.com/org/repo.git",
  "commit": "40 lowercase hex characters",
  "layout": "skills-subdir",
  "skills_root": "skills",
  "metadata_index": "skills_index.json",
  "license_note": "Per-skill licenses tracked by source metadata",
  "status": "active",
  "refreshable": true,
  "timeout_seconds": 15
}
```

---

### Task 1: Structured confirmation payload

**Files:**
- Modify: `pipeline/skill_registry/runtime.py`
- Modify: `pipeline/skill_registry/cli.py`
- Test: `tests/unit/test_runtime.py`
- Test: `tests/integration/test_runtime_cli.py`

**Interfaces:**
- Consumes: existing `read_skill(root, identifier, allow_unreviewed=False)` and registry record fields.
- Produces: `SkillConfirmationRequired.payload` with `error` and complete `skill` metadata; safe reads return the same metadata shape plus `instructions`.

- [ ] **Step 1: Add failing unit tests for confirmation metadata**

Add tests that build an unknown fixture and assert:

```python
def test_unknown_read_returns_structured_confirmation(tmp_path):
    record = build_registry(
        tmp_path,
        [{"name": "unknown-skill", "risk": "unknown"}],
    )[0]
    with pytest.raises(SkillConfirmationRequired) as caught:
        read_skill(tmp_path, "unknown-skill")

    assert caught.value.payload == {
        "error": "confirmation_required",
        "skill": {
            "skill_id": record["skill_id"],
            "load_name": "unknown-skill",
            "risk": "unknown",
            "risk_reasons": ["fixture"],
            "core": False,
            "source_id": "fixture",
            "source_commit": "a" * 40,
            "source_path": "skills/unknown-skill",
            "license": "MIT",
            "content_sha256": record["content_sha256"],
        },
    }
    assert "instructions" not in caught.value.payload


def test_safe_read_exposes_integrity_metadata(tmp_path):
    record = build_registry(tmp_path, [{"name": "safe-skill", "risk": "safe"}])[0]
    result = read_skill(tmp_path, "safe-skill")
    assert result["skill"]["source_path"] == record["source_path"]
    assert result["skill"]["content_sha256"] == record["content_sha256"]
```

- [ ] **Step 2: Run the focused unit test and verify failure**

Run:

```bash
PYTHONPATH=pipeline python -m pytest tests/unit/test_runtime.py -q
```

Expected: FAIL because `SkillConfirmationRequired` has no `payload` and safe metadata lacks the two new fields.

- [ ] **Step 3: Implement one shared metadata builder and payload exception**

In `runtime.py`, replace the empty exception and duplicate return metadata with:

```python
class SkillConfirmationRequired(RegistryRuntimeError):
    def __init__(self, payload: dict[str, object]) -> None:
        skill = payload["skill"]
        super().__init__(
            f"confirmation required for {skill['risk']} skill: {skill['load_name']}"
        )
        self.payload = payload


def _skill_metadata(record: dict[str, object], core: set[str]) -> dict[str, object]:
    return {
        "skill_id": record["skill_id"],
        "load_name": record["load_name"],
        "risk": record["risk"],
        "risk_reasons": record["risk_reasons"],
        "core": record["skill_id"] in core,
        "source_id": record["source_id"],
        "source_commit": record["source_commit"],
        "source_path": record["source_path"],
        "license": record["license"],
        "content_sha256": record["content_sha256"],
    }
```

For `unknown` and `review`, raise:

```python
raise SkillConfirmationRequired(
    {"error": "confirmation_required", "skill": _skill_metadata(record, core)}
)
```

For successful reads, return:

```python
return {
    "skill": _skill_metadata(record, core),
    "instructions": marker.read_text(encoding="utf-8"),
}
```

- [ ] **Step 4: Replace the old string mock with structured CLI tests**

In `tests/integration/test_runtime_cli.py`, replace the existing confirmation
mock that raises a string-only exception with:

```python
CONFIRMATION = {
    "error": "confirmation_required",
    "skill": {
        "skill_id": "asr_0000000000000001",
        "load_name": "unknown-skill",
        "risk": "unknown",
        "risk_reasons": ["fixture"],
        "core": False,
        "source_id": "fixture",
        "source_commit": "a" * 40,
        "source_path": "skills/unknown-skill",
        "license": "MIT",
        "content_sha256": "b" * 64,
    },
}


def needs_confirmation(root, identifier, allow):
    raise SkillConfirmationRequired(CONFIRMATION)


def test_read_unknown_json_emits_metadata_without_instructions(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "read_skill", needs_confirmation)
    result = cli.main([
        "read", "unknown-skill", "--root", str(tmp_path), "--format", "json"
    ])
    captured = capsys.readouterr()
    payload = json.loads(captured.err)
    assert result == 3
    assert payload["error"] == "confirmation_required"
    assert payload["skill"]["source_commit"] == "a" * 40
    assert "instructions" not in payload
    assert captured.out == ""


def test_read_unknown_text_reports_decision_fields(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "read_skill", needs_confirmation)
    result = cli.main(["read", "unknown-skill", "--root", str(tmp_path)])
    captured = capsys.readouterr()
    assert result == 3
    assert "risk=unknown" in captured.err
    assert "source=fixture@" in captured.err
    assert "license=MIT" in captured.err
    assert "fixture" in captured.err
```

- [ ] **Step 5: Implement deterministic CLI rendering**

In the confirmation exception branch:

```python
except SkillConfirmationRequired as error:
    if args.format == "json":
        print(json.dumps(error.payload, indent=2, sort_keys=True), file=sys.stderr)
    else:
        skill = error.payload["skill"]
        reasons = ",".join(skill["risk_reasons"])
        print(
            f"confirmation_required={skill['load_name']} "
            f"risk={skill['risk']} reasons={reasons} "
            f"source={skill['source_id']}@{skill['source_commit']} "
            f"license={skill['license']} hash={skill['content_sha256']}",
            file=sys.stderr,
        )
    return 3
```

- [ ] **Step 6: Run unit and integration tests**

Run:

```bash
PYTHONPATH=pipeline python -m pytest \
  tests/unit/test_runtime.py \
  tests/integration/test_runtime_cli.py -q
```

Expected: PASS; unknown JSON contains metadata only, safe reads remain successful, dangerous remains blocked.

- [ ] **Step 7: Commit**

```bash
git add pipeline/skill_registry/runtime.py pipeline/skill_registry/cli.py \
  tests/unit/test_runtime.py tests/integration/test_runtime_cli.py
git commit -m "fix: expose informed skill confirmation"
```

---

### Task 2: Explicit source lifecycle and resilient refresh

**Files:**
- Modify: `registry/sources.lock.json`
- Modify: `pipeline/skill_registry/refresh.py`
- Modify: `pipeline/skill_registry/cli.py`
- Test: `tests/unit/test_refresh.py`
- Test: `tests/integration/test_refresh_cli.py`

**Interfaces:**
- Consumes: source lock entries with `status`, `refreshable`, and `timeout_seconds`.
- Produces: complete refresh payload with source statuses `retired`, `current`, `behind`, or `error`.

- [ ] **Step 1: Add lifecycle fields to test fixtures and failing unit cases**

Add these cases:

```python
def write_lock(root, sources):
    registry = root / "registry"
    registry.mkdir()
    (registry / "sources.lock.json").write_text(
        json.dumps({"sources": sources}), encoding="utf-8"
    )
    return root


def active_source(source_id, url, commit):
    return {
        "source_id": source_id,
        "url": url,
        "commit": commit,
        "status": "active",
        "refreshable": True,
        "timeout_seconds": 15,
    }


def test_refresh_skips_retired_source(tmp_path):
    root = write_lock(tmp_path, [{
        "source_id": "legacy",
        "url": "https://github.com/deleted/repo.git",
        "commit": "a" * 40,
        "status": "retired",
        "refreshable": False,
        "timeout_seconds": 15,
    }])
    calls = []
    payload = refresh_sources(root, runner=lambda *args, **kwargs: calls.append(args))
    assert calls == []
    assert payload == {
        "result": "pass",
        "sources": [{
            "source_id": "legacy",
            "pinned_commit": "a" * 40,
            "observed_commit": None,
            "status": "retired",
        }],
    }


def test_refresh_reports_error_and_continues(tmp_path):
    root = write_lock(tmp_path, [
        active_source("broken", "https://example.invalid/broken.git", "a" * 40),
        active_source("healthy", "https://example.invalid/healthy.git", "b" * 40),
    ])

    def runner(command, **kwargs):
        if "broken" in command[2]:
            raise subprocess.CalledProcessError(2, command)
        assert kwargs["timeout"] == 15
        return f"{'b' * 40}\tHEAD\n"

    payload = refresh_sources(root, runner=runner)
    assert payload["result"] == "error"
    assert [item["status"] for item in payload["sources"]] == ["error", "current"]
```

Add a runner assertion that receives `timeout=15`.

- [ ] **Step 2: Run focused tests and verify failure**

```bash
PYTHONPATH=pipeline python -m pytest tests/unit/test_refresh.py -q
```

Expected: FAIL because refresh still queries retired sources and fails fast.

- [ ] **Step 3: Implement lifecycle-aware per-source refresh**

Keep `SourceRefreshError` only for an unreadable/invalid source lock. Implement the loop as:

```python
records: list[dict[str, object]] = []
for source in sources:
    if source["status"] == "retired" or not source["refreshable"]:
        records.append({
            "source_id": source["source_id"],
            "pinned_commit": source["commit"],
            "observed_commit": None,
            "status": "retired",
        })
        continue
    try:
        output = runner(
            ["git", "ls-remote", source["url"], "HEAD"],
            text=True,
            stderr=subprocess.PIPE,
            timeout=source["timeout_seconds"],
        )
        observed = output.split()[0]
        if not COMMIT.fullmatch(observed):
            raise ValueError("invalid commit")
    except (IndexError, ValueError, subprocess.SubprocessError, OSError) as error:
        records.append({
            "source_id": source["source_id"],
            "pinned_commit": source["commit"],
            "observed_commit": None,
            "status": "error",
            "error": type(error).__name__,
        })
        continue
    records.append({
        "source_id": source["source_id"],
        "pinned_commit": source["commit"],
        "observed_commit": observed,
        "status": "current" if observed == source["commit"] else "behind",
    })
return {
    "result": "error" if any(item["status"] == "error" for item in records) else "pass",
    "sources": records,
}
```

- [ ] **Step 4: Update real source lock lifecycle**

Set:

```json
"legacy-local": {
  "status": "retired",
  "refreshable": false,
  "timeout_seconds": 15
}
```

and:

```json
"sickn33-agentic-awesome-skills": {
  "status": "active",
  "refreshable": true,
  "timeout_seconds": 15
}
```

Preserve URLs, commits, layouts, metadata paths, and license notes exactly.

- [ ] **Step 5: Add failing CLI partial-error test**

First add `"result": "pass"` to the payload in the existing
`test_refresh_cli_renders_machine_report`. Then patch `refresh_sources` to
return one error and one current record. Assert JSON prints the complete payload
and `cli.main()` returns `1`:

```python
assert result == 1
assert json.loads(captured.out)["sources"][1]["status"] == "current"
assert captured.err == ""
```

- [ ] **Step 6: Update CLI exit handling**

Render the payload first, then return:

```python
return 1 if payload["result"] == "error" else 0
```

Text mode prints every source, including error and retired entries. Invalid lock errors go to stderr.

- [ ] **Step 7: Run refresh tests**

```bash
PYTHONPATH=pipeline python -m pytest \
  tests/unit/test_refresh.py \
  tests/integration/test_refresh_cli.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add registry/sources.lock.json pipeline/skill_registry/refresh.py \
  pipeline/skill_registry/cli.py tests/unit/test_refresh.py \
  tests/integration/test_refresh_cli.py
git commit -m "fix: model retired sources in refresh"
```

---

### Task 3: Bind registry records to locked provenance

**Files:**
- Modify: `pipeline/skill_registry/validator.py`
- Modify: `registry/quarantine.json`
- Test: `tests/contracts/test_validator.py`

**Interfaces:**
- Consumes: `stable_skill_id(source_id, source_path)` and source lifecycle contract from Task 2.
- Produces: strict failures for commit mismatch, identity mismatch, duplicate source path, and invalid lifecycle.

- [ ] **Step 1: Add failing verifier tests**

Add these helpers and four tests by mutating one cloned repository fixture at a time:

```python
def write_json(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def check_ids(root):
    return {finding["check_id"] for finding in verify_repository(root).findings}


def test_verify_rejects_record_commit_not_equal_to_source_lock(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    payload = json.loads((root / "registry/skills.json").read_text())
    payload["skills"][0]["source_commit"] = "b" * 40
    write_json(root / "registry/skills.json", payload)
    assert "registry.provenance" in check_ids(root)


def test_verify_rejects_skill_id_not_derived_from_source(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    payload = json.loads((root / "registry/skills.json").read_text())
    payload["skills"][0]["skill_id"] = "asr_0000000000000000"
    write_json(root / "registry/skills.json", payload)
    assert "registry.identity" in check_ids(root)


def test_verify_rejects_duplicate_source_path_across_active_and_quarantine(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    active = json.loads((root / "registry/skills.json").read_text())["skills"][0]
    quarantine = json.loads((root / "registry/quarantine.json").read_text())
    quarantine["records"].append({**active, "disposition": "quarantined"})
    write_json(root / "registry/quarantine.json", quarantine)
    assert "registry.source-path" in check_ids(root)


def test_verify_rejects_invalid_source_lifecycle(repo_root, tmp_path):
    root = clone_repository_fixture(repo_root, tmp_path)
    lock = json.loads((root / "registry/sources.lock.json").read_text())
    lock["sources"][0].update({"status": "retired", "refreshable": True})
    write_json(root / "registry/sources.lock.json", lock)
    assert "registry.source-lock" in check_ids(root)
```

- [ ] **Step 2: Run focused tests and verify failure**

```bash
PYTHONPATH=pipeline python -m pytest tests/contracts/test_validator.py -q
```

Expected: the new assertions fail under the current verifier.

- [ ] **Step 3: Validate the source lifecycle schema**

Import `stable_skill_id` and construct:

```python
source_by_id = {
    source["source_id"]: source
    for source in sources
    if isinstance(source, dict) and isinstance(source.get("source_id"), str)
}
```

Require:

```python
source.get("status") in {"active", "retired"}
and isinstance(source.get("refreshable"), bool)
and isinstance(source.get("timeout_seconds"), int)
and 1 <= source["timeout_seconds"] <= 60
and not (source["status"] == "retired" and source["refreshable"])
```

- [ ] **Step 4: Verify identity, commit, and source-path uniqueness**

For `skills + quarantine`, check:

```python
source = source_by_id.get(record.get("source_id"))
source_path = record.get("source_path")
if source is None or record.get("source_commit") != source.get("commit"):
    add(findings, "registry.provenance", ["DR-04"], skill_id=record.get("skill_id"))
if (
    not isinstance(source_path, str)
    or source_path.startswith("/")
    or ".." in source_path.split("/")
):
    add(findings, "registry.source-path", ["DR-04"], skill_id=record.get("skill_id"))
elif record.get("skill_id") != stable_skill_id(str(record.get("source_id")), source_path):
    add(findings, "registry.identity", ["DR-04"], skill_id=record.get("skill_id"))
```

Count `(source_id, source_path)` pairs and fail every duplicated pair.

- [ ] **Step 5: Reconcile the two legacy quarantine identities**

Add only the following `source_path` field to each matching record in
`registry/quarantine.json`:

```json
{
  "skill_id": "asr_a94f930da863c865",
  "source_path": "workflows-and-management/planning-and-execution/linear"
}
```

```json
{
  "skill_id": "asr_c5910b994e034997",
  "source_path": "engineering/tooling-and-monorepos/SPDD"
}
```

Add a contract assertion that each existing ID equals
`stable_skill_id(record["source_id"], record["source_path"])`. These paths
reconstruct the existing IDs. Do not regenerate IDs or move catalog content.

- [ ] **Step 6: Run validator and full unit tests**

```bash
PYTHONPATH=pipeline python -m pytest tests/contracts/test_validator.py -q
PYTHONPATH=pipeline python -m pytest tests/unit -q
```

Expected: PASS.

- [ ] **Step 7: Run strict verifier against the real repository**

```bash
PYTHONPATH=pipeline python -m skill_registry.cli verify --strict
```

Expected: `result=pass failed=0`. If another current record violates the new
invariant, stop and report that exact record; do not weaken the verifier.

- [ ] **Step 8: Commit**

```bash
git add pipeline/skill_registry/validator.py registry/quarantine.json \
  tests/contracts/test_validator.py
git commit -m "fix: bind skills to locked provenance"
```

---

### Task 4: Add required CI

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `pyproject.toml` only if pytest markers or test paths already require correction; do not add dependencies.

**Interfaces:**
- Consumes: existing editable install and pytest suite.
- Produces: required GitHub check named `test` for Python 3.11–3.13 and `strict-verifier` on Python 3.11.

- [ ] **Step 1: Create the CI workflow**

Use exactly:

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - run: python -m pip install -e '.[dev]'
      - run: python -m pytest -q

  strict-verifier:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - run: python -m pip install -e '.[dev]'
      - run: git diff --check
      - run: python -m skill_registry.cli verify --strict
```

- [ ] **Step 2: Validate workflow syntax locally without adding tooling**

Run:

```bash
python - <<'PY'
from pathlib import Path
import yaml

payload = yaml.safe_load(Path('.github/workflows/ci.yml').read_text())
assert payload['jobs']['test']['strategy']['matrix']['python-version'] == ['3.11', '3.12', '3.13']
assert 'strict-verifier' in payload['jobs']
print('ci-contract=pass')
PY
```

Expected: `ci-contract=pass`.

- [ ] **Step 3: Run the same local commands CI will run**

```bash
git diff --check
PYTHONPATH=pipeline python -m pytest -q
PYTHONPATH=pipeline python -m skill_registry.cli verify --strict
```

Expected: all exit `0`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: enforce tests and strict verification"
```

---

### Task 5: Correct operator documentation and remove stale tree

**Files:**
- Modify: `README.md`
- Modify: `docs/migration-from-agentic-library.md`
- Delete: `DIRECTORY_TREE.md`

**Interfaces:**
- Consumes: Plan A CLI/source lifecycle behavior.
- Produces: documentation that names the authoritative files and gives executable confirmation/refresh examples.

- [ ] **Step 1: Delete the stale generated tree**

Delete `DIRECTORY_TREE.md`; do not regenerate it. The catalog and search command are the maintained navigation surfaces.

- [ ] **Step 2: Update README confirmation example**

Document:

```bash
skill-registry read --root "$AGENTIC_SKILL_REGISTRY_ROOT" \
  --format json youtube-transcript
echo "$?"  # 3: confirmation required; no instructions returned
```

Explain that the response includes source ID, pinned commit, source path, license, registered hash, risk, and reasons. Approval reruns with `--allow-unreviewed`; it does not bypass integrity checks.

- [ ] **Step 3: Update source lifecycle documentation**

State plainly:

- `legacy-local` is retained only as retired provenance and is never queried;
- active refreshable sources are checked independently;
- `refresh` reports all sources and exits `1` if any active source errors;
- refresh never imports or updates catalog content.

- [ ] **Step 4: Verify docs and forbidden architecture**

```bash
git diff --check
! test -e DIRECTORY_TREE.md
! rg -n "superpowers-mcp@|list_skills|mcpServers" \
  README.md docs pipeline skills
```

Expected: all exit `0`.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/migration-from-agentic-library.md DIRECTORY_TREE.md
git commit -m "docs: explain stabilized registry trust boundary"
```

---

### Task 6: Plan A acceptance gate

**Files:**
- No production changes unless a verifier exposes a Plan A regression.
- Record evidence in the pull request description, not a generated repository report.

**Interfaces:**
- Consumes: Tasks 1–5.
- Produces: explicit authorization gate for Plan B.

- [ ] **Step 1: Run repository checks**

```bash
git diff --check
PYTHONPATH=pipeline python -m pytest -q
PYTHONPATH=pipeline python -m skill_registry.cli verify --strict
```

Expected: all exit `0`; verifier prints `result=pass failed=0`.

- [ ] **Step 2: Run confirmation smoke tests**

```bash
set +e
PYTHONPATH=pipeline python -m skill_registry.cli read \
  --root "$PWD" --format json youtube-transcript \
  > /tmp/asr-confirmation.out 2> /tmp/asr-confirmation.json
status=$?
set -e
test "$status" = "3"
jq -e '.error == "confirmation_required" and .skill.source_id and .skill.source_commit and .skill.content_sha256 and (has("instructions") | not)' \
  /tmp/asr-confirmation.json
test ! -s /tmp/asr-confirmation.out
```

Expected: all assertions pass.

- [ ] **Step 3: Run refresh smoke test**

```bash
PYTHONPATH=pipeline python -m skill_registry.cli refresh --root "$PWD" --format json \
  > /tmp/asr-refresh.json
jq -e '.sources[] | select(.source_id == "legacy-local") | .status == "retired"' \
  /tmp/asr-refresh.json
```

Expected: legacy source is retired and no deleted-repository error occurs.

- [ ] **Step 4: Confirm CI on the feature PR**

Required checks:

```text
test (3.11)           success
test (3.12)           success
test (3.13)           success
strict-verifier       success
```

- [ ] **Step 5: Stop or authorize Plan B**

Authorize Plan B only when every preceding result passes. Stop and open a focused corrective task if:

- current registry data violates provenance invariants;
- confirmation leaks instructions;
- a retired source is queried;
- one source failure suppresses another source's report;
- CI or strict verification fails.

Do not weaken a verifier to make the gate pass.
