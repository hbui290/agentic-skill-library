import os
import re
import shutil
import subprocess
import json
import hashlib
import tempfile
from datetime import datetime, timezone

skills_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
manifest_path = os.path.join(skills_dir, ".antigravity-install-manifest.json")
readme_path = os.path.join(skills_dir, "README.md")
sources_path = os.path.join(skills_dir, "sources.json")
data_dir = os.path.join(skills_dir, "data")
reports_dir = os.path.join(skills_dir, "reports")
origins_path = os.path.join(data_dir, "origins.json")
similars_path = os.path.join(data_dir, "similars.json")
librarian_index_path = os.path.join(skills_dir, "librarian-index.json")

# Naming mappings for classifications
MACRO_CATEGORIES = [
    "ai-and-data", "andruia", "business-and-finance", "devops-and-security",
    "engineering", "marketing-and-seo", "product-and-design",
    "productivity-and-content", "workflows-and-management"
]

def run_cmd(cmd, cwd=None):
    # cmd is an argv list — never a shell string (source URLs are untrusted input).
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Error executing: {' '.join(cmd)}")
        print(result.stderr)
        return False, result.stderr
    return True, result.stdout

def find_leaf_skills():
    # A skill dir is the shallowest dir under a macro category that directly
    # contains regular files (handles skills nested at any depth).
    leafs = []
    for macro in MACRO_CATEGORIES:
        macro_path = os.path.join(skills_dir, macro)
        if not os.path.exists(macro_path):
            continue
        for dirpath, dirs, files in os.walk(macro_path):
            if dirpath != macro_path and any(not f.startswith('.') for f in files):
                leafs.append(os.path.relpath(dirpath, skills_dir))
                dirs[:] = []  # do not descend into a skill
    return sorted(leafs)

def get_current_skill_mapping():
    # Map from skill_folder_name -> absolute_path of its parent directory
    mapping = {}
    dups = set()
    for rel in find_leaf_skills():
        base = os.path.basename(rel)
        if base in mapping:
            dups.add(base)
        mapping[base] = os.path.join(skills_dir, os.path.dirname(rel))
    if dups:
        print(f"⚠️  duplicate skill basenames collapse in mapping: {sorted(dups)}")
    return mapping

