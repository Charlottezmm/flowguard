from __future__ import annotations

import json
from pathlib import Path

from flowguard.mcp_server import handle_message


TOOL_NAMES = [
    "flowguard_latest_status",
    "flowguard_failed_step",
    "flowguard_workflow_map",
    "flowguard_agent_context",
]


def _write_latest(tmp_path: Path) -> None:
    run_dir = tmp_path / ".flowguard" / "runs" / "latest"
    run_dir.mkdir(parents=True)
    (run_dir / "trace.json").write_text(
        json.dumps(
            {
                "run_id": "latest",
                "workflow": "demo",
                "steps": [
                    {
                        "id": "demo.step",
                        "name": "demo.step",
                        "status": "failed",
                        "source": "demo.py",
                        "failures": ["bad"],
                        "checks": [],
                        "error": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "workflow_map.json").write_text(
        json.dumps({"workflow": "demo", "steps": [{"id": "demo.step", "downstream": []}]}),
        encoding="utf-8",
    )
    (run_dir / "agent_context.md").write_text("# Agent Context\n", encoding="utf-8")


def _call_tool(name: str) -> dict:
    return handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": {}}})


def _tool_text(response: dict) -> str:
    return response["result"]["content"][0]["text"]


def test_mcp_initialize_and_stable_tool_list(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    initialize = handle_message({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    tools = handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})

    assert initialize["result"]["protocolVersion"] == "2025-11-25"
    assert initialize["result"]["capabilities"] == {"tools": {}}
    assert initialize["result"]["serverInfo"] == {"name": "flowguard", "version": "0.3.0"}
    assert [tool["name"] for tool in tools["result"]["tools"]] == TOOL_NAMES
    assert tools["result"]["tools"] == [
        {
            "name": "flowguard_latest_status",
            "description": "Read the latest FlowGuard run status.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "flowguard_failed_step",
            "description": "Read the latest failed FlowGuard step.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "flowguard_workflow_map",
            "description": "Read the latest FlowGuard workflow map.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "flowguard_agent_context",
            "description": "Read the latest FlowGuard agent context.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    ]


def test_mcp_does_not_advertise_write_capable_tools(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    tools = handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    advertised_names = [tool["name"] for tool in tools["result"]["tools"]]

    assert advertised_names == TOOL_NAMES
    assert not any(
        token in name
        for name in advertised_names
        for token in ("run", "execute", "write", "save", "create", "golden", "baseline", "sync")
    )


def test_mcp_read_only_tool_calls(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_latest(tmp_path)

    status = _call_tool("flowguard_latest_status")
    failed_step = _call_tool("flowguard_failed_step")
    workflow_map = _call_tool("flowguard_workflow_map")
    context = _call_tool("flowguard_agent_context")

    assert json.loads(_tool_text(status)) == {
        "workflow": "demo",
        "run_id": "latest",
        "status": "failed",
        "failed_step": "demo.step",
    }
    assert json.loads(_tool_text(failed_step)) == {
        "id": "demo.step",
        "name": "demo.step",
        "status": "failed",
        "source": "demo.py",
        "failures": ["bad"],
        "checks": [],
        "error": None,
    }
    assert json.loads(_tool_text(workflow_map)) == {
        "workflow": "demo",
        "steps": [{"id": "demo.step", "downstream": []}],
    }
    assert context["result"]["content"] == [{"type": "text", "text": "# Agent Context\n"}]


def test_mcp_missing_latest_returns_json_rpc_errors(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    for tool_name in TOOL_NAMES:
        result = _call_tool(tool_name)

        assert result["error"]["code"] == -32001
        assert "FlowGuard" in result["error"]["message"]
        assert ".flowguard/runs/latest" in result["error"]["message"]


def test_mcp_unknown_tool_returns_json_rpc_error(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = _call_tool("flowguard_save_named_run")

    assert result["error"] == {"code": -32602, "message": "Unknown FlowGuard MCP tool: flowguard_save_named_run"}


def test_mcp_ignores_notifications_without_response(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert handle_message({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {}}) is None
