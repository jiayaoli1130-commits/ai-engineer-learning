from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ResultWrapper(BaseModel):
    code: int
    msg: str
    data: Any


class IngestRequest(BaseModel):
    file_path: str


class SearchRequest(BaseModel):
    query: str
    n_results: int = 3


class DeleteDocumentRequest(BaseModel):
    document_id: str
