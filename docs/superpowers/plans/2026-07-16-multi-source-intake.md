# Multi-Source Intake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic, review-gated pipeline that imports pinned public GitHub skill repositories into the existing local registry without bulk installation, automatic trust, or loading the catalog into agent context.

**Architecture:** Two CLI phases separate untrusted preparation from mutation. `prepare-source` fetches an exact commit, validates and inventories bundles, proposes classification, records duplicate evidence, and writes a manifest plus review template without changing the repository. `commit-source` requires a complete human review, re-fetches the same commit to prevent TOCTOU, copies approved snapshots, atomically updates authoritative JSON, and runs the strict verifier.

**Tech Stack:** Python 3.11+, standard library, PyYAML, Git CLI, pytest. No new dependency.

## Global Constraints

- Begin only after `docs/superpowers/plans/2026-07-16-runtime-stabilization.md` is merged and CI is green.
- Version one accepts only public `https://github.com/<owner>/<repo>.git` sources pinned to an exact lowercase 40-hex commit.
- Preflight the selected subtree through GitHub's unauthenticated tree API before any Git fetch.
- No private repositories, tokens, SSH URLs, arbitrary archive URLs, floating branches, background sync, or automatic updates.
- Preparation must not modify `catalog/`, `registry/`, or `librarian-index.json`.
- Commit requires a clean Git worktree and a complete review file.
- Every imported record begins `unknown` with `initial-review-required`; none enters Core automatically.
- Similarity is review evidence only; never auto-merge, auto-delete, auto-block, or auto-promote.
- Preserve upstream bundle bytes. Store attribution in registry metadata; do not inject files into bundles.
- Reuse `tree_sha256`, `stable_skill_id`, current registry JSON, and current search/read runtime.
- Enforce 10,000 blobs and 250 MiB per selected source subtree, plus 1,000 files and 50 MiB per bundle; reject symlinks and hardlinks.
- Do not add MCP, embeddings, vector database, hosted service, GUI, telemetry, ratings, marketplace, or installer behavior.

---

## File Map

- Create `pipeline/skill_registry/text.py`: shared deterministic tokenization and similarity.
- Create `pipeline/skill_registry/intake.py`: source validation, pinned checkout, bundle scan, classification, dedup evidence, manifest/review validation, and commit orchestration.
- Modify `pipeline/skill_registry/runtime.py`: consume shared tokenizer without changing ranking weights.
- Modify `pipeline/skill_registry/filesystem.py`: atomic JSON writes used by commit.
- Modify `pipeline/skill_registry/cli.py`: `prepare-source` and `commit-source` commands.
- Modify `pipeline/skill_registry/validator.py`: validate source joins and canonical records created by intake.
- Modify `registry/skills.json`: only through the tested commit command/pilot.
- Modify `registry/sources.lock.json`: only through the tested commit command/pilot.
- Modify `registry/quarantine.json`: only for reviewed quarantine candidates.
- Modify `librarian-index.json`: append discovery metadata for committed candidates.
- Create `tests/unit/test_text.py`: tokenizer/similarity contract.
- Create `tests/unit/test_intake.py`: source, bundle, classification, dedup, manifest, review, TOCTOU, and rollback tests.
- Create `tests/integration/test_intake_cli.py`: CLI exit/output/mutation boundaries.
- Modify `tests/contracts/test_validator.py`: new-source provenance/canonical contract.
- Modify `tests/integration/test_runtime_cli.py`: imported records remain governed by existing search/read policy.
- Modify `README.md`: operator workflow and safety boundary.
- Create `docs/source-intake.md`: manifest/review schema, pilot and rollback runbook.

## Interfaces Produced

- Constants: `MAX_BUNDLE_FILES = 1_000`, `MAX_BUNDLE_BYTES = 50 * 1024 * 1024`, `MAX_SOURCE_FILES = 10_000`, and `MAX_SOURCE_BYTES = 250 * 1024 * 1024`.
- Error: `IntakeError(RuntimeError)` for all user-facing intake failures.
- Text primitives: `tokenize(value) -> set[str]` and `jaccard(left, right) -> float`.
- Source checks: `validate_source_spec`, `preflight_source_tree`, `checkout_pinned_source`, `discover_source_bundles`, and `inspect_bundle`.
- Destination checks: `slugify_load_name`, `next_load_name`, and `catalog_destination`.
- Review evidence: `propose_classification` and `duplicate_evidence`.
- Two-phase workflow: `prepare_source(root, spec, staging)` and `commit_source(root, manifest_path, review_path)`.

Manifest schema:

```json
{
  "schema_version": 1,
  "source": {
    "source_id": "microsoftdocs-agent-skills",
    "url": "https://github.com/MicrosoftDocs/Agent-Skills.git",
    "commit": "40 lowercase hex",
    "skills_root": "skills",
    "license": "CC-BY-4.0",
    "license_note": "Upstream repository license verified during preparation"
  },
  "candidates": []
}
```

Review decisions: `import`, `canonical`, `quarantine`, `reject`.

Review schema binds decisions to the exact prepared manifest bytes:

```json
{
  "schema_version": 1,
  "manifest_sha256": "64 lowercase hex",
  "decisions": []
}
```

`commit-source` computes SHA-256 over the manifest file bytes and requires exact
equality with `review.manifest_sha256` before checkout or repository mutation.

---

### Task 1: Shared text primitives without ranking regression

**Files:**
- Create: `pipeline/skill_registry/text.py`
- Modify: `pipeline/skill_registry/runtime.py`
- Create: `tests/unit/test_text.py`
- Modify: `tests/unit/test_runtime.py`

**Interfaces:**
- Produces: `tokenize(value) -> set[str]` and `jaccard(left, right) -> float`.
- Preserves: exact current search scoring and fixed-query ordering.

- [ ] **Step 1: Write failing text tests**

```python
from skill_registry.text import jaccard, tokenize


def test_tokenize_is_lowercase_ascii_and_deterministic():
    assert tokenize("PDF / Code-Review v2") == {"pdf", "code", "review", "v2"}


def test_jaccard_handles_empty_sets():
    assert jaccard(set(), set()) == 0.0
    assert jaccard({"pdf"}, set()) == 0.0


def test_jaccard_reports_overlap():
    assert jaccard({"code", "review"}, {"review", "security"}) == 1 / 3
```

- [ ] **Step 2: Run and verify failure**

