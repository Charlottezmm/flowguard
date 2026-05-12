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
4. Add minimal outcome checks to critical steps.
5. Run the workflow or tests.
6. Read `.flowguard/runs/latest/agent_context.md`.
7. Make the smallest relevant fix.
8. Re-run FlowGuard checks.

## Constraints

- Keep changes minimal.
- Do not convert the project into a new framework.
- Prefer local artifacts over hosted services.
- Treat `agent_context.md` as the primary handoff artifact for debugging.

