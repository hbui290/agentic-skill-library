import json
from pathlib import Path


class MigrationError(RuntimeError):
    pass


def verify(root: Path) -> dict[str, int]:
    manifest = json.loads((root / "registry/migration/legacy-manifest.json").read_text())
    entries = manifest["entries"]
    if len(entries) != len(set(entries)):
        raise MigrationError("duplicate legacy path")
    missing = [entry for entry in entries if not (root / entry).is_dir()]
    if missing:
        raise MigrationError(f"missing legacy path: {missing[0]}")
    active = sum((root / entry / "SKILL.md").is_file() for entry in entries)
    return {
        "legacy": len(entries),
        "active_candidates": active,
        "markerless": len(entries) - active,
    }


if __name__ == "__main__":
    result = verify(Path(__file__).resolve().parents[1])
    print(json.dumps(result, sort_keys=True))
    if result != {"legacy": 1954, "active_candidates": 1952, "markerless": 2}:
        raise SystemExit(1)
