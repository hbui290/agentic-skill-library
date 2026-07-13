# Agentic Library

A categorized, multi-source library of ~2,000 agent skills (`SKILL.md` playbooks) for AI coding agents — Claude Code, Antigravity, Codex CLI, Cursor, Gemini CLI, and others. The whole library lives on disk; an agent never loads all of it into context. A machine-readable **librarian index** lets an agent find the one skill it needs by keyword search, then load just that skill on demand via MCP.

> **Attribution:** This is a restructured, multi-source fork. The founding collection comes from [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills) (itself an aggregation of ~79 upstream repositories, with per-skill licenses tracked there). The original skills belong to their authors. This fork adds: the 9-category hierarchy, the librarian index, multi-source ingestion, and deduplication.

---

## Quick Setup

```bash
# 1. Clone and populate
git clone https://github.com/hbui290/agentic-library.git ~/.agents/skills
python3 ~/.agents/skills/scripts/update_skills.py

# 2. Register the MCP loader (Claude Code)
claude mcp add skills-library --scope user \
  --env SKILLS_PATH="$HOME/.agents/flat-skills" \
  --env SUPERPOWERS_SKILLS_DIR="$HOME/.agents/flat-skills" \
  -- npx -y superpowers-mcp@6.0.1 start
```

The update script clones every source in `sources.json`, auto-classifies new skills, deduplicates, and rebuilds the manifest, directory tree, flat-link directory (`~/.agents/flat-skills`, for MCP), and the librarian index.

---

## How It Works (4 layers)

| Layer | What | Where |
|---|---|---|
| **1. Collect** | `update_skills.py` pulls every repo in `sources.json` and auto-classifies | this repo |
| **2. Index** | `librarian-index.json` — each skill's name, category path, description, risk, source, license | `librarian-index.json` |
| **3. Search** | An agent greps the index by keyword (~0 tokens) to pick 1–3 candidates | any grep tool / a `find-skill` meta-skill |
| **4. Load** | Load only the chosen skill via MCP `read_skill`, or read `~/.agents/flat-skills/<name>/SKILL.md` | `skills-library` MCP server |

The point: the agent searches a compact index instead of listing ~2,000 skills into context, then loads exactly one.

---

## Directory Structure

Skills are organized into **9 macro categories**, each with subcategories:

| Category | Covers |
|---|---|
| [ai-and-data](./ai-and-data) | AI, LLMs, prompts, RAG, MLOps, data processing |
| [andruia](./andruia) | Andru.ia consultancy and niche-intelligence skills |
| [business-and-finance](./business-and-finance) | Business, finance, legal, Odoo ERP, operations |
| [devops-and-security](./devops-and-security) | Cloud, Docker, CI/CD, pentesting, security |
| [engineering](./engineering) | Programming, algorithms, databases, debugging, architecture |
| [marketing-and-seo](./marketing-and-seo) | SEO, marketing, copywriting, CRO, social |
| [product-and-design](./product-and-design) | UI/UX, aesthetics, 3D/motion, design systems |
| [productivity-and-content](./productivity-and-content) | Office automation, health, education, scientific computing |
| [workflows-and-management](./workflows-and-management) | Project management, Git, planning, documentation |

Full nested tree with file links: [DIRECTORY_TREE.md](./DIRECTORY_TREE.md).

**Naming rules:** kebab-case folders; `-and-` to join related concepts; numeric prefixes for sequential project skills (e.g. `00-andruia-consultant`). Structure is a strict 3 levels: `Macro → Subcategory → Skill`.

---

## Configuration & Manifest Contract

*   **Source Manifest:** [.antigravity-install-manifest.json](./.antigravity-install-manifest.json)
*   **Total Registered Skills:** **1,954**

Physical directory structure must always match the manifest 100%.

---

## Librarian Index & Multi-Source

