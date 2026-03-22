"""Unit tests for the Hopfield-style scaffold helpers."""

from __future__ import annotations

from backend.app.services.generation.schemas import MemoryItemPayload
from backend.app.services.memory.hopfield_memory import associative_read, summarize_memory_for_prompt


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