```bash
PYTHONPATH=pipeline python -m pytest tests/unit/test_text.py -q
```

Expected: FAIL with `ModuleNotFoundError: skill_registry.text`.

- [ ] **Step 3: Implement the minimal module**

```python
import re

TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(value: object) -> set[str]:
    return set(TOKEN.findall(str(value).lower()))


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0
```

- [ ] **Step 4: Replace runtime `_tokens` with shared `tokenize`**

Import `tokenize`, remove the local regex/helper, and preserve `_score` exactly except for calls changing from `_tokens(value)` to `tokenize(value)`.

- [ ] **Step 5: Run text and search regression tests**

```bash
PYTHONPATH=pipeline python -m pytest \
  tests/unit/test_text.py \
  tests/unit/test_runtime.py \
  tests/integration/test_search_quality.py -q
```

Expected: PASS with unchanged fixed-query results.

- [ ] **Step 6: Commit**

```bash
git add pipeline/skill_registry/text.py pipeline/skill_registry/runtime.py \
  tests/unit/test_text.py tests/unit/test_runtime.py
git commit -m "refactor: share deterministic skill tokenization"
```

---

### Task 2: Validate and inspect a pinned public GitHub source

**Files:**
- Create: `pipeline/skill_registry/intake.py`
- Create: `tests/unit/test_intake.py`

**Interfaces:**
- Consumes: `tree_sha256`, PyYAML frontmatter parsing pattern, Git CLI through injected runner.
- Produces: validated source spec, exact checkout, deterministic candidate inventory.

- [ ] **Step 1: Create the concrete intake test fixture layer**

Put these helpers at the top of `tests/unit/test_intake.py`; later tasks reuse
them instead of inventing unnamed fixtures:

```python
def valid_source_spec(**changes):
    value = {
        "source_id": "new-source",
        "url": "https://github.com/example/skills.git",
        "commit": "c" * 40,
        "skills_root": "skills",
        "license": "MIT",
        "license_note": "Fixture source license",
    }
    value.update(changes)
    return value


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def make_skill(parent, name, extra_files=None):
    bundle = parent / name
    bundle.mkdir(parents=True)
    (bundle / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Use {name}.\n---\n\n# {name}\n",
        encoding="utf-8",
    )
    for relative, content in (extra_files or {}).items():
        path = bundle / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return bundle


def discovery(name, taxonomy, category, description, skill_id=None):
    value = {
        "name": name,
        "flat_name": name,
        "taxonomy": taxonomy,
        "category_fine": category,
        "description": description,
    }
    if skill_id is not None:
        value["skill_id"] = skill_id
    return value


def repository_digest(root):
    digest = hashlib.sha256()
    paths = list((root / "registry").rglob("*")) + list((root / "catalog").rglob("*"))
    paths.append(root / "librarian-index.json")
    for path in sorted((item for item in paths if item.is_file()), key=lambda item: item.as_posix()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


@pytest.fixture
def valid_root(tmp_path):
    root = tmp_path / "repo"
    (root / "catalog").mkdir(parents=True)
    source = {
        "source_id": "existing-source",
        "url": "https://github.com/example/existing.git",
        "commit": "a" * 40,
        "layout": "skills-subdir",
        "skills_root": "skills",
        "metadata_index": "",
        "license_note": "Fixture source license",
        "status": "active",
        "refreshable": True,
        "timeout_seconds": 15,
    }
    write_json(root / "registry/sources.lock.json", {"schema_version": 1, "sources": [source]})
    write_json(root / "registry/skills.json", {"schema_version": 1, "skills": []})
    write_json(root / "registry/quarantine.json", {"schema_version": 1, "records": []})
    write_json(root / "registry/aliases.json", {"schema_version": 1, "aliases": []})
    write_json(root / "registry/risk-overrides.json", {"schema_version": 1, "overrides": []})
    write_json(root / "registry/exceptions.json", {"schema_version": 1, "exceptions": []})
    write_json(root / "registry/core.json", {"schema_version": 1, "skill_ids": []})
    write_json(root / "registry/schema-version.json", {"schema_version": 1})
    write_json(root / "registry/upstream-review.json", {
        "schema_version": 1,
        "source_id": "existing-source",
        "pinned_commit": "a" * 40,
        "observed_commit": "a" * 40,
        "records": [],
    })
    write_json(root / "librarian-index.json", {"schemaVersion": 1, "entries": []})
    subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "fixture@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Fixture"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-m", "fixture"], check=True, capture_output=True)
    return root


@pytest.fixture
def fake_checkout(tmp_path, monkeypatch):
    upstream = tmp_path / "upstream"
    make_skill(upstream / "skills", "new-skill")

    def checkout(spec, destination):
        shutil.copytree(upstream, destination, dirs_exist_ok=True)

    monkeypatch.setattr(intake, "preflight_source_tree", lambda spec: {"file_count": 1, "byte_count": 100})
    monkeypatch.setattr(intake, "checkout_pinned_source", checkout)
    return upstream


@pytest.fixture
def prepared_paths(valid_root, tmp_path, fake_checkout):
    stage = tmp_path / "stage"
    prepare_source(valid_root, valid_source_spec(), stage)
    review_path = stage / "review.json"
    review = json.loads(review_path.read_text())
    review["decisions"][0].update({
        "decision": "import",
        "reason": "Fixture candidate reviewed",
        "taxonomy": "engineering/testing",
        "category_fine": "testing",
        "canonical_skill_id": None,
    })
    write_json(review_path, review)
    return stage / "manifest.json", review_path


@pytest.fixture
def manifest(prepared_paths):
    return prepared_paths[0]


@pytest.fixture
def review(prepared_paths):
    return prepared_paths[1]


@pytest.fixture
def valid_review(review):
    return json.loads(review.read_text())


def apply_review_mutation(review, mutation):
    decisions = review["decisions"]
    if mutation == "pending_decision":
        decisions[0]["decision"] = "pending"
    elif mutation == "missing_candidate":
        decisions.pop()
    elif mutation == "extra_candidate":
        extra = copy.deepcopy(decisions[0])
        extra["source_path"] = "skills/extra"
        decisions.append(extra)
    elif mutation == "duplicate_candidate":
        decisions.append(copy.deepcopy(decisions[0]))
    elif mutation == "empty_reason":
        decisions[0]["reason"] = ""
    elif mutation == "invalid_taxonomy":
        decisions[0]["taxonomy"] = "../escape"
    elif mutation == "canonical_without_target":
        decisions[0].update({"decision": "canonical", "canonical_skill_id": None})
    elif mutation == "unknown_canonical_target":
        decisions[0].update({"decision": "canonical", "canonical_skill_id": "asr_ffffffffffffffff"})
    elif mutation == "manifest_digest_mismatch":
        review["manifest_sha256"] = "0" * 64
    else:
        raise AssertionError(mutation)


def mark_worktree_dirty(root):
    (root / "dirty.txt").write_text("dirty\n", encoding="utf-8")


def fail_on_second_write(real_write):
    calls = 0

    def wrapper(path, value):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected write failure")
        return real_write(path, value)

    return wrapper
```

