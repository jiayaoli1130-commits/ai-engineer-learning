import json
from typing import Any, Callable

from app.rag.rag_store import retrieve_knowledge
from app.tools.business_tools import (
    calculate_reimbursement_policy,
    create_review_ticket,
    query_employee,
    query_reimbursement,
)


MCP_TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "retrieve_knowledge": {
        "description": "Search company policy and knowledge-base chunks.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "n_results": {"type": "integer", "default": 3},
                "max_distance": {"type": "number"},
            },
            "required": ["query"],
        },
        "callable": retrieve_knowledge,
    },
    "query_employee": {
        "description": "Query employee record by uid.",
        "parameters": {
            "type": "object",
            "properties": {"uid": {"type": "string"}},
            "required": ["uid"],
        },
        "callable": query_employee,
    },
    "query_reimbursement": {
        "description": "Query reimbursement record by reimbursement_id.",
        "parameters": {
            "type": "object",
            "properties": {"reimbursement_id": {"type": "string"}},
            "required": ["reimbursement_id"],
        },
        "callable": query_reimbursement,
    },
    "create_review_ticket": {
        "description": "Create a review ticket for a reimbursement record.",
        "parameters": {
            "type": "object",
            "properties": {
                "reimbursement_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["reimbursement_id", "reason"],
        },
        "callable": create_review_ticket,
    },
    "calculate_reimbursement_policy": {
        "description": "Calculate reimbursable and over-limit amounts.",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "limit": {"type": "number"},
            },
            "required": ["amount", "limit"],
        },
        "callable": calculate_reimbursement_policy,
    },
}


def list_mcp_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["parameters"],
        }
        for name, spec in MCP_TOOL_REGISTRY.items()
    ]


def _parse_tool_payload(raw_result: str) -> Any:
    try:
        return json.loads(raw_result)
    except json.JSONDecodeError:
        return raw_result


def call_mcp_tool(tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    tool_spec = MCP_TOOL_REGISTRY.get(tool_name)
    if tool_spec is None:
        return {
            "success": False,
            "error": f"Unknown MCP tool: {tool_name}",
            "tool_name": tool_name,
        }

    func: Callable[..., str] = tool_spec["callable"]
    arguments = arguments or {}

    try:
        raw_result = func(**arguments)
    except TypeError as exc:
        return {
            "success": False,
            "error": f"Invalid MCP tool arguments: {exc}",
            "tool_name": tool_name,
            "arguments": arguments,
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"MCP tool execution failed: {exc}",
            "tool_name": tool_name,
            "arguments": arguments,
        }

    return {
        "success": True,
        "tool_name": tool_name,
        "arguments": arguments,
        "result": _parse_tool_payload(raw_result),
    }


def handle_mcp_request(request: dict[str, Any]) -> dict[str, Any]:
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "serverInfo": {
                    "name": "enterprise-agentic-rag-platform",
                    "version": "0.5.0",
                },
                "capabilities": {"tools": {}},
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": list_mcp_tools()},
        }

    if method == "tools/call":
        tool_result = call_mcp_tool(
            params.get("name", ""),
            params.get("arguments") or {},
        )
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(tool_result, ensure_ascii=False),
                    }
                ],
                "isError": not tool_result.get("success"),
            },
        }

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32601,
            "message": f"Unsupported method: {method}",
        },
    }
