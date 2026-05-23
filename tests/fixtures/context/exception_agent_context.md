<!-- flowguard agent_context schema: v0.1 -->

# Agent Context

Workflow: exception_demo
Run: latest
Reporting: latest failed step

Failed step: issue.triage
Status: error

Failed checks:
- none

Error:
- RuntimeError('boom')

Upstream:
- issue.parse

Downstream impacted:
- none

Relevant files:
- examples/github_issue_triage/pipeline.py

Input summary:
{"args": [{"title": "Bug"}], "kwargs": {}}

Output summary:
null

Suggested focus:
Inspect issue.triage and its input summary. Fix the exception before changing downstream steps.

Verification:
- Re-run the workflow that produced this context.
- Check .flowguard/runs/latest/agent_context.md.
