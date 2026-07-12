# 🌌 Agentic Skills Library (Categorized)

> [!IMPORTANT]
> **Attribution Notice:** This repository is a restructured fork of [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills) (formerly `antigravity-awesome-skills`). The original skills are authored by the contributors of the upstream repository. This fork reorganizes the flat folder structure into a categorized multi-tier hierarchy to optimize context search and prevent flat-directory parsing performance bottlenecks for AI agents in Antigravity IDE, Claude Code, and other environments.

Welcome to the **Skills Library** for agentic tools (Antigravity IDE & CLI, Claude Code, Codex CLI, Cursor, Gemini CLI...). This repository contains behavior playbooks (`SKILL.md`) that help AI agents perform automated tasks, planning, debugging, and system optimization.

To improve search efficiency and avoid I/O bottlenecks in flat directories, the skills are categorized into a multi-tier folder structure.

---

## 📥 Quick Setup

To set up the skills library on a new machine, run this single command in your terminal:

```bash
git clone https://github.com/hbui290/agentic-categorized-skills.git ~/.agents/skills && python3 ~/.agents/skills/scripts/update_skills.py
```

This command will:
1. Clone the repository to your local directory `~/.agents/skills`.
2. Automatically pull the latest upstream skills, run auto-classification, rebuild index/manifests, and establish the flat-linking directory `~/.agents/flat-skills` for MCP.

Next, configure the **`superpowers`** MCP server in your IDE's `mcp_config.json` as described in the [MCP Integration](#-mcp-integration) section below.

---

## 🌲 Detailed Directory Tree

To view the complete list and nested structure of all registered skills with direct file links, please refer to the dedicated [DIRECTORY_TREE.md](./DIRECTORY_TREE.md) file.

## 📂 Directory Structure Details

The library is organized into **9 Macro Categories**, each containing specialized subcategories:

### 1. [ai-and-data](./ai-and-data)
Skills related to Artificial Intelligence, Data Processing, MLOps, RAG, and Large Language Models (LLMs).

### 2. [andruia](./andruia)
Consultancy, expert skill design, and niche intelligence playbooks for Andruia.

### 3. [business-and-finance](./business-and-finance)
Business analysis, finance, Odoo development, legal compliance, and operations.

### 4. [devops-and-security](./devops-and-security)
Security, pentesting, cloud infrastructure management, automation, and CI/CD pipelines.

### 5. [engineering](./engineering)
Software development, algorithms, system architecture, mobile/game development, and codebase management.

### 6. [marketing-and-seo](./marketing-and-seo)
Marketing strategies, SEO, Conversion Rate Optimization (CRO), and social media outreach.

### 7. [product-and-design](./product-and-design)
UI/UX design, aesthetic styles, 3D motion, animation, and frontend performance.

### 8. [productivity-and-content](./productivity-and-content)
Office automation, health and wellness, educational content, and scientific computing.

### 9. [workflows-and-management](./workflows-and-management)
Project management, collaboration workflows, agent execution paths, and technical documentation.

---

## 🎯 Agent Taxonomy & Classification Rules

To help AI agents maintain consistency when adding or moving skills, adhere to the following classification guidelines:

### 1. Domain Mapping Decision Matrix

Refer to the matrix below to select the appropriate **Macro Category** for a new skill:

