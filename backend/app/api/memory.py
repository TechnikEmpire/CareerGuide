"""Memory endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.services.generation.schemas import MemoryItemPayload, MemoryUpsertRequest
from backend.app.services.memory.memory_store import default_memory_store

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/upsert", response_model=MemoryItemPayload)
def upsert_memory(request: MemoryUpsertRequest) -> MemoryItemPayload:
    """Insert or update a user memory item in the current store."""

    return default_memory_store.upsert_item(request.item)


@router.get("/list", response_model=list[MemoryItemPayload])
def list_memory(user_id: str = "demo-user") -> list[MemoryItemPayload]:
    """List stored memory items for one user."""

    return default_memory_store.list_items(user_id=user_id)
