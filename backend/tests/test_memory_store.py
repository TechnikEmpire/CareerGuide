"""Direct tests for the persistent memory store."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from backend.app.config import settings
from backend.app.services.generation.schemas import MemoryItemPayload
from backend.app.services.memory.memory_store import SqliteMemoryStore
from backend.db import session as db_session


@pytest.fixture()
def temporary_memory_database(tmp_path) -> Iterator[None]:
    """Run memory-store tests against an isolated SQLite database."""

    previous_database_url = settings.database_url
    test_database_url = f"sqlite:///{tmp_path / 'memory-store-test.db'}"

    settings.database_url = test_database_url
    db_session.configure_database(test_database_url)
    db_session.init_db()
    try:
        yield
    finally:
        settings.database_url = previous_database_url
        db_session.configure_database(previous_database_url)
        db_session.init_db()


def test_sqlite_memory_store_persists_items_across_instances(
    temporary_memory_database: None,
) -> None:
    """Memory items should survive beyond one store instance."""

    store_a = SqliteMemoryStore()
    store_b = SqliteMemoryStore()

    inserted = store_a.upsert_item(
        MemoryItemPayload(
            id="memory-1",
            user_id="memory-user",
            text="I prefer remote work.",
            category="user_constraint",
            importance=0.7,
            confidence=0.6,
        )
    )

    listed = store_b.list_items(user_id="memory-user")
    assert listed == [inserted]


def test_sqlite_memory_store_dedupes_by_normalized_text(
    temporary_memory_database: None,
) -> None:
    """Normalized duplicate memory text should not create multiple rows."""

    store = SqliteMemoryStore()
    store.upsert_item(
        MemoryItemPayload(
            id="memory-1",
            user_id="memory-user",
            text="I prefer remote work.",
            category="user_constraint",
            importance=0.7,
            confidence=0.6,
        )
    )
    deduped = store.upsert_item(
        MemoryItemPayload(
            id="memory-2",
            user_id="memory-user",
            text="  i prefer   remote work.  ",
            category="user_constraint",
            importance=0.9,
            confidence=0.8,
        )
    )

    listed = store.list_items(user_id="memory-user")
    assert len(listed) == 1
    assert listed[0].id == "memory-1"
    assert listed[0].importance == 0.9
    assert listed[0].confidence == 0.8
    assert listed[0].text == deduped.text
