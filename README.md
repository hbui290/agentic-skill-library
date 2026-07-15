# Agentic Skill Registry

This is the successor to `hbui290/agentic-library`. It preserves the full
1,954-record catalog while rebuilding the operational pipeline around a pinned,
reviewable registry and a small Core distribution.

## Migration in progress

The complete legacy catalog now lives under `catalog/`. The old in-place update
pipeline is disabled and archived under `legacy/scripts/`; do not use it against
this layout. The original `hbui290/agentic-library` repository remains unchanged
and is the read-only `upstream` source.

Current read-only verification:

```bash
python3 tools/verify_migration.py
python3 -m pytest tests/migration tests/contracts
```

The expected migration reconciliation is:

```text
1954 legacy records
1952 active candidates with SKILL.md
2 markerless records held for quarantine
```

Operational source refresh, Core admission, package installation, and MCP
integration remain intentionally unavailable until their corresponding registry
gates are delivered.

See [migration documentation](docs/migration-from-agentic-library.md) for the
compatibility boundary and [the implementation blueprint](docs/superpowers/specs/2026-07-15-agentic-skill-registry-design.md)
for the staged delivery contract.