def auto_classify_skill(skill_name):
    # Determine which macro and subcategory a new skill should go into based on keywords
    name = skill_name.lower()

    # 1. First, determine the Macro Category using broader keyword checks
    macro = "engineering" # Default macro

    if "andruia" in name:
        macro = "andruia"
    elif any(kw in name for kw in ["agent", "prompt", "llm", "rag", "ai-", "-ai", "ml-", "-ml", "hugging", "claude", "gemini", "memory", "search", "vector", "embed", "mcp", "orchestrat", "langgraph", "pydantic", "context", "token", "cache"]):
        macro = "ai-and-data"
    elif any(kw in name for kw in ["docker", "kubernetes", "aws", "azure", "cloud", "ci-cd", "security", "pentest", "hacking", "vulnerability", "monitoring", "pipeline", "deploy", "dns", "ssl"]):
        macro = "devops-and-security"
    elif any(kw in name for kw in ["seo", "marketing", "copywrit", "conversion", "cro", "email", "social", "linkedin", "ads", "growth"]):
        macro = "marketing-and-seo"
    elif any(kw in name for kw in ["design", "ui", "ux", "aesthetics", "figma", "3d", "motion", "animation", "radix", "tailwind", "css", "theme"]):
        macro = "product-and-design"
    elif any(kw in name for kw in ["finance", "trading", "business", "hr", "odoo", "legal", "compliance", "startup", "sales", "audit", "billing", "revenue"]):
        macro = "business-and-finance"
    elif any(kw in name for kw in ["office", "slide", "document", "excel", "word", "health", "fitness", "wellness", "edu", "coach", "scientific", "math", "video", "transcribe", "youtube"]):
        macro = "productivity-and-content"
    elif any(kw in name for kw in ["workflow", "planning", "project", "git", "github", "wiki", "documentation", "standards", "ddd", "agile", "notes", "jira", "linear"]):
        macro = "workflows-and-management"

    # 2. Next, match the specific Subcategory within that Macro Category
    sub = "uncategorized-and-misc" # Default subcategory

    if macro == "andruia":
        if "consultant" in name: sub = "00-andruia-consultant"
        elif "smith" in name: sub = "10-andruia-skill-smith"
        elif "niche" in name or "intel" in name: sub = "20-andruia-niche-intelligence"
        else: sub = "uncategorized"

    elif macro == "ai-and-data":
        if "prompt" in name: sub = "prompt-engineering-group"
        elif "hugging" in name or "hug-" in name: sub = "hugging-face"
        elif "mcp" in name or "framework" in name: sub = "llm-frameworks-and-mcp"
        elif "rag" in name or "search" in name or "vector" in name or "embed" in name: sub = "rag-and-search"
        elif "memory" in name or "context" in name: sub = "context-and-memory"
        elif "claude" in name or "gemini" in name or "notebooklm" in name: sub = "claude-and-assistants"
        elif "agent" in name or "orchestrat" in name: sub = "agents-and-orchestration"

    elif macro == "devops-and-security":
        if "aws" in name: sub = "aws-cloud"
        elif "azure" in name: sub = "azure-cloud"
        elif "security" in name or "pentest" in name or "hacking" in name or "vulner" in name: sub = "cybersecurity-and-pentesting"
        elif "pipeline" in name or "ci-cd" in name or "github-actions" in name: sub = "ci-cd-and-pipelines"

    elif macro == "marketing-and-seo":
        if "seo" in name: sub = "search-engine-optimization"
        elif "cro" in name or "conversion" in name: sub = "conversion-rate-optimization"
        elif "marketing" in name or "strategy" in name or "copy" in name: sub = "marketing-strategy-and-copy"

    elif macro == "product-and-design":
        if "3d" in name or "animation" in name: sub = "3d-motion-and-animation"
        elif "tailwind" in name or "radix" in name or "system" in name: sub = "design-systems-and-components"

    elif macro == "business-and-finance":
        if "odoo" in name: sub = "odoo-development"
        elif "finance" in name or "trading" in name: sub = "finance-and-trading"
        elif "startup" in name or "business" in name: sub = "startup-and-business-analysis"

    elif macro == "productivity-and-content":
        if "health" in name or "wellness" in name or "fit" in name: sub = "health-and-wellness-analyzers"

    elif macro == "workflows-and-management":
        if "git" in name or "github" in name: sub = "git-and-github-workflows"
        elif "plan" in name or "execut" in name: sub = "planning-and-execution"

    elif macro == "engineering":
        if "refactor" in name or "clean" in name or "quality" in name: sub = "code-quality-and-refactoring"
        elif "database" in name or "postgres" in name or "sql" in name: sub = "databases-and-migrations"
        elif "debug" in name or "error" in name or "bug" in name: sub = "debugging-and-error-handling"
        elif "frontend" in name or "ui" in name: sub = "frontend-and-ui"
        elif "game" in name or "unity" in name or "godot" in name: sub = "game-dev"
        elif "api" in name or "route" in name: sub = "backend-and-apis"

    return macro, sub

# ---------------------------------------------------------------------------
# Multi-source + dedup helpers
# ---------------------------------------------------------------------------

def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def dir_hash(path):
    # Content identity of a skill dir: relative paths + file bytes (dotfiles excluded).
    # NUL delimiters keep {ab:"c"} and {a:"bc"} distinct; symlinks hash their
    # target string so dangling links cannot crash the walk.
    h = hashlib.sha256()
    for dirpath, dirs, files in os.walk(path):
        dirs.sort()
        for f in sorted(files):
            if f.startswith('.'):
                continue
            fp = os.path.join(dirpath, f)
            h.update(os.path.relpath(fp, path).encode() + b"\0")
            # copytree dereferences symlinks into regular files, so hash a live
            # symlink by its resolved content to stay stable across install;
            # only a dangling link falls back to its target string (no crash).
            if os.path.islink(fp) and not os.path.exists(fp):
                h.update(b"dangling:" + os.readlink(fp).encode())
            else:
                with open(fp, "rb") as fh:
                    h.update(fh.read())
            h.update(b"\0")
    return h.hexdigest()

def frontmatter_description(skill_path):
    sm = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(sm):
        return None
    try:
        head = open(sm, encoding="utf-8", errors="replace").read(2000)
    except OSError:
        return None
    m = re.match(r'^---\s*\n(.*?)\n---', head, re.S)
    if not m:
        return None
    d = re.search(r'^description\s*:\s*(.+)', m.group(1), re.M)
    return d.group(1).strip().strip('"\'') if d else None

def desc_tokens(desc):
    return {w for w in re.findall(r"[a-z0-9]+", desc.lower()) if len(w) > 2}

