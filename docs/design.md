# FlowGuard Design Notes

This document contains technical design notes for the current implementation.
Strategic positioning, scope, and product boundaries live in
`docs/positioning.md`. Version planning lives in `docs/v1_scope.md`.

## Artifact Ownership

`trace.json` is the source of truth for run facts. Other artifacts are derived
views:

- `workflow_map.json` is derived from observed step order and source metadata.
- `agent_context.md` is the agent-facing repair context.
- `outcome_report.html` is the human-facing local report.

Do not add another artifact that duplicates run facts unless `trace.json` cannot
represent the data cleanly.

Historical note: early specs mentioned `contracts.json` and
`failed_contracts.md`. v1 will not restore them. Checks remain in `trace.json`,
and agent-facing failure summaries are rendered through `agent_context.md`.

## Current Artifact Set

Each run writes:

```text
.flowguard/runs/latest/
  trace.json
  workflow_map.json
  agent_context.md
  outcome_report.html
```

Golden baselines are stored separately under:

```text
.flowguard/goldens/<workflow>/<name>/baseline.json
```

## Run Root Semantics

`flowguard_run()` captures the current working directory when the run starts.
Runtime artifact writes and relative file checks use that run root even if a
step changes the process working directory during execution.

This keeps `.flowguard/runs/latest/` stable and prevents file checks from being
anchored to a transient step-local directory.

## `workflow_map.json`

The workflow map is derived from the observed step order in the latest run.
FlowGuard does not perform static analysis of arbitrary Python code.

Example:

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

For the current implementation, `upstream` is the previous observed step id and
`downstream` is the next observed step id. The first step has no upstream step,
and the final step has no downstream step.

## `agent_context.md`

`agent_context.md` is the FlowGuard Repair Protocol artifact. Its current schema
is documented in `docs/agent_context_spec.md`.

Treat text changes to this file as protocol changes, not ordinary copy edits.

## `outcome_report.html`

`outcome_report.html` is a static report for humans. It should remain local and
file-based. It should not become a hosted dashboard or web server.

## MCP Boundary

The MCP adapter is a read-only query layer over local artifacts. It should use
the local query API rather than reimplementing artifact reads directly.

It must not:

- execute workflows
- edit code
- write artifacts
- synchronize with hosted services
- become a workflow control plane

## v0.3 Design Work

The next design work is schema formalization:

- add explicit `schema_version` fields where appropriate
- document stable fields versus display-only fields
- add schema validation tests
- add compatibility tests for reading v0.2 artifacts

This work is tracked in `docs/v1_scope.md`.
