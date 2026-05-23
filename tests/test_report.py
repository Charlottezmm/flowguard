from __future__ import annotations

from pathlib import Path

from flowguard import expect, flowguard_run, step
from flowguard.report import build_outcome_report


def test_build_outcome_report_escapes_html_and_shows_failure() -> None:
    trace = {
        "run_id": "latest",
        "workflow": "demo<script>",
        "steps": [
            {
                "id": "demo.step",
                "name": "demo.step",
                "status": "failed",
                "duration_ms": 2,
                "source": "demo.py",
                "output_summary": "<bad>",
                "failures": ["field <name> missing"],
                "error": None,
            }
        ],
    }
    workflow_map = {
        "workflow": "demo<script>",
        "steps": [
            {
                "id": "demo.step",
                "name": "demo.step",
                "index": 0,
                "status": "failed",
                "source": "demo.py",
                "upstream": [],
                "downstream": [],
            }
        ],
    }

    html = build_outcome_report(trace, workflow_map)

    assert "FlowGuard Outcome Report" in html
    assert "status-failed" in html
    assert "demo&lt;script&gt;" in html
    assert "&lt;bad&gt;" in html
    assert "field &lt;name&gt; missing" in html
    assert "<bad>" not in html


def test_runtime_writes_outcome_report_artifact(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    @step("demo.step")
    @expect.min_count("items", 1)
    def make_result() -> dict:
        return {"items": []}

    with flowguard_run("demo"):
        make_result()

    report_path = Path(".flowguard/runs/latest/outcome_report.html")
    assert report_path.exists()

    html = report_path.read_text(encoding="utf-8")
    assert "FlowGuard Outcome Report" in html
    assert "demo.step" in html
    assert "items must contain at least 1 items" in html
    assert "agent_context.md" in html
