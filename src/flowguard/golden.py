from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .comparison import compare_runs
from .paths import validate_path_segment
from .query import RUN_DIR, load_latest_run, load_workflow_map
from .schema import GOLDEN_SCHEMA_VERSION, add_schema_version, validate_artifact_schema


GOLDEN_DIR = Path(".flowguard/goldens")


@dataclass(frozen=True)
class GoldenComparison:
    passed: bool
    differences: list[str]
    baseline_path: Path
    agent_diff: str


def create_golden(workflow: str, name: str = "default") -> Path:
    _validate_golden_reference(workflow, name)
    trace = load_latest_run()
    if trace.get("workflow") != workflow:
        raise ValueError(f"latest workflow is {trace.get('workflow')}, not {workflow}")
    workflow_map = load_workflow_map()
    baseline = normalize_run(trace, workflow_map)
    baseline_path = _baseline_path(workflow, name)
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(json.dumps(baseline, indent=2, ensure_ascii=False), encoding="utf-8")
    return baseline_path


def compare_golden(workflow: str, name: str = "default") -> GoldenComparison:
    _validate_golden_reference(workflow, name)
    baseline_path = _baseline_path(workflow, name)
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline = _baseline_for_compare(baseline)
    latest = normalize_run(load_latest_run(), load_workflow_map())
    comparison = compare_runs(baseline, latest, left_label=f"golden:{name}", right_label="latest")
    if comparison.passed:
        return GoldenComparison(True, [], baseline_path, comparison.agent_diff)
    differences = ["latest run does not match golden baseline", *_diff_top_level(baseline, latest)]
    return GoldenComparison(False, differences, baseline_path, comparison.agent_diff)


def normalize_run(trace: dict[str, Any], workflow_map: dict[str, Any]) -> dict[str, Any]:
    map_steps = {_step_id(step): step for step in workflow_map.get("steps", [])}
    return {
        "schema_version": GOLDEN_SCHEMA_VERSION,
        "workflow": trace.get("workflow", "default"),
        "steps": [_normalize_step(step, map_steps.get(_step_id(step), {})) for step in trace.get("steps", [])],
    }


def _normalize_step(step: dict[str, Any], map_step: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _step_id(step),
        "name": step.get("name", _step_id(step)),
        "status": step.get("status", "unknown"),
        "source": _stable_source(step.get("source")),
        "failures": list(step.get("failures", [])),
        "checks": [_normalize_check(check) for check in step.get("checks", step.get("check_results", []))],
        "error": step.get("error"),
        "upstream": list(map_step.get("upstream", [])),
        "downstream": list(map_step.get("downstream", [])),
    }


def _baseline_path(workflow: str, name: str) -> Path:
    return GOLDEN_DIR / workflow / name / "baseline.json"


def _validate_golden_reference(workflow: str, name: str) -> None:
    validate_path_segment("golden workflow", workflow)
    validate_path_segment("golden name", name)


def _baseline_for_compare(baseline: dict[str, Any]) -> dict[str, Any]:
    schema_version = validate_artifact_schema("golden", baseline)
    if schema_version == "legacy-v0.2":
        return add_schema_version("golden", baseline)
    return baseline


def _step_id(step: dict[str, Any]) -> str:
    return str(step.get("id") or step.get("name") or step.get("step") or "unknown")


def _stable_source(source: Any) -> str | None:
    if not source:
        return None
    path = Path(str(source))
    if path.is_absolute():
        return path.name
    return str(path)


def _normalize_check(check: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(check)
    actual = normalized.get("actual")
    if isinstance(actual, str):
        normalized["actual"] = _stable_path(actual)
    return normalized


def _stable_path(value: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        return value
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return path.name


def _diff_top_level(baseline: dict[str, Any], latest: dict[str, Any]) -> list[str]:
    differences = []
    if baseline.get("workflow") != latest.get("workflow"):
        differences.append(f"workflow changed: {baseline.get('workflow')} -> {latest.get('workflow')}")
    if len(baseline.get("steps", [])) != len(latest.get("steps", [])):
        differences.append(f"step count changed: {len(baseline.get('steps', []))} -> {len(latest.get('steps', []))}")
    for index, (expected, actual) in enumerate(zip(baseline.get("steps", []), latest.get("steps", []))):
        if expected != actual:
            differences.append(f"step {index} changed: {expected.get('id')} -> {actual.get('id')}")
            break
    return differences
