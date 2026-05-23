from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from shutil import rmtree
from typing import Any

from .context import build_agent_context
from .report import build_outcome_report
from .workflow_map import build_workflow_map


RUN_DIR = Path(".flowguard/runs/latest")


def begin_run(workflow: str) -> dict[str, Any]:
    """Start a clean latest run for an explicit workflow execution."""
    run_dir = RUN_DIR
    if run_dir.exists():
        rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    now = _now()
    trace = {
        "run_id": "latest",
        "workflow": workflow,
        "started_at": now,
        "updated_at": now,
        "steps": [],
    }
    _write_trace(run_dir, trace)
    _write_workflow_map(run_dir, trace)
    _write_agent_context(run_dir, trace)
    _write_outcome_report(run_dir, trace)
    return trace


def ensure_run(workflow: str = "default") -> dict[str, Any]:
    run_dir = RUN_DIR
    run_dir.mkdir(parents=True, exist_ok=True)

    trace_path = run_dir / "trace.json"
    if trace_path.exists():
        trace = _read_json(trace_path, {})
        trace.setdefault("run_id", "latest")
        trace.setdefault("workflow", workflow)
        trace.setdefault("started_at", _now())
        trace.setdefault("steps", [])
        return trace

    now = _now()
    trace = {
        "run_id": "latest",
        "workflow": workflow,
        "started_at": now,
        "updated_at": now,
        "steps": [],
    }
    _write_trace(run_dir, trace)
    _write_workflow_map(run_dir, trace)
    _write_agent_context(run_dir, trace)
    _write_outcome_report(run_dir, trace)
    return trace


def write_run_artifacts(step_result: dict[str, Any], workflow: str = "default") -> None:
    run_dir = RUN_DIR
    run_dir.mkdir(parents=True, exist_ok=True)

    trace = ensure_run(workflow)
    trace["updated_at"] = _now()
    trace["steps"].append(step_result)
    _write_trace(run_dir, trace)

    _write_workflow_map(run_dir, trace)
    _write_agent_context(run_dir, trace)
    _write_outcome_report(run_dir, trace)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_trace(run_dir: Path, trace: dict[str, Any]) -> None:
    (run_dir / "trace.json").write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_workflow_map(run_dir: Path, trace: dict[str, Any]) -> None:
    workflow_map = build_workflow_map(trace)
    (run_dir / "workflow_map.json").write_text(
        json.dumps(workflow_map, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_agent_context(run_dir: Path, trace: dict[str, Any]) -> None:
    workflow_map = build_workflow_map(trace)
    (run_dir / "agent_context.md").write_text(build_agent_context(trace, workflow_map), encoding="utf-8")


def _write_outcome_report(run_dir: Path, trace: dict[str, Any]) -> None:
    workflow_map = build_workflow_map(trace)
    (run_dir / "outcome_report.html").write_text(build_outcome_report(trace, workflow_map), encoding="utf-8")
