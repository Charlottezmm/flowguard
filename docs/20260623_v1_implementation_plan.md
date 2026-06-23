# FlowGuard v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development or an equivalent fresh-worker loop to
> implement this plan one PR at a time. Do not start the next PR until the
> current PR is reviewed, verified, and merged.

**Goal:** Ship FlowGuard v1.0 by freezing the existing local repair loop and
proving that a new user can complete it end to end.

**Architecture:** v1 stabilizes the current local file-based architecture.
`trace.json` remains the source of truth; `workflow_map.json`,
`agent_context.md`, `outcome_report.html`, named runs, golden baselines, query,
CLI, and MCP remain derived or read-only layers over local artifacts.

**Tech Stack:** Python standard library, pytest, local Markdown/HTML artifacts,
JSON files, stdio MCP adapter. No new runtime dependencies by default.

---

## Implementation Rules

- Keep every PR small and reviewable.
- Prefer contract tests before implementation changes.
- Do not add hosted services, dashboards, write-capable MCP tools, workflow
  builders, or multi-language runtime support.
- Do not restore `contracts.json` or `failed_contracts.md`.
- Do not change the intentional demo failure just to make the demo pass.
- Treat `agent_context.md` text changes as protocol changes.
- Treat `trace.json` as the source of truth.
- Keep `agent_context.md` and `outcome_report.html` separate audience views.

## PR Sequence

### PR 1: v1 Contract Spec

**Goal:** Land the written v1 contract before changing runtime behavior.

**Files:**

- Create or keep: `docs/20260623_v1_technical_design.md`
- Modify: `docs/v1_scope.md`
- Modify: `README.md`

**Steps:**

1. Add a README link to the v1 technical design.
2. Update `docs/v1_scope.md` so it points to the technical design as the v1
   contract source.
3. Keep this PR documentation-only.
4. Run:

   ```bash
   PYTHONPATH=src .venv/bin/python -m pytest
   python -m compileall src tests examples
   ```

**Acceptance:**

- The v1 stable surface is documented.
- Non-goals are explicit.
- No runtime behavior changes.

**Suggested commit:**

```bash
git add README.md docs/v1_scope.md docs/20260623_v1_technical_design.md
git commit -m "docs: define v1 technical contract"
```

### PR 2: Runtime API Freeze Tests

**Goal:** Lock the public Python runtime API behavior.

**Files:**

- Modify: `tests/test_runtime.py`
- Modify if needed: `tests/test_expectations.py`
- Modify only if tests expose a real gap: `src/flowguard/runtime.py`
- Modify only if tests expose a real gap: `src/flowguard/expectations.py`

**Tests to add:**

- `flowguard_run()` always writes the four latest artifacts.
- run root is captured when the run starts.
- a failed expectation records failed status without preventing artifact writes.
- an exception records error facts and still writes `agent_context.md`.
- `@step` preserves stable step fields.
- `@expect...` writes structured check facts used by trace/query/golden.

**Steps:**

1. Add failing tests for any missing public contract.
2. Run targeted tests:

   ```bash
   PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime.py tests/test_expectations.py
   ```

3. Implement only the minimal code needed if a test reveals behavior is missing.
4. Run full tests:

   ```bash
   PYTHONPATH=src .venv/bin/python -m pytest
   python -m compileall src tests examples
   ```

**Acceptance:**

- Runtime public behavior is covered by tests.
- No new runtime feature surface is introduced.

**Suggested commit:**

```bash
git add src/flowguard/runtime.py src/flowguard/expectations.py tests/test_runtime.py tests/test_expectations.py
git commit -m "test: freeze runtime API behavior"
```

### PR 3: Artifact Schema Contract Tests

**Goal:** Make stable artifact fields and compatibility behavior explicit enough
for v1.

**Files:**

- Modify: `tests/test_schema.py`
- Modify: `tests/test_query.py`
- Modify: `tests/test_golden.py`
- Modify only if needed: `src/flowguard/schema.py`
- Modify only if needed: `src/flowguard/query.py`
- Modify only if needed: `src/flowguard/golden.py`

**Tests to add or tighten:**

- current schema versions are artifact-specific
- missing `schema_version` reads as legacy v0.2 for supported artifacts
- new artifacts never write `legacy-v0.2`
- unknown future versions fail loudly
- stable fields exist in newly generated `trace.json`
- stable fields exist in newly generated `workflow_map.json`
- stable fields exist in newly created golden `baseline.json`

**Steps:**

1. Add or tighten schema tests.
2. Run:

   ```bash
   PYTHONPATH=src .venv/bin/python -m pytest tests/test_schema.py tests/test_query.py tests/test_golden.py
   ```

3. If implementation changes are needed, keep them inside schema/query/golden
   loading and validation paths.
