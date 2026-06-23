from __future__ import annotations

import json
from pathlib import Path

from flowguard.context import build_agent_context


FIXTURES = Path(__file__).parent / "fixtures" / "context"
SCHEMA_HEADER = "<!-- flowguard agent_context schema: v0.1 -->"
FAILED_SECTION_MARKERS = [
    "Workflow:",
    "Run:",
    "Reporting:",
    "Failed step:",
    "Status:",
    "Failed checks:",
    "Upstream:",
    "Downstream impacted:",
    "Relevant files:",
    "Input summary:",
    "Output summary:",
    "Suggested focus:",
    "Verification:",
]


def _json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_expectation_failure_context_matches_golden() -> None:
    assert build_agent_context(
        _json("expectation_failure_trace.json"),
        _json("expectation_failure_workflow_map.json"),
    ) == _text("expectation_failure_agent_context.md")


def test_failed_context_starts_with_schema_header_and_sections_are_ordered() -> None:
    context = build_agent_context(
        _json("expectation_failure_trace.json"),
        _json("expectation_failure_workflow_map.json"),
    )

    assert context.startswith(f"{SCHEMA_HEADER}\n\n# Agent Context\n")
    positions = [context.index(marker) for marker in FAILED_SECTION_MARKERS]
    assert positions == sorted(positions)
    assert "Error:" not in context
    assert "Upstream impacted" not in context
    assert "Downstream impacted:" in context


def test_exception_context_matches_golden() -> None:
    assert build_agent_context(
        _json("exception_trace.json"),
        _json("exception_workflow_map.json"),
    ) == _text("exception_agent_context.md")


def test_error_context_includes_error_section_after_failed_checks() -> None:
    context = build_agent_context(
        _json("exception_trace.json"),
        _json("exception_workflow_map.json"),
    )

    assert "Failed checks:\n- none\n\nError:\n- RuntimeError('boom')" in context


def test_no_failure_context_matches_golden() -> None:
    context = build_agent_context(
        _json("no_failure_trace.json"),
        _json("no_failure_workflow_map.json"),
    )

    assert context == _text("no_failure_agent_context.md")
    assert context.startswith(f"{SCHEMA_HEADER}\n\n# Agent Context\n")
    assert context.count("flowguard agent_context schema:") == 1
    assert "No failed checks in the latest run." in context


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


def test_relevant_files_come_from_runtime_sources_only_and_are_limited() -> None:
    downstream_ids = [f"downstream.{index}" for index in range(8)]
    trace = {
        "run_id": "latest",
        "workflow": "file_demo",
        "steps": [
            {
                "id": "failed.step",
                "name": "failed.step",
                "status": "failed",
                "source": "src/failed.py",
                "input_summary": "{}",
                "output_summary": "{}",
                "failures": ["bad output"],
                "error": None,
            },
            *[
                {
                    "id": step_id,
                    "name": step_id,
                    "status": "success",
                    "source": f"src/downstream_{index}.py",
                    "input_summary": "{}",
                    "output_summary": "{}",
                    "failures": [],
                    "error": None,
                }
                for index, step_id in enumerate(downstream_ids)
            ],
        ],
    }
    workflow_map = {
        "workflow": "file_demo",
        "steps": [
            {
                "id": "failed.step",
                "name": "failed.step",
                "index": 0,
                "status": "failed",
                "source": "src/failed.py",
                "upstream": [],
                "downstream": downstream_ids,
            },
            *[
                {
                    "id": step_id,
                    "name": step_id,
                    "index": index + 1,
                    "status": "success",
                    "source": f"src/downstream_{index}.py",
                    "upstream": ["failed.step"],
                    "downstream": [],
                }
                for index, step_id in enumerate(downstream_ids)
            ],
        ],
    }

    context = build_agent_context(trace, workflow_map)

    relevant_section = context.split("Relevant files:\n", 1)[1].split("\n\nInput summary:", 1)[0]
    assert relevant_section.splitlines() == [
        "- src/failed.py",
        "- src/downstream_0.py",
        "- src/downstream_1.py",
        "- src/downstream_2.py",
        "- src/downstream_3.py",
    ]
    assert "src/downstream_4.py" not in relevant_section
