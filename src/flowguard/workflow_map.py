from __future__ import annotations

from typing import Any


def build_workflow_map(trace: dict[str, Any]) -> dict[str, Any]:
    """Build a minimal workflow map from observed run order."""
    steps = trace.get("steps", [])
    step_ids = [_step_id(step) for step in steps]

    return {
        "workflow": trace.get("workflow", "default"),
        "steps": [
            {
                "id": step_id,
                "name": step.get("name", step_id),
                "index": index,
                "status": step.get("status", "unknown"),
                "source": step.get("source"),
                "upstream": [step_ids[index - 1]] if index > 0 else [],
                "downstream": [step_ids[index + 1]] if index < len(step_ids) - 1 else [],
            }
            for index, (step, step_id) in enumerate(zip(steps, step_ids))
        ],
    }


def _step_id(step: dict[str, Any]) -> str:
    return str(step.get("id") or step.get("name") or step.get("step") or "unknown")
