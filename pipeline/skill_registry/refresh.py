import json
import re
import subprocess
from pathlib import Path
from typing import Callable


COMMIT = re.compile(r"^[0-9a-f]{40}$")


class SourceRefreshError(RuntimeError):
    pass


def refresh_sources(root: Path, runner: Callable[..., str] = subprocess.check_output) -> dict[str, object]:
    try:
        sources = json.loads((root / "registry/sources.lock.json").read_text(encoding="utf-8"))["sources"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise SourceRefreshError("invalid source lock") from error

    records = []
    for source in sources:
        try:
            output = runner(["git", "ls-remote", source["url"], "HEAD"], text=True, stderr=subprocess.PIPE)
            observed = output.split()[0]
        except (IndexError, KeyError, subprocess.SubprocessError, OSError) as error:
            raise SourceRefreshError(f"source {source.get('source_id', '<unknown>')} returned no commit") from error
        if not COMMIT.fullmatch(observed):
            raise SourceRefreshError(f"source {source.get('source_id', '<unknown>')} returned no commit")
        records.append(
            {
                "source_id": source["source_id"],
                "pinned_commit": source["commit"],
                "observed_commit": observed,
                "status": "current" if observed == source["commit"] else "behind",
            }
        )
    return {"sources": records}
