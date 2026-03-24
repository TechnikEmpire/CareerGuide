"""Memory endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.services.generation.schemas import MemoryItemPayload, MemoryUpsertRequest
from backend.app.services.memory.memory_store import default_memory_store

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/upsert", response_model=MemoryItemPayload)
def upsert_memory(request: MemoryUpsertRequest) -> MemoryItemPayload:
    """Insert or update a user memory item in the persistent store."""

    return default_memory_store.upsert_item(request.item)


@router.get("/list", response_model=list[MemoryItemPayload])
def list_memory(user_id: str = "demo-user") -> list[MemoryItemPayload]:
    """List persisted memory items for one user."""

    return default_memory_store.list_items(user_id=user_id)


@router.delete("/{memory_id}", response_model=MemoryItemPayload)
def delete_memory(memory_id: str, user_id: str = "demo-user") -> MemoryItemPayload:
    """Delete one persisted memory item for one user."""

    deleted = default_memory_store.delete_item(user_id=user_id, item_id=memory_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Memory item was not found for this user.")
    return deleted
