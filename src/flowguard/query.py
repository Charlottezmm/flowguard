from __future__ import annotations

import json
from pathlib import Path
from typing import Any


RUN_DIR = Path(".flowguard/runs/latest")
GOLDEN_DIR = Path(".flowguard/goldens")


def load_latest_run(run_dir: Path = RUN_DIR) -> dict[str, Any]:
    return _read_json(run_dir / "trace.json")


def load_workflow_map(run_dir: Path = RUN_DIR) -> dict[str, Any]:
    return _read_json(run_dir / "workflow_map.json")


def load_agent_context(run_dir: Path = RUN_DIR) -> str:
    path = run_dir / "agent_context.md"
    if not path.exists():
        raise FileNotFoundError(f"FlowGuard agent context not found: {path}")
    return path.read_text(encoding="utf-8")


def load_golden_baseline(workflow: str, name: str = "default", golden_dir: Path = GOLDEN_DIR) -> dict[str, Any]:
    return _read_json(golden_dir / workflow / name / "baseline.json")


def find_failed_step(trace: dict[str, Any] | None = None) -> dict[str, Any] | None:
    trace = trace or load_latest_run()
    failed_steps = [
        step
        for step in trace.get("steps", [])
        if step.get("status") in {"failed", "error"} or step.get("failures") or step.get("error")
    ]
    return failed_steps[-1] if failed_steps else None


def summarize_run(trace: dict[str, Any] | None = None) -> dict[str, Any]:
    trace = trace or load_latest_run()
    failed_step = find_failed_step(trace)
    statuses = [step.get("status") for step in trace.get("steps", [])]
    if "error" in statuses:
        status = "error"
    elif failed_step:
        status = "failed"
    else:
        status = "success"

    return {
        "workflow": trace.get("workflow", "default"),
        "run_id": trace.get("run_id", "latest"),
        "status": status,
        "failed_step": _step_id(failed_step) if failed_step else None,
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"FlowGuard artifact not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _step_id(step: dict[str, Any] | None) -> str | None:
    if not step:
        return None
    return str(step.get("id") or step.get("name") or step.get("step") or "unknown")
