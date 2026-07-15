import json
import os
import subprocess
import sys


def test_verify_cli_writes_machine_report(repo_root):
    env = os.environ | {"PYTHONPATH": str(repo_root / "pipeline")}
    output = repo_root / ".verification-test.json"
    result = subprocess.run(
        [sys.executable, "-m", "skill_registry.cli", "verify", "--strict", "--format", "json", "--output", str(output)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
    )
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads(output.read_text())["result"] == "pass"
    finally:
        output.unlink(missing_ok=True)
