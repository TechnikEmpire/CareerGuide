"""Storage helpers for user memory items."""

from __future__ import annotations

from sqlalchemy import select

from backend.app.services.generation.schemas import MemoryItemPayload
from backend.app.services.memory.memory_consolidate import normalize_memory_text
from backend.db.models import MemoryItem
from backend.db.session import get_session, init_db


def _memory_item_to_payload(record: MemoryItem) -> MemoryItemPayload:
    return MemoryItemPayload(
        id=record.id,
        user_id=record.user_id,
        text=record.text,
        category=record.category,
        importance=record.importance,
        confidence=record.confidence,
    )


class SqliteMemoryStore:
    """SQLite-backed memory store keyed by user id."""

    def list_items(self, user_id: str) -> list[MemoryItemPayload]:
        """Return persisted memory items for one user."""

        init_db()
        with get_session() as session:
            records = session.scalars(
                select(MemoryItem)
                .where(MemoryItem.user_id == user_id)
                .order_by(MemoryItem.created_at.asc())
            ).all()
        return [_memory_item_to_payload(record) for record in records]

    def upsert_item(self, item: MemoryItemPayload) -> MemoryItemPayload:
        """Insert or replace a memory item and dedupe by normalized text."""

        init_db()
        normalized_text = normalize_memory_text(item.text)
        cleaned_text = item.text.strip()
        if not normalized_text:
            return item.model_copy(update={"text": cleaned_text})

        with get_session() as session:
            conflicting_record = session.get(MemoryItem, item.id)
            if conflicting_record is not None and conflicting_record.user_id != item.user_id:
                raise ValueError(
                    f"Memory item id {item.id!r} is already owned by user {conflicting_record.user_id!r}."
                )

            user_records = session.scalars(
                select(MemoryItem)
                .where(MemoryItem.user_id == item.user_id)
                .order_by(MemoryItem.created_at.asc())
            ).all()

            exact_match = next((record for record in user_records if record.id == item.id), None)
            normalized_matches = [
                record
                for record in user_records
                if normalize_memory_text(record.text) == normalized_text
            ]

            target = exact_match or (normalized_matches[0] if normalized_matches else None)
            if target is None:
                target = MemoryItem(
                    id=item.id,
                    user_id=item.user_id,
                    text=cleaned_text,
                    category=item.category,
                    importance=item.importance,
                    confidence=item.confidence,
                )
                session.add(target)
            else:
                target.text = cleaned_text
                target.category = item.category
                target.importance = max(target.importance, item.importance)
                target.confidence = max(target.confidence, item.confidence)

            for duplicate in normalized_matches:
                if duplicate is not target:
                    session.delete(duplicate)

            session.commit()
            session.refresh(target)
            return _memory_item_to_payload(target)

    def delete_item(self, user_id: str, item_id: str) -> MemoryItemPayload | None:
        """Delete one persisted memory item owned by the given user."""

        init_db()
        with get_session() as session:
            record = session.get(MemoryItem, item_id)
            if record is None or record.user_id != user_id:
                return None

            payload = _memory_item_to_payload(record)
            session.delete(record)
            session.commit()
            return payload


default_memory_store = SqliteMemoryStore()
