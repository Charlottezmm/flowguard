from __future__ import annotations

import json
from pathlib import Path

import pytest

from flowguard.query import (
    find_failed_step,
    load_agent_context,
    load_golden_baseline,
    load_latest_run,
    load_named_run,
    load_workflow_map,
    list_named_runs,
    save_named_run,
    summarize_run,
)


def test_query_loads_latest_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = Path(".flowguard/runs/latest")
    run_dir.mkdir(parents=True)
    (run_dir / "trace.json").write_text(
        json.dumps(
            {
                "run_id": "latest",
                "workflow": "demo",
                "steps": [{"id": "demo.step", "status": "failed", "failures": ["bad"], "error": None}],
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "workflow_map.json").write_text(json.dumps({"workflow": "demo", "steps": []}), encoding="utf-8")
    (run_dir / "agent_context.md").write_text("# Agent Context\n", encoding="utf-8")

    assert load_latest_run()["workflow"] == "demo"
    assert load_workflow_map()["workflow"] == "demo"
    assert load_agent_context() == "# Agent Context\n"
    assert find_failed_step()["id"] == "demo.step"
    assert summarize_run() == {"workflow": "demo", "run_id": "latest", "status": "failed", "failed_step": "demo.step"}


def test_query_rejects_unknown_future_trace_schema(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = Path(".flowguard/runs/latest")
    run_dir.mkdir(parents=True)
    (run_dir / "trace.json").write_text(
        json.dumps({"schema_version": "flowguard.trace.v9.9", "run_id": "latest", "workflow": "demo", "steps": []}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported FlowGuard trace schema_version"):
        load_latest_run()


def test_query_rejects_unknown_future_workflow_map_schema(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = Path(".flowguard/runs/latest")
    run_dir.mkdir(parents=True)
    (run_dir / "workflow_map.json").write_text(
        json.dumps({"schema_version": "flowguard.workflow_map.v9.9", "workflow": "demo", "steps": []}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported FlowGuard workflow_map schema_version"):
        load_workflow_map()


def test_query_fails_loud_when_latest_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(FileNotFoundError, match="trace.json"):
        load_latest_run()


def test_query_loads_golden_baseline(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    baseline = Path(".flowguard/goldens/demo/default/baseline.json")
    baseline.parent.mkdir(parents=True)
    baseline.write_text(json.dumps({"workflow": "demo", "steps": []}), encoding="utf-8")

    assert load_golden_baseline("demo", "default") == {"workflow": "demo", "steps": []}


def test_query_rejects_unknown_future_golden_schema(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    baseline = Path(".flowguard/goldens/demo/default/baseline.json")
    baseline.parent.mkdir(parents=True)
    baseline.write_text(
        json.dumps({"schema_version": "flowguard.golden.v9.9", "workflow": "demo", "steps": []}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported FlowGuard golden schema_version"):
        load_golden_baseline("demo", "default")


def test_query_treats_status_failed_as_failed_step(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = Path(".flowguard/runs/latest")
    run_dir.mkdir(parents=True)
    (run_dir / "trace.json").write_text(
        json.dumps({"run_id": "latest", "workflow": "demo", "steps": [{"id": "status.only", "status": "failed"}]}),
        encoding="utf-8",
    )

    assert find_failed_step()["id"] == "status.only"
    assert summarize_run()["status"] == "failed"


def test_save_list_and_load_named_run(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = Path(".flowguard/runs/latest")
    run_dir.mkdir(parents=True)
    trace = {"run_id": "latest", "workflow": "demo", "steps": [{"id": "demo.step", "status": "success"}]}
    workflow_map = {"workflow": "demo", "steps": [{"id": "demo.step", "upstream": [], "downstream": []}]}
    (run_dir / "trace.json").write_text(json.dumps(trace), encoding="utf-8")
    (run_dir / "workflow_map.json").write_text(json.dumps(workflow_map), encoding="utf-8")
    (run_dir / "agent_context.md").write_text("# Agent Context\n", encoding="utf-8")
    (run_dir / "outcome_report.html").write_text("<html></html>\n", encoding="utf-8")

    saved_path = save_named_run("demo", "before-fix")

    assert saved_path == Path(".flowguard/runs/named/demo/before-fix")
    assert list_named_runs() == [{"workflow": "demo", "name": "before-fix", "path": str(saved_path)}]
    assert list_named_runs("demo") == [{"workflow": "demo", "name": "before-fix", "path": str(saved_path)}]
    named = load_named_run("demo", "before-fix")
    assert named["trace"]["workflow"] == "demo"
    assert named["workflow_map"]["workflow"] == "demo"
    assert (saved_path / "agent_context.md").read_text(encoding="utf-8") == "# Agent Context\n"
    assert (saved_path / "outcome_report.html").read_text(encoding="utf-8") == "<html></html>\n"


def test_save_named_run_rejects_workflow_mismatch(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = Path(".flowguard/runs/latest")
    run_dir.mkdir(parents=True)
    (run_dir / "trace.json").write_text(json.dumps({"run_id": "latest", "workflow": "actual", "steps": []}), encoding="utf-8")
    (run_dir / "workflow_map.json").write_text(json.dumps({"workflow": "actual", "steps": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="latest workflow is actual, not expected"):
        save_named_run("expected", "before-fix")


def test_named_run_references_reject_path_traversal(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = Path(".flowguard/runs/latest")
    run_dir.mkdir(parents=True)
    (run_dir / "trace.json").write_text(json.dumps({"run_id": "latest", "workflow": "demo", "steps": []}), encoding="utf-8")
    (run_dir / "workflow_map.json").write_text(json.dumps({"workflow": "demo", "steps": []}), encoding="utf-8")

    for unsafe in ["", ".", "..", "../escape", "nested/name", "/tmp/escape", "nested\\name"]:
        with pytest.raises(ValueError, match="must be a simple path segment"):
            save_named_run("demo", unsafe)
        with pytest.raises(ValueError, match="must be a simple path segment"):
            load_named_run("demo", unsafe)

    for unsafe_workflow in ["../workflow", "/tmp/workflow", "nested/workflow"]:
        with pytest.raises(ValueError, match="must be a simple path segment"):
            save_named_run(unsafe_workflow, "before-fix")
        with pytest.raises(ValueError, match="must be a simple path segment"):
            list_named_runs(unsafe_workflow)
