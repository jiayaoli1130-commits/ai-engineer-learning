from fastapi.testclient import TestClient

from app import main as api_server


client = TestClient(api_server.app)


def test_chat_endpoint_wraps_agent_reply(monkeypatch):
    monkeypatch.setattr(
        api_server,
        "run_agent",
        lambda message, session_id="default", include_trace=False: {
            "answer": f"echo: {message}",
            "trace": [
                {
                    "tool_name": "get_weather",
                    "arguments": {"location": "北京"},
                    "result_summary": "返回字段: condition",
                    "result": {"condition": "晴朗"},
                }
            ],
            "sources": [],
            "session_id": session_id,
        },
    )

    response = client.post("/chat", json={"message": "hello", "session_id": "s1"})

    assert response.status_code == 200
    assert response.json() == {
        "code": 200,
        "msg": "success",
        "data": {
            "answer": "echo: hello",
            "trace": [
                {
                    "tool_name": "get_weather",
                    "arguments": {"location": "北京"},
                    "result_summary": "返回字段: condition",
                    "result": {"condition": "晴朗"},
                }
            ],
            "sources": [],
            "session_id": "s1",
        },
    }


def test_cors_allows_vercel_preview_origin():
    response = client.options(
        "/chat",
        headers={
            "Origin": "https://preview-ai-engineer-learning.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "https://preview-ai-engineer-learning.vercel.app"
    )


def test_knowledge_ingest_endpoint(monkeypatch):
    monkeypatch.setattr(
        api_server,
        "ingest_document",
        lambda file_path: {
            "success": True,
            "file": file_path,
            "chunks": 2,
            "collection": "company_rules",
        },
    )

    response = client.post(
        "/knowledge/ingest",
        json={"file_path": "./docs/company_rules.md"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["file"] == "./docs/company_rules.md"


def test_knowledge_upload_endpoint_saves_and_ingests_file(monkeypatch, tmp_path):
    monkeypatch.setattr(api_server, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(
        api_server,
        "ingest_document",
        lambda file_path: {
            "success": True,
            "file": file_path,
            "chunks": 1,
            "collection": "company_rules",
        },
    )

    response = client.post(
        "/knowledge/upload",
        files={"file": ("upload.md", b"# Upload\n\nHello", "text/markdown")},
    )

    saved_path = tmp_path / "upload.md"

    assert response.status_code == 200
    assert saved_path.read_text(encoding="utf-8") == "# Upload\n\nHello"
    assert response.json() == {
        "code": 200,
        "msg": "upload and ingest success",
        "data": {
            "filename": "upload.md",
            "saved_path": str(saved_path),
            "ingest_result": {
                "success": True,
                "file": str(saved_path),
                "chunks": 1,
                "collection": "company_rules",
            },
        },
    }


def test_knowledge_upload_endpoint_rejects_unsupported_file_type(tmp_path, monkeypatch):
    monkeypatch.setattr(api_server, "UPLOAD_DIR", tmp_path)

    response = client.post(
        "/knowledge/upload",
        files={"file": ("notes.docx", b"not supported", "application/octet-stream")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "code": 400,
        "msg": "暂不支持的文件类型: .docx",
        "data": None,
    }
    assert not (tmp_path / "notes.docx").exists()


def test_knowledge_search_endpoint(monkeypatch):
    monkeypatch.setattr(
        api_server,
        "search_knowledge",
        lambda query, n_results, max_distance=None: {
            "query": query,
            "max_distance": max_distance,
            "results": [{"content": "matched"}],
        },
    )

    response = client.post(
        "/knowledge/search",
        json={"query": "人体工学椅 报销", "n_results": 1, "max_distance": 0.8},
    )

    assert response.status_code == 200
    assert response.json()["data"]["max_distance"] == 0.8
    assert response.json()["data"]["results"][0]["content"] == "matched"


def test_knowledge_documents_endpoint(monkeypatch):
    monkeypatch.setattr(
        api_server,
        "list_documents",
        lambda: [
            {
                "document_id": "doc123",
                "filename": "company_rules.md",
                "source": "docs/company_rules.md",
                "total_chunks": 3,
            }
        ],
    )

    response = client.get("/knowledge/documents")

    assert response.status_code == 200
    assert response.json() == {
        "code": 200,
        "msg": "success",
        "data": [
            {
                "document_id": "doc123",
                "filename": "company_rules.md",
                "source": "docs/company_rules.md",
                "total_chunks": 3,
            }
        ],
    }


def test_knowledge_delete_endpoint(monkeypatch):
    monkeypatch.setattr(
        api_server,
        "delete_document",
        lambda document_id: {
            "success": True,
            "message": "文档已删除",
            "document_id": document_id,
            "deleted_chunks": 2,
        },
    )

    response = client.post("/knowledge/delete", json={"document_id": "doc123"})

    assert response.status_code == 200
    assert response.json()["data"] == {
        "success": True,
        "message": "文档已删除",
        "document_id": "doc123",
        "deleted_chunks": 2,
    }


def test_knowledge_reset_endpoint(monkeypatch):
    monkeypatch.setattr(
        api_server,
        "reset_collection",
        lambda: {
            "success": True,
            "message": "知识库已重置",
            "collection": "company_rules",
        },
    )

    response = client.post("/knowledge/reset")

    assert response.status_code == 200
    assert response.json()["data"]["success"] is True


def test_business_employee_endpoint(monkeypatch):
    monkeypatch.setattr(
        api_server,
        "query_employee_record",
        lambda uid: {"found": True, "employee": {"uid": uid, "name": "张三"}},
    )

    response = client.get("/business/employees/1001")

    assert response.status_code == 200
    assert response.json()["data"]["employee"]["name"] == "张三"


def test_business_reimbursement_endpoint(monkeypatch):
    monkeypatch.setattr(
        api_server,
        "query_reimbursement_record",
        lambda reimbursement_id: {
            "found": True,
            "reimbursement": {"id": reimbursement_id, "item_name": "人体工学椅"},
        },
    )

    response = client.get("/business/reimbursements/R1001")

    assert response.status_code == 200
    assert response.json()["data"]["reimbursement"]["id"] == "R1001"


def test_business_ticket_endpoint(monkeypatch):
    monkeypatch.setattr(
        api_server,
        "create_review_ticket_record",
        lambda reimbursement_id, reason: {
            "success": True,
            "ticket": {
                "id": "TTEST001",
                "reimbursement_id": reimbursement_id,
                "reason": reason,
                "status": "open",
            },
        },
    )

    response = client.post(
        "/business/tickets",
        json={"reimbursement_id": "R1001", "reason": "缺少提前审批"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["ticket"]["id"] == "TTEST001"


def test_mcp_tools_endpoint(monkeypatch):
    monkeypatch.setattr(
        api_server,
        "list_mcp_tools",
        lambda: [{"name": "query_employee", "description": "Query employee."}],
    )

    response = client.get("/mcp/tools")

    assert response.status_code == 200
    assert response.json()["data"]["tools"][0]["name"] == "query_employee"


def test_mcp_tool_call_endpoint(monkeypatch):
    monkeypatch.setattr(
        api_server,
        "call_mcp_tool",
        lambda name, arguments: {
            "success": True,
            "tool_name": name,
            "arguments": arguments,
            "result": {"found": True},
        },
    )

    response = client.post(
        "/mcp/tools/call",
        json={"name": "query_employee", "arguments": {"uid": "1001"}},
    )

    assert response.status_code == 200
    assert response.json()["data"]["tool_name"] == "query_employee"
    assert response.json()["data"]["result"] == {"found": True}


def test_mcp_jsonrpc_endpoint(monkeypatch):
    monkeypatch.setattr(
        api_server,
        "handle_mcp_request",
        lambda request: {
            "jsonrpc": "2.0",
            "id": request["id"],
            "result": {"tools": []},
        },
    )

    response = client.post(
        "/mcp/jsonrpc",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
    )

    assert response.status_code == 200
    assert response.json()["data"]["id"] == 1
    assert response.json()["data"]["result"] == {"tools": []}
