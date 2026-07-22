import argparse
import sys
from pathlib import Path

from skill_registry.filesystem import dump_json_atomic
from skill_registry.safety import SafetyProfileError, build_profile_registry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        payload = build_profile_registry(args.root.resolve())
        dump_json_atomic(args.root / "registry" / "safety-signals.json", payload)
    except (OSError, SafetyProfileError) as error:
        print(f"error={error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
