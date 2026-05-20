import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List

import chromadb
from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "data" / "vector_db" / "my_vector_db"
COLLECTION_NAME = "company_rules"
DEFAULT_DOC_PATH = PROJECT_ROOT / "docs" / "company_rules.md"
SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf"}

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

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
    max_chars: int = 900,
    overlap_chars: int = 150,
) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []

    raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    units: List[str] = []

    for paragraph in raw_paragraphs:
        if len(paragraph) <= max_chars:
            units.append(paragraph)
            continue

        sentences = re.split(r"(?<=[。！？!?；;.])", paragraph)
        sentences = [s.strip() for s in sentences if s.strip()]

        for sentence in sentences:
            if len(sentence) <= max_chars:
                units.append(sentence)
            else:
                units.extend(split_large_unit(sentence, max_chars, overlap_chars))

    chunks: List[str] = []
    current = ""

    for unit in units:
        if not current:
            current = unit
            continue

        if len(current) + len(unit) + 2 <= max_chars:
            current += "\n\n" + unit
            continue

        chunks.append(current.strip())
        overlap = current[-overlap_chars:] if overlap_chars > 0 else ""
        current = f"{overlap}\n\n{unit}".strip()

    if current:
        chunks.append(current.strip())

    return chunks


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

    doc_hash = build_doc_hash(file_path)
    ids = []
    documents = []
    metadatas = []

    for index, chunk in enumerate(chunks):
        chunk_hash = hashlib.md5(chunk.encode("utf-8")).hexdigest()[:10]
        chunk_id = f"{path.stem}_{doc_hash}_{index}_{chunk_hash}"

        ids.append(chunk_id)
        documents.append(chunk)
        metadatas.append(
            {
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
        "file": str(path),
        "chunks": len(chunks),
        "collection": COLLECTION_NAME,
    }


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

    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, count),
        include=["documents", "metadatas", "distances"],
    )

    items = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for content, metadata, distance in zip(documents, metadatas, distances):
        items.append(
            {
                "content": content,
                "metadata": metadata,
                "distance": distance,
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