Import `copy`, `hashlib`, `io`, `json`, `os`, `shutil`, `subprocess`, `Path`,
and `pytest`, plus the `intake` module and public functions named in each task.

- [ ] **Step 2: Write failing source validation tests**

```python
@pytest.mark.parametrize("url", [
    "git@github.com:org/repo.git",
    "https://gitlab.com/org/repo.git",
    "https://github.com/org/repo",
    "https://github.com/org/repo.git?token=secret",
])
def test_validate_source_rejects_noncanonical_url(url):
    with pytest.raises(IntakeError):
        validate_source_spec(valid_source_spec(url=url))


def test_validate_source_requires_exact_commit():
    with pytest.raises(IntakeError):
        validate_source_spec(valid_source_spec(commit="main"))


def test_validate_source_requires_license_evidence():
    with pytest.raises(IntakeError):
        validate_source_spec(valid_source_spec(license=""))


@pytest.mark.parametrize("skills_root", [
    "**", "skills/*", "skills/[ab]", "skills?", "skills//nested", ".", "../skills",
])
def test_validate_source_rejects_nonliteral_skills_root(skills_root):
    with pytest.raises(IntakeError, match="skills_root"):
        validate_source_spec(valid_source_spec(skills_root=skills_root))


def test_preflight_rejects_truncated_tree():
    body = io.BytesIO(json.dumps({"truncated": True, "tree": []}).encode())
    with pytest.raises(IntakeError, match="truncated"):
        preflight_source_tree(valid_source_spec(), opener=lambda request, timeout: body)


def test_preflight_rejects_source_byte_limit(monkeypatch):
    monkeypatch.setattr(intake, "MAX_SOURCE_BYTES", 10)
    tree = {"truncated": False, "tree": [
        {"type": "blob", "path": "skills/example/SKILL.md", "size": 11}
    ]}
    with pytest.raises(IntakeError, match="source byte limit"):
        preflight_source_tree(
            valid_source_spec(),
            opener=lambda request, timeout: io.BytesIO(json.dumps(tree).encode()),
        )


def test_preflight_rejects_source_file_limit(monkeypatch):
    monkeypatch.setattr(intake, "MAX_SOURCE_FILES", 1)
    tree = {"truncated": False, "tree": [
        {"type": "blob", "path": "skills/a/SKILL.md", "size": 1},
        {"type": "blob", "path": "skills/b/SKILL.md", "size": 1},
    ]}
    with pytest.raises(IntakeError, match="source file limit"):
        preflight_source_tree(
            valid_source_spec(),
            opener=lambda request, timeout: io.BytesIO(json.dumps(tree).encode()),
        )


def test_checkout_disables_credentials_and_uses_sparse_filter(tmp_path):
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        stdout = "c" * 40 + "\n" if command[-2:] == ["rev-parse", "HEAD"] else ""
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    checkout_pinned_source(valid_source_spec(), tmp_path / "checkout", runner=runner)
    commands = [command for command, _ in calls]
    assert any(
        "sparse-checkout" in command and "--cone" in command and command[-1] == "skills"
        for command in commands
    )
    assert any("--filter=blob:none" in command for command in commands)
    for _, kwargs in calls:
        assert kwargs["timeout"] == 60
        assert kwargs["env"]["GIT_TERMINAL_PROMPT"] == "0"
        assert kwargs["env"]["GIT_ASKPASS"] == "/usr/bin/false"
        assert kwargs["env"]["GCM_INTERACTIVE"] == "never"
        assert kwargs["env"]["GIT_CONFIG_NOSYSTEM"] == "1"
        assert kwargs["env"]["GIT_ATTR_NOSYSTEM"] == "1"
        assert kwargs["env"]["GIT_LFS_SKIP_SMUDGE"] == "1"
```

Also reject absolute `skills_root` and `..` segments. `prepare_source`, which has
access to the repository root, rejects a `source_id` already present in
`sources.lock.json`; keep that check out of the pure source-spec validator.

- [ ] **Step 3: Write failing bundle safety tests**

```python
def test_inspect_bundle_rejects_symlink(tmp_path):
    bundle = make_skill(tmp_path, "example")
    (bundle / "escape").symlink_to(tmp_path / "outside")
    with pytest.raises(IntakeError, match="symlink"):
        inspect_bundle(bundle)


def test_inspect_bundle_rejects_hardlink(tmp_path):
    bundle = make_skill(tmp_path, "example")
    os.link(bundle / "SKILL.md", bundle / "copy.md")
    with pytest.raises(IntakeError, match="hardlink"):
        inspect_bundle(bundle)


def test_inspect_bundle_rejects_file_count_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(intake, "MAX_BUNDLE_FILES", 1)
    bundle = make_skill(tmp_path, "example", extra_files={"a.txt": "a"})
    with pytest.raises(IntakeError, match="file limit"):
        inspect_bundle(bundle)


def test_inspect_bundle_rejects_byte_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(intake, "MAX_BUNDLE_BYTES", 10)
    bundle = make_skill(tmp_path, "example")
    with pytest.raises(IntakeError, match="byte limit"):
        inspect_bundle(bundle)
```

Require a root `SKILL.md` with non-empty string `name` and `description`.

- [ ] **Step 4: Run focused tests and verify failure**

```bash
PYTHONPATH=pipeline python -m pytest tests/unit/test_intake.py -q
```

Expected: FAIL because intake module does not exist.

- [ ] **Step 5: Implement validation constants and source normalization**

