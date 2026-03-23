"""Runtime tests for sentence-level memory extraction."""

from __future__ import annotations

from collections.abc import Iterator
import sys
import types

import pytest

from backend.app.config import settings
from backend.app.services.memory.memory_extract import extract_candidate_memory_items
from backend.app.services.memory.runtime_classifier import clear_runtime_classifier_cache
from backend.app.services.memory import sentence_split as sentence_split_module
from backend.app.services.memory.sentence_split import (
    clear_sentence_splitter_cache,
    split_text_into_sentence_like_segments,
)


@pytest.fixture()
def restore_memory_extraction_settings() -> Iterator[None]:
    previous_backend = settings.memory_extraction_backend
    previous_splitter = settings.memory_extraction_sentence_splitter
    previous_confidence = settings.memory_extraction_min_confidence
    previous_min_chars = settings.memory_extraction_min_segment_characters
    previous_device = settings.memory_extraction_device

    clear_runtime_classifier_cache()
    clear_sentence_splitter_cache()
    try:
        yield
    finally:
        settings.memory_extraction_backend = previous_backend
        settings.memory_extraction_sentence_splitter = previous_splitter
        settings.memory_extraction_min_confidence = previous_confidence
        settings.memory_extraction_min_segment_characters = previous_min_chars
        settings.memory_extraction_device = previous_device
        clear_runtime_classifier_cache()
        clear_sentence_splitter_cache()


def test_split_text_into_sentence_like_segments_uses_pysbd_when_available(
    restore_memory_extraction_settings: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, bool]] = []

    class FakeSegmenter:
        def __init__(self, language: str, clean: bool) -> None:
            calls.append((language, clean))

        def segment(self, text: str) -> list[str]:
            return text.split("||")

    monkeypatch.setitem(sys.modules, "pysbd", types.SimpleNamespace(Segmenter=FakeSegmenter))
    settings.memory_extraction_sentence_splitter = "pysbd"
    clear_sentence_splitter_cache()

    segments = split_text_into_sentence_like_segments(
        "I prefer remote work.||I need async collaboration."
    )

    assert segments == [
        "I prefer remote work.",
        "I need async collaboration.",
    ]
    assert calls == [("en", False)]


def test_extract_candidate_memory_items_classifies_sentence_segments(
    restore_memory_extraction_settings: None,
) -> None:
    settings.memory_extraction_backend = "bilstm"
    settings.memory_extraction_sentence_splitter = "regex"
    settings.memory_extraction_min_confidence = 0.75
    settings.memory_extraction_device = "cpu"

    candidates = extract_candidate_memory_items(
        user_id="memory-user",
        text="I prefer remote work and async collaboration. What skills do data analysts need?",
    )

    assert len(candidates) == 1
    assert candidates[0].text == "I prefer remote work and async collaboration."
    assert candidates[0].category == "user_memory"
    assert candidates[0].confidence >= 0.75


def test_extract_candidate_memory_items_supports_russian_sentences(
    restore_memory_extraction_settings: None,
) -> None:
    settings.memory_extraction_backend = "bilstm"
    settings.memory_extraction_sentence_splitter = "regex"
    settings.memory_extraction_min_confidence = 0.75
    settings.memory_extraction_device = "cpu"

    candidates = extract_candidate_memory_items(
        user_id="memory-user",
        text="Я предпочитаю удаленную работу и спокойный график. Какие навыки нужны для аналитики данных?",
    )

    assert len(candidates) == 1
    assert candidates[0].text == "Я предпочитаю удаленную работу и спокойный график."
    assert candidates[0].confidence >= 0.75


def test_extract_candidate_memory_items_supports_explicit_heuristic_fallback(
    restore_memory_extraction_settings: None,
) -> None:
    settings.memory_extraction_backend = "heuristic"

    candidates = extract_candidate_memory_items(
        user_id="memory-user",
        text="I prefer remote work and async collaboration.",
    )

    assert len(candidates) == 1
    assert candidates[0].text == "I prefer remote work and async collaboration."
    assert candidates[0].category == "user_constraint"


def test_split_text_into_sentence_like_segments_falls_back_to_regex_when_pysbd_is_unavailable(
    restore_memory_extraction_settings: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings.memory_extraction_sentence_splitter = "pysbd"
    monkeypatch.setattr(sentence_split_module, "_get_pysbd_segmenter", lambda language: None)

    segments = split_text_into_sentence_like_segments(
        "I prefer remote work and async collaboration. I need a low-stress transition."
    )

    assert segments == [
        "I prefer remote work and async collaboration.",
        "I need a low-stress transition.",
    ]
