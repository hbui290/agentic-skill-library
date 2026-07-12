"""Build librarian-index.json — the librarian's search index.

Joins the cached upstream machine-readable index (descriptions, fine
categories, risk, dates) with this repo's local taxonomy, and falls back to
SKILL.md frontmatter for skills the upstream index does not know.
Standalone: python3 scripts/build_librarian_index.py (no network needed —
reads data/upstream_index_<source>.json cached by update_skills.py).
"""
import os
import json
from datetime import datetime, timezone

from update_skills import (skills_dir, data_dir, sources_path, manifest_path,
                           librarian_index_path, load_json, save_json,
                           dir_hash, frontmatter_description)

aliases_path = os.path.join(data_dir, "aliases.json")
origins_path = os.path.join(data_dir, "origins.json")
similars_path = os.path.join(data_dir, "similars.json")


def main():
    cfg = load_json(sources_path, {"sources": []})
    sources = {s["name"]: s for s in cfg.get("sources", [])}

    # Merge cached upstream indexes, keyed by skill basename (priority order:
    # earlier sources win a key).
    upstream = {}
    for s in sorted(cfg.get("sources", []), key=lambda x: x.get("priority", 99)):
        cached = os.path.join(data_dir, f"upstream_index_{s['name']}.json")
        for e in load_json(cached, []):
            key = e.get("id") or os.path.basename(e.get("path", ""))
            if key and key not in upstream:
                e["_source"] = s["name"]
                upstream[key] = e

    manifest = load_json(manifest_path, {"entries": []})
    entries_rel = manifest.get("entries", [])
    origins = load_json(origins_path, {})
    similars = load_json(similars_path, {})
    aliases = load_json(aliases_path, {}).get("aliases", {})

    # flat_name rule mirrors sync_flat_skills.py: duplicates get slugged paths.
    base_counts = {}
    for rel in entries_rel:
        b = os.path.basename(rel)
        base_counts[b] = base_counts.get(b, 0) + 1

    entries = []
    missing_frontmatter = []
    for rel in entries_rel:
        name = os.path.basename(rel)
        path = os.path.join(skills_dir, rel)
        up = upstream.get(name) or upstream.get(name.split("__")[0])
        desc = frontmatter_description(path) or (up or {}).get("description", "")
        if not desc:
            missing_frontmatter.append(name)
        rec = origins.get(name, {})
        source_repo = rec.get("owner", "")
        src_cfg = sources.get(source_repo, {})
        entries.append({
            "name": name,
            "taxonomy": os.path.dirname(rel),
            "flat_name": rel.replace("/", "-") if base_counts[name] > 1 else name,
            "category_fine": (up or {}).get("category", ""),
            "description": desc,
            "risk": (up or {}).get("risk", "unknown"),
            "source_repo": source_repo,
            "origin": (up or {}).get("source", "") or source_repo,
            "license": (up or {}).get("license", "") or src_cfg.get("license_note", ""),
            "content_hash": dir_hash(path),
            "date_added": (up or {}).get("date_added", ""),
            "similar_to": similars.get(name, []),
            "canonical": aliases.get(name),
        })

    index = {
        "schemaVersion": 1,
        "updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "count": len(entries),
        "missingFrontmatter": missing_frontmatter,
        "entries": entries,
    }
    save_json(librarian_index_path, index)
    with_desc = sum(1 for e in entries if e["description"])
    with_fine = sum(1 for e in entries if e["category_fine"])
    print(f"librarian-index.json: {len(entries)} entries "
          f"({with_desc} with description, {with_fine} with fine category, "
          f"{len(missing_frontmatter)} missing frontmatter).")


if __name__ == "__main__":
    main()
