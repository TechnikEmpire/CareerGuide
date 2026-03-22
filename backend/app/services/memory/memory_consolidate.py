"""Memory consolidation helpers."""

from __future__ import annotations

from backend.app.services.generation.schemas import MemoryItemPayload


def consolidate_memory_items(items: list[MemoryItemPayload]) -> list[MemoryItemPayload]:
    """Collapse duplicate memory items by normalized text."""

    consolidated: dict[str, MemoryItemPayload] = {}
    for item in items:
        normalized_text = " ".join(item.text.lower().split())
        consolidated[normalized_text] = item
    return list(consolidated.values())
