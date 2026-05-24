---
name: flowguard
description: Use when debugging or adding reliability checks to Python AI workflows. FlowGuard maps workflow steps, records run facts, and creates agent repair context for AI coding agents.
---

# FlowGuard

Use FlowGuard when a user asks to debug, inspect, stabilize, or add reliability checks to an AI workflow.

## Workflow

1. Locate workflow entrypoints and step-like functions.
2. Identify artifacts passed between steps.
3. Add FlowGuard runtime only where it helps explain workflow state.
4. Add `@step` instrumentation mechanically from code structure when the step boundary is clear.
5. Before adding `@expect...`, ask or confirm what output would be good enough in product terms.
6. Translate confirmed intent into the narrowest checks that can fail for the real problem.
7. Run the workflow or tests.
8. Read `.flowguard/runs/latest/agent_context.md`.
9. Inspect `.flowguard/runs/latest/workflow_map.json` when upstream or downstream step order matters.
10. Open `.flowguard/runs/latest/outcome_report.html` when a human-readable run summary is useful.
11. If a golden baseline exists, run `flowguard golden compare` before and after fixes.
12. Make the smallest relevant fix.
13. Re-run FlowGuard checks.

## Check Intent

`@step` records what happened. It can usually be added from code structure.

`@expect...` encodes what "correct" means. It is not mechanical. Ask or confirm
the intent before adding expectations:

- What output would make this step good enough?
- What bad output previously slipped through?
- What downstream step would be polluted by that bad output?
- Which check would fail on that bad output?

Do not add checks only to make FlowGuard pass. Avoid weak checks that are true
but do not encode the user's intent, such as `non_empty` or `file_exists` when
the real requirement is semantic quality, completeness, or downstream usability.

Prefer checks that are narrow, deterministic, and tied to the failure being
debugged.

## Constraints

- Keep changes minimal.
- Do not convert the project into a new framework.
- Prefer local artifacts over hosted services.
- Treat `agent_context.md` as the primary handoff artifact for debugging.
- Treat `workflow_map.json` and `outcome_report.html` as supporting artifacts, not replacement diagnosis.
- Treat MCP as read-only query support. Do not use it to execute workflows or mutate artifacts.
- Do not use FlowGuard to replace unit tests, type checks, or ordinary deterministic assertions.
- Do not add hosted services, dashboards, workflow builders, or write-capable MCP behavior.
