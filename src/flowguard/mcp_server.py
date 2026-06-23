from __future__ import annotations

import json
import sys
from typing import Any

from .query import find_failed_step, load_agent_context, load_workflow_map, summarize_run


PROTOCOL_VERSION = "2025-11-25"


def handle_message(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    message_id = message.get("id")
    if message_id is None and method and str(method).startswith("notifications/"):
        return None
    if method == "initialize":
        return _response(
            message_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "flowguard", "version": "0.3.0"},
            },
        )
    if method == "tools/list":
        return _response(message_id, {"tools": _tools()})
    if method == "tools/call":
        params = message.get("params", {})
        tool_name = str(params.get("name", ""))
        try:
            return _response(message_id, _call_tool(tool_name))
        except KeyError:
            return _error(message_id, -32602, f"Unknown FlowGuard MCP tool: {tool_name}")
        except (FileNotFoundError, ValueError) as exc:
            return _error(message_id, -32001, str(exc))
    if method == "ping":
        return _response(message_id, {})
    return _error(message_id, -32601, f"Unsupported method: {method}")


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
            response = handle_message(message)
        except Exception as exc:  # pragma: no cover - defensive stdio boundary
            response = _error(None, -32603, str(exc))
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)


def _tools() -> list[dict[str, Any]]:
    empty_schema = {"type": "object", "properties": {}, "additionalProperties": False}
    return [
        {
            "name": "flowguard_latest_status",
            "description": "Read the latest FlowGuard run status.",
            "inputSchema": empty_schema,
        },
        {
            "name": "flowguard_failed_step",
            "description": "Read the latest failed FlowGuard step.",
            "inputSchema": empty_schema,
        },
        {
            "name": "flowguard_workflow_map",
            "description": "Read the latest FlowGuard workflow map.",
            "inputSchema": empty_schema,
        },
        {
            "name": "flowguard_agent_context",
            "description": "Read the latest FlowGuard agent context.",
            "inputSchema": empty_schema,
        },
    ]


def _call_tool(name: str) -> dict[str, Any]:
    if name == "flowguard_latest_status":
        return _tool_text(json.dumps(summarize_run(), ensure_ascii=False))
    if name == "flowguard_failed_step":
        return _tool_text(json.dumps(find_failed_step(), ensure_ascii=False))
    if name == "flowguard_workflow_map":
        return _tool_text(json.dumps(load_workflow_map(), ensure_ascii=False))
    if name == "flowguard_agent_context":
        return _tool_text(load_agent_context())
    raise KeyError(name)


def _tool_text(text: str, is_error: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"content": [{"type": "text", "text": text}]}
    if is_error:
        result["isError"] = True
    return result


def _response(message_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _error(message_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


if __name__ == "__main__":
    main()
