from __future__ import annotations

from html import escape
from typing import Any


def build_outcome_report(trace: dict[str, Any], workflow_map: dict[str, Any] | None = None) -> str:
    """Build a static HTML outcome report for the latest run."""
    workflow = str(trace.get("workflow", "default"))
    run_id = str(trace.get("run_id", "latest"))
    steps = list(trace.get("steps", []))
    status = _run_status(steps)
    map_steps = {str(step.get("id") or step.get("name") or step.get("step")): step for step in (workflow_map or {}).get("steps", [])}

    rows = "\n".join(_step_row(index, step, map_steps) for index, step in enumerate(steps))
    if not rows:
        rows = '<tr><td colspan="7" class="muted">No steps recorded.</td></tr>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FlowGuard Outcome Report</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 32px;
      color: #202124;
      background: #f8f9fb;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
    }}
    h1 {{
      margin-bottom: 8px;
      font-size: 28px;
    }}
    .meta {{
      margin: 0 0 24px;
      color: #5f6368;
    }}
    .status {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 6px;
      font-weight: 700;
      text-transform: uppercase;
      font-size: 12px;
    }}
    .status-success {{ background: #e6f4ea; color: #137333; }}
    .status-failed {{ background: #fce8e6; color: #a50e0e; }}
    .status-error {{ background: #fce8e6; color: #a50e0e; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: #ffffff;
      border: 1px solid #dadce0;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid #e8eaed;
      text-align: left;
      vertical-align: top;
      font-size: 14px;
    }}
    th {{
      background: #f1f3f4;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    code, pre {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
    }}
    pre {{
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;
      max-width: 360px;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
    }}
    .muted {{
      color: #5f6368;
    }}
    .links {{
      margin-top: 18px;
    }}
  </style>
</head>
<body>
  <main>
    <h1>FlowGuard Outcome Report</h1>
    <p class="meta">
      Workflow: <strong>{escape(workflow)}</strong> |
      Run: <strong>{escape(run_id)}</strong> |
      Status: {_status_badge(status)}
    </p>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Step</th>
          <th>Status</th>
          <th>Duration</th>
          <th>Upstream</th>
          <th>Downstream</th>
          <th>Output / Failures</th>
        </tr>
      </thead>
      <tbody>
{rows}
      </tbody>
    </table>
    <p class="links">
      Repair context: <a href="agent_context.md">agent_context.md</a>
    </p>
  </main>
</body>
</html>
"""


def _run_status(steps: list[dict[str, Any]]) -> str:
    statuses = [step.get("status") for step in steps]
    if "error" in statuses:
        return "error"
    if "failed" in statuses:
        return "failed"
    return "success"


def _step_row(index: int, step: dict[str, Any], map_steps: dict[str, dict[str, Any]]) -> str:
    step_id = str(step.get("id") or step.get("name") or step.get("step") or "unknown")
    map_step = map_steps.get(step_id, {})
    failures = list(step.get("failures", []))
    error = step.get("error")
    details = [f"<pre>{escape(str(step.get('output_summary', '')))}</pre>"]
    if failures:
        details.append(_list_html("Failed checks", failures))
    if error:
        details.append(_list_html("Error", [error]))

    return f"""        <tr>
          <td>{index}</td>
          <td><code>{escape(step_id)}</code><br><span class="muted">{escape(str(step.get("source", "")))}</span></td>
          <td>{_status_badge(str(step.get("status", "unknown")))}</td>
          <td>{escape(str(step.get("duration_ms", "")))} ms</td>
          <td>{_inline_list(map_step.get("upstream", []))}</td>
          <td>{_inline_list(map_step.get("downstream", []))}</td>
          <td>{"".join(details)}</td>
        </tr>"""


def _status_badge(status: str) -> str:
    class_name = "status-failed" if status not in {"success", "failed", "error"} else f"status-{status}"
    return f'<span class="status {class_name}">{escape(status)}</span>'


def _inline_list(items: Any) -> str:
    values = list(items or [])
    if not values:
        return '<span class="muted">none</span>'
    return ", ".join(f"<code>{escape(str(item))}</code>" for item in values)


def _list_html(title: str, items: list[Any]) -> str:
    body = "".join(f"<li>{escape(str(item))}</li>" for item in items)
    return f"<strong>{escape(title)}:</strong><ul>{body}</ul>"
