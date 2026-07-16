import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_baseline_contract_matches_source_snapshot():
    baseline = json.loads((ROOT / "registry/migration/baseline.json").read_text())
    manifest = json.loads((ROOT / ".antigravity-install-manifest.json").read_text())
    index = json.loads((ROOT / "librarian-index.json").read_text())
    legacy_index = {
        **index,
        "count": baseline["legacy_record_count"],
        "entries": [entry for entry in index["entries"] if "skill_id" not in entry],
    }
    assert baseline["source_commit"] == "a3f3ac3bb434884b9847cf6df43a534ec00a6d71"
    assert baseline["legacy_record_count"] == 1954
    assert len(manifest["entries"]) == 1954
    assert sha256(ROOT / ".antigravity-install-manifest.json") == baseline["files"]["manifest_sha256"]
    legacy_index_bytes = json.dumps(legacy_index, indent=2, ensure_ascii=False).encode()
    assert hashlib.sha256(legacy_index_bytes).hexdigest() == baseline["files"]["index_sha256"]
    assert sha256(ROOT / "sources.json") == baseline["files"]["sources_sha256"]
