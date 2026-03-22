"""Memory extraction helpers."""

from __future__ import annotations

import uuid

from backend.app.services.generation.schemas import MemoryItemPayload


def extract_candidate_memory_items(user_id: str, text: str) -> list[MemoryItemPayload]:
    """Extract basic preference or constraint statements from a user message.

    The heuristic is intentionally simple and inspectable. It gives us a place to
    hang tests and future model-based extraction without hiding the current logic.
    """

    lowered_text = text.lower()
    candidates: list[MemoryItemPayload] = []

    trigger_phrases = ("prefer", "want", "need", "cannot", "can't")
    if any(phrase in lowered_text for phrase in trigger_phrases):
        candidates.append(
            MemoryItemPayload(
                id=str(uuid.uuid4()),
                user_id=user_id,
                text=text.strip(),
                category="user_constraint",
                importance=0.7,
                confidence=0.6,
            )
        )
    return candidates