def collect_source_skills(repo_dir, layout):
    # Returns [(skill_name, src_path)] with container units expanded recursively
    # to the same leaf definition find_leaf_skills uses: a dir that directly
    # contains regular files is one skill; a container (subdirs only) recurses.
    if layout == "skills-subdir":
        base = os.path.join(repo_dir, "skills")
        if not os.path.isdir(base):
            print("⚠️  declared layout 'skills-subdir' but no skills/ dir found — skipping source")
            return []
    else:
        base = repo_dir
    skills = []

    def walk_unit(name, path):
        entries = [e for e in os.listdir(path) if not e.startswith('.')]
        if any(os.path.isfile(os.path.join(path, e)) for e in entries):
            skills.append((name, path))
            return
        for child in entries:
            child_path = os.path.join(path, child)
            if os.path.isdir(child_path):
                walk_unit(child, child_path)

    for unit in os.listdir(base):
        unit_path = os.path.join(base, unit)
        if os.path.isdir(unit_path) and not unit.startswith('.'):
            walk_unit(unit, unit_path)
    return skills

def install_skill(name, src_path):
    # Returns the placed "macro/sub" path, or None if the destination already
    # exists (duplicate leaf name within one source run — skip, never raise).
    macro, sub = auto_classify_skill(name)
    dest_parent = os.path.join(skills_dir, macro, sub)
    dest = os.path.join(dest_parent, name)
    if os.path.exists(dest):
        return None
    os.makedirs(dest_parent, exist_ok=True)
    shutil.copytree(src_path, dest)
    return f"{macro}/{sub}"

def replace_skill_dir(src_path, dest_path):
    # Update a skill without a data-loss window: copy to a temp sibling first;
    # only when the copy fully succeeded is the old version removed and swapped.
    tmp = dest_path + ".tmp-upd"
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    try:
        shutil.copytree(src_path, tmp)
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    shutil.rmtree(dest_path)
    os.rename(tmp, dest_path)

def flat_name_map(entries):
    # Shared flat-naming rule (used by sync_flat_skills and the librarian index):
    # unique basenames keep their name; duplicates get the path slug.
    counts = {}
    for e in entries:
        b = os.path.basename(e)
        counts[b] = counts.get(b, 0) + 1
    return {e: (e.replace("/", "-") if counts[os.path.basename(e)] > 1
                else os.path.basename(e)) for e in entries}