```python
SOURCE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
GITHUB_URL = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git$")
SAFE_RELATIVE_PATH = re.compile(r"^[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*$")
MAX_BUNDLE_FILES = 1_000
MAX_BUNDLE_BYTES = 50 * 1024 * 1024
MAX_SOURCE_FILES = 10_000
MAX_SOURCE_BYTES = 250 * 1024 * 1024


class IntakeError(RuntimeError):
    pass
```

`validate_source_spec` returns a new normalized dictionary and rejects
unknown/missing fields instead of mutating input. `skills_root` must match
`SAFE_RELATIVE_PATH`; every segment must differ from `.` and `..`. This forbids
Git pathspec/glob characters while permitting literal paths such as
`skills/.curated`.

- [ ] **Step 6: Implement unauthenticated source preflight**

Derive owner and repository from the validated URL and request:

```text
https://api.github.com/repos/OWNER/REPOSITORY/git/trees/COMMIT?recursive=1
```

Use `urllib.request.Request` with only `Accept: application/vnd.github+json` and
`User-Agent: agentic-skill-registry`; invoke the injected opener with timeout
`30`. Reject HTTP/JSON errors, `truncated=true`, non-list trees,
missing/non-integer blob sizes, more than `MAX_SOURCE_FILES`, or more than
`MAX_SOURCE_BYTES` for blobs where path equals `skills_root` or starts with
`skills_root + "/"`. Return counts and bytes;
never persist the API response.

- [ ] **Step 7: Implement exact sparse checkout with credentials disabled**

Use an injected runner with these commands:

```python
commands = [
    ["git", "init", str(destination)],
    ["git", "-C", str(destination), "remote", "add", "origin", spec["url"]],
    ["git", "-C", str(destination), "sparse-checkout", "set", "--cone", "--", spec["skills_root"]],
    ["git", "-C", str(destination), "-c", "credential.helper=", "fetch", "--depth", "1", "--filter=blob:none", "origin", spec["commit"]],
    ["git", "-C", str(destination), "-c", "credential.helper=", "checkout", "--detach", "FETCH_HEAD"],
]
```

Create an empty temporary HOME and pass only a minimal environment containing
`PATH`, that HOME, `GIT_TERMINAL_PROMPT=0`, `GIT_ASKPASS=/usr/bin/false`, and
`GCM_INTERACTIVE=never`, plus `GIT_CONFIG_NOSYSTEM=1`, `GIT_ATTR_NOSYSTEM=1`,
and `GIT_LFS_SKIP_SMUDGE=1`. The last three prevent system-defined filters,
attributes, and Git LFS smudge downloads from bypassing the preflight size cap.
Then run `git -C DEST rev-parse HEAD` and require exact
equality with the requested commit. Pass `timeout=60`, `check=True`, `text=True`,
and capture stdout/stderr. Never invoke a shell. Add a runner test asserting the
credential/filter environment, cone-mode literal sparse path, blob filter, and timeout.

- [ ] **Step 8: Implement candidate discovery and bundle inspection**

Discovery recursively finds directories whose direct child is `SKILL.md` under the resolved `skills_root`. It skips descendants after accepting a bundle root so nested markers remain bundle assets rather than independent candidates.

Inspection:

```python
def inspect_bundle(bundle: Path) -> dict[str, object]:
    files = []
    total = 0
    for path in sorted(bundle.rglob("*"), key=lambda item: item.relative_to(bundle).as_posix()):
        if path.is_symlink():
            raise IntakeError(f"symlink rejected: {path.relative_to(bundle)}")
        if path.is_file():
            if path.stat().st_nlink > 1:
                raise IntakeError(f"hardlink rejected: {path.relative_to(bundle)}")
            files.append(path)
            total += path.stat().st_size
    if len(files) > MAX_BUNDLE_FILES:
        raise IntakeError("bundle file limit exceeded")
    if total > MAX_BUNDLE_BYTES:
        raise IntakeError("bundle byte limit exceeded")
    metadata = parse_skill_frontmatter(bundle / "SKILL.md")
    return {
        "name": metadata["name"].strip(),
        "description": metadata["description"].strip(),
        "file_count": len(files),
        "byte_count": total,
        "content_sha256": tree_sha256(bundle),
    }
```

The parser must use `yaml.safe_load` and reject malformed/non-object frontmatter.

- [ ] **Step 9: Run intake safety tests**

```bash
PYTHONPATH=pipeline python -m pytest tests/unit/test_intake.py -q
```

Expected: source and bundle safety cases PASS.

- [ ] **Step 10: Commit**

```bash
git add pipeline/skill_registry/intake.py tests/unit/test_intake.py
git commit -m "feat: inspect pinned GitHub skill sources"
```

---

### Task 3: Propose classification and duplicate evidence

**Files:**
- Modify: `pipeline/skill_registry/intake.py`
- Modify: `tests/unit/test_intake.py`

**Interfaces:**
- Consumes: candidate metadata from Task 2, `tokenize`, `jaccard`, current registry/index records.
- Produces: proposed taxonomy/category and evidence list without making a decision.

- [ ] **Step 1: Write failing classification tests**

```python
def test_classification_aggregates_existing_taxonomy_votes():
    candidate = {"name": "pytest-helper", "description": "Test Python code with pytest"}
    index = [
        discovery("unit-tests", "engineering/testing", "testing", "pytest unit testing"),
        discovery("test-review", "engineering/testing", "testing", "review automated tests"),
        discovery("pdf", "documents/pdf", "documents", "edit PDF files"),
    ]
    assert propose_classification(candidate, index) == {
        "taxonomy": "engineering/testing",
        "category_fine": "testing",
        "classification_status": "proposed",
    }


def test_classification_falls_back_when_no_terms_match():
    assert propose_classification(
        {"name": "xyzzy", "description": "plugh"}, []
    ) == {
        "taxonomy": "workflows-and-management/uncategorized-and-misc",
        "category_fine": "uncategorized",
        "classification_status": "proposed",
    }
```

- [ ] **Step 2: Write failing dedup tests**

Cover four independent signals:

