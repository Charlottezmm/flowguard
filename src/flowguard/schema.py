from __future__ import annotations

from typing import Any


TRACE_SCHEMA_VERSION = "flowguard.trace.v0.3"
WORKFLOW_MAP_SCHEMA_VERSION = "flowguard.workflow_map.v0.3"
GOLDEN_SCHEMA_VERSION = "flowguard.golden.v0.3"
LEGACY_V02_SCHEMA_VERSION = "legacy-v0.2"

_CURRENT_SCHEMA_VERSIONS = {
    "trace": TRACE_SCHEMA_VERSION,
    "workflow_map": WORKFLOW_MAP_SCHEMA_VERSION,
    "golden": GOLDEN_SCHEMA_VERSION,
}


def current_schema_version(artifact_type: str) -> str:
    try:
        return _CURRENT_SCHEMA_VERSIONS[artifact_type]
    except KeyError as exc:
        raise ValueError(f"Unknown FlowGuard artifact type: {artifact_type}") from exc


def add_schema_version(artifact_type: str, artifact: dict[str, Any]) -> dict[str, Any]:
    versioned = dict(artifact)
    versioned["schema_version"] = current_schema_version(artifact_type)
    return versioned


def validate_schema_version(artifact_type: str, artifact: dict[str, Any]) -> str:
    if not isinstance(artifact, dict):
        raise ValueError(f"FlowGuard {artifact_type} artifact must be a JSON object")

    expected = current_schema_version(artifact_type)
    actual = artifact.get("schema_version")
    if actual is None:
        return LEGACY_V02_SCHEMA_VERSION
    if actual != expected:
        raise ValueError(
            f"Unsupported FlowGuard {artifact_type} schema_version: {actual}. "
            f"Expected {expected} or omitted legacy-v0.2 schema_version."
        )
    return expected


def validate_artifact_schema(artifact_type: str, artifact: dict[str, Any]) -> str:
    schema_version = validate_schema_version(artifact_type, artifact)
    if artifact_type == "trace":
        _require_string(artifact_type, artifact, "run_id")
        _require_string(artifact_type, artifact, "workflow")
        _require_list(artifact_type, artifact, "steps")
    elif artifact_type == "workflow_map":
        _require_string(artifact_type, artifact, "workflow")
        _require_list(artifact_type, artifact, "steps")
    elif artifact_type == "golden":
        _require_string(artifact_type, artifact, "workflow")
        _require_list(artifact_type, artifact, "steps")
    else:
        current_schema_version(artifact_type)
    return schema_version


def _require_string(artifact_type: str, artifact: dict[str, Any], field: str) -> None:
    if not isinstance(artifact.get(field), str):
        raise ValueError(f"FlowGuard {artifact_type} field '{field}' must be a string")


def _require_list(artifact_type: str, artifact: dict[str, Any], field: str) -> None:
    if not isinstance(artifact.get(field), list):
        raise ValueError(f"FlowGuard {artifact_type} field '{field}' must be a list")
