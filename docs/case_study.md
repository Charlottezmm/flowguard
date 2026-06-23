# FlowGuard v1 Case Study

This case study demonstrates the full local repair loop:

```text
silent quality failure
-> FlowGuard artifacts
-> agent_context.md readback
-> fixed run
-> run compare
-> golden create
-> golden compare
```

It uses `support_reply_case_study` in `examples/case_study/pipeline.py`. The
example has no network calls, no paid API, and no private credentials. It is
deterministic and does not replace the existing GitHub issue triage demo.

## Scenario

A support reply generator returns a plausible answer for a customer export bug.
The broken reply is syntactically fine and the workflow exits normally, but it
has only one evidence item. That is a silent quality failure: downstream humans
would see a generic reply, while the agent needs to know the actual repair
focus.

FlowGuard records the failed check in `trace.json`, renders
`agent_context.md`, and keeps `outcome_report.html` as the separate human view.

## Broken Run

```bash
PYTHONPATH=src .venv/bin/python examples/case_study/pipeline.py --variant broken
PYTHONPATH=src .venv/bin/python -m flowguard.cli
PYTHONPATH=src .venv/bin/python -m flowguard.cli run save --workflow support_reply_case_study --name before-fix
```

Expected repair context:

```text
Failed step: support.reply
Failed checks:
- evidence_items must contain at least 2 items
```

The broken run writes the normal FlowGuard artifacts:

```text
.flowguard/runs/latest/agent_context.md
.flowguard/runs/latest/outcome_report.html
.flowguard/runs/latest/trace.json
.flowguard/runs/latest/workflow_map.json
```

## Fixed Run

The fixed variant represents the code change an agent would make after reading
`agent_context.md`: include enough evidence to explain why the support reply
should escalate the export issue.

```bash
PYTHONPATH=src .venv/bin/python examples/case_study/pipeline.py --variant fixed
PYTHONPATH=src .venv/bin/python -m flowguard.cli run save --workflow support_reply_case_study --name after-fix
```

The fixed latest context should say:

```text
No failed checks in the latest run.
```

## Prove The Fix

Compare the broken named run to the fixed named run:

```bash
PYTHONPATH=src .venv/bin/python -m flowguard.cli run compare --workflow support_reply_case_study --left before-fix --right after-fix
```

The command exits non-zero because the two runs differ. That is expected. The
diff proves the repair:

```text
Run comparison failed: before-fix -> after-fix
- `support.reply`: before-fix=failed, after-fix=success
```

## Prevent Regression

Create a golden baseline from the fixed latest run and compare it:

```bash
PYTHONPATH=src .venv/bin/python -m flowguard.cli golden create --workflow support_reply_case_study --name fixed
PYTHONPATH=src .venv/bin/python -m flowguard.cli golden compare --workflow support_reply_case_study --name fixed
```

The comparison should pass:

```text
Golden comparison passed: .flowguard/goldens/support_reply_case_study/fixed/baseline.json
```

If the broken variant runs again, the same golden comparison fails and reports:

```text
- `support.reply`: golden:fixed=success, latest=failed
```

This keeps `trace.json` as the source of truth and does not create
`contracts.json` or `failed_contracts.md`.
