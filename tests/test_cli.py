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


def test_cli_reports_short_errors_without_traceback(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = subprocess.run(
        [sys.executable, "-m", "flowguard.cli", "run", "save", "--workflow", "demo", "--name", "../escape"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "FlowGuard error:" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_run_save_and_list(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = Path(".flowguard/runs/latest")
    run_dir.mkdir(parents=True)
    (run_dir / "trace.json").write_text(
        json.dumps({"run_id": "latest", "workflow": "demo", "steps": [{"id": "demo.step", "status": "success"}]}),
        encoding="utf-8",
    )
    (run_dir / "workflow_map.json").write_text(json.dumps({"workflow": "demo", "steps": []}), encoding="utf-8")
    (run_dir / "agent_context.md").write_text("# Agent Context\n", encoding="utf-8")
    (run_dir / "outcome_report.html").write_text("<html></html>\n", encoding="utf-8")

    save = subprocess.run(
        [sys.executable, "-m", "flowguard.cli", "run", "save", "--workflow", "demo", "--name", "before-fix"],
        check=True,
        capture_output=True,
        text=True,
    )
    listed = subprocess.run(
        [sys.executable, "-m", "flowguard.cli", "run", "list", "--workflow", "demo"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Saved named run: .flowguard/runs/named/demo/before-fix" in save.stdout
    assert "demo/before-fix" in listed.stdout


def test_cli_run_compare_named_run_to_latest(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = Path(".flowguard/runs/latest")
    run_dir.mkdir(parents=True)
    (run_dir / "workflow_map.json").write_text(json.dumps({"workflow": "demo", "steps": []}), encoding="utf-8")
    (run_dir / "agent_context.md").write_text("# Agent Context\n", encoding="utf-8")
    (run_dir / "outcome_report.html").write_text("<html></html>\n", encoding="utf-8")

    (run_dir / "trace.json").write_text(
        json.dumps({"run_id": "latest", "workflow": "demo", "steps": [{"id": "demo.step", "status": "success", "failures": [], "checks": [], "error": None}]}),
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, "-m", "flowguard.cli", "run", "save", "--workflow", "demo", "--name", "before-fix"],
        check=True,
        capture_output=True,
        text=True,
    )

    (run_dir / "trace.json").write_text(
        json.dumps({"run_id": "latest", "workflow": "demo", "steps": [{"id": "demo.step", "status": "failed", "failures": ["bad"], "checks": [], "error": None}]}),
        encoding="utf-8",
    )
    compare = subprocess.run(
        [sys.executable, "-m", "flowguard.cli", "run", "compare", "--workflow", "demo", "--left", "before-fix", "--right", "latest"],
        capture_output=True,
        text=True,
    )

    assert compare.returncode == 1
    assert "Run comparison failed: before-fix -> latest" in compare.stdout
    assert "## step_status_changed" in compare.stdout
    assert "- `demo.step`: before-fix=success, latest=failed" in compare.stdout


def test_cli_run_compare_two_named_runs(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = Path(".flowguard/runs/latest")
    run_dir.mkdir(parents=True)
    (run_dir / "workflow_map.json").write_text(json.dumps({"workflow": "demo", "steps": []}), encoding="utf-8")
    (run_dir / "agent_context.md").write_text("# Agent Context\n", encoding="utf-8")
    (run_dir / "outcome_report.html").write_text("<html></html>\n", encoding="utf-8")

    for name, status in [("before-fix", "failed"), ("after-fix", "success")]:
        (run_dir / "trace.json").write_text(
            json.dumps({"run_id": "latest", "workflow": "demo", "steps": [{"id": "demo.step", "status": status, "failures": [], "checks": [], "error": None}]}),
            encoding="utf-8",
        )
        subprocess.run(
            [sys.executable, "-m", "flowguard.cli", "run", "save", "--workflow", "demo", "--name", name],
            check=True,
            capture_output=True,
            text=True,
        )

    compare = subprocess.run(
        [sys.executable, "-m", "flowguard.cli", "run", "compare", "--workflow", "demo", "--left", "before-fix", "--right", "after-fix"],
        capture_output=True,
        text=True,
    )

    assert compare.returncode == 1
    assert "Run comparison failed: before-fix -> after-fix" in compare.stdout
    assert "- `demo.step`: before-fix=failed, after-fix=success" in compare.stdout


def test_cli_golden_compare_failure_outputs_agent_diff(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = Path(".flowguard/runs/latest")
    run_dir.mkdir(parents=True)
    (run_dir / "workflow_map.json").write_text(json.dumps({"workflow": "demo", "steps": []}), encoding="utf-8")
    (run_dir / "agent_context.md").write_text("# Agent Context\n", encoding="utf-8")

    (run_dir / "trace.json").write_text(
        json.dumps({"run_id": "latest", "workflow": "demo", "steps": [{"id": "demo.step", "status": "success", "failures": [], "checks": [], "error": None}]}),
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, "-m", "flowguard.cli", "golden", "create", "--workflow", "demo", "--name", "default"],
        check=True,
        capture_output=True,
        text=True,
    )

    (run_dir / "trace.json").write_text(
        json.dumps({"run_id": "latest", "workflow": "demo", "steps": [{"id": "demo.step", "status": "failed", "failures": ["bad"], "checks": [], "error": None}]}),
        encoding="utf-8",
    )
    compare = subprocess.run(
        [sys.executable, "-m", "flowguard.cli", "golden", "compare", "--workflow", "demo", "--name", "default"],
        capture_output=True,
        text=True,
    )

    assert compare.returncode == 1
    assert "Golden comparison failed: .flowguard/goldens/demo/default/baseline.json" in compare.stdout
    assert "## step_status_changed" in compare.stdout
    assert "- `demo.step`: golden:default=success, latest=failed" in compare.stdout
