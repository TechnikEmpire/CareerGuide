"""Memory consolidation helpers."""

from __future__ import annotations

from backend.app.services.generation.schemas import MemoryItemPayload


def normalize_memory_text(text: str) -> str:
    """Normalize memory text for duplicate detection."""

    return " ".join(text.lower().split())


def consolidate_memory_items(items: list[MemoryItemPayload]) -> list[MemoryItemPayload]:
    """Collapse duplicate memory items by normalized text."""

    consolidated: dict[str, MemoryItemPayload] = {}
    for item in items:
        normalized_text = normalize_memory_text(item.text)
        if not normalized_text:
            continue
        consolidated[normalized_text] = item
    return list(consolidated.values())
