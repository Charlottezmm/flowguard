# FlowGuard

**Stack traces for AI workflows.**

When ordinary code breaks, your coding agent gets rich signal: a stack trace, a
failing test, or a type error. When an AI workflow "breaks", a step can run,
return, raise nothing, and still produce quietly wrong output. The agent sees
`success` and starts guessing.

FlowGuard manufactures the missing signal. It captures what actually happened in
one workflow run and turns it into structured repair context for coding agents
and a readable local report for humans.

## The Problem: Silent Quality Failure

A workflow step completes without error. No exception, no crash. But the output
is semantically wrong: the model hallucinated, returned an empty list, or
produced a shape that still parses. That bad output flows downstream, so the
symptom often appears far away from the cause.

Your coding agent can read code, but it cannot see the run. FlowGuard gives it
something to read instead of guess.

## What FlowGuard Does

- Builds a lightweight `workflow_map.json` for the feature or workflow you are
  working on.
- Records run facts: per-step inputs, outputs, errors, failures, structured
  checks, and downstream impact.
- Generates `agent_context.md`, a compact repair context for Codex, Claude Code,
  Cursor, and similar coding agents.
- Generates `outcome_report.html`, a static local report for human review.
- Compares latest runs against local golden baselines.
- Exposes local read-only query helpers and a stable read-only MCP stdio
  server.

FlowGuard runs at development time, on your machine, against local files. There
is no server, no account, and no hosted service.

## What It Is For

FlowGuard is for steps where "did this do what I meant?" cannot be answered by a
compiler, type checker, or simple assertion. In practice that means LLM calls,
unstable external API responses, extraction and transformation steps, and other
places where correctness depends on observed output and user intent.

It works on one feature or workflow at a time: usually a handful to a few dozen
steps inside a normal repository.

FlowGuard is not an observability platform, not a workflow builder, and not an
enterprise LLMOps product. If you need dashboards, hosted traces, team-wide
aggregation, or cloud sync, FlowGuard is the wrong tool.

For the longer positioning and boundaries, see
[`docs/positioning.md`](docs/positioning.md).

## Quickstart

From a clean checkout:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
PYTHONPATH=src .venv/bin/python examples/github_issue_triage/pipeline.py
PYTHONPATH=src .venv/bin/python -m flowguard.cli
sed -n '1,80p' .flowguard/runs/latest/agent_context.md
PYTHONPATH=src .venv/bin/python -m flowguard.cli run save --workflow github_issue_triage --name quickstart
PYTHONPATH=src .venv/bin/python -m flowguard.cli run compare --workflow github_issue_triage --left quickstart --right latest
PYTHONPATH=src .venv/bin/python -m flowguard.cli golden create --workflow github_issue_triage --name quickstart
PYTHONPATH=src .venv/bin/python -m flowguard.cli golden compare --workflow github_issue_triage --name quickstart
```

The demo intentionally reports a failed step, `issue.triage`. The quickstart is
successful when:

- `.flowguard/runs/latest/` contains `trace.json`, `workflow_map.json`,
  `agent_context.md`, and `outcome_report.html`.
- the CLI context command and `agent_context.md` readback both say
  `Failed step: issue.triage`.
- named-run comparison prints `Run comparison passed`.
- golden comparison prints `Golden comparison passed`.

For a command-by-command checklist, see
[`docs/quickstart_check.md`](docs/quickstart_check.md).

## Two Audiences, Two Views

`trace.json` is the source of truth for run facts. Other artifacts are derived
views:

- **`agent_context.md` is for your coding agent.** It is terse and structured:
  failed step id, failed checks, downstream impact, relevant files, and suggested
  focus.
- **`outcome_report.html` is for you.** It is a scannable static report for
  human review.

These views are deliberately separate. One file should not try to serve both
humans and agents.

## Agent Usage

```text
Use FlowGuard to map this workflow, inspect the failed run, and create a repair context.
```

## Example Output

`agent_context.md`:

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

The demo intentionally returns an incomplete issue triage result. This is not a
bug in the demo; it is the failure case used to show how FlowGuard turns a
silent workflow quality issue into agent repair context. Do not "fix" the demo
solely to make it pass unless you are explicitly testing a happy path.

FlowGuard catches the silent failure and writes:

```text
.flowguard/runs/latest/
  trace.json
  workflow_map.json
  agent_context.md
  outcome_report.html
