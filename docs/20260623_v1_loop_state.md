# FlowGuard v1 Loop State

Last updated: 2026-06-23 Asia/Shanghai

## Current State

- Goal: ship FlowGuard v1.0 by freezing the local repair loop and proving a new
  user can complete it end to end.
- Current objective: PR1 - v1 Contract Spec
- Status: pr_open
- Branch: `codex/flowguard-v1-contract-spec`
- PR: https://github.com/Charlottezmm/flowguard/pull/20
- Last automation tick: 2026-06-23 Asia/Shanghai, first manual tick after
  heartbeat creation.
- Next action: wait for PR1 review, GitHub CI, and merge gates. Do not start
  PR2 until PR1 is merged.

## Verification Evidence

- Local working-tree verification for current objective, before PR creation:
- Targeted docs test:
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_docs.py` passed, 3
  tests.
- Full tests: `PYTHONPATH=src .venv/bin/python -m pytest` passed, 61 tests.
- Compile check: `.venv/bin/python -m compileall src tests examples` passed.
- Demo artifact check: demo generated only `trace.json`, `workflow_map.json`,
  `agent_context.md`, and `outcome_report.html`.
- Agent context readback: `.flowguard/runs/latest/agent_context.md` reports
  intentional failure `issue.triage`.
- Boundary check: no `contracts.json` or `failed_contracts.md` found.
- PR merge gate: pending GitHub CI and final merge.
- Last completed objective: PR0 merged in
  https://github.com/Charlottezmm/flowguard/pull/19.

## Blockers

- None

## Objective Queue

- [x] PR0: Loop Engineer Operating Contract
- [ ] PR1: v1 Contract Spec
- [ ] PR2: Runtime API Freeze Tests
- [ ] PR3: Artifact Schema Contract Tests
- [ ] PR4: Repair Context Protocol Freeze
- [ ] PR5: Stable Read-only MCP Surface
- [ ] PR6: Clean Environment Quickstart
- [ ] PR7: Real Or Near-real Case Study
- [ ] PR8: Screenshot-ready Outcome Report
- [ ] PR9: v1.0 Release Cleanup

## Loop Notes

- PR0 is documentation-only and does not modify FlowGuard runtime behavior.
- PR1 starts only after PR0 is merged.
- Automation cadence: 30-minute heartbeat is approved.
- Auto-merge policy: approved for non-release PRs only when the GitHub PR is not
  a draft, branch protection is satisfied, required GitHub checks pass or no
  required checks are configured, targeted verification, full verification,
  artifact readback, spec review, and quality review all pass, and the merge is
  performed as a normal GitHub merge or squash merge without bypassing
  protections.
- Auto-merge rollback policy: if an auto-merged PR is later found wrong, create
  a narrow revert PR rather than force-pushing protected history.
- Release/tag/publish policy: not yet approved; PR9 must stop before tagging or
  publishing unless a release policy is added.
