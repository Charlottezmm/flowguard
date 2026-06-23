# FlowGuard v1 Technical Design

Date: 2026-06-23
Status: Contract source

## Purpose

FlowGuard v1 freezes the local handoff loop that v0.3 made possible:

```text
capture uncertain workflow behavior
-> judge it with intent-bearing checks
-> compare runs
-> hand coding agents stable repair context
```

v1 is not a feature-expansion release. It is the release where the existing
FlowGuard core becomes stable enough for a new user to install, run, understand,
and use during AI workflow debugging.

## Product Positioning

FlowGuard is:

```text
Stack traces for AI workflows.
```

It creates the missing failure signal for silent quality failures:

- a workflow step runs successfully
- no exception is raised
- the output is semantically wrong
- downstream steps are polluted
- a coding agent has no run facts and starts guessing

FlowGuard records the run facts and turns them into:

- `agent_context.md` for coding agents
- `outcome_report.html` for humans

## Non-Goals

v1 must not expand FlowGuard into a broader platform. The following remain out
of scope:

- hosted service
- dashboard
- workflow builder
- production LLMOps
- cloud sync
- multi-user permissions
- write-capable MCP tools
- multi-language runtime
- auto-instrumentation
- framework adapters for LangChain, LlamaIndex, or similar systems
- provider drift detection
- restored `contracts.json` or `failed_contracts.md`

## Current Baseline

v0.3.0 has shipped:

- Python runtime with `flowguard_run()`, `@step`, and `@expect...`
- structured checks
- file artifact checks
- response-like checks
- local golden baselines
- local read-only query helpers
- experimental read-only MCP adapter
- artifact-specific `schema_version` fields for stable JSON artifacts
- v0.2 read compatibility for artifacts without `schema_version`
- fail-loud behavior for unknown future artifact versions
- named run save/list support
- named run and golden comparison
- agent-readable comparison diffs
- path hardening for named run and golden references
- integration guide and check cookbook
- FlowGuard skill guidance for check intent

v1 should stabilize this surface instead of adding a new one.

## Stable Runtime API

The v1 public Python runtime surface is:

```python
from flowguard import expect, flowguard_run, step
```

### `flowguard_run(workflow: str)`

`flowguard_run()` starts a local run for one workflow. Its v1 contract is:

- write artifacts under `.flowguard/runs/latest/`
- use the process current working directory as the run root when the run starts
- keep writing artifacts even when a step fails a check or raises an exception
- record run facts in `trace.json`
- derive `workflow_map.json`, `agent_context.md`, and `outcome_report.html`
- never call external services
- never require hosted state or credentials

### `@step`

`@step` marks a workflow function as an observed step. Its v1 contract is:

- record step id, name, source, status, input summary, output summary, failures,
  checks, and error facts
- preserve observed run order
- produce deterministic step facts for the same function behavior
- not infer user intent by itself

Agents may add `@step` mechanically when mapping an existing workflow.

### `@expect...`

`@expect...` marks intent-bearing checks. Its v1 contract is:

- checks must encode meaningful correctness intent
- weak checks that only exist to pass, such as arbitrary `non_empty` or
  `file_exists` checks without business meaning, are invalid usage
- failed checks should create repair signal for `agent_context.md`
- checks run locally over objects or files already produced by the workflow

Agents may draft checks, but the intended definition of correct output must be
confirmed by the user or by existing project tests/docs.

## Artifact Model

`trace.json` remains the source of truth. Other artifacts are derived views.

Each run writes exactly these stable run artifacts:

```text
.flowguard/runs/latest/
  trace.json
  workflow_map.json
  agent_context.md
  outcome_report.html
```

Golden baselines remain under:

```text
.flowguard/goldens/<workflow>/<name>/baseline.json
```

Named run snapshots remain under:

```text
.flowguard/runs/named/<workflow>/<name>/
```

The named run path is local metadata. It must not rewrite `trace.json` run facts.

## Stable JSON Schemas

v1 keeps artifact-specific schema versions.

| Artifact | v0.3 schema | v1 decision |
| --- | --- | --- |
| `trace.json` | `flowguard.trace.v0.3` | Keep unless v1 changes stable fields. |
| `workflow_map.json` | `flowguard.workflow_map.v0.3` | Keep unless v1 changes stable fields. |
| `baseline.json` | `flowguard.golden.v0.3` | Keep unless v1 changes stable fields. |

If v1 changes stable fields, bump only the affected artifact type, for example:

```text
flowguard.trace.v1
flowguard.workflow_map.v1
flowguard.golden.v1
```

Do not write `legacy-v0.2`. That label is read-only compatibility behavior for
old artifacts that have no `schema_version`.

Unknown future schema versions must fail loudly. Silent acceptance of future
schema versions is a bug because it can make agents trust fields with changed
semantics.

## Stable Artifact Fields

### `trace.json`

Stable top-level fields:

- `schema_version`
- `run_id`
- `workflow`
- `steps`

Stable step fields:

- `id`
- `name`
- `status`
- `source`
- `failures`
- `checks`
- `error`

Unstable run facts:

- `started_at`
- `updated_at`
- `duration_ms`
- `input_summary`
- `output_summary`

The unstable fields may be useful for humans and agents, but golden comparison
must not depend on exact values.

### `workflow_map.json`

Stable fields:

