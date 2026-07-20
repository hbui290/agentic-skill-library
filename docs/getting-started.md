# Getting started

This guide is for operating Agentic Skill Library locally. Read the
[README](../README.md) first for the product overview.

## 1. Install the local CLI

```bash
git clone https://github.com/hbui290/agentic-skill-library.git \
  ~/.agents/agentic-skill-library
cd ~/.agents/agentic-skill-library

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
export AGENTIC_SKILL_REGISTRY_ROOT="$HOME/.agents/agentic-skill-library"

skill-registry verify --strict
```

Expected output includes:

```text
result=pass failed=0
```

## 2. Install the one native skill

Install only [`skills/skill-librarian`](../skills/skill-librarian/) using
OpenAI's `$skill-installer`. Do not install `catalog/` into
`~/.codex/skills`; catalog skills remain repository data until the Librarian
selects one for a task.

## 3. Search without loading instructions

```bash
skill-registry search \
  --root "$AGENTIC_SKILL_REGISTRY_ROOT" \
  --limit 10 --format json \
  youtube transcript
```

Search returns metadata only. The JSON response is:

```json
{"query": "youtube transcript", "matches": []}
```

No-match is valid: the command exits `0` and the agent can continue without a
library skill.

## 4. Read a selected active skill

Any selected active skill can be read directly:

```bash
skill-registry read \
  --root "$AGENTIC_SKILL_REGISTRY_ROOT" \
  --format json moyu
```

Before returning instructions, the CLI checks:

```text
record state
→ quarantine and dangerous policy
→ catalog path containment and SKILL.md
→ symlink safety and tree hash
```

`unknown`, `review`, and `safe` are catalog metadata, not a confirmation gate.
Quarantine, inactive, dangerous, path, symlink, and hash failures always exit
`1` and cannot be bypassed.

## 5. Let the Librarian route a task

The Librarian searches up to ten candidates and may retry once with broader
terms. It selects up to five domain skills concurrently for a phase, assigns
them `primary` or `supporting` roles, and chooses `single`, `sequential`, or
`parallel` composition.

A large task can have additional phases. Each new phase gets a new search and
selection; only the prior phase's needed output is handed forward. It does not
keep every earlier `SKILL.md` in context.

Official Superpowers process skills are separate from the domain-skill quota.

## Next references

- [Architecture](architecture.md)
- [Trust model](trust-model.md)
- [Source intake](source-intake.md)
