from __future__ import annotations

import json
from pathlib import Path

from flowguard import flowguard_run, step
from flowguard.workflow_map import build_workflow_map


def _workflow_map() -> dict:
    return json.loads(Path(".flowguard/runs/latest/workflow_map.json").read_text(encoding="utf-8"))


def test_build_workflow_map_from_trace_order() -> None:
    workflow_map = build_workflow_map(
        {
            "workflow": "demo",
            "steps": [
                {
                    "id": "issue.parse",
                    "name": "issue.parse",
                    "status": "success",
                    "source": "examples/github_issue_triage/pipeline.py",
                },
                {
                    "id": "issue.triage",
                    "name": "issue.triage",
                    "status": "failed",
                    "source": "examples/github_issue_triage/pipeline.py",
                },
                {
                    "id": "repair_brief.create",
                    "name": "repair_brief.create",
                    "status": "success",
                    "source": "examples/github_issue_triage/pipeline.py",
                },
            ],
        }
    )

    assert workflow_map == {
        "workflow": "demo",
        "steps": [
            {
                "id": "issue.parse",
                "name": "issue.parse",
                "index": 0,
                "status": "success",
                "source": "examples/github_issue_triage/pipeline.py",
                "upstream": [],
                "downstream": ["issue.triage"],
            },
            {
                "id": "issue.triage",
                "name": "issue.triage",
                "index": 1,
                "status": "failed",
                "source": "examples/github_issue_triage/pipeline.py",
                "upstream": ["issue.parse"],
                "downstream": ["repair_brief.create"],
            },
            {
                "id": "repair_brief.create",
                "name": "repair_brief.create",
                "index": 2,
                "status": "success",
                "source": "examples/github_issue_triage/pipeline.py",
                "upstream": ["issue.triage"],
                "downstream": [],
            },
        ],
    }


def test_runtime_writes_workflow_map_artifact(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    @step("issue.parse")
    def parse_issue() -> dict:
        return {"title": "Bug"}

    @step("issue.triage")
    def triage_issue(issue: dict) -> dict:
        return {"issue": issue}

    @step("repair_brief.create")
    def create_repair_brief(triage: dict) -> dict:
        return {"triage": triage}

    with flowguard_run("github_issue_triage"):
        issue = parse_issue()
        triage = triage_issue(issue)
        create_repair_brief(triage)

    workflow_map = _workflow_map()

    assert workflow_map["workflow"] == "github_issue_triage"
    assert [step["id"] for step in workflow_map["steps"]] == [
        "issue.parse",
        "issue.triage",
        "repair_brief.create",
    ]
    assert workflow_map["steps"][1]["upstream"] == ["issue.parse"]
    assert workflow_map["steps"][1]["downstream"] == ["repair_brief.create"]
