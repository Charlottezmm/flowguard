from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_cli_context_remains_default(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = Path(".flowguard/runs/latest")
    run_dir.mkdir(parents=True)
    (run_dir / "agent_context.md").write_text("# Agent Context\n", encoding="utf-8")

    result = subprocess.run([sys.executable, "-m", "flowguard.cli"], check=True, capture_output=True, text=True)

    assert result.stdout == "# Agent Context\n\n"


def test_cli_golden_create_and_compare(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = Path(".flowguard/runs/latest")
    run_dir.mkdir(parents=True)
    (run_dir / "trace.json").write_text(
        json.dumps({"run_id": "latest", "workflow": "demo", "steps": [{"id": "demo.step", "status": "success", "failures": [], "checks": [], "error": None}]}),
        encoding="utf-8",
    )
    (run_dir / "workflow_map.json").write_text(json.dumps({"workflow": "demo", "steps": []}), encoding="utf-8")
    (run_dir / "agent_context.md").write_text("# Agent Context\n", encoding="utf-8")

    create = subprocess.run(
        [sys.executable, "-m", "flowguard.cli", "golden", "create", "--workflow", "demo", "--name", "default"],
        check=True,
        capture_output=True,
        text=True,
    )
    compare = subprocess.run(
        [sys.executable, "-m", "flowguard.cli", "golden", "compare", "--workflow", "demo", "--name", "default"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Created golden baseline" in create.stdout
    assert "Golden comparison passed" in compare.stdout


def test_cli_golden_requires_subcommand(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = subprocess.run([sys.executable, "-m", "flowguard.cli", "golden"], capture_output=True, text=True)

    assert result.returncode != 0
    assert "usage:" in result.stderr
