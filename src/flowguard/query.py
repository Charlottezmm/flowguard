from __future__ import annotations

import json
from pathlib import Path
from shutil import copy2, rmtree
from typing import Any

from .schema import validate_artifact_schema


RUN_DIR = Path(".flowguard/runs/latest")
GOLDEN_DIR = Path(".flowguard/goldens")
NAMED_RUNS_DIR = Path(".flowguard/runs/named")
RUN_ARTIFACTS = ("trace.json", "workflow_map.json", "agent_context.md", "outcome_report.html")


def load_latest_run(run_dir: Path = RUN_DIR) -> dict[str, Any]:
    trace = _read_json(run_dir / "trace.json")
    validate_artifact_schema("trace", trace)
    return trace


def load_workflow_map(run_dir: Path = RUN_DIR) -> dict[str, Any]:
    workflow_map = _read_json(run_dir / "workflow_map.json")
    validate_artifact_schema("workflow_map", workflow_map)
    return workflow_map


def save_named_run(workflow: str, name: str, run_dir: Path = RUN_DIR, named_runs_dir: Path = NAMED_RUNS_DIR) -> Path:
    _validate_path_segment("workflow", workflow)
    _validate_path_segment("name", name)
    trace = load_latest_run(run_dir)
    if trace.get("workflow") != workflow:
        raise ValueError(f"latest workflow is {trace.get('workflow')}, not {workflow}")

    destination = named_runs_dir / workflow / name
    if destination.exists():
        rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    for artifact_name in RUN_ARTIFACTS:
        source = run_dir / artifact_name
        if source.exists():
            copy2(source, destination / artifact_name)

    return destination


def list_named_runs(workflow: str | None = None, named_runs_dir: Path = NAMED_RUNS_DIR) -> list[dict[str, str]]:
    if workflow is not None:
        _validate_path_segment("workflow", workflow)
    if not named_runs_dir.exists():
        return []

    runs = []
    workflow_dirs = [named_runs_dir / workflow] if workflow else sorted(path for path in named_runs_dir.iterdir() if path.is_dir())
    for workflow_dir in workflow_dirs:
        if not workflow_dir.exists() or not workflow_dir.is_dir():
            continue
        for run_dir in sorted(path for path in workflow_dir.iterdir() if path.is_dir()):
            runs.append({"workflow": workflow_dir.name, "name": run_dir.name, "path": str(run_dir)})
    return runs


def load_named_run(workflow: str, name: str, named_runs_dir: Path = NAMED_RUNS_DIR) -> dict[str, Any]:
    _validate_path_segment("workflow", workflow)
    _validate_path_segment("name", name)
    run_dir = named_runs_dir / workflow / name
    return {
        "trace": load_latest_run(run_dir),
        "workflow_map": load_workflow_map(run_dir),
        "path": run_dir,
    }


def load_agent_context(run_dir: Path = RUN_DIR) -> str:
    path = run_dir / "agent_context.md"
    if not path.exists():
        raise FileNotFoundError(f"FlowGuard agent context not found: {path}")
    return path.read_text(encoding="utf-8")


def load_golden_baseline(workflow: str, name: str = "default", golden_dir: Path = GOLDEN_DIR) -> dict[str, Any]:
    baseline = _read_json(golden_dir / workflow / name / "baseline.json")
    validate_artifact_schema("golden", baseline)
    return baseline


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


def _validate_path_segment(label: str, value: str) -> None:
    path = Path(value)
    if (
        not value
        or value in {".", ".."}
        or path.is_absolute()
        or path.name != value
        or "/" in value
        or "\\" in value
        or ".." in path.parts
    ):
        raise ValueError(f"named run {label} must be a simple path segment: {value!r}")
