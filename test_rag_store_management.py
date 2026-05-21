from app.rag import rag_store


class FakeCollection:
    def __init__(self):
        self.deleted_ids = []
        self.upsert_payload = None

    def get(self, where=None, include=None):
        if where == {"document_id": "abc123"}:
            return {"ids": ["old_1", "old_2"], "metadatas": []}

        if where and "source" in where:
            return {"ids": ["legacy_1"], "metadatas": []}

        return {
            "ids": ["new_1"],
            "metadatas": [
                {
                    "document_id": "abc123",
                    "filename": "policy.md",
                    "source": "uploads/policy.md",
                    "total_chunks": 2,
                }
            ],
        }

    def delete(self, ids):
        self.deleted_ids.extend(ids)

    def upsert(self, ids, documents, metadatas):
        self.upsert_payload = {
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas,
        }


def test_ingest_document_replaces_old_chunks_and_stores_document_id(monkeypatch, tmp_path):
    file_path = tmp_path / "policy.md"
    file_path.write_text("# Policy", encoding="utf-8")
    fake_collection = FakeCollection()

    monkeypatch.setattr(rag_store, "collection", fake_collection)
    monkeypatch.setattr(rag_store, "build_doc_hash", lambda file_path: "abc123")
    monkeypatch.setattr(rag_store, "read_document", lambda file_path: "# Policy")
    monkeypatch.setattr(rag_store, "chunk_text", lambda text: ["chunk one", "chunk two"])

    result = rag_store.ingest_document(str(file_path))

    assert fake_collection.deleted_ids == ["old_1", "old_2", "legacy_1"]
    assert result["document_id"] == "abc123"
    assert result["deleted_old_chunks"] == 3
    assert fake_collection.upsert_payload["ids"][0].startswith("policy_abc123_0_")
    assert fake_collection.upsert_payload["metadatas"][0]["document_id"] == "abc123"


def test_list_and_delete_documents_use_document_id(monkeypatch):
    fake_collection = FakeCollection()

    monkeypatch.setattr(rag_store, "collection", fake_collection)

    documents = rag_store.list_documents()
    delete_result = rag_store.delete_document("abc123")

    assert documents == [
        {
            "document_id": "abc123",
            "filename": "policy.md",
            "source": "uploads/policy.md",
            "total_chunks": 2,
        }
    ]
    assert delete_result["success"] is True
    assert delete_result["deleted_chunks"] == 2
