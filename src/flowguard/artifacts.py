from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_run_artifacts(step_result: dict[str, Any]) -> None:
    run_dir = Path(".flowguard/runs/latest")
    run_dir.mkdir(parents=True, exist_ok=True)

    trace_path = run_dir / "trace.json"
    trace = _read_json(trace_path, {"run_id": "latest", "steps": []})
    trace["updated_at"] = datetime.now(timezone.utc).isoformat()
    trace["steps"].append(step_result)
    trace_path.write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8")

    _write_agent_context(run_dir, trace)


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_agent_context(run_dir: Path, trace: dict[str, Any]) -> None:
    failures = [step for step in trace["steps"] if step.get("failures") or step.get("error")]
    if failures:
        latest = failures[-1]
        body = [
            "# Agent Context",
            "",
            f"Failed step: {latest['step']}",
            "",
            "Failed checks:",
            *[f"- {failure}" for failure in latest.get("failures", [])],
        ]
        if latest.get("error"):
            body.extend(["", "Error:", f"- {latest['error']}"])
    else:
        body = ["# Agent Context", "", "No failed checks in the latest run."]

    (run_dir / "agent_context.md").write_text("\n".join(body) + "\n", encoding="utf-8")

