# FlowGuard

**Workflow context bridge for AI coding agents.**

Your AI workflow says `success`. FlowGuard helps your coding agent understand what actually happened.

## Problem

AI coding agents can read code, but they often miss the workflow context humans keep in their head: which step produced which artifact, what the last run returned, which API response was empty, and which downstream step will break next.

FlowGuard turns messy workflow state into structured context for agents and readable repair reports for humans.

## What It Does

- Builds a lightweight `workflow_map.json` for AI workflow projects.
- Records run facts such as step inputs, outputs, failures, structured checks, and impacted downstream steps.
- Generates `agent_context.md`, a compact repair context for Codex, Claude Code, Cursor, and similar agents.
- Generates `outcome_report.html`, a static local report for human review.
- Compares latest runs against local golden baselines.
- Exposes local read-only query helpers and an experimental read-only MCP adapter.

## Agent Usage

```text
Use FlowGuard to map this workflow, inspect the failed run, and create a repair context.
```

## Example Output

```md
# Agent Context

Failed step: issue.triage

Failed checks:
- repro_steps must contain at least 2 items
- affected_files must contain at least 1 items

Downstream impacted:
- repair_brief.create

Relevant files:
- examples/github_issue_triage/pipeline.py

Suggested focus:
Add enough reproduction steps and affected files before handing off to a coding agent.
```

## Demo

```bash
PYTHONPATH=src .venv/bin/python examples/github_issue_triage/pipeline.py
PYTHONPATH=src .venv/bin/python -m flowguard.cli
```

The demo intentionally returns an incomplete issue triage result. FlowGuard catches the silent failure and writes:

```text
.flowguard/runs/latest/
  trace.json
  workflow_map.json
  agent_context.md
  outcome_report.html
```

`agent_context.md` is the dynamic repair context for coding agents. `outcome_report.html` is a static local report for humans.

## v0.2 Local Checks

FlowGuard v0.2 adds structured check results while preserving the v0.1
`failures` strings. Workflows can also check local file artifacts and
response-like objects already returned by a step.

```python
@expect.file_exists("artifact.path")
@expect.file_non_empty("artifact.path")
@expect.file_valid_json("artifact.path")
@expect.response_status("response", min=200, max=299)
@expect.response_non_empty("response.json.items")
def inspect_result(result: dict) -> dict:
    ...
```

FlowGuard does not make HTTP requests for response checks; it only validates
objects your workflow already captured.

File check paths are read from step output fields. Relative file paths resolve
from the workflow run root, which is the current working directory that started
the run. Absolute paths are allowed, but golden baselines normalize paths so
checkout-specific prefixes do not become comparison noise.

## Golden Runs

Create and compare a local semantic baseline:

```bash
PYTHONPATH=src .venv/bin/python -m flowguard.cli golden create --workflow github_issue_triage --name default
PYTHONPATH=src .venv/bin/python -m flowguard.cli golden compare --workflow github_issue_triage --name default
```

Golden comparisons ignore unstable fields such as timestamps, durations, and
input/output summary strings.

## Query And MCP

Python code can read latest artifacts through `flowguard.query`, including
`load_latest_run()`, `summarize_run()`, `find_failed_step()`, and
`load_agent_context()`.

An experimental read-only MCP stdio server is available:

```bash
PYTHONPATH=src .venv/bin/python -m flowguard.mcp_server
```

It exposes latest run status, failed step, workflow map, and agent context. It
does not run workflows or write files.

## Status

FlowGuard is experimental. v0.2 focuses on local checks, golden baselines, and read-only artifact queries.

## Roadmap

- v0.1: Skill draft, Python runtime, workflow map, trace, agent context.
- v0.2: Structured checks, API/file checks, golden runs, local query API, minimal read-only MCP adapter.
- v1.0: stable Skill + runtime + MCP, run comparison, real-world case study.
