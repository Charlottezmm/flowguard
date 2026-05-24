from __future__ import annotations

import pytest

from flowguard.comparison import ComparisonResult, compare_runs


def _run(steps: list[dict], workflow: str = "demo") -> dict:
    return {
        "schema_version": "flowguard.golden.v0.3",
        "workflow": workflow,
        "steps": steps,
    }


def _step(
    step_id: str,
    status: str = "success",
    checks: list[dict] | None = None,
    failures: list[str] | None = None,
    error: str | None = None,
    downstream: list[str] | None = None,
) -> dict:
    return {
        "id": step_id,
        "name": step_id,
        "status": status,
        "source": f"{step_id}.py",
        "failures": failures or [],
        "checks": checks or [],
        "error": error,
        "upstream": [],
        "downstream": downstream or [],
    }


def _check(
    kind: str,
    status: str,
    path: str,
    message: str,
    expected: str,
    actual: str = "",
) -> dict:
    return {
        "kind": kind,
        "status": status,
        "path": path,
        "message": message,
        "expected": expected,
        "actual": actual,
    }


def test_compare_runs_returns_passed_result_with_no_differences() -> None:
    left = _run([_step("build", checks=[_check("non_empty", "passed", "artifact.path", "exists", "file")])])
    right = _run([_step("build", checks=[_check("non_empty", "passed", "artifact.path", "exists", "file")])])

    result = compare_runs(left, right, left_label="baseline", right_label="latest")

    assert result == ComparisonResult(
        passed=True,
        differences=[],
        agent_diff="# FlowGuard Run Comparison\n\nWorkflow: demo\n\nNo differences.",
    )


def test_compare_runs_fails_loud_on_workflow_mismatch() -> None:
    with pytest.raises(ValueError, match="workflow mismatch: baseline=demo, latest=other"):
        compare_runs(_run([], "demo"), _run([], "other"), left_label="baseline", right_label="latest")


def test_compare_runs_aligns_steps_by_id_and_reports_step_changes() -> None:
    left = _run([_step("build"), _step("test")])
    right = _run([_step("test"), _step("deploy")])

    result = compare_runs(left, right, left_label="baseline", right_label="latest")

    assert result.passed is False
    assert result.differences == [
        {
            "type": "step_removed",
            "step_id": "build",
            "baseline": {"id": "build", "status": "success", "name": "build"},
            "latest": None,
        },
        {
            "type": "step_added",
            "step_id": "deploy",
            "baseline": None,
            "latest": {"id": "deploy", "status": "success", "name": "deploy"},
        },
    ]
    assert "- step_removed `build`: baseline had status success; missing in latest" in result.agent_diff
    assert "- step_added `deploy`: latest has status success; missing in baseline" in result.agent_diff


def test_compare_runs_reports_status_check_failure_error_and_downstream_changes() -> None:
    left = _run(
        [
            _step(
                "test",
                status="success",
                checks=[
                    _check("non_empty", "passed", "result.name", "name exists", "non-empty"),
                    _check("equals", "passed", "result.count", "count matches", "3"),
                    _check("schema", "passed", "result", "schema matches", "v1"),
                ],
                failures=["old failure"],
                error=None,
                downstream=["deploy"],
            )
        ]
    )
    right = _run(
        [
            _step(
                "test",
                status="failed",
                checks=[
                    _check("non_empty", "failed", "result.name", "name exists", "non-empty"),
                    _check("schema", "passed", "result", "schema matches", "v1"),
                    _check("range", "passed", "result.score", "score in range", "0..1"),
                ],
                failures=["new failure"],
                error="boom",
                downstream=["notify"],
            )
        ]
    )

    result = compare_runs(left, right, left_label="baseline", right_label="latest")

    assert result.passed is False
    assert result.differences == [
        {
            "type": "step_status_changed",
            "step_id": "test",
            "baseline": "success",
            "latest": "failed",
        },
        {
            "type": "check_status_changed",
            "step_id": "test",
            "check": {
                "kind": "non_empty",
                "path": "result.name",
                "message": "name exists",
                "expected": "non-empty",
            },
            "baseline": "passed",
            "latest": "failed",
        },
        {
            "type": "check_removed",
            "step_id": "test",
            "check": {
                "kind": "equals",
                "path": "result.count",
                "message": "count matches",
                "expected": "3",
            },
            "baseline": "passed",
            "latest": None,
        },
        {
            "type": "check_added",
            "step_id": "test",
            "check": {
                "kind": "range",
                "path": "result.score",
                "message": "score in range",
                "expected": "0..1",
            },
            "baseline": None,
            "latest": "passed",
        },
        {
            "type": "failure_removed",
            "step_id": "test",
            "failure": "old failure",
            "baseline": "old failure",
            "latest": None,
        },
        {
            "type": "failure_added",
            "step_id": "test",
            "failure": "new failure",
            "baseline": None,
            "latest": "new failure",
        },
        {
            "type": "error_changed",
            "step_id": "test",
            "baseline": None,
            "latest": "boom",
        },
        {
            "type": "downstream_impact_changed",
            "step_id": "test",
            "baseline": ["deploy"],
            "latest": ["notify"],
        },
    ]
    assert "## step_status_changed" in result.agent_diff
    assert "- `test`: baseline=success, latest=failed" in result.agent_diff
    assert "## check_status_changed" in result.agent_diff
    assert "- `test` non_empty result.name name exists expected=non-empty: baseline=passed, latest=failed" in result.agent_diff
    assert "## failure_added" in result.agent_diff
    assert "- `test`: new failure" in result.agent_diff
    assert "## downstream_impact_changed" in result.agent_diff