```python
def candidate(**changes):
    value = {
        "source_id": "new-source",
        "source_path": "skills/new-skill",
        "name": "new-skill",
        "load_name": "new-skill",
        "description": "Review Python tests",
        "content_sha256": "b" * 64,
    }
    value.update(changes)
    return value


def existing(**changes):
    value = {
        "skill_id": "asr_existing",
        "source_id": "existing-source",
        "source_path": "skills/existing",
        "load_name": "existing-skill",
        "content_sha256": "a" * 64,
    }
    value.update(changes)
    return value


def test_duplicate_evidence_detects_exact_hash():
    evidence = duplicate_evidence(
        candidate(content_sha256="a" * 64), [existing()], []
    )
    assert evidence == [{
        "kind": "exact_hash",
        "skill_id": "asr_existing",
        "action": "canonical_candidate",
    }]


def test_duplicate_evidence_detects_same_source_path():
    evidence = duplicate_evidence(
        candidate(source_id="existing-source", source_path="skills/existing"),
        [existing()],
        [],
    )
    assert evidence == [{
        "kind": "same_source_path",
        "skill_id": "asr_existing",
        "action": "update_review",
    }]


def test_duplicate_evidence_detects_name_collision():
    evidence = duplicate_evidence(
        candidate(load_name="existing-skill"), [existing()], []
    )
    assert evidence == [{
        "kind": "name_collision",
        "skill_id": "asr_existing",
        "action": "review",
    }]


def test_duplicate_evidence_marks_similarity_for_review_only():
    evidence = duplicate_evidence(
        candidate(name="python-test-review", description="security"),
        [existing(load_name="python-test-audit")],
        [discovery(
            "python-test-audit",
            "engineering/testing",
            "testing",
            "python test review security",
            skill_id="asr_existing",
        )],
    )
    assert evidence == [{
        "kind": "functional_similarity",
        "skill_id": "asr_existing",
        "score": 0.8,
        "action": "review",
    }]
```

For similarity, assert evidence contains:

```python
{
    "kind": "functional_similarity",
    "skill_id": "asr_existing",
    "score": 0.8,
    "action": "review",
}
```

and never contains a decision.

- [ ] **Step 3: Run focused tests and verify failure**

```bash
PYTHONPATH=pipeline python -m pytest tests/unit/test_intake.py -q
```

Expected: FAIL because classification/dedup functions are missing.

- [ ] **Step 4: Implement deterministic classification**

For each existing discovery entry, calculate overlap between candidate `name + description` tokens and entry `name + description + taxonomy + category_fine` tokens. Add the positive overlap count to a score keyed by `(taxonomy, category_fine)`. Select the highest score, then lexicographically smallest taxonomy/category for ties. Zero score uses the documented fallback.

- [ ] **Step 5: Implement evidence-only dedup**

Emit deterministic evidence sorted by `(kind, skill_id)`:

- exact hash when `content_sha256` matches;
- same identity when source ID and source path match;
- name collision when normalized name or load name matches;
- functional similarity when Jaccard over name+description tokens is at least `0.75`.

Do not set `canonical_skill_id`, state, risk, or review decision.

- [ ] **Step 6: Run tests**

```bash
PYTHONPATH=pipeline python -m pytest tests/unit/test_intake.py tests/unit/test_text.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add pipeline/skill_registry/intake.py tests/unit/test_intake.py
git commit -m "feat: propose skill classification and duplicates"
```

---

### Task 4: Produce deterministic manifest and complete review contract

**Files:**
- Modify: `pipeline/skill_registry/intake.py`
- Modify: `pipeline/skill_registry/filesystem.py`
- Modify: `tests/unit/test_intake.py`

**Interfaces:**
- Consumes: Tasks 2–3.
- Produces: `prepare_source(root, spec, staging)`, atomic JSON helper, `manifest.json`, and `review.json` template.

- [ ] **Step 1: Add failing no-mutation and determinism tests**

```python
def test_prepare_source_does_not_mutate_repository(valid_root, tmp_path, fake_checkout):
    before = repository_digest(valid_root)
    payload = prepare_source(valid_root, valid_source_spec(), tmp_path / "stage")
    assert repository_digest(valid_root) == before
    assert payload == json.loads((tmp_path / "stage/manifest.json").read_text())


def test_prepare_source_rejects_existing_source_id(valid_root, tmp_path, fake_checkout):
    spec = valid_source_spec(source_id="existing-source")
    with pytest.raises(IntakeError, match="source_id already exists"):
        prepare_source(valid_root, spec, tmp_path / "stage")


def test_prepare_source_is_deterministic(valid_root, tmp_path, fake_checkout):
    first = prepare_source(valid_root, valid_source_spec(), tmp_path / "a")
    second = prepare_source(valid_root, valid_source_spec(), tmp_path / "b")
    assert first == second


def test_prepare_binds_review_to_exact_manifest(valid_root, tmp_path, fake_checkout):
    prepare_source(valid_root, valid_source_spec(), tmp_path / "stage")
    manifest_bytes = (tmp_path / "stage/manifest.json").read_bytes()
    review = json.loads((tmp_path / "stage/review.json").read_text())
    assert review["manifest_sha256"] == hashlib.sha256(manifest_bytes).hexdigest()
```

Do not include wall-clock fields in the final manifest; deterministic output is preferred, so remove `prepared_at` entirely.

- [ ] **Step 2: Add failing review validation tests**

```python
@pytest.mark.parametrize("mutation", [
    "pending_decision",
    "missing_candidate",
    "extra_candidate",
    "duplicate_candidate",
    "empty_reason",
    "invalid_taxonomy",
    "canonical_without_target",
    "unknown_canonical_target",
    "manifest_digest_mismatch",
])
def test_validate_review_rejects_incomplete_contract(mutation, manifest, valid_review):
    apply_review_mutation(valid_review, mutation)
    with pytest.raises(IntakeError):
        validate_review(manifest.read_bytes(), valid_review, known_skill_ids={"asr_existing"})
```

- [ ] **Step 3: Implement atomic JSON writing**

In `filesystem.py`:

```python
def dump_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
```

Remove the temporary file in an exception handler if it exists.

- [ ] **Step 4: Implement `prepare_source` orchestration**

Use `tempfile.TemporaryDirectory`, exact checkout, discovery, inspection, classification, and dedup. Candidate records contain:

```python
{
    "source_path": relative_source_path,
    "name": inspected["name"],
    "description": inspected["description"],
    "content_sha256": inspected["content_sha256"],
    "file_count": inspected["file_count"],
    "byte_count": inspected["byte_count"],
    "proposed_taxonomy": classification["taxonomy"],
    "proposed_category_fine": classification["category_fine"],
    "duplicate_evidence": evidence,
}
```

Sort candidates by `source_path`. Write manifest and a review template where every decision is `pending`, taxonomy/category copy proposals, canonical target is null, and reason is empty.