| Skill Task Domain | Macro Category | Example Subcategories |
| :--- | :--- | :--- |
| AI, LLMs, Prompts, MLOps, Data | `ai-and-data` | `agents-and-orchestration`, `rag-and-search` |
| Consultancy, Niche Intelligence for Andruia | `andruia` | `00-andruia-consultant` |
| Business, Finance, Legal, Odoo ERP | `business-and-finance` | `odoo-development`, `startup-and-business-analysis` |
| AWS/Azure Cloud, Docker, CI/CD, Pentesting, Security | `devops-and-security` | `cybersecurity-and-pentesting`, `azure-cloud` |
| Programming, Languages, Algorithms, DB, Low-level | `engineering` | `languages-and-syntax`, `code-quality-and-refactoring` |
| SEO, Marketing, Copywriting, Social media, CRO | `marketing-and-seo` | `search-engine-optimization`, `marketing-strategy-and-copy` |
| UI/UX Design, Aesthetics, 3D/Motion, Figma | `product-and-design` | `ux-principles-and-design-taste`, `design-systems-and-components` |
| Office tools, Health, Education, Math/Science | `productivity-and-content` | `cloud-and-office-automation`, `scientific-computing` |
| Project management, DDD, Git, Planning, Docs | `workflows-and-management` | `planning-and-execution`, `git-and-github-workflows` |

### 2. Folder Naming Rules
*   **Kebab-case:** All subcategories and skill folder names must be lowercase and separated by hyphens (e.g., `code-quality-and-refactoring`).
*   **Conjunctions (`*-and-*`):** Use `and` to combine closely related concepts (e.g., `languages-and-syntax`). Do not use symbols like `&` or `+`.
*   **Special Prefixes:** Use numerical prefixes for sequential project-specific skills (e.g., `00-andruia-consultant`, `10-andruia-skill-smith`).

### 3. Adding a New Skill
1.  **Select Destination:** Match the task against the matrix to find the correct `Macro/Subcategory` path (e.g., `./ai-and-data/prompt-engineering-group/your-skill`).
2.  **Create Structure:** Create the skill directory and place a structured `SKILL.md` inside it.
3.  **Register in Manifest:** Add the relative path to the `entries` array in [.antigravity-install-manifest.json](./.antigravity-install-manifest.json) in alphabetical order, and update the `updatedAt` timestamp.

---

## 🧭 Classification & Search Principles

### 1. Classification Principles
*   **Context-driven Grouping:** Skills are grouped by their practical application context.
*   **Strict 3-level Hierarchy:** To prevent recursive scanning loops and file I/O bottlenecks, the structure is restricted to 3 levels: `Root` ➔ `Macro Category` ➔ `Subcategory` ➔ `Skill Directory`.
*   **Disk-to-Manifest Sync:** Physical directory structure must always match the index in `.antigravity-install-manifest.json` 100%.

### 2. Search & Resolution Principles
*   **Manifest-First Lookup:** AI agents should load `.antigravity-install-manifest.json` in memory to locate skills instead of recursively scanning the disk with shell tools.
*   **Relative Path Filtering:** Filter the manifest list by keywords (e.g., `react`) to resolve relevant skills.
*   **Identifier Separation:** The calling token (e.g., `@clean-code`) is defined in the frontmatter metadata of `SKILL.md` independently of the physical folder path.

---

## ⚙️ Configuration & Manifest Contract

*   **Source Manifest:** [.antigravity-install-manifest.json](./.antigravity-install-manifest.json)
*   **Total Registered Skills:** **1,952**

---

## 📚 Librarian Index & Multi-Source

This library is an **encyclopedia**: it aggregates skills from multiple upstream repositories while never loading the whole catalog into an agent's context. Two components make that work:

### Librarian Index — [librarian-index.json](./librarian-index.json)
Machine-readable search index rebuilt on every update. Each entry carries `name`, `taxonomy` (macro/subcategory path), `description`, `category_fine`, `risk`, `source_repo`, `origin`, `license`, `content_hash`, `similar_to`, and `canonical`. Agents search it by keyword (grep — ~0 tokens) instead of listing skills. Rebuild standalone (no network):
```bash
python3 ~/.agents/skills/scripts/build_librarian_index.py
```

### Source Registry — [sources.json](./sources.json)
Every upstream repo is one entry (`name`, `git_url`, `layout`, `priority`, `license_note`). `update_skills.py` pulls each source in priority order. Adding a source = appending an entry and re-running the update script.

