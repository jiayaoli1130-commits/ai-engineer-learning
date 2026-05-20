from fastapi.testclient import TestClient

import api_server


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
