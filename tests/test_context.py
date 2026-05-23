from __future__ import annotations

import json
from pathlib import Path

from flowguard.context import build_agent_context


FIXTURES = Path(__file__).parent / "fixtures" / "context"


def _json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_expectation_failure_context_matches_golden() -> None:
    assert build_agent_context(
        _json("expectation_failure_trace.json"),
        _json("expectation_failure_workflow_map.json"),
    ) == _text("expectation_failure_agent_context.md")


def test_exception_context_matches_golden() -> None:
    assert build_agent_context(
        _json("exception_trace.json"),
        _json("exception_workflow_map.json"),
    ) == _text("exception_agent_context.md")


def test_no_failure_context_matches_golden() -> None:
    assert build_agent_context(
        _json("no_failure_trace.json"),
        _json("no_failure_workflow_map.json"),
    ) == _text("no_failure_agent_context.md")


def test_missing_workflow_map_still_generates_context() -> None:
    context = build_agent_context(_json("expectation_failure_trace.json"))

    assert "Failed step: issue.triage" in context
    assert "Downstream impacted:\n- repair_brief.create" in context


def test_long_summaries_are_truncated() -> None:
    long_value = "x" * 1300
    trace = {
        "run_id": "latest",
        "workflow": "long_demo",
        "steps": [
            {
                "id": "demo.step",
                "name": "demo.step",
                "status": "failed",
                "source": "demo.py",
                "input_summary": long_value,
                "output_summary": long_value,
                "failures": ["output must not be empty"],
                "error": None,
            }
        ],
    }

    context = build_agent_context(trace)

    assert context.count("...(truncated, full value in trace.json)") == 2
    assert long_value not in context