- [ ] **Step 5: Implement strict review validation**

Valid rules:

- exactly one review per manifest source path;
- `manifest_sha256` equals SHA-256 of the exact manifest file bytes;
- decision in `import|canonical|quarantine|reject`;
- non-empty reason;
- taxonomy has exactly two safe path segments and no `..`;
- category is a non-empty slug;
- canonical decision requires a known, non-self canonical ID;
- non-canonical decisions require null canonical ID.

- [ ] **Step 6: Run tests**

```bash
PYTHONPATH=pipeline python -m pytest tests/unit/test_intake.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add pipeline/skill_registry/intake.py pipeline/skill_registry/filesystem.py \
  tests/unit/test_intake.py
git commit -m "feat: stage source manifests for review"
```

---

### Task 5: Commit reviewed candidates with TOCTOU and rollback protection

**Files:**
- Modify: `pipeline/skill_registry/intake.py`
- Modify: `pipeline/skill_registry/validator.py`
- Modify: `tests/unit/test_intake.py`
- Modify: `tests/contracts/test_validator.py`

**Interfaces:**
- Consumes: manifest/review contract and source checkout from earlier tasks.
- Produces: `commit_source(root, manifest_path, review_path)` while preserving registry schema version `1`; URL and license evidence remain authoritative in `sources.lock.json`.

- [ ] **Step 1: Add failing TOCTOU tests**

```python
def test_commit_refetches_and_rejects_changed_hash(valid_root, manifest, review, fake_checkout):
    marker = fake_checkout / "skills/new-skill/SKILL.md"
    marker.write_text(marker.read_text() + "changed\n", encoding="utf-8")
    before = repository_digest(valid_root)
    with pytest.raises(IntakeError, match="changed since preparation"):
        commit_source(valid_root, manifest, review)
    assert repository_digest(valid_root) == before


def test_commit_rejects_missing_reviewed_candidate(valid_root, manifest, review, fake_checkout):
    shutil.rmtree(fake_checkout / "skills/new-skill")
    with pytest.raises(IntakeError, match="missing from pinned source"):
        commit_source(valid_root, manifest, review)


def test_commit_rejects_manifest_changed_after_review(valid_root, manifest, review):
    before = repository_digest(valid_root)
    manifest.write_bytes(manifest.read_bytes() + b"\n")
    with pytest.raises(IntakeError, match="manifest digest"):
        commit_source(valid_root, manifest, review)
    assert repository_digest(valid_root) == before
```

- [ ] **Step 2: Add failing mutation/rollback tests**

```python
def test_commit_requires_clean_worktree(valid_root, manifest, review):
    mark_worktree_dirty(valid_root)
    with pytest.raises(IntakeError, match="clean worktree"):
        commit_source(valid_root, manifest, review)


def test_commit_rolls_back_catalog_and_json_on_write_failure(
    valid_root, manifest, review, monkeypatch
):
    before = repository_digest(valid_root)
    real_write = intake.dump_json_atomic
    monkeypatch.setattr(intake, "dump_json_atomic", fail_on_second_write(real_write))
    with pytest.raises(OSError):
        commit_source(valid_root, manifest, review)
    assert repository_digest(valid_root) == before


@pytest.mark.parametrize("taxonomy", ["../escape", "engineering/*", "engineering", "/absolute/x"])
def test_catalog_destination_rejects_unsafe_taxonomy(valid_root, taxonomy):
    with pytest.raises(IntakeError, match="catalog destination"):
        catalog_destination(valid_root, taxonomy, "new-skill")


def test_commit_rejects_existing_catalog_destination(valid_root, manifest, review):
    collision = valid_root / "catalog/engineering/testing/new-skill"
    collision.mkdir(parents=True)
    before = repository_digest(valid_root)
    with pytest.raises(IntakeError, match="destination exists"):
        commit_source(valid_root, manifest, review)
    assert repository_digest(valid_root) == before


def test_catalog_destination_rejects_symlinked_parent(valid_root, tmp_path):
    (valid_root / "catalog/engineering").symlink_to(tmp_path / "outside")
    with pytest.raises(IntakeError, match="symlink"):
        catalog_destination(valid_root, "engineering/testing", "new-skill")
```

- [ ] **Step 3: Preserve schema v1 and normalize the source lock**

Do not copy source URL or license notes into every skill record. Append one
record to `sources.lock.json` containing URL, pinned commit, layout, skills root,
license note, lifecycle, and refresh settings. Skill and quarantine records join
through `source_id` and retain the existing per-skill `license` field. Add a
contract test proving every new record joins to exactly one locked source.
`registry/schema-version.json` remains `1`.

The committed source-lock record is:

```json
{
  "source_id": "new-source",
  "url": "https://github.com/example/skills.git",
  "commit": "cccccccccccccccccccccccccccccccccccccccc",
  "layout": "skills-subdir",
  "skills_root": "skills",
  "metadata_index": null,
  "license_note": "Fixture source license",
  "status": "active",
  "refreshable": true,
  "timeout_seconds": 15
}
```

Production values come directly from the reviewed manifest; tests use the
fixture values above.

- [ ] **Step 4: Implement stable IDs, safe load names, and catalog destinations**

Use `stable_skill_id(source_id, source_path)`. Preserve all existing load names.
Normalize only new upstream names:

```python
def slugify_load_name(name: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not value or len(value) > 128:
        raise IntakeError("invalid load name")
    return value
```

For a new name collision:

```python
def next_load_name(name: str, source_id: str, used: set[str]) -> str:
    if name not in used:
        return name
    base = f"{source_id}--{name}"
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}--{suffix}"
        suffix += 1
    return candidate
```

Call `next_load_name(slugify_load_name(upstream_name), source_id, used_names)`.
Then derive the only permitted destination:

```python
def catalog_destination(root: Path, taxonomy: str, load_name: str) -> tuple[str, Path]:
    parts = taxonomy.split("/")
    safe = re.compile(r"^[a-z0-9][a-z0-9-]*$")
    if len(parts) != 2 or not all(safe.fullmatch(part) for part in parts):
        raise IntakeError("unsafe catalog destination taxonomy")
    if not safe.fullmatch(load_name):
        raise IntakeError("unsafe catalog destination load name")
    raw_catalog = root / "catalog"
    if raw_catalog.is_symlink():
        raise IntakeError("catalog destination root is a symlink")
    catalog_root = raw_catalog.resolve()
    raw_destination = raw_catalog / parts[0] / parts[1] / load_name
    cursor = raw_catalog
    for part in [*parts, load_name]:
        cursor = cursor / part
        if cursor.is_symlink():
            raise IntakeError("catalog destination parent is a symlink")
    destination = raw_destination.resolve()
    if not destination.is_relative_to(catalog_root):
        raise IntakeError("catalog destination escaped root")
    if destination.exists():
        raise IntakeError(f"catalog destination exists: {destination.relative_to(root)}")
    return destination.relative_to(root).as_posix(), destination
```

Compute every destination and verify uniqueness before copying or writing any
file. Reject a symlinked `catalog/` root or any existing/symlinked parent in the
destination chain. Temporary copy directories must be siblings of the validated
destination and must pass the same containment check.

- [ ] **Step 5: Implement commit transaction**

Algorithm:

1. Load manifest and review bytes; reject a manifest digest mismatch.
2. Run `git status --porcelain` and require empty output.
3. Load and validate current registry JSON and the complete review contract.
4. Re-run source preflight and re-fetch the exact commit into a fresh temporary directory.
5. Re-inspect every reviewed non-reject candidate and require hash equality.
6. Build all destination paths and new JSON objects in memory; reject escapes, parent symlinks, duplicate destinations, or existing targets before writing.
7. Run verifier-compatible validation in memory, then copy each accepted bundle to a validated temporary sibling and rename it into place.
8. Write `sources.lock.json`, `skills.json`, `quarantine.json`, and `librarian-index.json` atomically.
9. Run `verify_repository(root)` and require `result == "pass"`.
10. On any exception, restore original JSON bytes and remove only catalog directories created by this operation.

Decision mapping:

- `import`: active, canonical null;
- `canonical`: active, canonical target from review;
- `quarantine`: quarantine record, risk unknown, state quarantined;
- `reject`: no catalog copy and no record.

All non-reject records use:

```python
"risk": "unknown",
"risk_reasons": ["initial-review-required"],
"first_seen_version": "0.2.0",
```

- [ ] **Step 6: Update verifier and contract tests**

Require every new record's `source_id` and `source_commit` to match one locked
source. Require canonical targets to exist, be active, and not themselves point
to another canonical record. Preserve the current rule that Core contains only
active safe records and preserve schema version `1`.

- [ ] **Step 7: Run focused tests**

```bash
PYTHONPATH=pipeline python -m pytest \
  tests/unit/test_intake.py \
  tests/contracts/test_validator.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add pipeline/skill_registry/intake.py pipeline/skill_registry/validator.py \
  registry/skills.json \
  tests/unit/test_intake.py tests/contracts/test_validator.py
git commit -m "feat: commit reviewed source snapshots"
```

---

### Task 6: Expose prepare and commit CLI commands

**Files:**
- Modify: `pipeline/skill_registry/cli.py`
- Create: `tests/integration/test_intake_cli.py`

**Interfaces:**
- Consumes: `prepare_source` and `commit_source`.
- Produces: stable CLI commands with JSON/text output and exit `0/1`.

- [ ] **Step 1: Add failing parser and command tests**

Required prepare invocation:

```bash
skill-registry prepare-source \
  --root PATH \
  --source-id microsoftdocs-agent-skills \
  --url https://github.com/MicrosoftDocs/Agent-Skills.git \
  --commit COMMIT \
  --skills-root skills \
  --license CC-BY-4.0 \
  --license-note "Upstream repository license verified during preparation" \
  --staging PATH \
  --format json
```

Required commit invocation:

```bash
skill-registry commit-source \
  --root PATH \
  --manifest PATH/manifest.json \
  --review PATH/review.json \
  --format json
```

Tests assert:

- prepare success exit `0` and repo digest unchanged;
- invalid source exit `1` on stderr;
- pending review commit exit `1` with no mutation;
- reviewed commit success exit `0` and reports imported/canonical/quarantined/rejected counts;
- no command prints secrets or full skill instructions.

- [ ] **Step 2: Run tests and verify failure**

```bash
PYTHONPATH=pipeline python -m pytest tests/integration/test_intake_cli.py -q
```

Expected: FAIL because commands do not exist.

- [ ] **Step 3: Add parser definitions**

Use flat commands, not nested subparsers. `--commit`, `--source-id`, `--url`, `--license`, `--license-note`, and `--staging` are required for prepare. `--manifest` and `--review` are required for commit. Both support `--format text|json`.

- [ ] **Step 4: Implement output and error handling**

Catch `IntakeError`, print `error=<message>` to stderr, return `1`. JSON success uses `json.dumps(payload, indent=2, sort_keys=True)`. Text prepare prints candidate and review-required counts; text commit prints decision counts and strict verifier result.

- [ ] **Step 5: Run CLI and regression tests**

```bash
PYTHONPATH=pipeline python -m pytest \
  tests/integration/test_intake_cli.py \
  tests/integration/test_runtime_cli.py \
  tests/integration/test_refresh_cli.py -q
```

Expected: PASS; existing verify/refresh/search/read behavior remains intact.

- [ ] **Step 6: Commit**

```bash
git add pipeline/skill_registry/cli.py tests/integration/test_intake_cli.py
git commit -m "feat: expose reviewed source intake commands"
```

---

### Task 7: Document and pilot a second source

**Files:**
- Modify: `README.md`
- Create: `docs/source-intake.md`
- Modify through CLI: `registry/sources.lock.json`
- Modify through CLI: `registry/skills.json`
- Modify through CLI: `registry/quarantine.json`
- Modify through CLI: `librarian-index.json`
- Add through CLI: reviewed catalog bundles under `catalog/`
- Modify: `tests/integration/test_search_quality.py`

**Interfaces:**
- Consumes: complete intake CLI.
- Produces: one real pinned second source and an operator runbook.

- [ ] **Step 1: Document the two-phase workflow**

Explain:

- prepare is untrusted and non-mutating;
- review decisions and canonical rules;
- commit requires clean Git and re-fetches exact commit;
- all imported records remain unknown;
- rollback is `git revert` of the import commit, not manual deletion;
- never point intake at private repos or provide credentials.

- [ ] **Step 2: Verify the pinned official MicrosoftDocs source**

