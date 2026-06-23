from __future__ import annotations

import json
from pathlib import Path

from flowguard.golden import compare_golden, create_golden, normalize_run


def _write_latest(tmp_path: Path, trace: dict, workflow_map: dict | None = None) -> None:
    run_dir = tmp_path / ".flowguard" / "runs" / "latest"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "trace.json").write_text(json.dumps(trace), encoding="utf-8")
    (run_dir / "workflow_map.json").write_text(json.dumps(workflow_map or {"workflow": trace["workflow"], "steps": []}), encoding="utf-8")
    (run_dir / "agent_context.md").write_text("# Agent Context\n", encoding="utf-8")


def test_normalize_run_ignores_unstable_fields() -> None:
    normalized = normalize_run(
        {
            "run_id": "latest",
            "workflow": "demo",
            "started_at": "now",
            "updated_at": "later",
            "steps": [
                {
                    "id": "demo.step",
                    "name": "demo.step",
                    "status": "failed",
                    "duration_ms": 99,
                    "source": "/tmp/demo.py",
                    "input_summary": "volatile",
                    "output_summary": "volatile",
                    "failures": ["bad"],
                    "checks": [{"kind": "non_empty", "status": "failed", "message": "bad", "path": "name", "params": {}}],
                    "error": None,
                }
            ],
        },
        {"workflow": "demo", "steps": [{"id": "demo.step", "upstream": [], "downstream": []}]},
    )

    assert normalized == {
        "schema_version": "flowguard.golden.v0.3",
        "workflow": "demo",
        "steps": [
            {
                "id": "demo.step",
                "name": "demo.step",
                "status": "failed",
                "source": "demo.py",
                "failures": ["bad"],
                "checks": [{"kind": "non_empty", "status": "failed", "message": "bad", "path": "name", "params": {}}],
                "error": None,
                "upstream": [],
                "downstream": [],
            }
        ],
    }


def test_create_and_compare_golden(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    trace = {
        "run_id": "latest",
        "workflow": "demo",
        "started_at": "first",
        "updated_at": "first",
        "steps": [{"id": "demo.step", "name": "demo.step", "status": "success", "duration_ms": 1, "failures": [], "checks": [], "error": None}],
    }
    _write_latest(tmp_path, trace)

    baseline_path = create_golden("demo", "default")

    assert baseline_path == Path(".flowguard/goldens/demo/default/baseline.json")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert baseline["schema_version"] == "flowguard.golden.v0.3"
    assert baseline["schema_version"] != "legacy-v0.2"
    result = compare_golden("demo", "default")
    assert result.passed is True
    assert result.differences == []

    changed_trace = {**trace, "started_at": "second", "steps": [{**trace["steps"][0], "duration_ms": 500}]}
    _write_latest(tmp_path, changed_trace)

    assert compare_golden("demo", "default").passed is True

    broken_trace = {**trace, "steps": [{**trace["steps"][0], "status": "failed", "failures": ["bad"]}]}
    _write_latest(tmp_path, broken_trace)
    failed = compare_golden("demo", "default")

    assert failed.passed is False
    assert "latest run does not match golden baseline" in failed.differences
    assert "## step_status_changed" in failed.agent_diff
    assert "- `demo.step`: golden:default=success, latest=failed" in failed.agent_diff


def test_compare_golden_accepts_v02_baseline_without_schema_version(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    trace = {
        "run_id": "latest",
        "workflow": "demo",
        "steps": [{"id": "demo.step", "name": "demo.step", "status": "success", "failures": [], "checks": [], "error": None}],
    }
    _write_latest(tmp_path, trace)
    baseline = Path(".flowguard/goldens/demo/default/baseline.json")
    baseline.parent.mkdir(parents=True)
    baseline.write_text(json.dumps({"workflow": "demo", "steps": normalize_run(trace, {"workflow": "demo", "steps": []})["steps"]}), encoding="utf-8")

    result = compare_golden("demo", "default")

    assert result.passed is True
    assert result.differences == []


def test_compare_golden_rejects_unknown_future_schema_version(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_latest(tmp_path, {"run_id": "latest", "workflow": "demo", "steps": []})
    baseline = Path(".flowguard/goldens/demo/default/baseline.json")
    baseline.parent.mkdir(parents=True)
    baseline.write_text(
        json.dumps({"schema_version": "flowguard.golden.v9.9", "workflow": "demo", "steps": []}),
        encoding="utf-8",
    )

    try:
        compare_golden("demo", "default")
    except ValueError as exc:
        assert "Unsupported FlowGuard golden schema_version" in str(exc)
    else:
        raise AssertionError("unknown future golden schema should fail loud")


def test_golden_normalizes_file_check_paths(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    artifact = tmp_path / "artifacts" / "result.json"
    artifact.parent.mkdir()
    artifact.write_text("{}", encoding="utf-8")
    trace = {
        "run_id": "latest",
        "workflow": "demo",
        "steps": [
            {
                "id": "demo.step",
                "name": "demo.step",
                "status": "success",
                "source": "demo.py",
                "failures": [],
                "checks": [
                    {
                        "kind": "file_exists",
                        "status": "passed",
                        "message": "artifact.path references an existing file",
                        "path": "artifact.path",
                        "params": {},
                        "expected": "existing file",
                        "actual": str(artifact),
                    }
                ],
                "error": None,
            }
        ],
    }
    _write_latest(tmp_path, trace)

    baseline_path = create_golden("demo", "default")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    assert baseline["steps"][0]["checks"][0]["actual"] == "artifacts/result.json"


def test_create_golden_rejects_workflow_mismatch(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_latest(tmp_path, {"run_id": "latest", "workflow": "actual", "steps": []})

    try:
        create_golden("expected", "default")
    except ValueError as exc:
        assert "latest workflow is actual, not expected" in str(exc)
    else:
        raise AssertionError("workflow mismatch should fail")


def test_golden_references_reject_path_traversal(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_latest(tmp_path, {"run_id": "latest", "workflow": "demo", "steps": []})

    for unsafe in ["", ".", "..", "../escape", "nested/name", "/tmp/escape", "nested\\name"]:
        try:
            create_golden("demo", unsafe)
        except ValueError as exc:
            assert "must be a simple path segment" in str(exc)
        else:
            raise AssertionError(f"unsafe golden name should fail: {unsafe!r}")

        try:
            compare_golden("demo", unsafe)
        except ValueError as exc:
            assert "must be a simple path segment" in str(exc)
        else:
            raise AssertionError(f"unsafe golden name should fail: {unsafe!r}")

    for unsafe_workflow in ["../workflow", "/tmp/workflow", "nested/workflow"]:
        try:
            create_golden(unsafe_workflow, "default")
        except ValueError as exc:
            assert "must be a simple path segment" in str(exc)
        else:
            raise AssertionError(f"unsafe golden workflow should fail: {unsafe_workflow!r}")
