# Loop Engineer Operating Contract

Date: 2026-06-23
Status: Proposed

## Purpose

This document defines the reusable Loop Engineer operating model for FlowGuard
v1 and future projects.

A Loop Engineer does not manually prompt one coding agent step by step. A Loop
Engineer designs and supervises a repeatable control loop that discovers the
next unit of work, assigns it to fresh agents, verifies the result, persists
state, and decides whether to continue, retry, or stop.

The loop is not one large prompt. It is a small delivery system.

## Definition

Loop engineering is the practice of designing an agentic work loop with:

- a concrete goal
- durable state outside one conversation
- one isolated work objective at a time
- fresh worker agents for implementation and review
- deterministic verification gates
- explicit retry and stop conditions
- scheduled or repeated wakeups until the goal is complete

For software work, the core cycle is:

```text
select objective
-> assign implementation
-> observe diff and command output
-> verify with independent agents and deterministic checks
-> repair or open/update PR
-> persist state
-> repeat on the next wakeup
```

## Required Building Blocks

Every project loop should define these six pieces before autonomous execution:

1. **Automation cadence**: how the loop wakes up and when it stops.
2. **Isolation**: branch or worktree rules so agents do not overwrite each
   other.
3. **Skills and project rules**: files the agents must read before acting.
4. **Tooling and connectors**: test commands, GitHub, CI, logs, or product
   readback paths.
5. **Fresh agents**: separate implementer, verifier, spec reviewer, and quality
   reviewer roles.
6. **Durable memory**: a state file in the repo that records the current
   objective, branch, PR, verification evidence, blockers, and next action.

## Agent Roles

### Orchestrator

The orchestrator owns the loop. It must:

- read the project rules and loop state
- select exactly one objective
- create or reuse the correct branch or worktree
- dispatch worker agents with scoped instructions
- read verification output directly
- decide retry, stop, or PR update
- persist the state after each material step

The orchestrator must not grade its own implementation as complete without
independent verification.

### Implementer Agent

The implementer owns the smallest code or documentation change for the current
objective. It must:

- stay inside the objective scope
- write or tighten tests before behavior changes
- make the smallest implementation change
- run the targeted verification it can run locally
- report changed files, commands, output summary, and concerns

### Verification Agent

The verifier owns command evidence. It must:

- run the required targeted commands
- run full verification when appropriate
- inspect generated artifacts when the contract requires readback
- report exact pass/fail status
- avoid accepting tool success as business success without reading outputs

### Spec Reviewer Agent

The spec reviewer checks whether the diff matches the current objective. It
must reject:

- cross-PR scope creep
- missing required tests
- unapproved behavior changes
- generated artifacts committed by mistake
- changes that violate project non-goals

### Quality Reviewer Agent

The quality reviewer checks maintainability and risk. It must look for:

- brittle tests
- duplicated or speculative abstractions
- swallowed errors
- vague success states
- unrelated formatting or refactors
- hidden compatibility breaks

## State File Contract

Each autonomous project should maintain a loop state file. For FlowGuard v1 the
state file is:

```text
docs/20260623_v1_loop_state.md
```

The state file should use this structure:

```markdown
# FlowGuard v1 Loop State

Last updated: YYYY-MM-DD HH:MM TZ

## Current State

- Goal: ship FlowGuard v1.0
- Current objective: PR N - name
- Status: not_started | implementing | verifying | pr_open | merged | blocked | complete
- Branch:
- PR:
- Last automation tick:
- Next action:

## Verification Evidence

- Targeted tests:
- Full tests:
- Demo artifact check:
- Agent context readback:
- Boundary check:

## Blockers

- None

## Objective Queue

- [ ] PR 1: ...
- [ ] PR 2: ...
```

The state file is not a substitute for tests, CI, or GitHub PR state. It is the
loop's durable memory between wakeups.

## Objective Selection Rules

The loop must select one objective at a time.

1. If the state is `blocked`, do not continue until the blocker changes.
2. If a PR is open, inspect its CI and review state before changing code.
3. If CI failed, run a repair loop on the same branch.
4. If review requested changes, address only those changes.
5. If the PR is merged, mark the objective complete and select the next
   unchecked objective.
6. If no PR exists for the current objective, create or continue the branch for
   that objective.
7. Do not start the next objective in the same branch.

## Per-Objective Loop

Each objective runs through this cycle:

```text
prepare
-> implement
-> targeted verification
-> full verification
-> artifact or product readback
-> spec review
-> quality review
-> repair if needed
-> open or update PR
-> persist state
```

If any step fails, the loop records the failure and retries only after changing
strategy. Repeating the same command or prompt without a new hypothesis is not a
valid repair loop.

## Stop Conditions

The loop must stop and report when:

- the current objective is complete and a PR is open
- the same blocker appears across three consecutive ticks
- required credentials or permissions are missing
- tests fail in a way the loop cannot reproduce locally
- the requested change conflicts with project boundaries
- continuing would require destructive or irreversible action
- the loop would need to merge or release without explicit project policy

## FlowGuard v1 Loop Contract

FlowGuard v1 follows `docs/20260623_v1_implementation_plan.md`.

The objective queue is:

1. PR 1: v1 Contract Spec
2. PR 2: Runtime API Freeze Tests
3. PR 3: Artifact Schema Contract Tests
4. PR 4: Repair Context Protocol Freeze
5. PR 5: Stable Read-only MCP Surface
6. PR 6: Clean Environment Quickstart
7. PR 7: Real Or Near-real Case Study
8. PR 8: Screenshot-ready Outcome Report
9. PR 9: v1.0 Release Cleanup

FlowGuard-specific boundaries:

- do not add hosted services
- do not add dashboards
- do not add workflow builders
- do not add write-capable MCP tools
- do not add multi-language runtime support
- do not restore `contracts.json` or `failed_contracts.md`
- do not change the intentional demo failure to pass
- keep `trace.json` as the source of truth
- keep `agent_context.md` and `outcome_report.html` as separate views

FlowGuard verification gates for every implementation PR:

```bash
PYTHONPATH=src .venv/bin/python -m pytest
python -m compileall src tests examples
PYTHONPATH=src .venv/bin/python examples/github_issue_triage/pipeline.py
PYTHONPATH=src .venv/bin/python -m flowguard.cli
find .flowguard/runs/latest -maxdepth 1 -type f -print | sort
find .flowguard -name contracts.json -o -name failed_contracts.md
```

The loop must also read `.flowguard/runs/latest/agent_context.md` and confirm
that the intentional demo failure still reports `issue.triage`.

## Automation Policy

The FlowGuard v1 loop may run unattended only under these policies:

- It may create branches for one objective at a time.
- It may commit scoped changes after verification passes.
- It may open or update PRs with verification evidence.
- It may repair failing checks on the same objective branch.
- It may continue to the next objective only after the previous PR is merged or
  an explicit repository policy allows auto-merge.
- It must not tag or publish releases without an explicit release policy.

Recommended cadence:

```text
Every 30 minutes while active.
```

Shorter intervals are useful only when CI is fast and token cost is acceptable.

## Completion Report

At the end of every objective, the loop reports:

- changed files
- PR URL
- targeted verification output
- full verification output
- artifact checks
- boundary checks
- remaining risk
- next objective or stop reason

