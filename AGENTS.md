# FlowGuard Agent Instructions

FlowGuard turns workflow run facts into repair context for AI coding agents.

## Required Reading

- Read `docs/v0.1_execution_plan.md` before v0.1 implementation work.
- Read `docs/design.md` before changing artifact schemas.
- Read the relevant source, tests, exports, and callers before editing code.

## Engineering Rules

1. State assumptions before coding when requirements are ambiguous.
2. Make the smallest change that satisfies the task.
3. Touch only files needed for the current task.
4. Prefer deterministic code over LLM-generated judgment.
5. Do not add speculative abstractions for future flexibility.
6. Surface conflicting patterns instead of blending them.
7. Match existing codebase conventions.
8. Tests must verify intent, not only implementation details.
9. Fail loud: silent skips, swallowed errors, and vague success states are bugs.
10. Checkpoint after each significant milestone with concrete verification.

## v0.1 Boundaries

- Keep FlowGuard local-first.
- Do not add paid APIs, hosted services, MCP, dashboards, or web servers.
- Do not add external runtime dependencies unless explicitly justified.
- Generated artifacts must be reproducible and useful to coding agents.

## Verification

Use the project virtual environment when available:

```bash
PYTHONPATH=src .venv/bin/python examples/github_issue_triage/pipeline.py
PYTHONPATH=src .venv/bin/python -m flowguard.cli
PYTHONPATH=src .venv/bin/python -m pytest
```

`AGENTS.md` tells AI agents how to work in this repo. FlowGuard's
`agent_context.md` tells AI agents what happened in a run and what to fix next.
