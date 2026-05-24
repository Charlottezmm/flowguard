from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ComparisonResult:
    passed: bool
    differences: list[dict[str, Any]]
    agent_diff: str


def compare_runs(
    left: dict[str, Any],
    right: dict[str, Any],
    left_label: str = "left",
    right_label: str = "right",
) -> ComparisonResult:
    left_workflow = left.get("workflow")
    right_workflow = right.get("workflow")
    if left_workflow != right_workflow:
        raise ValueError(f"workflow mismatch: {left_label}={left_workflow}, {right_label}={right_workflow}")

    differences: list[dict[str, Any]] = []
    left_steps = _steps_by_id(left.get("steps", []), left_label)
    right_steps = _steps_by_id(right.get("steps", []), right_label)

    for step_id in left_steps:
        if step_id not in right_steps:
            differences.append(
                {
                    "type": "step_removed",
                    "step_id": step_id,
                    left_label: _step_summary(left_steps[step_id]),
                    right_label: None,
                }
            )

    for step_id in right_steps:
        if step_id not in left_steps:
            differences.append(
                {
                    "type": "step_added",
                    "step_id": step_id,
                    left_label: None,
                    right_label: _step_summary(right_steps[step_id]),
                }
            )

    for step_id in left_steps:
        if step_id in right_steps:
            differences.extend(_compare_step(step_id, left_steps[step_id], right_steps[step_id], left_label, right_label))

    return ComparisonResult(
        passed=not differences,
        differences=differences,
        agent_diff=_format_agent_diff(str(left_workflow), differences, left_label, right_label),
    )


def _compare_step(
    step_id: str,
    left_step: dict[str, Any],
    right_step: dict[str, Any],
    left_label: str,
    right_label: str,
) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []

    if left_step.get("status") != right_step.get("status"):
        differences.append(
            {
                "type": "step_status_changed",
                "step_id": step_id,
                left_label: left_step.get("status"),
                right_label: right_step.get("status"),
            }
        )

    differences.extend(_compare_checks(step_id, left_step, right_step, left_label, right_label))
    differences.extend(_compare_failures(step_id, left_step, right_step, left_label, right_label))

    if left_step.get("error") != right_step.get("error"):
        differences.append(
            {
                "type": "error_changed",
                "step_id": step_id,
                left_label: left_step.get("error"),
                right_label: right_step.get("error"),
            }
        )

    if left_step.get("downstream", []) != right_step.get("downstream", []):
        differences.append(
            {
                "type": "downstream_impact_changed",
                "step_id": step_id,
                left_label: list(left_step.get("downstream", [])),
                right_label: list(right_step.get("downstream", [])),
            }
        )

    return differences


def _compare_checks(
    step_id: str,
    left_step: dict[str, Any],
    right_step: dict[str, Any],
    left_label: str,
    right_label: str,
) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []
    left_checks = _checks_by_identity(left_step.get("checks", []), step_id, left_label)
    right_checks = _checks_by_identity(right_step.get("checks", []), step_id, right_label)

    for check_key, left_check in left_checks.items():
        if check_key not in right_checks:
            differences.append(
                {
                    "type": "check_removed",
                    "step_id": step_id,
                    "check": _check_identity_dict(left_check),
                    left_label: left_check.get("status"),
                    right_label: None,
                }
            )
        elif left_check.get("status") != right_checks[check_key].get("status"):
            differences.append(
                {
                    "type": "check_status_changed",
                    "step_id": step_id,
                    "check": _check_identity_dict(left_check),
                    left_label: left_check.get("status"),
                    right_label: right_checks[check_key].get("status"),
                }
            )

    for check_key, right_check in right_checks.items():
        if check_key not in left_checks:
            differences.append(
                {
                    "type": "check_added",
                    "step_id": step_id,
                    "check": _check_identity_dict(right_check),
                    left_label: None,
                    right_label: right_check.get("status"),
                }
            )

    return differences