4. Run full verification:

   ```bash
   PYTHONPATH=src .venv/bin/python -m pytest
   python -m compileall src tests examples
   ```

**Acceptance:**

- Stable JSON artifact contracts are tested.
- Legacy read compatibility remains.
- Unknown future versions fail loudly.

**Suggested commit:**

```bash
git add src/flowguard/schema.py src/flowguard/query.py src/flowguard/golden.py tests/test_schema.py tests/test_query.py tests/test_golden.py
git commit -m "test: freeze artifact schema contracts"
```

### PR 4: Repair Context Protocol Freeze

**Goal:** Make `agent_context.md` a stable v1 repair protocol artifact.

**Files:**

- Modify: `docs/agent_context_spec.md`
- Modify: `tests/test_context.py`
- Modify fixtures under: `tests/fixtures/context/`
- Modify only if needed: `src/flowguard/context.py`

**Tests to add or tighten:**

- generated context starts with the existing header:

  ```md
  <!-- flowguard agent_context schema: v0.1 -->
  ```

- failed-run sections appear in documented order
- no-failure context remains stable
- error context includes `Error`
- expectation failure context includes `Failed checks`
- downstream wording remains `Downstream impacted`
- relevant files are sourced only from runtime facts
- summary truncation text remains deterministic

**Steps:**

1. Update `docs/agent_context_spec.md` from v0.1 artifact notes to v1 stable
   protocol contract.
2. Add or tighten snapshot tests.
3. Run:

   ```bash
   PYTHONPATH=src .venv/bin/python -m pytest tests/test_context.py
   ```

4. If snapshots change, inspect the whole generated context manually before
   accepting the change.
5. Run full tests.

**Acceptance:**

- `agent_context.md` protocol behavior is documented and tested.
- No second schema/version mechanism is introduced.
- Text changes are intentional and reviewed as protocol changes.

**Suggested commit:**

```bash
git add docs/agent_context_spec.md src/flowguard/context.py tests/test_context.py tests/fixtures/context
git commit -m "docs: freeze repair context protocol"
```

### PR 5: Stable Read-only MCP Surface

**Goal:** Move MCP from experimental wording toward a stable read-only v1
surface without adding write behavior.

**Files:**

- Modify: `src/flowguard/mcp_server.py`
- Modify: `tests/test_mcp_server.py`
- Modify: `docs/design.md`
- Modify: `README.md`

**Contract:**

MCP may expose:

- latest run status
- failed step
- workflow map
- agent context

MCP must not:

- execute workflows
- write artifacts
- create golden baselines
- save named runs
- edit code
- synchronize with hosted services

**Tests to add or tighten:**

- list-tools output is stable
- every tool returns the documented shape
- missing artifacts return clear JSON-RPC errors
- no write-capable tools are advertised

**Steps:**

1. Document the stable MCP tool surface.
2. Add MCP contract tests.
3. Run:

   ```bash
   PYTHONPATH=src .venv/bin/python -m pytest tests/test_mcp_server.py tests/test_query.py
   ```

4. Run full tests and compile check.

**Acceptance:**

- MCP remains read-only.
- Tool names and responses are tested.
- README no longer describes the v1 MCP surface as experimental after this PR.

**Suggested commit:**

```bash
git add README.md docs/design.md src/flowguard/mcp_server.py tests/test_mcp_server.py
git commit -m "test: stabilize read-only MCP surface"
```

### PR 6: Clean Environment Quickstart

**Goal:** Prove a stranger can follow the README from a clean checkout.

**Files:**

- Modify: `README.md`
- Modify or create: `docs/quickstart_check.md`
- Modify: `tests/test_docs.py`

**README flow:**

```text
install
-> run demo
-> read agent_context.md
-> save named run
-> compare named run to latest
-> create golden baseline
-> compare golden baseline
```

**Steps:**

1. Rewrite README quickstart around the shortest successful local path.
2. Add a quickstart check document with exact commands and expected outcomes.
3. Add docs tests for referenced local docs and commands where practical.
4. Run:

   ```bash
   PYTHONPATH=src .venv/bin/python -m pytest tests/test_docs.py
   PYTHONPATH=src .venv/bin/python examples/github_issue_triage/pipeline.py
   PYTHONPATH=src .venv/bin/python -m flowguard.cli
   ```

5. Run full tests.

**Acceptance:**

- README is usable by a new user.
- Quickstart still makes the intentional demo failure clear.
- Demo is not changed to pass.

**Suggested commit:**

```bash
git add README.md docs/quickstart_check.md tests/test_docs.py
git commit -m "docs: add v1 quickstart path"
```

### PR 7: Real Or Near-real Case Study

**Goal:** Add one complete case study that demonstrates the full v1 loop.

