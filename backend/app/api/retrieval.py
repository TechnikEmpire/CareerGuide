"""Retrieval inspection endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.services.generation.schemas import RetrievedChunk
from backend.app.services.memory.memory_store import default_memory_store
from backend.app.services.retrieval.rag_pipeline import build_retrieval_context

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


class RetrievalPreviewRequest(BaseModel):
    query: str
    user_id: str = "demo-user"


class RetrievalPreviewResponse(BaseModel):
    query: str
    chunks: list[RetrievedChunk]


@router.post("/preview", response_model=RetrievalPreviewResponse)
def preview_retrieval(request: RetrievalPreviewRequest) -> RetrievalPreviewResponse:
    """Expose ranked chunks for debugging and evaluation work."""

    memory_items = default_memory_store.list_items(user_id=request.user_id)
    retrieval_context = build_retrieval_context(question=request.query, memory_items=memory_items)
    return RetrievalPreviewResponse(query=request.query, chunks=retrieval_context.chunks)
