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
        if not isinstance(sources, list):
            raise TypeError
        for source in sources:
            if not isinstance(source, dict):
                raise TypeError
            source["source_id"]
            source["url"]
            source["commit"]
            source["status"]
            source["refreshable"]
            source["timeout_seconds"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise SourceRefreshError("invalid source lock") from error

    records: list[dict[str, object]] = []
    for source in sources:
        if source["status"] == "retired" or not source["refreshable"]:
            records.append(
                {
                    "source_id": source["source_id"],
                    "pinned_commit": source["commit"],
                    "observed_commit": None,
                    "status": "retired",
                }
            )
            continue
        try:
            output = runner(
                ["git", "ls-remote", source["url"], "HEAD"],
                text=True,
                stderr=subprocess.PIPE,
                timeout=source["timeout_seconds"],
            )
            observed = output.split()[0]
            if not COMMIT.fullmatch(observed):
                raise ValueError("invalid commit")
        except (IndexError, ValueError, subprocess.SubprocessError, OSError) as error:
            records.append(
                {
                    "source_id": source["source_id"],
                    "pinned_commit": source["commit"],
                    "observed_commit": None,
                    "status": "error",
                    "error": type(error).__name__,
                }
            )
            continue
        records.append(
            {
                "source_id": source["source_id"],
                "pinned_commit": source["commit"],
                "observed_commit": observed,
                "status": "current" if observed == source["commit"] else "behind",
            }
        )
    return {
        "result": "error" if any(item["status"] == "error" for item in records) else "pass",
        "sources": records,
    }
