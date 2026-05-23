<!-- flowguard agent_context schema: v0.1 -->

# Agent Context

Workflow: github_issue_triage
Run: latest
Reporting: latest failed step

Failed step: issue.triage
Status: failed

Failed checks:
- affected_files must contain at least 1 items
- repro_steps must contain at least 2 items

Upstream:
- issue.parse

Downstream impacted:
- repair_brief.create

Relevant files:
- examples/github_issue_triage/pipeline.py

Input summary:
{"args": [{"title": "Bug", "body": "raw issue"}], "kwargs": {}}

Output summary:
{"issue_type": "bug", "severity": "medium", "repro_steps": ["Run demo"], "affected_files": []}

Suggested focus:
Update issue.triage so its output satisfies the failed checks before repair_brief.create consumes it.

Verification:
- Re-run the workflow that produced this context.
- Check .flowguard/runs/latest/agent_context.md.
