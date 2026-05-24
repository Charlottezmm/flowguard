from __future__ import annotations

import json
from pathlib import Path

import pytest

from flowguard.query import (
    find_failed_step,
    load_agent_context,
    load_golden_baseline,
    load_latest_run,
    load_workflow_map,
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