def _compare_failures(
    step_id: str,
    left_step: dict[str, Any],
    right_step: dict[str, Any],
    left_label: str,
    right_label: str,
) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []
    left_failures = list(left_step.get("failures", []))
    right_failures = list(right_step.get("failures", []))
    right_failure_set = set(right_failures)
    left_failure_set = set(left_failures)

    for failure in left_failures:
        if failure not in right_failure_set:
            differences.append(
                {
                    "type": "failure_removed",
                    "step_id": step_id,
                    "failure": failure,
                    left_label: failure,
                    right_label: None,
                }
            )

    for failure in right_failures:
        if failure not in left_failure_set:
            differences.append(
                {
                    "type": "failure_added",
                    "step_id": step_id,
                    "failure": failure,
                    left_label: None,
                    right_label: failure,
                }
            )

    return differences


def _steps_by_id(steps: Any, label: str) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for step in steps or []:
        step_id = _step_id(step)
        if step_id in by_id:
            raise ValueError(f"duplicate step id in {label}: {step_id}")
        by_id[step_id] = step
    return by_id


def _checks_by_identity(checks: Any, step_id: str, label: str) -> dict[str, dict[str, Any]]:
    by_identity: dict[str, dict[str, Any]] = {}
    for check in checks or []:
        identity = _check_identity(check)
        if identity in by_identity:
            raise ValueError(f"duplicate check identity in {label} step {step_id}: {_format_check_identity(check)}")
        by_identity[identity] = check
    return by_identity


def _step_id(step: dict[str, Any]) -> str:
    return str(step.get("id") or step.get("name") or step.get("step") or "unknown")


def _step_summary(step: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _step_id(step),
        "status": step.get("status"),
        "name": step.get("name", _step_id(step)),
    }


def _check_identity(check: dict[str, Any]) -> str:
    return json.dumps(_check_identity_dict(check), sort_keys=True, default=str)


def _check_identity_dict(check: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": check.get("kind"),
        "path": check.get("path"),
        "message": check.get("message"),
        "expected": check.get("expected"),
    }


def _format_agent_diff(
    workflow: str,
    differences: list[dict[str, Any]],
    left_label: str,
    right_label: str,
) -> str:
    lines = ["# FlowGuard Run Comparison", "", f"Workflow: {workflow}"]
    if not differences:
        return "\n".join([*lines, "", "No differences."])

    current_type = None
    for difference in differences:
        difference_type = difference["type"]
        if difference_type != current_type:
            lines.extend(["", f"## {difference_type}"])
            current_type = difference_type
        lines.append(_format_difference(difference, left_label, right_label))
    return "\n".join(lines)


def _format_difference(difference: dict[str, Any], left_label: str, right_label: str) -> str:
    step_id = difference["step_id"]
    difference_type = difference["type"]
    if difference_type == "step_removed":
        return f"- step_removed `{step_id}`: {left_label} had status {difference[left_label]['status']}; missing in {right_label}"
    if difference_type == "step_added":
        return f"- step_added `{step_id}`: {right_label} has status {difference[right_label]['status']}; missing in {left_label}"
    if difference_type == "check_status_changed":
        return (
            f"- `{step_id}` {_format_check_identity(difference['check'])}: "
            f"{left_label}={difference[left_label]}, {right_label}={difference[right_label]}"
        )
    if difference_type == "check_removed":
        return f"- `{step_id}` {_format_check_identity(difference['check'])}: missing in {right_label}"
    if difference_type == "check_added":
        return f"- `{step_id}` {_format_check_identity(difference['check'])}: added in {right_label}"
    if difference_type in {"failure_added", "failure_removed"}:
        return f"- `{step_id}`: {difference['failure']}"
    return f"- `{step_id}`: {left_label}={difference[left_label]}, {right_label}={difference[right_label]}"


def _format_check_identity(check: dict[str, Any]) -> str:
    return f"{check.get('kind')} {check.get('path')} {check.get('message')} expected={check.get('expected')}"
