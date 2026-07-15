from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationReport:
    result: str
    passed: int
    failed: int
    warnings: int
    skipped: int
    findings: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return {"schema_version": 1, "result": self.result, "checks": list(self.findings), "summary": {"passed": self.passed, "failed": self.failed, "warnings": self.warnings, "skipped": self.skipped}}
