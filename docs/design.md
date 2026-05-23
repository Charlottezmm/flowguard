# FlowGuard Design Notes

FlowGuard is a workflow context bridge for AI coding agents.

## Execution Plan

The v0.1 implementation plan and agent briefs live in `docs/v0.1_execution_plan.md`.
The repair handoff format is documented in `docs/agent_context_spec.md`.

The first version focuses on local artifacts:

- `workflow_map.json`
- `trace.json`
- `agent_context.md`
- `outcome_report.html`

The goal is to reduce repeated human explanation during AI-assisted debugging.

## v0.1 Artifact Schemas

### `workflow_map.json`

The workflow map is derived from the observed step order in the latest run. v0.1
does not perform static analysis of arbitrary Python code.

```json
{
  "workflow": "github_issue_triage",
  "steps": [
    {
      "id": "issue.triage",
      "name": "issue.triage",
      "index": 1,
      "status": "failed",
      "source": "examples/github_issue_triage/pipeline.py",
      "upstream": ["issue.parse"],
      "downstream": ["repair_brief.create"]
    }
  ]
}
```

For v0.1, `upstream` is the previous observed step id and `downstream` is the
next observed step id. The first step has no upstream step, and the final step
has no downstream step.

## v0.1 Demo

The v0.1 demo uses a GitHub issue triage workflow instead of a marketing or video pipeline.

```text
GitHub issue text
-> parsed issue
-> issue triage
-> repair brief
```

This keeps the open-source demo clearly developer-focused and avoids mixing FlowGuard with closed-source business workflows.
