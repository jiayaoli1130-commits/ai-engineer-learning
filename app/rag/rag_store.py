import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "my_vector_db"
COLLECTION_NAME = "company_rules"
DEFAULT_DOC_PATH = PROJECT_ROOT / "docs" / "company_rules.md"
SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf"}

DB_PATH.mkdir(parents=True, exist_ok=True)

client = chromadb.PersistentClient(path=str(DB_PATH))
collection = client.get_or_create_collection(name=COLLECTION_NAME)


def resolve_document_path(file_path: str) -> Path:
    path = Path(file_path).expanduser()

    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()

    return path


def reset_collection() -> Dict[str, Any]:
    global collection

    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    return {
        "success": True,
        "message": "知识库已重置",
        "collection": COLLECTION_NAME,
    }


def read_document(file_path: str) -> str:
    path = resolve_document_path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(f"暂不支持的文件类型: {suffix}，当前支持: {supported}")

    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")

    reader = PdfReader(str(path))
    pages: List[str] = []

    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"\n\n[Page {i}]\n{text}")

    return "\n".join(pages).strip()


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_large_unit(text: str, max_chars: int, overlap_chars: int) -> List[str]:
    chunks = []
    start = 0

    while start < len(text):
        end = start + max_chars
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(0, end - overlap_chars)

    return chunks


def chunk_text(
    text: str,
    max_chars: int = 600,
    overlap_chars: int = 80,
) -> List[str]:
    """
    更适合 Markdown 制度文档的切块方式。

    优先按 Markdown 二级标题 ## 切分。
    如果某个章节仍然太长，再继续细切。
    """
    text = normalize_text(text)
    sections = re.split(r"(?=^##\s+)", text, flags=re.MULTILINE)
    sections = [s.strip() for s in sections if s.strip()]
    if any(re.match(r"^##\s+", section) for section in sections):
        sections = [s for s in sections if re.match(r"^##\s+", s)]

    final_chunks = []

    for section in sections:
        if len(section) <= max_chars:
            final_chunks.append(section)
            continue

        paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
        current = ""

        for paragraph in paragraphs:
            if not current:
                current = paragraph
                continue

            if len(current) + len(paragraph) + 2 <= max_chars:
                current += "\n\n" + paragraph
            else:
                final_chunks.append(current.strip())
                overlap = current[-overlap_chars:] if overlap_chars > 0 else ""
                current = f"{overlap}\n\n{paragraph}".strip()

        if current:
            final_chunks.append(current.strip())

    return final_chunks


def build_doc_hash(file_path: str) -> str:
    path = resolve_document_path(file_path)
    raw = str(path).encode("utf-8")
    return hashlib.md5(raw).hexdigest()[:10]


def ingest_document(file_path: str) -> Dict[str, Any]:
    path = resolve_document_path(file_path)
    text = read_document(file_path)
    chunks = chunk_text(text)

    if not chunks:
        raise ValueError("文档内容为空，无法入库")

    document_id = build_doc_hash(file_path)
    old_ids = []
    for where in ({"document_id": document_id}, {"source": str(path)}):
        old_items = collection.get(where=where)
        for old_id in old_items.get("ids", []):
            if old_id not in old_ids:
                old_ids.append(old_id)

    if old_ids:
        collection.delete(ids=old_ids)

    ids = []
    documents = []
    metadatas = []

    for index, chunk in enumerate(chunks):
        chunk_hash = hashlib.md5(chunk.encode("utf-8")).hexdigest()[:10]
        chunk_id = f"{path.stem}_{document_id}_{index}_{chunk_hash}"

        ids.append(chunk_id)
        documents.append(chunk)
        metadatas.append(
            {
                "document_id": document_id,
                "source": str(path),
                "filename": path.name,
                "chunk_index": index,
                "total_chunks": len(chunks),
            }
        )

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    return {
        "success": True,
        "document_id": document_id,
        "file": str(path),
        "chunks": len(chunks),
        "deleted_old_chunks": len(old_ids),
        "collection": COLLECTION_NAME,
    }


def list_documents() -> List[Dict[str, Any]]:
    items = collection.get(include=["metadatas"])
    docs: Dict[str, Dict[str, Any]] = {}

    for metadata in items.get("metadatas", []):
        if not metadata:
            continue

        document_id = metadata.get("document_id")
        filename = metadata.get("filename")
        source = metadata.get("source")
        total_chunks = metadata.get("total_chunks")

        if not document_id:
            continue

        docs[document_id] = {
            "document_id": document_id,
            "filename": filename,
            "source": source,
            "total_chunks": total_chunks,
        }

    return list(docs.values())


def delete_document(document_id: str) -> Dict[str, Any]:
    items = collection.get(where={"document_id": document_id})
    ids = items.get("ids", [])

    if not ids:
        return {
            "success": False,
            "message": "未找到该文档",
            "document_id": document_id,
        }

    collection.delete(ids=ids)

    return {
        "success": True,
        "message": "文档已删除",
        "document_id": document_id,
        "deleted_chunks": len(ids),
    }


