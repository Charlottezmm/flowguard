# FlowGuard Quickstart Check

This checklist verifies the README quickstart from a clean checkout. It uses
only local files and the project virtual environment.

## Commands

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
PYTHONPATH=src .venv/bin/python examples/github_issue_triage/pipeline.py
PYTHONPATH=src .venv/bin/python -m flowguard.cli
sed -n '1,80p' .flowguard/runs/latest/agent_context.md
PYTHONPATH=src .venv/bin/python -m flowguard.cli run save --workflow github_issue_triage --name quickstart
PYTHONPATH=src .venv/bin/python -m flowguard.cli run compare --workflow github_issue_triage --left quickstart --right latest
PYTHONPATH=src .venv/bin/python -m flowguard.cli golden create --workflow github_issue_triage --name quickstart
PYTHONPATH=src .venv/bin/python -m flowguard.cli golden compare --workflow github_issue_triage --name quickstart
```

## Expected Outcomes

After the demo command, the latest run directory contains exactly the four
runtime artifacts:

```text
.flowguard/runs/latest/agent_context.md
.flowguard/runs/latest/outcome_report.html
.flowguard/runs/latest/trace.json
.flowguard/runs/latest/workflow_map.json
```

`agent_context.md` reports the intentional demo failure:

```text
Failed step: issue.triage
```

The CLI context command and direct `agent_context.md` readback print the same
repair context. The demo failure is expected; it proves FlowGuard captured a
silent quality failure instead of making the example pass.

The named run commands should print:

```text
Saved named run: .flowguard/runs/named/github_issue_triage/quickstart
Run comparison passed: quickstart -> latest
```

The golden commands should print:

```text
Created golden baseline: .flowguard/goldens/github_issue_triage/quickstart/baseline.json
Golden comparison passed: .flowguard/goldens/github_issue_triage/quickstart/baseline.json
```

No quickstart command should create `contracts.json` or
`failed_contracts.md`.
