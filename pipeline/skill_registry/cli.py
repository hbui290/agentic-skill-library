import argparse
import json
from pathlib import Path

from skill_registry.validator import verify_repository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skill-registry")
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--strict", action="store_true")
    verify.add_argument("--root", type=Path, default=Path.cwd())
    verify.add_argument("--format", choices=("text", "json"), default="text")
    verify.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = verify_repository(args.root.resolve())
    payload = report.to_dict()
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    elif args.format == "json":
        print(rendered, end="")
    else:
        print(f"result={report.result} failed={report.failed}")
    return 1 if report.failed or (args.strict and (report.warnings or report.skipped)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
