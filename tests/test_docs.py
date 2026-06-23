from __future__ import annotations

import re
from pathlib import Path


QUICKSTART_COMMANDS = [
    "python3 -m venv .venv",
    '.venv/bin/python -m pip install -e ".[dev]"',
    "PYTHONPATH=src .venv/bin/python examples/github_issue_triage/pipeline.py",
    "PYTHONPATH=src .venv/bin/python -m flowguard.cli",
    "sed -n '1,80p' .flowguard/runs/latest/agent_context.md",
    (
        "PYTHONPATH=src .venv/bin/python -m flowguard.cli run save "
        "--workflow github_issue_triage --name quickstart"
    ),
    (
        "PYTHONPATH=src .venv/bin/python -m flowguard.cli run compare "
        "--workflow github_issue_triage --left quickstart --right latest"
    ),
    (
        "PYTHONPATH=src .venv/bin/python -m flowguard.cli golden create "
        "--workflow github_issue_triage --name quickstart"
    ),
    (
        "PYTHONPATH=src .venv/bin/python -m flowguard.cli golden compare "
        "--workflow github_issue_triage --name quickstart"
    ),
]


def test_readme_documents_clean_checkout_quickstart() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "## Quickstart" in readme
    for command in QUICKSTART_COMMANDS:
        assert command in readme

    assert "[`docs/quickstart_check.md`](docs/quickstart_check.md)" in readme
    assert "Failed step: issue.triage" in readme
    assert "Run comparison passed" in readme
    assert "Golden comparison passed" in readme


def test_quickstart_check_matches_readme_commands_and_boundaries() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    quickstart = Path("docs/quickstart_check.md").read_text(encoding="utf-8")

    for command in QUICKSTART_COMMANDS:
        assert command in readme
        assert command in quickstart

    for artifact_name in [
        "agent_context.md",
        "outcome_report.html",
        "trace.json",
        "workflow_map.json",
    ]:
        assert f".flowguard/runs/latest/{artifact_name}" in quickstart

    assert "Failed step: issue.triage" in quickstart
    assert "contracts.json" in quickstart
    assert "failed_contracts.md" in quickstart


def test_referenced_local_markdown_docs_exist() -> None:
    for doc_path in [Path("README.md"), Path("docs/quickstart_check.md")]:
        doc = doc_path.read_text(encoding="utf-8")
        for match in re.finditer(r"\[[^\]]+\]\((docs/[^)#]+\.md)\)", doc):
            assert Path(match.group(1)).is_file()


def test_quickstart_commands_reference_existing_local_entrypoints() -> None:
    assert Path("examples/github_issue_triage/pipeline.py").is_file()
    assert Path("src/flowguard/cli.py").is_file()


def test_flowguard_skill_documents_check_intent_workflow() -> None:
    skill = Path("skills/flowguard/SKILL.md").read_text(encoding="utf-8")

    assert "@step" in skill
    assert "@expect" in skill
    assert "ask or confirm" in skill
    assert "weak checks" in skill
    assert "Do not add checks only to make FlowGuard pass" in skill


def test_integration_guide_covers_python_workflow_setup() -> None:
    guide = Path("docs/integration_guide.md").read_text(encoding="utf-8")

    assert "# FlowGuard Integration Guide" in guide
    assert "Identify the uncertain step" in guide
    assert "Add mechanical step instrumentation" in guide
    assert "Confirm check intent before adding expectations" in guide
    assert "Run the workflow and read the artifacts" in guide
    assert "PYTHONPATH=src .venv/bin/python -m flowguard.cli" in guide


def test_check_cookbook_covers_required_examples() -> None:
    cookbook = Path("docs/check_cookbook.md").read_text(encoding="utf-8")

    for section in [
        "LLM Output",
        "API Response",
        "File Artifact",
        "JSON Artifact",
        "Downstream Dependency Failure",
    ]:
        assert f"## {section}" in cookbook

    assert "Weak check to avoid" in cookbook
