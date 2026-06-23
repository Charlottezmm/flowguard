from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE = REPO_ROOT / "examples" / "case_study" / "pipeline.py"
DOC = REPO_ROOT / "docs" / "case_study.md"
WORKFLOW = "support_reply_case_study"
RUN_ARTIFACTS = [
    "agent_context.md",
    "outcome_report.html",
    "trace.json",
    "workflow_map.json",
]


def _run(tmp_path: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        [sys.executable, *args],
        cwd=tmp_path,
        env=env,
        check=check,
        capture_output=True,
        text=True,
    )


def _flowguard(tmp_path: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return _run(tmp_path, ["-m", "flowguard.cli", *args], check=check)


def _trace(tmp_path: Path) -> dict:
    return json.loads((tmp_path / ".flowguard/runs/latest/trace.json").read_text(encoding="utf-8"))


def _latest_artifacts(tmp_path: Path) -> list[str]:
    return sorted(path.name for path in (tmp_path / ".flowguard/runs/latest").iterdir() if path.is_file())


def test_case_study_full_loop_is_local_and_deterministic(tmp_path) -> None:
    _run(tmp_path, [str(PIPELINE), "--variant", "broken"])

    broken_trace = _trace(tmp_path)
    assert _latest_artifacts(tmp_path) == RUN_ARTIFACTS
    assert broken_trace["workflow"] == WORKFLOW
    reply_step = next(step for step in broken_trace["steps"] if step["id"] == "support.reply")
    assert reply_step["status"] == "failed"
    assert reply_step["failures"] == ["evidence_items must contain at least 2 items"]
    assert reply_step["checks"][0]["kind"] == "min_count"
    assert reply_step["checks"][0]["actual"] == 1

    agent_context = (tmp_path / ".flowguard/runs/latest/agent_context.md").read_text(encoding="utf-8")
    assert "Failed step: support.reply" in agent_context
    assert "evidence_items must contain at least 2 items" in agent_context
    assert "Downstream impacted:\n- support.handoff" in agent_context
    assert "Update support.reply so its output satisfies the failed checks" in agent_context

    _flowguard(tmp_path, ["run", "save", "--workflow", WORKFLOW, "--name", "before-fix"])

    _run(tmp_path, [str(PIPELINE), "--variant", "fixed"])
    fixed_trace = _trace(tmp_path)
    fixed_reply_step = next(step for step in fixed_trace["steps"] if step["id"] == "support.reply")
    assert fixed_reply_step["status"] == "success"
    assert fixed_reply_step["checks"][0]["actual"] == 2

    _flowguard(tmp_path, ["run", "save", "--workflow", WORKFLOW, "--name", "after-fix"])
    compare = _flowguard(
        tmp_path,
        ["run", "compare", "--workflow", WORKFLOW, "--left", "before-fix", "--right", "after-fix"],
        check=False,
    )
    assert compare.returncode == 1
    assert "Run comparison failed: before-fix -> after-fix" in compare.stdout
    assert "- `support.reply`: before-fix=failed, after-fix=success" in compare.stdout
    assert "## failure_removed" in compare.stdout
    assert "- `support.reply`: evidence_items must contain at least 2 items" in compare.stdout

    _flowguard(tmp_path, ["golden", "create", "--workflow", WORKFLOW, "--name", "fixed"])
    golden_pass = _flowguard(tmp_path, ["golden", "compare", "--workflow", WORKFLOW, "--name", "fixed"])
    assert "Golden comparison passed" in golden_pass.stdout

    _run(tmp_path, [str(PIPELINE), "--variant", "broken"])
    golden_regression = _flowguard(tmp_path, ["golden", "compare", "--workflow", WORKFLOW, "--name", "fixed"], check=False)
    assert golden_regression.returncode == 1
    assert "Golden comparison failed" in golden_regression.stdout
    assert "- `support.reply`: golden:fixed=success, latest=failed" in golden_regression.stdout
    assert _latest_artifacts(tmp_path) == RUN_ARTIFACTS
    assert not list((tmp_path / ".flowguard").rglob("contracts.json"))
    assert not list((tmp_path / ".flowguard").rglob("failed_contracts.md"))


def test_case_study_doc_names_the_repeatable_loop() -> None:
    text = DOC.read_text(encoding="utf-8")

    for required in [
        "silent quality failure",
        "FlowGuard artifacts",
        "agent_context.md",
        "run compare",
        "golden create",
        "golden compare",
        "no network",
        "no paid API",
        "no private credentials",
        "support_reply_case_study",
    ]:
        assert required in text
