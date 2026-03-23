"""Unit tests for the Hopfield-style scaffold helpers."""

from __future__ import annotations

import pytest

from backend.app.config import settings
from backend.app.services.generation.schemas import MemoryItemPayload
from backend.app.services.memory.hopfield_memory import (
    associative_read,
    recall_memory_items,
    summarize_memory_for_prompt,
)
from backend.app.services.retrieval.embeddings import get_embedding_provider


@pytest.fixture(autouse=True)
def use_deterministic_memory_embeddings() -> None:
    """Keep Hopfield-memory unit tests offline and deterministic."""

    previous_provider = settings.retrieval_embedding_provider
    previous_model = settings.retrieval_embedding_model_name
    previous_vector_size = settings.retrieval_vector_size
    previous_mode = settings.memory_hopfield_mode
    previous_top_k = settings.memory_hopfield_top_k

    settings.retrieval_embedding_provider = "deterministic"
    settings.retrieval_embedding_model_name = "deterministic"
    settings.retrieval_vector_size = 256
    settings.memory_hopfield_mode = "topk"
    settings.memory_hopfield_top_k = 2
    get_embedding_provider.cache_clear()
    try:
        yield
    finally:
        settings.retrieval_embedding_provider = previous_provider
        settings.retrieval_embedding_model_name = previous_model
        settings.retrieval_vector_size = previous_vector_size
        settings.memory_hopfield_mode = previous_mode
        settings.memory_hopfield_top_k = previous_top_k
        get_embedding_provider.cache_clear()


def test_associative_read_returns_probability_distribution() -> None:
    """The read weights should sum to one."""

    weights = associative_read(
        query_vector=[1.0, 0.0],
        memory_vectors=[[1.0, 0.0], [0.0, 1.0]],
        beta=4.0,
    )
    assert len(weights) == 2
    assert abs(sum(weights) - 1.0) < 1e-6
    assert weights[0] > weights[1]


def test_memory_summary_prioritizes_relevant_items() -> None:
    """The summary should expose the ranked memory items transparently."""

    summary = summarize_memory_for_prompt(
        question="I need a business-aware software role with manageable workload",
        memory_items=[
            MemoryItemPayload(
                id="1",
                user_id="demo-user",
                text="I prefer roles that mix business context and technical work.",
                category="preference",
                importance=0.9,
                confidence=0.8,
            ),
            MemoryItemPayload(
                id="2",
                user_id="demo-user",
                text="I enjoy marine biology documentaries.",
                category="preference",
                importance=0.2,
                confidence=0.6,
            ),
        ],
    )
    assert "business context" in summary.lower()


def test_recall_memory_items_supports_top1_mode() -> None:
    """Top-1 mode should return a single best-matching memory item."""

    result = recall_memory_items(
        question="I want a remote role with flexible collaboration",
        memory_items=[
            MemoryItemPayload(
                id="1",
                user_id="demo-user",
                text="I prefer remote work and async collaboration.",
                category="preference",
                importance=0.9,
                confidence=0.8,
            ),
            MemoryItemPayload(
                id="2",
                user_id="demo-user",
                text="I enjoy marine biology documentaries.",
                category="preference",
                importance=0.2,
                confidence=0.6,
            ),
        ],
        mode="top1",
    )

    assert result.mode == "top1"
    assert len(result.hits) == 1
    assert result.hits[0].item.id == "1"
    assert result.hits[0].weight == 1.0


def test_recall_memory_items_supports_topk_mode() -> None:
    """Top-k mode should return multiple weighted memory hits."""

    result = recall_memory_items(
        question="I need a low-stress remote transition into data work.",
        memory_items=[
            MemoryItemPayload(
                id="1",
                user_id="demo-user",
                text="I prefer remote work.",
                category="preference",
                importance=0.9,
                confidence=0.8,
            ),
            MemoryItemPayload(
                id="2",
                user_id="demo-user",
                text="I need a low-stress transition.",
                category="constraint",
                importance=0.9,
                confidence=0.9,
            ),
            MemoryItemPayload(
                id="3",
                user_id="demo-user",
                text="I enjoy marine biology documentaries.",
                category="preference",
                importance=0.2,
                confidence=0.6,
            ),
        ],
        mode="topk",
        top_k=2,
    )

    assert result.mode == "topk"
    assert len(result.hits) == 2
    assert {hit.item.id for hit in result.hits} == {"1", "2"}
    assert abs(sum(hit.weight for hit in result.hits) - 1.0) < 1e-6


def test_hopfield_top1_and_topk_show_distinct_behavior_on_same_memory_set() -> None:
    """Top-1 and top-k should differ clearly on the same query and memories."""

    memory_items = [
        MemoryItemPayload(
            id="1",
            user_id="demo-user",
            text="I prefer remote work.",
            category="preference",
            importance=0.9,
            confidence=0.8,
        ),
        MemoryItemPayload(
            id="2",
            user_id="demo-user",
            text="I need a low-stress transition into data work.",
            category="constraint",
            importance=0.9,
            confidence=0.9,
        ),
        MemoryItemPayload(
            id="3",
            user_id="demo-user",
            text="I enjoy marine biology documentaries.",
            category="preference",
            importance=0.2,
            confidence=0.6,
        ),
    ]
    question = "I want a remote, low-stress transition into data work."

    top1_result = recall_memory_items(
        question=question,
        memory_items=memory_items,
        mode="top1",
    )
    topk_result = recall_memory_items(
        question=question,
        memory_items=memory_items,
        mode="topk",
        top_k=2,
    )

    assert top1_result.mode == "top1"
    assert len(top1_result.hits) == 1

    assert topk_result.mode == "topk"
    assert len(topk_result.hits) == 2
    assert abs(sum(hit.weight for hit in topk_result.hits) - 1.0) < 1e-6

    previous_mode = settings.memory_hopfield_mode
    previous_top_k = settings.memory_hopfield_top_k
    try:
        settings.memory_hopfield_mode = "top1"
        settings.memory_hopfield_top_k = 1
        top1_summary = summarize_memory_for_prompt(
            question=question,
            memory_items=memory_items,
            max_items=1,
        )

        settings.memory_hopfield_mode = "topk"
        settings.memory_hopfield_top_k = 2
        topk_summary = summarize_memory_for_prompt(
            question=question,
            memory_items=memory_items,
            max_items=2,
        )
    finally:
        settings.memory_hopfield_mode = previous_mode
        settings.memory_hopfield_top_k = previous_top_k

    assert "mode=top1" in top1_summary
    assert "rank=2" not in top1_summary
    assert "mode=topk" in topk_summary
    assert "rank=2" in topk_summary
