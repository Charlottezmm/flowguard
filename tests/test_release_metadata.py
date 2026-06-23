from __future__ import annotations

from pathlib import Path

from flowguard.mcp_server import handle_message

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10 CI.
    import tomli as tomllib


def test_v1_release_metadata_is_documented_without_publish_claim() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    readme = Path("README.md").read_text(encoding="utf-8")
    review = Path("docs/20260623_v1_release_review.md").read_text(encoding="utf-8")
    initialize = handle_message({"jsonrpc": "2.0", "id": 1, "method": "initialize"})

    assert pyproject["project"]["version"] == "1.0.0"
    assert initialize is not None
    assert initialize["result"]["serverInfo"] == {
        "name": "flowguard",
        "version": pyproject["project"]["version"],
    }
    assert "FlowGuard v1.0 has a stable local core." in readme
    assert "FlowGuard is experimental. v0.3 focuses" not in readme
    assert "Release: `v1.0.0`" in review
    assert (
        "Release/tag/publish status: approved for GitHub release; no package registry"
        in review
    )
    assert "No package registry publish is authorized" in review
    assert "No hosted service." in review
    assert "No write-capable MCP tools." in review