```bash
PILOT_URL=https://github.com/MicrosoftDocs/Agent-Skills.git
PILOT_COMMIT=e03d6ea0dab78954ca902bad9f6556cafe772515
git ls-remote "$PILOT_URL" | awk '{print $1}' | grep -qx "$PILOT_COMMIT"
```

This commit was selected on 2026-07-16. It contains 191 root skill bundles under
`skills/`; GitHub identifies the repository license as `CC-BY-4.0`. The pilot
imports only `azure-blob-storage`; every other candidate is explicitly rejected
with reason `pilot-scope-limited` so V1 validates the pipeline without auditing
191 skills as a side quest.

- [ ] **Step 3: Prepare the pilot without repository mutation**

```bash
before=$(git status --porcelain=v1)
skill-registry prepare-source \
  --root "$PWD" \
  --source-id microsoftdocs-agent-skills \
  --url "$PILOT_URL" \
  --commit "$PILOT_COMMIT" \
  --skills-root skills \
  --license CC-BY-4.0 \
  --license-note "GitHub reports CC-BY-4.0 for MicrosoftDocs/Agent-Skills at the pinned commit" \
  --staging /tmp/microsoftdocs-agent-skills-intake \
  --format json > /tmp/microsoftdocs-agent-skills-prepare.json
after=$(git status --porcelain=v1)
test "$before" = "$after"
jq -e '.candidates | length == 191' /tmp/microsoftdocs-agent-skills-prepare.json
jq -e '.candidates | map(.source_path) | index("skills/azure-blob-storage") != null' \
  /tmp/microsoftdocs-agent-skills-prepare.json
```

If the count or pinned target differs, stop. Do not silently switch commit,
truncate candidates, or choose another skill.

- [ ] **Step 4: Perform manual review**

Edit `/tmp/microsoftdocs-agent-skills-intake/review.json` under these rules:

- `import` only `skills/azure-blob-storage`, and only when source/path/license/hash checks pass and duplicate evidence does not require canonical handling;
- `canonical` only for an exact duplicate with a valid existing target;
- `quarantine` for malformed or policy-sensitive content retained as evidence;
- `reject` every non-target candidate with reason `pilot-scope-limited` and reject the target for unresolved similarity;
- every decision has a concrete reason;
- accept or explicitly correct taxonomy/category for the imported target; rejected candidates retain proposals only as evidence.

The commit command validates the complete review before mutation. Do not create a
temporary clone or add a separate dry-run path in V1.

- [ ] **Step 5: Commit the reviewed pilot**

```bash
test -z "$(git status --porcelain)"
skill-registry commit-source \
  --root "$PWD" \
  --manifest /tmp/microsoftdocs-agent-skills-intake/manifest.json \
  --review /tmp/microsoftdocs-agent-skills-intake/review.json \
  --format json > /tmp/microsoftdocs-agent-skills-commit.json
jq -e '.result == "pass" and .imported == 1 and .rejected == 190' \
  /tmp/microsoftdocs-agent-skills-commit.json
```

- [ ] **Step 6: Add the fixed pilot search acceptance**

Add this exact case to `tests/integration/test_search_quality.py`:

```python
("azure blob storage", {"azure-blob-storage"}),
```

The expected load name is fixed before implementation; changing it requires a
reviewed update to this plan and the pilot source record.

- [ ] **Step 7: Run full verification**

```bash
git diff --check
PYTHONPATH=pipeline python -m pytest -q
PYTHONPATH=pipeline python -m skill_registry.cli verify --strict
```

Expected: all exit `0`, verifier prints `result=pass failed=0`.

- [ ] **Step 8: Commit pilot and documentation**

```bash
git add README.md docs/source-intake.md registry catalog librarian-index.json \
  tests/integration/test_search_quality.py
git commit -m "feat: import first reviewed secondary source"
```

---

### Task 8: Plan B acceptance and stop gate

**Files:**
- No production changes unless an acceptance test exposes a Plan B defect.
- Record evidence in the pull request description.

**Interfaces:**
- Consumes: Tasks 1–7.
- Produces: completed multi-source product goal.

- [ ] **Step 1: Verify repository integrity**

```bash
git diff --check
PYTHONPATH=pipeline python -m pytest -q
PYTHONPATH=pipeline python -m skill_registry.cli verify --strict
```

Expected: all exit `0`.

- [ ] **Step 2: Verify source and risk state**

```bash
jq -e '.sources | map(select(.source_id == "microsoftdocs-agent-skills")) | length == 1' \
  registry/sources.lock.json
jq -e '[.skills[] | select(.source_id == "microsoftdocs-agent-skills") | .risk] | all(. == "unknown")' \
  registry/skills.json
jq -e --slurpfile core registry/core.json \
  '[.skills[] | select(.source_id == "microsoftdocs-agent-skills") | .skill_id] as $ids |
   [$core[0].skill_ids[] | select(. as $id | $ids | index($id))] | length == 0' \
  registry/skills.json
```

Expected: source exists once; every imported active record is unknown; none is Core.

- [ ] **Step 3: Verify on-demand behavior**

```bash
load_name=azure-blob-storage
skill-registry search --root "$PWD" --format json azure blob storage \
  | jq -e --arg name "$load_name" '.matches[0:5] | map(.load_name) | index($name) != null'
set +e
skill-registry read --root "$PWD" --format json "$load_name" \
  > /tmp/imported-read.out 2> /tmp/imported-read.json
status=$?
set -e
test "$status" = "3"
test ! -s /tmp/imported-read.out
jq -e '.error == "confirmation_required" and (has("instructions") | not)' \
  /tmp/imported-read.json
```

Expected: discoverable in top five; read remains confirmation-gated with no instructions.

- [ ] **Step 4: Verify forbidden architecture**

```bash
test "$(find skills -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')" = "1"
! rg -n "mcpServers|superpowers-mcp@|list_skills|pgvector|embedding|openai.*embedding" \
  pipeline skills README.md docs/source-intake.md
```

Expected: only Librarian is installable; no forbidden architecture appears.

- [ ] **Step 5: Confirm CI and stop**

Required PR checks:

```text
test (3.11)           success
test (3.12)           success
test (3.13)           success
strict-verifier       success
```

Stop after these pass. Do not continue into `.well-known`, GitLab, private repositories, embeddings, MCP, marketplace, GUI, telemetry, reputation, automatic updates, or automatic Core promotion. Open a new design cycle only when a concrete source or client proves one of those capabilities necessary.