- `schema_version`
- `workflow`
- `steps`
- step `id`
- step `name`
- step `index`
- step `status`
- step `source`
- step `upstream`
- step `downstream`

`workflow_map.json` remains derived from observed run order. v1 does not add
static Python call graph analysis.

### Golden `baseline.json`

Stable fields:

- `schema_version`
- `workflow`
- `steps`
- normalized step `id`
- normalized step `name`
- normalized step `status`
- normalized step `source`
- normalized step `failures`
- normalized step `checks`
- normalized step `error`
- normalized step `upstream`
- normalized step `downstream`

Golden baselines intentionally exclude volatile timestamps, durations, and
summary strings.

## Repair Context Protocol

`agent_context.md` is the primary v1 agent-facing artifact. It is not a verbose
log and it is not a human report.

The existing header remains:

```md
<!-- flowguard agent_context schema: v0.1 -->
```

Do not add a second version mechanism to `agent_context.md`.

v1 should freeze the current section contract documented in
`docs/agent_context_spec.md`:

- `Workflow`
- `Run`
- `Reporting`
- `Failed step`
- `Status`
- `Failed checks`
- `Error`
- `Upstream`
- `Downstream impacted`
- `Relevant files`
- `Input summary`
- `Output summary`
- `Suggested focus`
- `Verification`

`Error` appears only when the selected failed step has an exception.

For v1, changes to section names, ordering, or deterministic suggested-focus
templates are protocol changes and require explicit tests.

## Run Comparison

Run comparison is a derived query view over normalized run artifacts. It must
not write a new source-of-truth artifact.

The v1 comparison contract includes:

- compare named run to named run
- compare named run to latest
- compare latest to golden baseline
- align steps by step id
- report added and removed steps
- report step status changes
- report added, removed, and status-changed checks
- report added and removed failure strings
- report error changes
- report downstream impact changes
- emit an agent-readable diff

Golden comparison and named-run comparison must share the same comparison
engine so agent-readable diffs stay consistent.

## Query API

The v1 query API is the local read layer for artifacts. It should remain a thin,
deterministic layer over local files.

Stable query behavior:

- read latest run facts
- summarize latest status
- find failed step
- read workflow map
- read agent context
- list named runs
- load named runs
- save named runs
- load golden baselines
- validate schema versions before trusting JSON artifacts

Query functions must fail loudly for unsupported schema versions and unsafe path
segments.

## MCP Surface

MCP is read-only in v1.

The MCP adapter must:

- use the local query API
- expose latest run status
- expose failed step
- expose workflow map
- expose agent context
- return clear errors when artifacts are missing or unsupported

The MCP adapter must not:

- execute workflows
- edit code
- write artifacts
- create golden baselines
- save named runs
- compare runs as a write operation
- synchronize with hosted services
- become a workflow control plane

If run comparison is exposed through MCP in v1, it must be read-only and must
not create, mutate, or delete artifacts.

## Human Report

`outcome_report.html` remains a local static HTML report for humans. Its v1 goal
is screenshot-ready clarity, not dashboard behavior.

The report should show:

- workflow
- run id
- overall status
- failed step
- failed checks
- downstream impact
- relevant source files when available
- link to `agent_context.md`

It must keep escaping untrusted values. Workflow outputs, failures, and errors
may contain HTML-like text and must not become executable markup.

## Documentation Surface

v1 documentation should optimize for a new user who has never seen the project.

Required docs:

- README quickstart
- positioning
- v1 contract
- integration guide
- check cookbook
- agent context spec
- case study

The README should prove the shortest useful loop:

```text
install
-> run demo
-> inspect agent_context.md
-> save run
-> compare run
-> create golden baseline
-> compare golden baseline
```

## Case Study Contract

v1 needs one real or near-real case study that demonstrates the full FlowGuard
loop:

```text
silent quality failure
-> FlowGuard artifacts
-> agent reads repair context
-> code is fixed
-> run comparison proves the fix
-> golden baseline prevents regression
```

The case study should be local and deterministic. It should not depend on paid
APIs, network services, or private credentials.

## Validation Matrix

v1 is ready only when these checks pass:

```bash
PYTHONPATH=src .venv/bin/python -m pytest
python -m compileall src tests examples
PYTHONPATH=src .venv/bin/python examples/github_issue_triage/pipeline.py
PYTHONPATH=src .venv/bin/python -m flowguard.cli
PYTHONPATH=src .venv/bin/python -m flowguard.cli run save --workflow github_issue_triage --name v1-check
PYTHONPATH=src .venv/bin/python -m flowguard.cli run compare --workflow github_issue_triage --left v1-check --right latest
PYTHONPATH=src .venv/bin/python -m flowguard.cli golden create --workflow github_issue_triage --name v1-check
PYTHONPATH=src .venv/bin/python -m flowguard.cli golden compare --workflow github_issue_triage --name v1-check
```

Additional release checks:

- clean-environment quickstart from README
- artifact schema contract tests
- Repair Context Protocol snapshot tests
- MCP smoke tests
- case study end-to-end test
- demo still reports intentional `issue.triage` failure
- latest run still writes the four expected artifacts
- no `contracts.json`
- no `failed_contracts.md`

## Release Rule

Do not create a v0.4 by default. Create a v0.4 only if a concrete issue appears
that blocks v1 readiness, is too large for a small hardening PR, and does not
belong naturally inside v1 stabilization.
