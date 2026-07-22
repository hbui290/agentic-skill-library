import re
from pathlib import Path


SAFETY_SCANNER_VERSION = 1
SIGNALS = frozenset(
    {"shell", "network", "credential", "filesystem_write", "prompt_injection"}
)
SEVERITIES = frozenset({"clean", "low", "medium", "high"})


RULES = (
    (
        "prompt_injection",
        "prompt-injection-override",
        re.compile(
            r"^\s*(?:[-*+]\s+|\d+[.)]\s+|#{1,6}\s+)?(?:please\s+)?"
            r"(?:ignore|disregard|forget|override)\s+(?:all\s+)?"
            r"(?:previous|prior|above)\s+(?:instructions|rules|prompts)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "credential",
        "credential-access",
        re.compile(
            r"\b(?:read|cat|print|copy|access|steal|upload|send|use)\s+[^\n]*"
            r"(?:~?/\.ssh/|\.aws/credentials|api[_ -]?key|access[_ -]?token|"
            r"secret|password|credentials?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "network",
        "network-command",
        re.compile(
            r"\b(?:curl|wget|httpx|fetch|requests|git\s+clone|"
            r"npm\s+(?:install|publish)|pip(?:3)?\s+install)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "filesystem_write",
        "filesystem-write",
        re.compile(
            r"\b(?:write|create|overwrite|delete|remove|touch|mkdir|rmdir|"
            r"rm|mv|cp|chmod|chown)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "shell",
        "shell-command",
        re.compile(
            r"\b(?:bash|zsh|fish|powershell|cmd(?:\.exe)?|sudo)\b",
            re.IGNORECASE,
        ),
    ),
)


def _severity(signals: set[str]) -> str:
    if not signals:
        return "clean"
    if {"credential", "prompt_injection"} & signals:
        return "high"
    if len(signals) > 1:
        return "medium"
    return "low"


def _negated(line: str, start: int) -> bool:
    return bool(
        re.search(
            r"\b(?:do\s+not|don't|never|avoid)(?:\s+\w+){0,2}\s*$",
            line[:start],
            re.IGNORECASE,
        )
    )


def _profile(
    content_sha256: str,
    status: str,
    signals: set[str],
    evidence: set[tuple[str, int, str]],
) -> dict[str, object]:
    return {
        "content_sha256": content_sha256,
        "scanner_version": SAFETY_SCANNER_VERSION,
        "status": status,
        "signals": sorted(signals),
        "severity": _severity(signals) if status == "scanned" else "high",
        "evidence": [
            {"path": path, "line": line, "rule": rule}
            for path, line, rule in sorted(evidence)
        ],
    }


def scan_skill_bundle(bundle: Path, content_sha256: str) -> dict[str, object]:
    """Return static, deterministic signals for regular files within *bundle*."""
    try:
        if bundle.is_symlink() or not bundle.is_dir():
            raise OSError("bundle must be a non-symlink directory")
        files = sorted(
            bundle.rglob("*"),
            key=lambda item: item.relative_to(bundle).as_posix().encode(),
        )
        signals: set[str] = set()
        evidence: set[tuple[str, int, str]] = set()
        for item in files:
            relative = item.relative_to(bundle).as_posix()
            if item.is_symlink():
                raise OSError(f"symlink rejected: {relative}")
            if not item.is_file():
                continue
            for line_number, line in enumerate(
                item.read_text(encoding="utf-8").splitlines(), start=1
            ):
                for signal, rule, pattern in RULES:
                    match = pattern.search(line)
                    if match and not (
                        signal in {"credential", "network"}
                        and _negated(line, match.start())
                    ):
                        signals.add(signal)
                        evidence.add((relative, line_number, rule))
    except (OSError, UnicodeError, ValueError):
        return _profile(content_sha256, "scan_error", set(), set())
    return _profile(content_sha256, "scanned", signals, evidence)


def compact_profile(
    profile: dict[str, object] | None, content_sha256: str
) -> dict[str, object]:
    """Project a hash-current profile without exposing scan evidence."""
    if profile is None:
        return _compact("unscanned", [], "high")
    if (
        profile.get("content_sha256") != content_sha256
        or profile.get("scanner_version") != SAFETY_SCANNER_VERSION
    ):
        return _compact("stale", [], "high")
    signals = profile.get("signals")
    severity = profile.get("severity")
    if (
        profile.get("status") not in {"scanned", "scan_error"}
        or not isinstance(signals, list)
        or not all(isinstance(signal, str) and signal in SIGNALS for signal in signals)
        or not isinstance(severity, str)
        or severity not in SEVERITIES
    ):
        return _compact("scan_error", [], "high")
    if profile["status"] == "scan_error":
        return _compact("scan_error", sorted(set(signals)), "high")
    return _compact("scanned", sorted(set(signals)), _severity(set(signals)))


def _compact(status: str, signals: list[str], severity: str) -> dict[str, object]:
    return {
        "status": status,
        "signals": signals,
        "severity": severity,
        "scanner_version": SAFETY_SCANNER_VERSION,
    }
