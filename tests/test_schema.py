from __future__ import annotations

import json
from pathlib import Path

import pytest

from flowguard import expect, flowguard_run, step
from flowguard.golden import create_golden
from flowguard.schema import (
    GOLDEN_SCHEMA_VERSION,
    TRACE_SCHEMA_VERSION,
    WORKFLOW_MAP_SCHEMA_VERSION,
    add_schema_version,
    current_schema_version,
    validate_artifact_schema,
)


def test_current_schema_versions_are_artifact_specific() -> None:
    assert current_schema_version("trace") == TRACE_SCHEMA_VERSION
    assert current_schema_version("workflow_map") == WORKFLOW_MAP_SCHEMA_VERSION
    assert current_schema_version("golden") == GOLDEN_SCHEMA_VERSION
    assert len({TRACE_SCHEMA_VERSION, WORKFLOW_MAP_SCHEMA_VERSION, GOLDEN_SCHEMA_VERSION}) == 3


def test_add_schema_version_never_writes_legacy_label() -> None:
    assert add_schema_version("trace", {"run_id": "latest"})["schema_version"] == "flowguard.trace.v0.3"
    assert add_schema_version("workflow_map", {"workflow": "demo"})["schema_version"] == "flowguard.workflow_map.v0.3"
    assert add_schema_version("golden", {"workflow": "demo"})["schema_version"] == "flowguard.golden.v0.3"


def test_trace_schema_requires_stable_top_level_fields() -> None:
    with pytest.raises(ValueError, match="FlowGuard trace field 'steps' must be a list"):
        validate_artifact_schema(
            "trace",
            {
                "schema_version": "flowguard.trace.v0.3",
                "run_id": "latest",
                "workflow": "demo",
                "steps": {},
            },
        )


def test_workflow_map_schema_requires_stable_top_level_fields() -> None:
    with pytest.raises(ValueError, match="FlowGuard workflow_map field 'workflow' must be a string"):
        validate_artifact_schema(
            "workflow_map",
            {
                "schema_version": "flowguard.workflow_map.v0.3",
                "workflow": None,
                "steps": [],
            },
        )


def test_golden_schema_allows_legacy_without_schema_version() -> None:
    assert validate_artifact_schema("golden", {"workflow": "demo", "steps": []}) == "legacy-v0.2"


@pytest.mark.parametrize(
    ("artifact_type", "artifact"),
    [
        ("trace", {"run_id": "latest", "workflow": "demo", "steps": []}),
        ("workflow_map", {"workflow": "demo", "steps": []}),
        ("golden", {"workflow": "demo", "steps": []}),
    ],
)
def test_missing_schema_version_reads_as_legacy_v02_for_supported_artifacts(
    artifact_type: str,
    artifact: dict,
) -> None:
    assert validate_artifact_schema(artifact_type, artifact) == "legacy-v0.2"


@pytest.mark.parametrize(
    ("artifact_type", "artifact"),
    [
        ("trace", {"schema_version": "flowguard.trace.v9", "run_id": "latest", "workflow": "demo", "steps": []}),
        ("workflow_map", {"schema_version": "flowguard.workflow_map.v9", "workflow": "demo", "steps": []}),
        ("golden", {"schema_version": "flowguard.golden.v9", "workflow": "demo", "steps": []}),
    ],
)
def test_unknown_future_schema_versions_fail_loudly(artifact_type: str, artifact: dict) -> None:
    with pytest.raises(ValueError, match=f"Unsupported FlowGuard {artifact_type} schema_version"):
        validate_artifact_schema(artifact_type, artifact)


def test_generated_trace_and_workflow_map_include_stable_schema_fields(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    @step("demo.make")
    @expect.required_fields(["name"])
    def make_item() -> dict:
        return {"name": "alpha"}

    with flowguard_run("demo"):
        make_item()

    trace = json.loads(Path(".flowguard/runs/latest/trace.json").read_text(encoding="utf-8"))
    workflow_map = json.loads(Path(".flowguard/runs/latest/workflow_map.json").read_text(encoding="utf-8"))

    assert trace["schema_version"] == TRACE_SCHEMA_VERSION
    assert {"schema_version", "run_id", "workflow", "steps"}.issubset(trace)
    assert {
        "id",
        "name",
        "status",
        "source",
        "failures",
        "checks",
        "error",
    }.issubset(trace["steps"][0])
    assert trace["schema_version"] != "legacy-v0.2"

    assert workflow_map["schema_version"] == WORKFLOW_MAP_SCHEMA_VERSION
    assert {"schema_version", "workflow", "steps"}.issubset(workflow_map)
    assert {
        "id",
        "name",
        "index",
        "status",
        "source",
        "upstream",
        "downstream",
    }.issubset(workflow_map["steps"][0])
    assert workflow_map["schema_version"] != "legacy-v0.2"


def test_created_golden_baseline_includes_stable_schema_fields(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    @step("demo.make")
    def make_item() -> dict:
        return {"name": "alpha"}

    with flowguard_run("demo"):
        make_item()

    baseline_path = create_golden("demo", "default")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    assert baseline["schema_version"] == GOLDEN_SCHEMA_VERSION
    assert {"schema_version", "workflow", "steps"}.issubset(baseline)
    assert {
        "id",
        "name",
        "status",
        "source",
        "failures",
        "checks",
        "error",
        "upstream",
        "downstream",
    }.issubset(baseline["steps"][0])
    assert baseline["schema_version"] != "legacy-v0.2"
