from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.agent.agent_core import run_agent
from app.rag.rag_store import ingest_document, reset_collection, search_knowledge
from app.schemas.request_response import (
    ChatRequest,
    IngestRequest,
    ResultWrapper,
    SearchRequest,
)


load_dotenv()

HOST = "127.0.0.1"
PORT = 8000

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


@app.post("/knowledge/search", response_model=ResultWrapper)
def knowledge_search(request: SearchRequest) -> ResultWrapper:
    try:
        result = search_knowledge(query=request.query, n_results=request.n_results)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Knowledge search failed: {exc}") from exc

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
