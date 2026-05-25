from typing import Any, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = "default"


class ResultWrapper(BaseModel):
    code: int
    msg: str
    data: Any


class IngestRequest(BaseModel):
    file_path: str


class SearchRequest(BaseModel):
    query: str
    n_results: int = 3
    max_distance: Optional[float] = None


class DeleteDocumentRequest(BaseModel):
    document_id: str


class CreateReviewTicketRequest(BaseModel):
    reimbursement_id: str
    reason: str


class McpToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = {}


class McpJsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: int | str | None = None
    method: str
    params: dict[str, Any] = {}
