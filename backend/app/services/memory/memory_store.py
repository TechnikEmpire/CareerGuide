"""Storage helpers for user memory items.

The scaffold keeps memory in process for simplicity. Later, this module can be
rewired to SQLite tables without forcing API or prompt-layer changes.
"""

from __future__ import annotations

from collections import defaultdict

from backend.app.services.generation.schemas import MemoryItemPayload


class InMemoryMemoryStore:
    """Simple in-process memory store keyed by user id."""

    def __init__(self) -> None:
        self._items_by_user: dict[str, list[MemoryItemPayload]] = defaultdict(list)

    def list_items(self, user_id: str) -> list[MemoryItemPayload]:
        """Return memory items for one user."""

        return list(self._items_by_user[user_id])

    def upsert_item(self, item: MemoryItemPayload) -> MemoryItemPayload:
        """Insert or replace a memory item by id."""

        items = self._items_by_user[item.user_id]
        for index, existing_item in enumerate(items):
            if existing_item.id == item.id:
                items[index] = item
                return item

        items.append(item)
        return item


default_memory_store = InMemoryMemoryStore()