### Deduplication (3 layers)
1. **Identical content** (SHA256 dir hash) → skipped; extra origin recorded in `data/origins.json`.
2. **Same name, different content** → stored as `<name>__<source>`, never overwritten; reported.
3. **Similar descriptions** (token overlap) → flagged in `data/similars.json`; reported.

Findings land in `reports/dedup-review.md`. The pipeline only *marks* duplicates — a human/agent review resolves them via `alias → canonical` mappings in [data/aliases.json](./data/aliases.json), and decisions persist across updates.

---

## 🔗 MCP Integration

To enable AI agents to automatically discover and use these skills, connect them using the **`superpowers`** MCP server:

1.  **Configure `mcp_config.json`:**
    Link the flat directory by specifying `SKILLS_PATH` and `SUPERPOWERS_SKILLS_DIR` in your IDE's MCP config:
    ```json
    "superpowers": {
      "command": "npx",
      "args": ["-y", "superpowers-mcp", "start"],
      "env": {
        "SKILLS_PATH": "~/.agents/flat-skills",
        "SUPERPOWERS_SKILLS_DIR": "~/.agents/flat-skills"
      }
    }
    ```

### 💡 Why is this structure optimized?
*   **Token Efficiency:**
    1.  *MCP Gateway:* The agent loads only the specific `SKILL.md` needed for the active task rather than reading the entire library.
    2.  *Categorization:* Dividing skills into directories allows semantic search tools to target relevant categories, filtering out noise and saving token overhead.

### ❓ Do I need to copy or symlink skills into each project?
*   **No, normally not:** The global `superpowers` MCP server maps the flat skills directory globally. You can invoke any skill using `@<skill-name>` (in the IDE chat) or `/` commands (where supported by CLI).
*   **When to copy/symlink locally:**
    1.  *Team Collaboration (Git):* To share skills with team members in the same repository.
    2.  *Scope Restricting:* To lock agent capabilities to a specific subset of local skills.
    3.  *Environments without MCP:* For runtimes that do not support MCP server installations.

---

## 🚀 How to Use Skills

AI agents map skills by the name defined in the `SKILL.md` frontmatter, independent of the folder path:
*   **IDE Chat:** Use `@<skill-name>` (e.g., `@clean-code`, `@figma-automation`).
*   **CLI Commands:** Use `/` commands (where supported).

## 🔄 Auto-Update Script

Use the automation script to fetch updates from upstream without breaking the categorization structure:
*   **Script Path:** [update_skills.py](./scripts/update_skills.py)
*   **Execution Command:**
    ```bash
    python3 ~/.agents/skills/scripts/update_skills.py
    ```

### ⚙️ Update Pipeline:
1.  **Multi-Source Clone:** Shallow-clones every repository listed in `sources.json`, in priority order.
2.  **Dedup + In-place Update:** Hash-skips unchanged skills, updates changed skills within their current category folders, namespaces name collisions, flags semantic similars (see Deduplication above).
3.  **Auto-Classification:** Places new skills into appropriate categories using keyword rules. Unknown skills fall back to `uncategorized-and-misc`.
4.  **Rebuild Manifest:** Re-indexes the directory structure to `.antigravity-install-manifest.json`.
5.  **Rebuild README:** Updates the ASCII directory tree in `README.md`.
6.  **Flat Sync:** Executes `sync_flat_skills.py` to rebuild symlinks in the flat directory for MCP.
7.  **Librarian Index:** Executes `build_librarian_index.py` to rebuild `librarian-index.json` (upstream index JOIN local taxonomy, frontmatter fallback).

---

## 🛡️ Verification

Verify the integrity of the local skills library:
```bash
python3 ~/.agents/skills/scripts/verify_exact_skills.py
```
If the output is:
```text
Manifest has 1952 entries.
SUCCESS: No duplicate entries in manifest.
SUCCESS: Every manifest entry exists on disk!
```
$\rightarrow$ Your skills library is 100% verified.
