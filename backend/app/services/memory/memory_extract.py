"""Memory extraction helpers."""

from __future__ import annotations

import uuid

from backend.app.config import settings
from backend.app.services.generation.schemas import MemoryItemPayload
from backend.app.services.memory.runtime_classifier import predict_runtime_memory_label
from backend.app.services.memory.sentence_split import split_text_into_sentence_like_segments


def extract_candidate_memory_items(user_id: str, text: str) -> list[MemoryItemPayload]:
    """Extract candidate memory sentences from one user message.

    The live path now defaults to sentence-level BiLSTM classification over
    pySBD sentence segments. A heuristic fallback remains available explicitly
    through runtime settings for environments that want the older behavior.
    """

    backend_name = settings.memory_extraction_backend.strip().lower()
    if backend_name == "heuristic":
        return _extract_heuristic_candidate_memory_items(user_id=user_id, text=text)
    if backend_name == "bilstm":
        return _extract_classifier_candidate_memory_items(user_id=user_id, text=text)
    raise ValueError(f"Unsupported memory extraction backend: {settings.memory_extraction_backend!r}")


def _extract_classifier_candidate_memory_items(user_id: str, text: str) -> list[MemoryItemPayload]:
    candidates: list[MemoryItemPayload] = []
    for segment in split_text_into_sentence_like_segments(text):
        if len(segment) < settings.memory_extraction_min_segment_characters:
            continue

        prediction = predict_runtime_memory_label(segment)
        if prediction["label"] != "MEMORY":
            continue

        confidence = float(prediction["confidence"])
        if confidence < settings.memory_extraction_min_confidence:
            continue

        candidates.append(
            MemoryItemPayload(
                id=str(uuid.uuid4()),
                user_id=user_id,
                text=segment,
                category=settings.memory_extraction_default_category,
                importance=settings.memory_extraction_default_importance,
                confidence=confidence,
            )
        )
    return candidates


def _extract_heuristic_candidate_memory_items(user_id: str, text: str) -> list[MemoryItemPayload]:
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
