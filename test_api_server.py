from fastapi.testclient import TestClient

from app import main as api_server


client = TestClient(api_server.app)


def test_chat_endpoint_wraps_agent_reply(monkeypatch):
    monkeypatch.setattr(api_server, "run_agent", lambda message: f"echo: {message}")

    response = client.post("/chat", json={"message": "hello"})

    assert response.status_code == 200
    assert response.json() == {
        "code": 200,
        "msg": "success",
        "data": "echo: hello",
    }


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
        lambda query, n_results: {
            "query": query,
            "results": [{"content": "matched"}],
        },
    )

    response = client.post(
        "/knowledge/search",
        json={"query": "人体工学椅报销", "n_results": 1},
    )

    assert response.status_code == 200
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
