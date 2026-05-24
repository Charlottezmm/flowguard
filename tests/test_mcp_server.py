from __future__ import annotations

import json
from pathlib import Path

from flowguard.mcp_server import handle_message


def _write_latest(tmp_path: Path) -> None:
    run_dir = tmp_path / ".flowguard" / "runs" / "latest"
    run_dir.mkdir(parents=True)
    (run_dir / "trace.json").write_text(
        json.dumps(
            {
                "run_id": "latest",
                "workflow": "demo",
                "steps": [{"id": "demo.step", "status": "failed", "failures": ["bad"], "checks": [], "error": None}],
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "workflow_map.json").write_text(json.dumps({"workflow": "demo", "steps": []}), encoding="utf-8")
    (run_dir / "agent_context.md").write_text("# Agent Context\n", encoding="utf-8")


def test_mcp_initialize_and_tool_list(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    initialize = handle_message({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    tools = handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})

    assert initialize["result"]["protocolVersion"] == "2025-11-25"
    assert initialize["result"]["capabilities"] == {"tools": {}}
    assert [tool["name"] for tool in tools["result"]["tools"]] == [
        "flowguard_latest_status",
        "flowguard_failed_step",
        "flowguard_workflow_map",
        "flowguard_agent_context",
    ]


def test_mcp_read_only_tool_calls(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_latest(tmp_path)

    status = handle_message(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "flowguard_latest_status", "arguments": {}}}
    )
    context = handle_message(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "flowguard_agent_context", "arguments": {}}}
    )

    assert json.loads(status["result"]["content"][0]["text"]) == {
        "workflow": "demo",
        "run_id": "latest",
        "status": "failed",
        "failed_step": "demo.step",
    }
    assert context["result"]["content"] == [{"type": "text", "text": "# Agent Context\n"}]


def test_mcp_missing_latest_returns_tool_error(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = handle_message(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "flowguard_latest_status", "arguments": {}}}
    )

    assert result["result"]["isError"] is True
    assert "trace.json" in result["result"]["content"][0]["text"]


def test_mcp_ignores_notifications_without_response(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert handle_message({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {}}) is None
