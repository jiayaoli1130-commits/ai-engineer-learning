import json

from app.tools import mcp_tools


def test_list_mcp_tools_exposes_rag_and_business_tools():
    names = {tool["name"] for tool in mcp_tools.list_mcp_tools()}

    assert "retrieve_knowledge" in names
    assert "query_employee" in names
    assert "query_reimbursement" in names
    assert "create_review_ticket" in names
    assert "calculate_reimbursement_policy" in names


def test_call_mcp_tool_invokes_registered_tool(monkeypatch):
    monkeypatch.setitem(
        mcp_tools.MCP_TOOL_REGISTRY,
        "echo_tool",
        {
            "description": "Echo input.",
            "parameters": {
                "type": "object",
                "properties": {"value": {"type": "string"}},
                "required": ["value"],
            },
            "callable": lambda value: json.dumps({"value": value}, ensure_ascii=False),
        },
    )

    result = mcp_tools.call_mcp_tool("echo_tool", {"value": "ok"})

    assert result == {
        "success": True,
        "tool_name": "echo_tool",
        "arguments": {"value": "ok"},
        "result": {"value": "ok"},
    }


def test_call_mcp_tool_returns_error_for_unknown_tool():
    result = mcp_tools.call_mcp_tool("missing_tool", {})

    assert result["success"] is False
    assert result["tool_name"] == "missing_tool"
    assert "Unknown MCP tool" in result["error"]


def test_handle_mcp_tools_list_request():
    response = mcp_tools.handle_mcp_request(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    )

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert "tools" in response["result"]


def test_handle_mcp_tools_call_request(monkeypatch):
    monkeypatch.setattr(
        mcp_tools,
        "call_mcp_tool",
        lambda tool_name, arguments=None: {
            "success": True,
            "tool_name": tool_name,
            "arguments": arguments,
            "result": {"ok": True},
        },
    )

    response = mcp_tools.handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": "call-1",
            "method": "tools/call",
            "params": {
                "name": "query_employee",
                "arguments": {"uid": "1001"},
            },
        }
    )

    content = response["result"]["content"][0]

    assert response["id"] == "call-1"
    assert response["result"]["isError"] is False
    assert content["type"] == "text"
    assert json.loads(content["text"])["result"] == {"ok": True}
