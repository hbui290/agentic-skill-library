import os
import shutil
import subprocess
import json
import tempfile
from collections import defaultdict
from datetime import datetime, timezone

skills_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
manifest_path = os.path.join(skills_dir, ".antigravity-install-manifest.json")
readme_path = os.path.join(skills_dir, "README.md")

# Naming mappings for classifications
MACRO_CATEGORIES = [
    "ai-and-data", "andruia", "business-and-finance", "devops-and-security",
    "engineering", "marketing-and-seo", "product-and-design",
    "productivity-and-content", "workflows-and-management"
]

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Error executing: {cmd}")
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
    for rel in find_leaf_skills():
        mapping[os.path.basename(rel)] = os.path.join(skills_dir, os.path.dirname(rel))
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

def main():
    print("🚀 Fetching latest updates from sickn33/agentic-awesome-skills on GitHub...")
    temp_dir = tempfile.mkdtemp()

    success, output = run_cmd(f"git clone --depth 1 https://github.com/sickn33/agentic-awesome-skills.git {temp_dir}")
    if not success:
        print("❌ Failed to clone repository.")
        shutil.rmtree(temp_dir)
        return

    repo_skills_dir = os.path.join(temp_dir, "skills")
    if not os.path.exists(repo_skills_dir):
        repo_skills_dir = temp_dir
    
    current_mapping = get_current_skill_mapping()
    
    cloned_units = [d for d in os.listdir(repo_skills_dir) if os.path.isdir(os.path.join(repo_skills_dir, d)) and not d.startswith(".")]

    # Expand container units: an upstream dir with regular files is one skill;
    # a container dir (subdirs only, e.g. libreoffice, sendblue, security)
    # contributes each child dir as an individual skill.
    cloned_skills = []  # (name, src_path)
    for unit in cloned_units:
        unit_path = os.path.join(repo_skills_dir, unit)
        entries = [e for e in os.listdir(unit_path) if not e.startswith('.')]
        has_files = any(os.path.isfile(os.path.join(unit_path, e)) for e in entries)
        if has_files:
            cloned_skills.append((unit, unit_path))
        else:
            for child in entries:
                child_path = os.path.join(unit_path, child)
                if os.path.isdir(child_path):
                    cloned_skills.append((child, child_path))

    updated_count = 0
    new_count = 0

    for skill, src_skill_path in cloned_skills:
        if skill in current_mapping:
            dest_parent = current_mapping[skill]
            dest_skill_path = os.path.join(dest_parent, skill)
            shutil.rmtree(dest_skill_path)
            shutil.copytree(src_skill_path, dest_skill_path)
            updated_count += 1
        else:
            macro, sub = auto_classify_skill(skill)
            dest_parent = os.path.join(skills_dir, macro, sub)
            os.makedirs(dest_parent, exist_ok=True)
            dest_skill_path = os.path.join(dest_parent, skill)
            shutil.copytree(src_skill_path, dest_skill_path)
            new_count += 1
            print(f"🆕 New skill classified: {skill} ➔ {macro}/{sub}")
            
    print(f"✅ Finished updating: {updated_count} skills updated, {new_count} new skills added & classified.")
    shutil.rmtree(temp_dir)

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
    gen_script = os.path.join(skills_dir, "scripts", "generate_full_ascii_tree.py")
    run_cmd(f"python3 {gen_script}")
    
    print("🛡️ Running path verification checks...")
    verify_script = os.path.join(skills_dir, "scripts", "verify_exact_skills.py")
    success, verify_out = run_cmd(f"python3 {verify_script}")
    print(verify_out)

    print("🔗 Syncing skills to flat directory...")
    sync_script = os.path.join(skills_dir, "scripts", "sync_flat_skills.py")
    success, sync_out = run_cmd(f"python3 {sync_script}")
    print(sync_out)

if __name__ == "__main__":
    main()
