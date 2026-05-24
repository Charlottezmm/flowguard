# FlowGuard Positioning

Last updated: 2026-05-24, after the v0.2 release.

This document is the strategic source of truth for what FlowGuard is, what it is
for, and what should stay out of scope. Technical schema details belong in
`docs/design.md` and protocol details belong in `docs/agent_context_spec.md`.

## One-Sentence Positioning

FlowGuard creates the missing failure signal for AI workflows.

Ordinary code failures give a coding agent strong signals: a stack trace, a
failing test, or a type error. AI workflow failures often look different: a step
runs, returns, raises nothing, and still produces semantically wrong output.
FlowGuard captures what happened in that run and turns it into structured repair
context for coding agents and a readable local report for humans.

The short public hook is:

```text
Stack traces for AI workflows.
```

## Enemy: Silent Quality Failure

FlowGuard is built for silent quality failures: cases where a step completes
without an exception, but the output is quietly wrong.

Examples include:

- an LLM returns an empty list or malformed-but-parseable structure
- an external API returns a shape that changed without breaking the client
- an extraction or transformation step produces data that type checks cannot
  judge
- a downstream symptom appears far away from the upstream cause

Coding agents can read code, but they cannot infer one concrete run unless the
run facts are captured. FlowGuard gives the agent something to read instead of
guessing.

## Scope

FlowGuard does not cover "all code" and does not cover only "LLM calls." Its
scope is narrower and more useful:

```text
The steps in one feature or workflow where correctness depends on observed
output and user intent, not only on types, compilation, or simple assertions.
```

In practice, this includes:

- LLM and AI model calls
- external API calls with unstable structure or content
- extraction, crawling, or transformation steps whose correctness is semantic
- steps where "good enough" is a product or business judgment

FlowGuard should map the whole feature or workflow so humans can understand the
context, but checks and repair context should focus on uncertain steps. Ordinary
deterministic code can appear in the map without FlowGuard pretending to replace
tests or type checking.

## Work Unit

FlowGuard works on the current feature or workflow, not on an entire repository.

A large codebase is the environment. The FlowGuard unit is the small workflow the
developer is actively changing: usually a handful to a few dozen steps.
`.flowguard/` tracks that current workflow and its latest development-time run.

## Product Boundary

FlowGuard is local, file-based, and development-time.

It is not:

- an observability platform
- a workflow builder
- a hosted service
- an enterprise LLMOps product
- a team permission or cloud synchronization system
- a general-purpose debugger for every function call
- a write-capable MCP control plane

This is a deliberate boundary. The long-term value is not enterprise surface
area; it is a small local format and repair-context loop that can become a
useful convention inside many repositories.

## Human And Agent Contract

`trace.json` is the source of truth for run facts. Other artifacts are derived
views:

- `workflow_map.json` renders observed step order and relationships
- `agent_context.md` renders terse repair context for coding agents
- `outcome_report.html` renders a scannable local report for humans

The human-facing and agent-facing views must not be blended.

| View | Audience | Purpose |
| --- | --- | --- |
| `agent_context.md` | coding agent | step ids, failed checks, downstream impact, relevant files, suggested focus |
| `outcome_report.html` | human | readable summary, severity, where to look, screenshot-friendly context |

The same failure should have opposite presentation styles: terse and
machine-actionable for the agent, readable and intent-level for the human.

## Check Intent

`@step` instrumentation is mostly mechanical. A coding agent can often add it
from code structure.

`@expect...` checks are different: they encode what "correct" means. That is
business or product intent, not only implementation detail. A weak check such as
`non_empty` or `file_exists` can be technically true while failing to capture the
real requirement.

FlowGuard's skill should therefore drive an intent conversation:

1. The agent locates the uncertain step.
2. The agent asks, in product language, what would make that step good enough.
3. The human confirms the intent.
4. The agent translates that intent into checks.
5. The workflow is rerun and the repair context is updated.

The rule is: prefer checks that can fail and encode intent. Do not add
trivially-passing checks to make a workflow look healthy.

## Architecture Layers

FlowGuard has four layers:

1. **Skill layer**: tells coding agents when to use FlowGuard, how to add it,
   how to ask for check intent, and how to read repair context.
2. **Python runtime layer**: captures step execution, summaries, status, errors,
   structured checks, source paths, and run root semantics.
3. **Artifact layer**: writes local files under `.flowguard/runs/latest/`.
4. **Read-only query layer**: exposes local helpers and MCP tools for reading
   artifacts without executing workflows or mutating state.

## Long-Term Direction

FlowGuard should not grow by becoming a platform. It should grow by making the
handoff loop stable:

```text
capture uncertain workflow behavior
-> judge it with intent-bearing checks
-> compare runs
-> hand coding agents stable repair context
```

Future capabilities such as auto-instrumentation or provider drift detection
should support that loop. They should not turn FlowGuard into hosted LLMOps,
workflow orchestration, or generic tracing.
