from __future__ import annotations

from pathlib import Path


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
