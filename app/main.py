import shutil
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.agent.langgraph_agent import run_graph_agent as run_agent
from app.rag.rag_store import (
    delete_document,
    ingest_document,
    list_documents,
    reset_collection,
    search_knowledge,
)
from app.schemas.request_response import (
    ChatRequest,
    CreateReviewTicketRequest,
    DeleteDocumentRequest,
    IngestRequest,
    McpJsonRpcRequest,
    McpToolCallRequest,
    ResultWrapper,
    SearchRequest,
)
from app.services.business_service import (
    create_review_ticket_record,
    query_employee_record,
    query_reimbursement_record,
)
from app.tools.mcp_tools import call_mcp_tool, handle_mcp_request, list_mcp_tools


load_dotenv()

HOST = "127.0.0.1"
PORT = 8000
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Enterprise Agentic RAG Platform",
    description="企业知识库智能体平台 built with FastAPI, OpenAI-compatible tool calling, ChromaDB, SQLite, and MCP-style tools.",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ai-engineer-learning.vercel.app",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "Enterprise Agentic RAG Platform",
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ResultWrapper)
def chat(request: ChatRequest) -> ResultWrapper:
    try:
        agent_result = run_agent(
            request.message,
            session_id=request.session_id,
            include_trace=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {exc}") from exc

    if isinstance(agent_result, str):
        agent_result = {
            "answer": agent_result,
            "trace": [],
            "sources": [],
            "session_id": request.session_id,
        }

    return ResultWrapper(
        code=200,
        msg="success",
        data=agent_result,
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


@app.get("/business/employees/{uid}", response_model=ResultWrapper)
def get_business_employee(uid: str) -> ResultWrapper:
    return ResultWrapper(
        code=200,
        msg="success",
        data=query_employee_record(uid),
    )


@app.get("/business/reimbursements/{reimbursement_id}", response_model=ResultWrapper)
def get_business_reimbursement(reimbursement_id: str) -> ResultWrapper:
    return ResultWrapper(
        code=200,
        msg="success",
        data=query_reimbursement_record(reimbursement_id),
    )


@app.post("/business/tickets", response_model=ResultWrapper)
def create_business_review_ticket(request: CreateReviewTicketRequest) -> ResultWrapper:
    return ResultWrapper(
        code=200,
        msg="success",
        data=create_review_ticket_record(
            reimbursement_id=request.reimbursement_id,
            reason=request.reason,
        ),
    )


@app.get("/mcp/tools", response_model=ResultWrapper)
def get_mcp_tools() -> ResultWrapper:
    return ResultWrapper(
        code=200,
        msg="success",
        data={"tools": list_mcp_tools()},
    )


@app.post("/mcp/tools/call", response_model=ResultWrapper)
def call_mcp_tool_endpoint(request: McpToolCallRequest) -> ResultWrapper:
    return ResultWrapper(
        code=200,
        msg="success",
        data=call_mcp_tool(request.name, request.arguments),
    )


@app.post("/mcp/jsonrpc", response_model=ResultWrapper)
def mcp_jsonrpc_endpoint(request: McpJsonRpcRequest) -> ResultWrapper:
    return ResultWrapper(
        code=200,
        msg="success",
        data=handle_mcp_request(request.model_dump()),
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=False,
        workers=1,
    )
