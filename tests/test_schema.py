from __future__ import annotations

import pytest

from flowguard.schema import validate_artifact_schema


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
