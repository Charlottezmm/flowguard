# FlowGuard Design Notes

FlowGuard is a workflow context bridge for AI coding agents.

The first version focuses on local artifacts:

- `workflow_map.json`
- `trace.json`
- `agent_context.md`
- `outcome_report.html`

The goal is to reduce repeated human explanation during AI-assisted debugging.

## v0.1 Demo

The v0.1 demo uses a GitHub issue triage workflow instead of a marketing or video pipeline.

```text
GitHub issue text
-> parsed issue
-> issue triage
-> repair brief
```

This keeps the open-source demo clearly developer-focused and avoids mixing FlowGuard with closed-source business workflows.
