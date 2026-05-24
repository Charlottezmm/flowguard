from __future__ import annotations

import json
from pathlib import Path

import pytest

from flowguard import expect, flowguard_run, step


def _trace() -> dict:
    return json.loads(Path(".flowguard/runs/latest/trace.json").read_text(encoding="utf-8"))


def _trace_at(root: Path) -> dict:
    return json.loads((root / ".flowguard/runs/latest/trace.json").read_text(encoding="utf-8"))


def test_explicit_run_writes_trace_and_cleans_latest(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    @step("demo.make")
    @expect.required_fields(["name"])
    def make_item() -> dict:
        return {"name": "alpha"}

    with flowguard_run("demo"):
        make_item()

    first_trace = _trace()
    assert first_trace["schema_version"] == "flowguard.trace.v0.3"
    assert first_trace["workflow"] == "demo"
    assert len(first_trace["steps"]) == 1
    assert first_trace["steps"][0]["id"] == "demo.make"
    assert first_trace["steps"][0]["name"] == "demo.make"
    assert first_trace["steps"][0]["status"] == "success"
    assert first_trace["steps"][0]["source"].endswith("tests/test_runtime.py")

    with flowguard_run("demo"):
        make_item()

    second_trace = _trace()
    assert len(second_trace["steps"]) == 1


def test_expectation_failure_is_recorded_as_failed(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    @step("demo.triage")
    @expect.min_count("repro_steps", 2)
    def triage() -> dict:
        return {"repro_steps": ["Run demo"]}

    with flowguard_run("demo"):
        assert triage() == {"repro_steps": ["Run demo"]}

    step_result = _trace()["steps"][0]
    assert step_result["status"] == "failed"
    assert step_result["failures"] == ["repro_steps must contain at least 2 items"]
    assert step_result["checks"] == [
        {
            "kind": "min_count",
            "status": "failed",
            "message": "repro_steps must contain at least 2 items",
            "path": "repro_steps",
            "params": {"count": 2},
            "expected": 2,
            "actual": 1,
        }
    ]
    assert step_result["error"] is None


def test_exception_is_recorded_as_error_before_reraise(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    @step("demo.error")
    def explode() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        with flowguard_run("demo"):
            explode()

    step_result = _trace()["steps"][0]
    assert step_result["status"] == "error"
    assert step_result["failures"] == []
    assert step_result["checks"] == []
    assert step_result["error"] == "RuntimeError('boom')"


def test_step_without_explicit_run_creates_usable_latest(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    @step("demo.default")
    @expect.non_empty("name")
    def make_item() -> dict:
        return {"name": "alpha"}

    make_item()

    trace = _trace()
    assert trace["workflow"] == "default"
    assert trace["steps"][0]["status"] == "success"
    assert trace["steps"][0]["checks"][0]["status"] == "passed"
    assert Path(".flowguard/runs/latest/agent_context.md").exists()


def test_file_checks_and_artifacts_use_run_start_directory_when_step_changes_cwd(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("artifact.json").write_text('{"ok": true}', encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()

    @step("demo.file")
    @expect.file_exists("artifact_path")
    def make_artifact() -> dict:
        monkeypatch.chdir(nested)
        return {"artifact_path": "artifact.json"}

    with flowguard_run("demo"):
        make_artifact()

    trace = _trace_at(tmp_path)
    step_result = trace["steps"][0]
    assert step_result["status"] == "success"
    assert step_result["checks"][0]["status"] == "passed"
    assert step_result["checks"][0]["actual"] == str(tmp_path / "artifact.json")
    assert not (nested / ".flowguard").exists()
