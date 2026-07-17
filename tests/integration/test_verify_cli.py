import json
import os
import shutil
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


def test_verify_cli_reports_malformed_input(repo_root, tmp_path):
    root = tmp_path / "repo"
    shutil.copytree(repo_root / "catalog", root / "catalog")
    shutil.copytree(repo_root / "registry", root / "registry")
    shutil.copy(repo_root / "librarian-index.json", root / "librarian-index.json")
    (root / "registry/skills.json").write_text("{")
    env = os.environ | {"PYTHONPATH": str(repo_root / "pipeline")}

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "skill_registry.cli",
            "verify",
            "--strict",
            "--format",
            "json",
            "--root",
            str(root),
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    payload = json.loads(result.stdout)
    assert "registry.input" in {
        item["check_id"] for item in payload["checks"]
    }
