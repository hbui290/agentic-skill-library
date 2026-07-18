import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_baseline_contract_matches_source_snapshot():
    baseline = json.loads((ROOT / "registry/migration/baseline.json").read_text())
    manifest = json.loads((ROOT / ".antigravity-install-manifest.json").read_text())
    migration_index = ROOT / "registry/migration/librarian-index.json"
    assert baseline["source_commit"] == "a3f3ac3bb434884b9847cf6df43a534ec00a6d71"
    assert baseline["legacy_record_count"] == 1954
    assert len(manifest["entries"]) == 1954
    assert sha256(ROOT / ".antigravity-install-manifest.json") == baseline["files"]["manifest_sha256"]
    assert sha256(migration_index) == baseline["files"]["index_sha256"]
    assert sha256(ROOT / "sources.json") == baseline["files"]["sources_sha256"]