### Librarian Index — [librarian-index.json](./librarian-index.json)
Rebuilt on every update. Each entry: `name`, `flat_name` (loadable flat-directory slug), `taxonomy` (macro/subcategory path), `description`, `category_fine`, `risk`, `source_repo`, `origin`, `license`, `content_hash`, `date_added`, `similar_to`, `canonical`. Agents search it by keyword instead of listing skills. Rebuild standalone (no network, but requires every `data/upstream_index_<source>.json` cache created by `update_skills.py`):
```bash
python3 ~/.agents/skills/scripts/build_librarian_index.py
```

### Source Registry — [sources.json](./sources.json)
Each upstream repo is one entry (`name`, `git_url`, `layout`, `priority`, `license_note`). `update_skills.py` pulls sources in priority order. To add a source, append an entry and re-run the update script.

### Deduplication (3 layers)
1. **Identical content** (SHA256 directory hash) → skipped; the extra origin is recorded in `data/origins.json`.
2. **Same name, different content** → stored as `<name>__<source>`, never overwritten; reported.
3. **Similar descriptions** (token overlap) → flagged in `data/similars.json`; reported.

Findings are written to `reports/dedup-review.md`. The pipeline only *marks* duplicates — a human (or reviewing agent) resolves them by adding `alias → canonical` mappings to [data/aliases.json](./data/aliases.json), and the decision persists across updates.

---

## MCP Integration

To let an agent discover and load skills on demand, run the `superpowers-mcp` server against the flat directory.

1.  **Claude Code (recommended):**
    ```bash
    claude mcp add skills-library --scope user \
      --env SKILLS_PATH="$HOME/.agents/flat-skills" \
      --env SUPERPOWERS_SKILLS_DIR="$HOME/.agents/flat-skills" \
      -- npx -y superpowers-mcp@6.0.1 start
    ```
    The server name `skills-library` and the pinned `superpowers-mcp@6.0.1` are what the librarian tooling expects — keep them in sync if you change either.

2.  **Other IDEs — `mcp_config.json`:**
    ```json
    "skills-library": {
      "command": "npx",
      "args": ["-y", "superpowers-mcp@6.0.1", "start"],
      "env": {
        "SKILLS_PATH": "/Users/<you>/.agents/flat-skills",
        "SUPERPOWERS_SKILLS_DIR": "/Users/<you>/.agents/flat-skills"
      }
    }
    ```
    Replace `<you>` with the local username. Use absolute paths because some IDE MCP clients do not expand `~`. Use `read_skill` to load one skill on demand. Avoid `list_skills` — it returns the whole ~2,000-skill catalog and defeats the token-efficiency design.

### Do I need to copy skills into each project?
No. The MCP server maps the flat directory globally, so any skill is reachable by `@<skill-name>` (IDE chat) or `/` commands (where supported). Copy locally only for: team sharing via Git, restricting an agent to a subset, or environments without MCP.

---

## Update Pipeline

```bash
python3 ~/.agents/skills/scripts/update_skills.py
```

1.  **Multi-source clone:** shallow-clones every repo in `sources.json`, in priority order.
2.  **Dedup + in-place update:** hash-skips unchanged skills, updates changed ones in place (atomic swap — no data-loss window), namespaces name collisions, flags semantic similars.
3.  **Auto-classification:** places new skills into categories by keyword rules; unknowns fall back to `uncategorized-and-misc`.
4.  **Rebuild manifest:** re-indexes to `.antigravity-install-manifest.json`.
5.  **Rebuild tree:** updates `DIRECTORY_TREE.md` and the skill count here.
6.  **Flat sync:** `sync_flat_skills.py` rebuilds the symlinks in `~/.agents/flat-skills`.
7.  **Librarian index:** `build_librarian_index.py` rebuilds `librarian-index.json`.

---

## Verification

```bash
python3 ~/.agents/skills/scripts/verify_exact_skills.py   # manifest ↔ disk
python3 ~/.agents/skills/scripts/test_pipeline.py         # pipeline unit tests
```

`verify_exact_skills.py` should report the current entry count with both SUCCESS lines:
```text
Manifest has N entries.
SUCCESS: No duplicate entries in manifest.
SUCCESS: Every manifest entry exists on disk!
```
`test_pipeline.py` runs stdlib-only reproduction tests for the dedup/hash/index logic (all should pass).