def normalize_for_match(text: str) -> str:
    return re.sub(r"[\W_]+", "", text.lower(), flags=re.UNICODE)


def char_ngrams(text: str, size: int) -> set[str]:
    if len(text) < size:
        return {text} if text else set()

    return {text[index : index + size] for index in range(len(text) - size + 1)}


def text_relevance_score(query: str, content: str) -> float:
    normalized_query = normalize_for_match(query)
    normalized_content = normalize_for_match(content)

    if not normalized_query or not normalized_content:
        return 0.0

    if normalized_query in normalized_content:
        return 10.0 + len(normalized_query) / max(len(normalized_content), 1)

    query_bigrams = char_ngrams(normalized_query, 2)
    query_trigrams = char_ngrams(normalized_query, 3)
    content_bigrams = char_ngrams(normalized_content, 2)
    content_trigrams = char_ngrams(normalized_content, 3)

    bigram_score = (
        len(query_bigrams & content_bigrams) / len(query_bigrams)
        if query_bigrams
        else 0.0
    )
    trigram_score = (
        len(query_trigrams & content_trigrams) / len(query_trigrams)
        if query_trigrams
        else 0.0
    )

    return bigram_score + (trigram_score * 2)


def build_search_item(
    item_id: str,
    content: str,
    metadata: Optional[Dict[str, Any]],
    distance: Optional[float],
    query: str,
    vector_rank: Optional[int] = None,
) -> Dict[str, Any]:
    lexical_score = text_relevance_score(query, content)
    vector_score = 0.0 if distance is None else 1 / (1 + max(distance, 0))

    return {
        "id": item_id,
        "content": content,
        "metadata": metadata or {},
        "distance": distance,
        "_lexical_score": lexical_score,
        "_vector_score": vector_score,
        "_vector_rank": vector_rank,
    }


def combine_search_scores(item: Dict[str, Any]) -> float:
    vector_rank = item.get("_vector_rank")
    rank_bonus = 0.0 if vector_rank is None else 1 / (vector_rank + 1)
    return (item["_lexical_score"] * 2.5) + item["_vector_score"] + rank_bonus


def search_knowledge(query: str, n_results: int = 3) -> Dict[str, Any]:
    if not query.strip():
        raise ValueError("query 不能为空")

    if n_results <= 0:
        raise ValueError("n_results 必须大于 0")

    count = collection.count()
    if count == 0:
        return {
            "query": query,
            "results": [],
            "message": "知识库为空，请先执行文档入库。",
        }

    vector_limit = min(max(n_results * 4, n_results), count)
    vector_results = collection.query(
        query_texts=[query],
        n_results=vector_limit,
        include=["documents", "metadatas", "distances"],
    )

    candidates: Dict[str, Dict[str, Any]] = {}
    ids = vector_results.get("ids", [[]])[0]
    documents = vector_results.get("documents", [[]])[0]
    metadatas = vector_results.get("metadatas", [[]])[0]
    distances = vector_results.get("distances", [[]])[0]

    for rank, (item_id, content, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances)
    ):
        candidates[item_id] = build_search_item(
            item_id=item_id,
            content=content,
            metadata=metadata,
            distance=distance,
            query=query,
            vector_rank=rank,
        )

    stored_items = collection.get(include=["documents", "metadatas"])
    stored_ids = stored_items.get("ids", [])
    stored_documents = stored_items.get("documents", [])
    stored_metadatas = stored_items.get("metadatas", [])

    for item_id, content, metadata in zip(stored_ids, stored_documents, stored_metadatas):
        lexical_score = text_relevance_score(query, content)
        if lexical_score <= 0:
            continue

        if item_id in candidates:
            candidates[item_id]["_lexical_score"] = lexical_score
            continue

        candidates[item_id] = build_search_item(
            item_id=item_id,
            content=content,
            metadata=metadata,
            distance=None,
            query=query,
        )

    ranked_items = sorted(
        candidates.values(),
        key=combine_search_scores,
        reverse=True,
    )
    items = []

    for item in ranked_items[:n_results]:
        items.append(
            {
                "content": item["content"],
                "metadata": item["metadata"],
                "distance": item["distance"],
                "score": round(combine_search_scores(item), 6),
            }
        )

    return {
        "query": query,
        "results": items,
    }


def retrieve_knowledge(query: str, n_results: int = 3) -> str:
    return json.dumps(
        search_knowledge(query=query, n_results=n_results),
        ensure_ascii=False,
    )


if __name__ == "__main__":
    result = ingest_document(str(DEFAULT_DOC_PATH))
    print("入库结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n检索测试:")
    test = retrieve_knowledge("我在淘宝买了一把人体工学椅，可以报销吗？")
    print(test)
