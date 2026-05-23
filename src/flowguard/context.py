from __future__ import annotations

from typing import Any

from .workflow_map import build_workflow_map


SCHEMA_HEADER = "<!-- flowguard agent_context schema: v0.1 -->"
SUMMARY_LIMIT = 1200
RELEVANT_FILE_LIMIT = 5


def build_agent_context(trace: dict[str, Any], workflow_map: dict[str, Any] | None = None) -> str:
    """Build a concise repair handoff artifact for coding agents."""
    workflow_map = workflow_map or build_workflow_map(trace)
    workflow = trace.get("workflow", "default")
    run_id = trace.get("run_id", "latest")
    failed_steps = [step for step in trace.get("steps", []) if step.get("failures") or step.get("error")]

    if not failed_steps:
        return _join(
            [
                SCHEMA_HEADER,
                "",
                "# Agent Context",
                "",
                f"Workflow: {workflow}",
                f"Run: {run_id}",
                "",
                "No failed checks in the latest run.",
            ]
        )

    failed_step = failed_steps[-1]
    failed_step_id = _step_id(failed_step)
    map_step = _find_map_step(workflow_map, failed_step_id)
    upstream = list(map_step.get("upstream", [])) if map_step else []
    downstream = list(map_step.get("downstream", [])) if map_step else []
    relevant_files = _relevant_files(failed_step, downstream, trace, workflow_map)

    lines = [
        SCHEMA_HEADER,
        "",
        "# Agent Context",
        "",
        f"Workflow: {workflow}",
        f"Run: {run_id}",
        "Reporting: latest failed step",
        "",
        f"Failed step: {failed_step_id}",
        f"Status: {failed_step.get('status', 'unknown')}",
        "",
        "Failed checks:",
        *_bullet_list(failed_step.get("failures", [])),
    ]

    if failed_step.get("error"):
        lines.extend(["", "Error:", f"- {failed_step['error']}"])

    lines.extend(
        [
            "",
            "Upstream:",
            *_bullet_list(upstream),
            "",
            "Downstream impacted:",
            *_bullet_list(downstream),
            "",
            "Relevant files:",
            *_bullet_list(relevant_files),
            "",
            "Input summary:",
            _truncate(str(failed_step.get("input_summary", ""))),
            "",
            "Output summary:",
            _truncate(str(failed_step.get("output_summary", ""))),
            "",
            "Suggested focus:",
            _suggested_focus(failed_step_id, downstream, bool(failed_step.get("error"))),
            "",
            "Verification:",
            "- Re-run the workflow that produced this context.",
            "- Check .flowguard/runs/latest/agent_context.md.",
        ]
    )
    return _join(lines)


def _join(lines: list[str]) -> str:
    return "\n".join(lines).rstrip() + "\n"


def _step_id(step: dict[str, Any]) -> str:
    return str(step.get("id") or step.get("name") or step.get("step") or "unknown")


def _find_map_step(workflow_map: dict[str, Any], step_id: str) -> dict[str, Any] | None:
    for step in workflow_map.get("steps", []):
        if _step_id(step) == step_id:
            return step
    return None


def _bullet_list(items: list[Any]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]


def _relevant_files(
    failed_step: dict[str, Any],
    downstream: list[str],
    trace: dict[str, Any],
    workflow_map: dict[str, Any],
) -> list[str]:
    sources: list[str] = []
    _append_source(sources, failed_step.get("source"))

    trace_steps_by_id = {_step_id(step): step for step in trace.get("steps", [])}
    map_steps_by_id = {_step_id(step): step for step in workflow_map.get("steps", [])}
    for step_id in downstream:
        trace_step = trace_steps_by_id.get(step_id)
        map_step = map_steps_by_id.get(step_id)
        _append_source(sources, trace_step.get("source") if trace_step else None)
        _append_source(sources, map_step.get("source") if map_step else None)

    return sources[:RELEVANT_FILE_LIMIT]


def _append_source(sources: list[str], source: Any) -> None:
    if source and source not in sources:
        sources.append(str(source))


def _truncate(value: str) -> str:
    if len(value) <= SUMMARY_LIMIT:
        return value
    keep = SUMMARY_LIMIT - len("...(truncated, full value in trace.json)")
    if keep < 1:
        return "...(truncated, full value in trace.json)"
    return value[:keep].rstrip() + "...(truncated, full value in trace.json)"


def _suggested_focus(step_id: str, downstream: list[str], has_error: bool) -> str:
    if has_error:
        return f"Inspect {step_id} and its input summary. Fix the exception before changing downstream steps."
    if downstream:
        return f"Update {step_id} so its output satisfies the failed checks before {downstream[0]} consumes it."
    return f"Update {step_id} so its output satisfies the failed checks."
