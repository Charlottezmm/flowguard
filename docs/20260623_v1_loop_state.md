# FlowGuard v1 Loop State

Last updated: 2026-06-23 23:12 Asia/Shanghai

## Current State

- Goal: ship FlowGuard v1.0 by freezing the local repair loop and proving a new
  user can complete it end to end.
- Current objective: PR9 - v1.0 Release Cleanup
- Status: pr_open
- Branch: `codex/flowguard-v1-release-cleanup`
- PR: https://github.com/Charlottezmm/flowguard/pull/28
- Last automation tick: 2026-06-23T14:20:38Z heartbeat.
- Next action: merge PR9 after fresh verification and GitHub CI pass, then tag
  `v1.0.0` and create the GitHub release.

## Verification Evidence

- Targeted tests: `PYTHONPATH=src .venv/bin/python -m pytest
  tests/test_mcp_server.py tests/test_release_metadata.py` passed, 7 tests.
- Full tests: `PYTHONPATH=src .venv/bin/python -m pytest` passed, 86 tests.
- Compile check: `.venv/bin/python -m compileall src tests examples` passed.
- Final release verification: demo pipeline, CLI context readback,
  `run save --workflow github_issue_triage --name v1-final`,
  `run compare --workflow github_issue_triage --left v1-final --right latest`,
  `golden create --workflow github_issue_triage --name v1-final`, and
  `golden compare --workflow github_issue_triage --name v1-final` passed.
- Demo artifact check: latest run generated exactly `trace.json`,
  `workflow_map.json`, `agent_context.md`, and `outcome_report.html`.
- Agent context readback: `.flowguard/runs/latest/agent_context.md` reports
  intentional failure `issue.triage`.
- MCP metadata readback: initialize response reports serverInfo version
  `1.0.0`.
- Boundary check: no `contracts.json` or `failed_contracts.md` found; no local
  `v1.0.0` tag found; `gh release view v1.0.0` reports release not found;
  `git diff --check` passed.
- Verifier: approved by fresh verifier.
- Spec review: approved by fresh reviewer after stale loop state was fixed.
- Quality review: approved by fresh reviewer after stale loop state was fixed.
- CI repair: GitHub Python 3.10 failed because `tests/test_release_metadata.py`
  imported Python 3.11+ `tomllib`; the test now falls back to `tomli` on Python
  3.10. Local Python 3.12 targeted tests, full tests, and compile check passed
  after the repair. GitHub CI then passed on Python 3.10 and Python 3.12.
- Release policy: approved by the project owner in chat on 2026-06-23. PR9 may
  be merged after fresh verification and GitHub CI pass, then `v1.0.0` may be
  tagged and published as a GitHub release. No PyPI or other package registry
  publish is authorized by this policy.
- PR merge gate: pending fresh verification and GitHub CI after recording the
  release policy.
- Last completed objective: PR8 merged in
  https://github.com/Charlottezmm/flowguard/pull/27.

## Blockers

- None

## Objective Queue

- [x] PR0: Loop Engineer Operating Contract
- [x] PR1: v1 Contract Spec
- [x] PR2: Runtime API Freeze Tests
- [x] PR3: Artifact Schema Contract Tests
- [x] PR4: Repair Context Protocol Freeze
- [x] PR5: Stable Read-only MCP Surface
- [x] PR6: Clean Environment Quickstart
- [x] PR7: Real Or Near-real Case Study
- [x] PR8: Screenshot-ready Outcome Report
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
- Release/tag/publish policy: approved for PR9 only. Authorized actions are:
  merge PR9, create and push tag `v1.0.0`, and create a GitHub release from
  `docs/20260623_v1_release_review.md`. No package registry publish is
  authorized.
