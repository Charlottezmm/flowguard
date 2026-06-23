# FlowGuard v1 Scope

This document defines the path from v0.2 to v1.0. It translates
`docs/positioning.md` into versioned deliverables and explicit non-goals.

The v1 contract source is
[`docs/20260623_v1_technical_design.md`](20260623_v1_technical_design.md).
Use that document for the stable runtime, artifact, query, MCP, repair-context,
and release-boundary contract.

## v1 Definition

FlowGuard v1 freezes a local, agent-native handoff loop:

```text
capture uncertain workflow behavior
-> judge it with intent-bearing checks
-> compare runs
-> hand coding agents a stable repair context protocol
```

v1 is not the version with the most features. It is the version where the core
loop is stable enough for a stranger to install, run, understand, and use during
AI workflow debugging.

## Current Baseline: v0.3

v0.3 has shipped the v0.2 baseline:

- Python runtime with `flowguard_run()`, `@step`, and `@expect...`
- structured check results while preserving `failures` strings
- file artifact checks
- response-like output checks
- local golden baselines
- read-only query helpers
- experimental read-only MCP adapter
- FlowGuard skill source exists and has been verified locally

v0.3 adds:

- artifact-specific schema versions for stable JSON artifacts
- documented stable fields versus derived or display-only fields
- compatibility tests for reading v0.2 artifacts
- check-intent workflow guidance in the FlowGuard skill
- integration guide and check cookbook
- named run save/list support
- run comparison for named runs, latest runs, and golden baselines
- agent-readable comparison diffs

The v0.3 capability verbs are:

```text
capture + judge + compare
```

## v0.3 Theme

v0.3 shipped as one release with several small PRs. The theme is:

```text
integration experience + run comparison
```

The implementation was split into small PRs so review and rollback stayed easy.

### PR 1: Positioning And Scope

Scope:

- add `docs/positioning.md`
- add `docs/v1_scope.md`
- update README positioning and roadmap
- reduce `docs/design.md` to technical notes that point to positioning for
  strategic scope
- make artifact ownership explicit: `trace.json` stores run facts, other
  artifacts are derived views

This PR should not change runtime behavior.

### PR 2: Artifact Schema Versioning

Scope:

- add `schema_version` to stable artifacts
- document stable fields versus display-only fields
- add JSON schema checks or equivalent validation tests
- add compatibility tests that can read v0.2 artifacts
- decide schema treatment for status values without freezing the project into
  only binary pass/fail semantics

Decision:

```text
v1 will not restore the old spec's contracts.json or failed_contracts.md.
Checks remain in trace.json. Agent-facing failure summaries are rendered through
agent_context.md.
```

This decision prevents future agents from reintroducing old artifacts after
reading historical specs.

### PR 3: Skill Intent Workflow And Docs

Scope:

- update the FlowGuard skill with the check-intent conversation
- explicitly forbid weak checks that always pass but do not encode intent
- add an integration guide for adding FlowGuard to an existing Python workflow
- add a check cookbook with examples for LLM output, API response, file artifact,
  JSON artifact, and downstream dependency failures
- explain that the agent may add `@step` mechanically, but must ask or confirm
  the intent behind `@expect...` checks

Integration guide and check cookbook are v0.3 deliverables. They should be part
of this PR unless PR 1 remains documentation-only and they are small enough to
land there without bloating the positioning work. They should not be postponed
past v0.3.

### PR 4: Run Comparison

Scope:

- save and list named runs
- compare two runs
- compare latest run against a golden baseline
- report step status changes, check changes, failure changes, and downstream
  impact changes
- provide an agent-readable diff
- expose comparison through CLI and read-only query helpers

Tests should construct known-difference runs and assert the exact comparison
output.

## v1.0 Theme

v1.0 is:

```text
handoff + stranger usability + closed loop
```

Required capabilities:

- frozen skill behavior
- stable Python runtime API
- stable artifact schema
- stable read-only MCP query surface
- finalized Repair Context Protocol for `agent_context.md`
- stable run comparison
- one real or near-real case study
- README rewritten around the public hook
- screenshot-ready `outcome_report.html`
- demo GIF or video

The case study must show the full loop:

```text
silent quality failure
-> FlowGuard artifacts
-> agent reads repair context
-> code is fixed
-> run comparison proves the fix
-> golden baseline prevents regression
```

## v1 Validation

v1 should be validated with:

- clean-environment quickstart from README
- artifact schema validation
- frozen API and schema snapshot tests
- MCP smoke tests
- the real-world case study as an end-to-end test
- at least a few external users after release, not as a release blocker

The "stranger can use it" test matters more than adding more surface area.

## v1 Non-Goals

v1 does not include:

- hosted service
- dashboard
- workflow builder
- production LLMOps
- multi-user permissions
- cloud sync
- multi-language runtimes
- automatic generation of full workflows
- write-capable MCP tools
- auto-instrumentation
- provider drift detection
- framework adapters for LangChain, LlamaIndex, or similar systems

## v1+ Candidates

After v1, the strongest candidates are:

- auto-instrumentation to reduce integration cost in larger codebases
- provider drift detection scoped to the same workflow and checks across
  provider, model, or prompt changes
- richer state for partially observable or non-deterministic steps
- framework adapters

These should remain subordinate to the core handoff loop.
