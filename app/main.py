import shutil
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.agent.agent_core import run_agent
from app.rag.rag_store import (
    delete_document,
    ingest_document,
    list_documents,
    reset_collection,
    search_knowledge,
)
from app.schemas.request_response import (
    ChatRequest,
    DeleteDocumentRequest,
    IngestRequest,
    ResultWrapper,
    SearchRequest,
)


load_dotenv()

HOST = "127.0.0.1"
PORT = 8000
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="AI Agent RAG Demo",
    description="A local RAG agent service built with FastAPI, OpenAI SDK, and ChromaDB.",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Start with: python.exe -m app.main

@app.post("/chat", response_model=ResultWrapper)
def chat(request: ChatRequest) -> ResultWrapper:
    try:
        answer = run_agent(request.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {exc}") from exc

    return ResultWrapper(
        code=200,
        msg="success",
        data=answer,
    )


@app.post("/knowledge/ingest", response_model=ResultWrapper)
def knowledge_ingest(request: IngestRequest) -> ResultWrapper:
    try:
        result = ingest_document(request.file_path)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Knowledge ingest failed: {exc}") from exc

    return ResultWrapper(
        code=200,
        msg="success",
        data=result,
    )


@app.post("/knowledge/upload", response_model=ResultWrapper)
def upload_knowledge_file(file: UploadFile = File(...)) -> ResultWrapper:
    try:
        original_filename = file.filename or "uploaded_file"
        filename = Path(original_filename).name
        suffix = Path(filename).suffix.lower()

        if suffix not in [".txt", ".md", ".pdf"]:
            return ResultWrapper(
                code=400,
                msg=f"暂不支持的文件类型: {suffix}",
                data=None,
            )

        save_path = UPLOAD_DIR / filename

        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        ingest_result = ingest_document(str(save_path))

        return ResultWrapper(
            code=200,
            msg="upload and ingest success",
            data={
                "filename": filename,
                "saved_path": str(save_path),
                "ingest_result": ingest_result,
            },
        )
    except Exception as exc:
        return ResultWrapper(
            code=500,
            msg=f"upload failed: {exc}",
            data=None,
        )


@app.post("/knowledge/search", response_model=ResultWrapper)
def knowledge_search(request: SearchRequest) -> ResultWrapper:
    try:
        result = search_knowledge(
            query=request.query,
            n_results=request.n_results,
            max_distance=request.max_distance,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Knowledge search failed: {exc}") from exc

    return ResultWrapper(
        code=200,
        msg="success",
        data=result,
    )


@app.get("/knowledge/documents", response_model=ResultWrapper)
def get_documents() -> ResultWrapper:
    try:
        documents = list_documents()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"List documents failed: {exc}") from exc

    return ResultWrapper(
        code=200,
        msg="success",
        data=documents,
    )


@app.post("/knowledge/delete", response_model=ResultWrapper)
def delete_knowledge_document(request: DeleteDocumentRequest) -> ResultWrapper:
    try:
        result = delete_document(request.document_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Delete document failed: {exc}") from exc

    return ResultWrapper(
        code=200,
        msg="success",
        data=result,
    )


@app.post("/knowledge/reset", response_model=ResultWrapper)
def knowledge_reset() -> ResultWrapper:
    try:
        result = reset_collection()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Knowledge reset failed: {exc}") from exc

    return ResultWrapper(
        code=200,
        msg="success",
        data=result,
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=False,
        workers=1,
    )