**Files:**

- Create: `docs/case_study.md`
- Create if needed: `examples/case_study/`
- Create if needed: `tests/test_case_study.py`

**Case study loop:**

```text
silent quality failure
-> FlowGuard artifacts
-> agent reads repair context
-> code is fixed
-> run comparison proves the fix
-> golden baseline prevents regression
```

**Constraints:**

- no paid API
- no network dependency
- no private credentials
- deterministic local behavior
- do not replace the existing intentional failure demo

**Steps:**

1. Choose the smallest case study that still demonstrates a semantic failure.
2. Add the case study docs.
3. Add local example code only if docs alone are insufficient.
4. Add a test that exercises the case study path if example code is added.
5. Run:

   ```bash
   PYTHONPATH=src .venv/bin/python -m pytest
   PYTHONPATH=src .venv/bin/python examples/github_issue_triage/pipeline.py
   ```

**Acceptance:**

- The case study proves the full loop.
- It is repeatable locally.
- It does not require external services.

**Suggested commit:**

```bash
git add docs/case_study.md examples/case_study tests/test_case_study.py
git commit -m "docs: add v1 case study"
```

### PR 8: Screenshot-ready Outcome Report

**Goal:** Improve the human report enough for v1 screenshots without turning it
into a dashboard.

**Files:**

- Modify: `src/flowguard/report.py`
- Modify: `tests/test_report.py`
- Modify if needed: `README.md`

**Report must show:**

- workflow
- run id
- status
- failed step
- failed checks
- downstream impact
- relevant files when available
- link to `agent_context.md`

**Tests to add or tighten:**

- HTML escapes workflow output, failure text, and error text
- failed checks are visible
- downstream impact is visible
- link to `agent_context.md` remains
- no external assets are required

**Steps:**

1. Add tests describing required report content and escaping.
2. Run:

   ```bash
   PYTHONPATH=src .venv/bin/python -m pytest tests/test_report.py
   ```

3. Make the smallest HTML/CSS changes needed.
4. Run demo and open or inspect `.flowguard/runs/latest/outcome_report.html`.
5. Run full tests.

**Acceptance:**

- Report is local static HTML.
- Report is screenshot-ready.
- Report is not a dashboard and starts no server.

**Suggested commit:**

```bash
git add src/flowguard/report.py tests/test_report.py README.md
git commit -m "style: improve outcome report for v1"
```

### PR 9: v1.0 Release Cleanup

**Goal:** Prepare and publish the v1.0.0 release after all contract and usability
work is merged.

**Files:**

- Modify: `pyproject.toml`
- Modify if needed: `src/flowguard/mcp_server.py`
- Modify: `README.md`
- Create: `docs/20260623_v1_release_review.md`

**Steps:**

1. Bump package version to `1.0.0`.
2. Bump MCP server metadata version to `1.0.0`.
3. Update README status from v0.3 experimental wording to v1 stable core
   wording.
4. Add v1 release review doc.
5. Run final verification:

   ```bash
   PYTHONPATH=src .venv/bin/python -m pytest
   python -m compileall src tests examples
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

6. Confirm:

   - tests pass
   - compile check passes
   - demo still reports intentional `issue.triage` failure
   - latest run still writes four expected artifacts
   - no `contracts.json`
   - no `failed_contracts.md`

7. Commit:

   ```bash
   git add pyproject.toml src/flowguard/mcp_server.py README.md docs/20260623_v1_release_review.md
   git commit -m "chore: prepare v1.0.0 release"
   ```

8. Tag and publish only after review:

   ```bash
   git tag v1.0.0
   git push origin main
   git push origin v1.0.0
   gh release create v1.0.0 --title "FlowGuard v1.0.0" --notes-file docs/20260623_v1_release_review.md
   ```

**Acceptance:**

- v1.0.0 is tagged.
- GitHub release is published.
- Release review records verification evidence.

## Final v1 Acceptance Checklist

- [ ] Runtime API behavior is frozen by tests.
- [ ] Artifact schemas and legacy compatibility are tested.
- [ ] Unknown future schema versions fail loudly.
- [ ] `agent_context.md` protocol is documented and snapshot-tested.
- [ ] MCP surface is stable and read-only.
- [ ] README quickstart works in a clean environment.
- [ ] Case study proves the full repair loop.
- [ ] `outcome_report.html` is screenshot-ready.
- [ ] Demo still reports intentional `issue.triage` failure.
- [ ] Latest run writes only the four expected artifacts.
- [ ] No `contracts.json` or `failed_contracts.md` is generated.
- [ ] Full test suite passes.
- [ ] `python -m compileall src tests examples` passes.
- [ ] `git diff --check` passes.
- [ ] `v1.0.0` tag and release are published.