```

## Local Checks

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

FlowGuard does not make HTTP requests for response checks. It only validates
objects your workflow already captured.

File check paths are read from step output fields. Relative file paths resolve
from the workflow run root, which is the current working directory that started
the run. Absolute paths are allowed, but golden baselines normalize paths so
checkout-specific prefixes do not become comparison noise.

For adding FlowGuard to an existing workflow, see
[`docs/integration_guide.md`](docs/integration_guide.md). For intent-bearing
check examples, see [`docs/check_cookbook.md`](docs/check_cookbook.md).

## Golden Runs

Create and compare a local semantic baseline:

```bash
PYTHONPATH=src .venv/bin/python -m flowguard.cli golden create --workflow github_issue_triage --name default
PYTHONPATH=src .venv/bin/python -m flowguard.cli golden compare --workflow github_issue_triage --name default
```

Golden comparisons ignore unstable fields such as timestamps, durations, and
input/output summary strings.

## Run Comparison

Save named local runs before and after a change:

```bash
PYTHONPATH=src .venv/bin/python -m flowguard.cli run save --workflow github_issue_triage --name before-fix
PYTHONPATH=src .venv/bin/python -m flowguard.cli run list --workflow github_issue_triage
```

Compare two run references:

```bash
PYTHONPATH=src .venv/bin/python -m flowguard.cli run compare --workflow github_issue_triage --left before-fix --right latest
```

Run comparison reports step status changes, check changes, failure changes,
error changes, and downstream impact changes in an agent-readable diff. It is a
derived view over local artifacts, not a new source-of-truth artifact.

## Query And MCP

Python code can read latest artifacts through `flowguard.query`, including
`load_latest_run()`, `summarize_run()`, `find_failed_step()`, and
`load_agent_context()`.

A stable read-only MCP stdio server is available:

```bash
PYTHONPATH=src .venv/bin/python -m flowguard.mcp_server
```

It exposes four tools:

- `flowguard_latest_status`: returns workflow, run id, overall status, and
  failed step id.
- `flowguard_failed_step`: returns the failed step object from the latest
  `trace.json`, or `null` when no step failed.
- `flowguard_workflow_map`: returns the latest `workflow_map.json`.
- `flowguard_agent_context`: returns the latest `agent_context.md`.

The MCP server is read-only. It does not run workflows, write files, create
golden baselines, save named runs, edit code, or synchronize with hosted
services. Missing or unsupported local artifacts return JSON-RPC errors.

## Status

FlowGuard v1.0 has a stable local core. The Python runtime, artifact schemas,
repair context protocol, read-only MCP surface, quickstart, case study, and
local report are frozen for the v1 workflow.

FlowGuard remains local-first and development-time. It is not a hosted service,
dashboard, workflow builder, team observability system, or cloud sync product.

## Roadmap

- **v0.1**: skill draft, Python runtime, workflow map, trace, agent context.
- **v0.2**: structured checks, file/response checks, golden runs, local query
  API, minimal read-only MCP adapter.
- **v0.3**: stable artifact schema, integration guide, check cookbook, named
  runs, and run comparison.
- **v1.0**: frozen skill + runtime + read-only MCP, run comparison, stable
  repair-context protocol, real-world case study.

For the detailed v1 path, see [`docs/v1_scope.md`](docs/v1_scope.md). For the
stable v1 contract source, see
[`docs/20260623_v1_technical_design.md`](docs/20260623_v1_technical_design.md).

## License

MIT.