def main():
    cfg = load_json(sources_path, None)
    if not cfg or not cfg.get("sources"):
        print("❌ sources.json missing or empty.")
        return
    sources = sorted(cfg["sources"], key=lambda s: s.get("priority", 99))
    primary = sources[0]["name"]

    origins = load_json(origins_path, {})
    similars = load_json(similars_path, {})

    # Backfill ownership: any pre-existing skill without a record belongs to the primary source.
    for rel in find_leaf_skills():
        origins.setdefault(os.path.basename(rel), {"owner": primary, "also": []})

    report = {"collisions": [], "similars": [], "multi_origin": [], "errors": []}
    new_names = []
    totals = {"updated": 0, "unchanged": 0, "new": 0}

    for src in sources:
        print(f"🚀 Fetching source '{src['name']}' from {src['git_url']}...")
        temp_dir = tempfile.mkdtemp()
        success, _ = run_cmd(["git", "clone", "--depth", "1", src["git_url"], temp_dir])
        if not success:
            print(f"❌ Failed to clone {src['name']} — skipping this source.")
            shutil.rmtree(temp_dir)
            continue

        # Cache the source's machine-readable index for the librarian index build.
        idx_file = src.get("index_file")
        if idx_file and os.path.isfile(os.path.join(temp_dir, idx_file)):
            os.makedirs(data_dir, exist_ok=True)
            shutil.copy2(os.path.join(temp_dir, idx_file),
                         os.path.join(data_dir, f"upstream_index_{src['name']}.json"))

        current_mapping = get_current_skill_mapping()

        for name, src_path in collect_source_skills(temp_dir, src.get("layout", "root")):
            try:
                if name in current_mapping:
                    rec = origins.setdefault(name, {"owner": primary, "also": []})
                    existing = os.path.join(current_mapping[name], name)
                    if rec["owner"] == src["name"]:
                        if dir_hash(src_path) != dir_hash(existing):
                            replace_skill_dir(src_path, existing)
                            totals["updated"] += 1
                        else:
                            totals["unchanged"] += 1
                    else:
                        # Layer 1: identical content from another source -> extra origin, no copy.
                        if dir_hash(src_path) == dir_hash(existing):
                            if src["name"] not in rec["also"]:
                                rec["also"].append(src["name"])
                                report["multi_origin"].append(f"{name} also provided identically by {src['name']}")
                        else:
                            # Layer 2: same name, different content -> namespace, never overwrite.
                            ns = f"{name}__{src['name']}"
                            if ns in current_mapping:
                                ns_existing = os.path.join(current_mapping[ns], ns)
                                if dir_hash(src_path) != dir_hash(ns_existing):
                                    replace_skill_dir(src_path, ns_existing)
                                    totals["updated"] += 1
                            else:
                                placed = install_skill(ns, src_path)
                                if placed is None:
                                    report["errors"].append(f"{ns}: destination already exists — skipped")
                                    continue
                                origins[ns] = {"owner": src["name"], "also": []}
                                current_mapping[ns] = os.path.join(skills_dir, placed)
                                report["collisions"].append(
                                    f"{name}: name owned by {rec['owner']}, differing content from {src['name']} stored as {placed}/{ns}")
                                new_names.append(ns)
                                totals["new"] += 1
                else:
                    placed = install_skill(name, src_path)
                    if placed is None:
                        report["errors"].append(f"{name}: destination already exists — skipped")
                        continue
                    origins[name] = {"owner": src["name"], "also": []}
                    current_mapping[name] = os.path.join(skills_dir, placed)
                    new_names.append(name)
                    totals["new"] += 1
                    print(f"🆕 New skill classified: {name} ➔ {placed}")
            except Exception as ex:
                report["errors"].append(f"{name}: {type(ex).__name__}: {ex}")
                print(f"⚠️  {name}: {type(ex).__name__}: {ex} — skipped, pipeline continues")

        shutil.rmtree(temp_dir)

    # Layer 3: semantic similarity for newly added skills, compared against the
    # POST-update on-disk descriptions (so same-run additions can match each other).
    mapping = get_current_skill_mapping()
    if new_names:
        disk_desc = {}
        for other, parent in mapping.items():
            d = frontmatter_description(os.path.join(parent, other))
            if d:
                disk_desc[other] = desc_tokens(d)
        for name in new_names:
            toks = disk_desc.get(name)
            if not toks:
                continue
            hits = []
            for other, otoks in disk_desc.items():
                if other == name or not otoks:
                    continue
                j = len(toks & otoks) / len(toks | otoks)
                if j >= 0.5 and len(toks & otoks) > 5:
                    hits.append(other)
            if hits:
                similars[name] = sorted(set(similars.get(name, []) + hits))
                report["similars"].append(f"{name} ~ {', '.join(hits)}")

    print(f"✅ Sources done: {totals['updated']} updated, {totals['unchanged']} unchanged, {totals['new']} new.")

    # Prune records for skills that no longer exist on disk.
    leaf_names = set(mapping)
    origins = {k: v for k, v in origins.items() if k in leaf_names}
    similars = {k: [s for s in v if s in leaf_names] for k, v in similars.items() if k in leaf_names}
    similars = {k: v for k, v in similars.items() if v}

    save_json(origins_path, origins)
    save_json(similars_path, similars)

    # Dedup review report (rewritten each run with that run's findings).
    os.makedirs(reports_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    lines = [f"# Dedup review — {stamp}", ""]
    for key, title in (("collisions", "Name collisions (namespaced, needs review)"),
                       ("similars", "Semantic similars (needs review)"),
                       ("multi_origin", "Multi-origin confirmations"),
                       ("errors", "Errors (skill skipped, pipeline continued)")):
        lines.append(f"## {title}")
        lines += [f"- {x}" for x in report[key]] if report[key] else ["- none"]
        lines.append("")
    lines.append("Resolve by adding `alias -> canonical` entries to data/aliases.json.")
    with open(os.path.join(reports_dir, "dedup-review.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("⚙️ Rebuilding .antigravity-install-manifest.json...")
    manifest_entries = find_leaf_skills()
    manifest_data = {
        "schemaVersion": 1,
        "updatedAt": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "entries": manifest_entries
    }
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
    print(f"Manifest rebuilt with {len(manifest_entries)} entries.")

    print("📝 Updating README.md tree and categories...")
    run_cmd(["python3", os.path.join(skills_dir, "scripts", "generate_full_ascii_tree.py")])

    print("🛡️ Running path verification checks...")
    success, verify_out = run_cmd(["python3", os.path.join(skills_dir, "scripts", "verify_exact_skills.py")])
    print(verify_out)

    print("🔗 Syncing skills to flat directory...")
    success, sync_out = run_cmd(["python3", os.path.join(skills_dir, "scripts", "sync_flat_skills.py")])
    print(sync_out)

    print("📇 Building librarian-index.json...")
    success, idx_out = run_cmd(["python3", os.path.join(skills_dir, "scripts", "build_librarian_index.py")])
    print(idx_out)

if __name__ == "__main__":
    main()
