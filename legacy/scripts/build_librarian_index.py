"""Build librarian-index.json — the librarian's search index.

Joins the cached upstream machine-readable index (descriptions, fine
categories, risk, dates) with this repo's local taxonomy, and falls back to
SKILL.md frontmatter for skills the upstream index does not know.
Standalone: python3 scripts/build_librarian_index.py (no network needed, but
requires every declared data/upstream_index_<source>.json cache created by
update_skills.py).
"""
import os
import json
import sys
from datetime import datetime, timezone

from update_skills import (skills_dir, data_dir, sources_path, manifest_path,
                           librarian_index_path, load_json, save_json,
                           dir_hash, frontmatter_description, flat_name_map)

aliases_path = os.path.join(data_dir, "aliases.json")
origins_path = os.path.join(data_dir, "origins.json")
similars_path = os.path.join(data_dir, "similars.json")

NO_SKILL_MD = "(no SKILL.md) files: "


def synthetic_description(path):
    # Keeps SKILL.md-less units (e.g. container remnants) findable by find.sh.
    try:
        files = sorted(f for f in os.listdir(path) if not f.startswith('.'))[:10]
    except OSError:
        files = []
    return NO_SKILL_MD + ", ".join(files)


def make_entry(rel, root, upstream, origins, similars, aliases, sources,
               base_counts, valid_names=None):
    name = os.path.basename(rel)
    path = os.path.join(root, rel)
    # Exact-key lookup only: a namespaced "foo__src" must NEVER inherit
    # foo's description/risk/license/date — that is a different skill.
    up = upstream.get(name)
    desc = frontmatter_description(path) or (up or {}).get("description", "")
    if not desc:
        desc = synthetic_description(path)
    rec = origins.get(name, {})
    source_repo = rec.get("owner", "")
    src_cfg = sources.get(source_repo, {})
    canonical = aliases.get(name)
    if canonical and valid_names is not None and canonical not in valid_names:
        print(f"⚠️  dangling canonical for '{name}': '{canonical}' not in library — ignored")
        canonical = None
    return {
        "name": name,
        "taxonomy": os.path.dirname(rel),
        "flat_name": rel.replace("/", "-") if base_counts.get(name, 1) > 1 else name,
        "category_fine": (up or {}).get("category", ""),
        "description": desc,
        "risk": (up or {}).get("risk", "unknown"),
        "source_repo": (up or {}).get("source_repo", "") or source_repo,
        "origin": (up or {}).get("source", "") or source_repo,
        "license": (up or {}).get("license", "") or src_cfg.get("license_note", ""),
        "content_hash": dir_hash(path),
        "date_added": (up or {}).get("date_added", ""),
        "similar_to": similars.get(name, []),
        "canonical": canonical,
    }


def main():
    cfg = load_json(sources_path, {"sources": []})
    missing_cache = [
        source["name"]
        for source in cfg.get("sources", [])
        if source.get("index_file") and not os.path.isfile(
            os.path.join(data_dir, f"upstream_index_{source['name']}.json"))
    ]
    if missing_cache:
        print("ERROR: upstream index cache missing for source(s): "
              f"{', '.join(missing_cache)}. Run scripts/update_skills.py first.",
              file=sys.stderr)
        return 1

    sources = {s["name"]: s for s in cfg.get("sources", [])}

    # Merge cached upstream indexes, keyed by skill basename (priority order:
    # earlier sources win a key).
    upstream = {}
    for s in sorted(cfg.get("sources", []), key=lambda x: x.get("priority", 99)):
        cached = os.path.join(data_dir, f"upstream_index_{s['name']}.json")
        for e in load_json(cached, []):
            key = e.get("id") or os.path.basename(e.get("path", ""))
            if key and key not in upstream:
                upstream[key] = e

    manifest = load_json(manifest_path, {"entries": []})
    entries_rel = manifest.get("entries", [])
    origins = load_json(origins_path, {})
    similars = load_json(similars_path, {})
    aliases = load_json(aliases_path, {}).get("aliases", {})

    fmap = flat_name_map(entries_rel)
    base_counts = {}
    for rel in entries_rel:
        b = os.path.basename(rel)
        base_counts[b] = base_counts.get(b, 0) + 1
    valid_names = {os.path.basename(rel) for rel in entries_rel}

    entries = []
    missing_frontmatter = []
    for rel in entries_rel:
        e = make_entry(rel, skills_dir, upstream, origins, similars, aliases,
                       sources, base_counts, valid_names=valid_names)
        e["flat_name"] = fmap[rel]  # single source of truth for the slug rule
        if e["description"].startswith(NO_SKILL_MD):
            missing_frontmatter.append(e["name"])
        entries.append(e)

    index = {
        "schemaVersion": 1,
        "updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "count": len(entries),
        "missingFrontmatter": missing_frontmatter,
        "entries": entries,
    }
    save_json(librarian_index_path, index)
    with_desc = sum(1 for e in entries if not e["description"].startswith(NO_SKILL_MD))
    with_fine = sum(1 for e in entries if e["category_fine"])
    print(f"librarian-index.json: {len(entries)} entries "
          f"({with_desc} with description, {with_fine} with fine category, "
          f"{len(missing_frontmatter)} missing frontmatter).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
