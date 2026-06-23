# FlowGuard v1.0.0 Release Review

Date: 2026-06-23
Release: `v1.0.0`
Release/tag/publish status: not authorized yet

## Release Result

FlowGuard v1.0.0 is prepared for release review.

This PR does not create a tag, publish a package, or create a GitHub release.
Those steps require an explicit release/tag/publish policy.

## What Is Frozen For v1

- Python runtime with `flowguard_run()`, `@step`, and `@expect...`.
- Latest run artifact set:
  - `trace.json`
  - `workflow_map.json`
  - `agent_context.md`
  - `outcome_report.html`
- Artifact-specific schema versions and legacy v0.2 read compatibility.
- Repair Context Protocol for `agent_context.md`.
- Stable read-only MCP stdio surface.
- Local query helpers, named runs, run comparison, and golden baselines.
- Clean checkout quickstart.
- Deterministic local case study.
- Screenshot-ready local outcome report.

`trace.json` remains the source of truth. `agent_context.md` and
`outcome_report.html` remain separate derived views for different audiences.

## Verification

Release cleanup verification was run locally on 2026-06-23:

```bash
PYTHONPATH=src .venv/bin/python -m pytest
.venv/bin/python -m compileall src tests examples
PYTHONPATH=src .venv/bin/python examples/github_issue_triage/pipeline.py
PYTHONPATH=src .venv/bin/python -m flowguard.cli
PYTHONPATH=src .venv/bin/python -m flowguard.cli run save --workflow github_issue_triage --name v1-final
PYTHONPATH=src .venv/bin/python -m flowguard.cli run compare --workflow github_issue_triage --left v1-final --right latest
PYTHONPATH=src .venv/bin/python -m flowguard.cli golden create --workflow github_issue_triage --name v1-final
PYTHONPATH=src .venv/bin/python -m flowguard.cli golden compare --workflow github_issue_triage --name v1-final
find .flowguard/runs/latest -maxdepth 1 -type f -print | sort
find .flowguard -name contracts.json -o -name failed_contracts.md
git diff --check
```

Observed results:

- `PYTHONPATH=src .venv/bin/python -m pytest` passed: 86 tests.
- `.venv/bin/python -m compileall src tests examples` passed.
- The GitHub issue triage demo completed and CLI readback still reports the
  intentional failed step: `issue.triage`.
- Latest run writes exactly four files:
  - `.flowguard/runs/latest/agent_context.md`
  - `.flowguard/runs/latest/outcome_report.html`
  - `.flowguard/runs/latest/trace.json`
  - `.flowguard/runs/latest/workflow_map.json`
- `run save --workflow github_issue_triage --name v1-final` passed.
- `run compare --workflow github_issue_triage --left v1-final --right latest`
  printed `Run comparison passed: v1-final -> latest`.
- `golden create --workflow github_issue_triage --name v1-final` passed.
- `golden compare --workflow github_issue_triage --name v1-final` printed
  `Golden comparison passed`.
- `find .flowguard -name contracts.json -o -name failed_contracts.md` returned
  no files.
- `git diff --check` passed.

## Boundary Check

v1.0.0 stays within the intended product boundary:

- No hosted service.
- No dashboard.
- No workflow builder.
- No cloud sync.
- No write-capable MCP tools.
- No multi-language runtime.
- No restoration of `contracts.json` or `failed_contracts.md`.
- No change to the intentional GitHub issue triage demo failure.
- No merging of `agent_context.md` and `outcome_report.html` into one view.

## Release Authorization

The release cleanup PR may be reviewed and merged, but release publication is
blocked until an explicit policy authorizes the following commands:

```bash
git tag v1.0.0
git push origin v1.0.0
gh release create v1.0.0 --title "FlowGuard v1.0.0" --notes-file docs/20260623_v1_release_review.md
```

Until that policy exists, stop before tagging or publishing.
