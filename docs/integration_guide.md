# FlowGuard Integration Guide

This guide shows how to add FlowGuard to an existing local Python workflow.
FlowGuard is for silent quality failures: a step runs, returns, raises no
exception, but produces output that is wrong enough to pollute later steps.

FlowGuard should stay small. Add it to the current feature or workflow, not to
an entire repository.

## 1. Identify the uncertain step

Start with the place where correctness depends on observed output and user
intent:

- an LLM or model call
- an external API response with unstable shape or content
- an extraction, crawl, transform, or ranking step
- a handoff object consumed by a later step

Do not start by instrumenting every function. Ordinary deterministic code should
stay covered by tests and type checks.

## 2. Add mechanical step instrumentation

Wrap the workflow execution in `flowguard_run()` and mark meaningful step
boundaries with `@step`.

```python
from flowguard import expect, flowguard_run, step


@step("issue.parse")
def parse_issue(raw_issue: dict) -> dict:
    return {
        "title": raw_issue["title"],
        "body": raw_issue["body"],
    }


@step("issue.triage")
def triage_issue(issue: dict) -> dict:
    return call_model_for_triage(issue)


with flowguard_run("github_issue_triage"):
    issue = parse_issue(raw_issue)
    triage = triage_issue(issue)
```

Good step ids describe the workflow role, not the implementation detail. Keep
them stable enough that a coding agent can connect `agent_context.md` back to
the code.

## 3. Confirm check intent before adding expectations

`@expect...` is the intent boundary. Before adding it, ask what should count as
good enough.

Useful intent questions:

- What bad output are we trying to catch?
- What downstream step breaks or gets polluted when this output is wrong?
- What fields, counts, status, or artifact properties prove the step is usable?
- Would this check fail on the known bad run?

Do not add weak checks just to make the run look healthy. For example,
`@expect.non_empty("summary")` is weak if the real requirement is "summary names
the customer-visible regression and the affected file."

## 4. Translate intent into narrow checks

Use checks that are deterministic and tied to the failure.

```python
@step("issue.triage")
@expect.required_fields(["issue_type", "severity", "repro_steps", "affected_files"])
@expect.min_count("repro_steps", 2)
@expect.min_count("affected_files", 1)
def triage_issue(issue: dict) -> dict:
    return call_model_for_triage(issue)
```

This is better than a generic non-empty check because it encodes the minimum
handoff shape the next step needs.

## 5. Run the workflow and read the artifacts

Run the workflow from the project root so relative file checks resolve from the
same run root.

```bash
PYTHONPATH=src .venv/bin/python examples/github_issue_triage/pipeline.py
PYTHONPATH=src .venv/bin/python -m flowguard.cli
```

The latest run writes:

```text
.flowguard/runs/latest/
  trace.json
  workflow_map.json
  agent_context.md
  outcome_report.html
```

Read `agent_context.md` first when debugging. It is the agent-facing repair
handoff. Use `workflow_map.json` when upstream or downstream order matters, and
open `outcome_report.html` when a human-readable summary is useful.

## 6. Compare against a golden baseline when available

Golden baselines are local semantic snapshots. Use them before and after a fix
when the workflow already has a meaningful baseline.

```bash
PYTHONPATH=src .venv/bin/python -m flowguard.cli golden compare --workflow github_issue_triage --name default
```

Create a new golden only after the run behavior is intentionally accepted.

```bash
PYTHONPATH=src .venv/bin/python -m flowguard.cli golden create --workflow github_issue_triage --name default
```

## Non-goals

Do not use this integration path to add hosted services, dashboards, workflow
builders, cloud sync, write-capable MCP tools, or broad auto-instrumentation.
FlowGuard is local-first and file-based.
