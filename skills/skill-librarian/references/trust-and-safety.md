# Trust and safety

`read` returns compact safety metadata after integrity checks. `scanned` means a
static scan completed for this bundle hash and scanner version; review its
signals against the planned action. `unscanned` has no usable cached profile,
`stale` has a mismatched content hash or scanner version, and `scan_error`
could not produce a usable profile; treat each conservatively. A scanned profile,
including `severity: clean`, is not safety approval or a guarantee that the
instructions are safe to follow.

Risk labels are metadata, not an approval gate. The Registry reports metadata;
it does not enforce host tools, intercept commands, or ask the owner for
approval. The consumer agent asks the owner only when its planned action exceeds
the explicit task scope or a high-risk signal requires confirmation. A signal
matching an in-scope action is not by itself a Registry block.

Dangerous, quarantine, inactive, path, symlink, and hash failures cannot be
bypassed. Do not grant credentials or broad permissions to a selected skill.
