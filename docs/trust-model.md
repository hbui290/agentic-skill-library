# Integrity model

The Registry CLI verifies that a selected file still matches the catalog before reading it.

## States and outcomes

| Record state | Read behavior |
| --- | --- |
| Active | Read after integrity checks |
| Dangerous | Always blocked |
| Quarantine | Always blocked |
| Inactive or missing | Blocked |

Risk labels and the legacy Core list are provenance metadata, not an approval workflow.

## Integrity checks

The CLI requires the path to stay inside `catalog/`, rejects unsafe symlinks, requires `SKILL.md`, and compares the current bundle tree hash with `registry/skills.json`.

Dangerous, quarantine, inactive, path, symlink, and hash failures cannot be bypassed.

## Provenance

Each record has a source ID, pinned source commit, source path, license, and content hash. `registry/skills.json` is authoritative; `librarian-index.json` is discovery metadata only.

The native-Librarian integration lock detects drift in the one native skill. It does not replace catalog provenance, content hash, or quarantine policy.

## Duplicates

Exact Office duplicates are canonicalized in metadata, so search shows the official record only. Original catalog bytes and provenance remain preserved.
