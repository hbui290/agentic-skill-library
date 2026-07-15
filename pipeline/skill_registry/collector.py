from pathlib import Path


def discover_catalog(root: Path) -> list[Path]:
    catalog = root / "catalog"
    found: list[Path] = []
    for macro in sorted(path for path in catalog.iterdir() if path.is_dir()):
        for subcategory in sorted(path for path in macro.iterdir() if path.is_dir()):
            found.extend(sorted(path for path in subcategory.iterdir() if path.is_dir()))
    return found
