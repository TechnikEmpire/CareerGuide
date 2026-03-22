"""Hopfield-style associative read helpers.

This module is intentionally small and transparent. The point of the project is
not to hide the memory mechanism behind marketing language. It is to show a clear
associative read over user memory vectors that can later be evaluated against a
RAG-only baseline.
"""

from __future__ import annotations

from math import exp

import numpy as np

from backend.app.config import settings
from backend.app.services.generation.schemas import MemoryItemPayload
from backend.app.services.retrieval.embeddings import DeterministicHashEmbeddingProvider


embedder = DeterministicHashEmbeddingProvider(vector_size=settings.memory_vector_size)


def softmax(values: list[float], beta: float = 8.0) -> list[float]:
    """Compute a temperature-scaled softmax distribution."""

    if not values:
        return []

    max_value = max(values)
    stabilized = [exp(beta * (value - max_value)) for value in values]
    total = sum(stabilized)
    return [value / total for value in stabilized]


def associative_read(
    query_vector: list[float],
    memory_vectors: list[list[float]],
    beta: float = 8.0,
) -> list[float]:
    """Return memory attention weights for a query vector.

    The read is deliberately explicit:
    1. score the query against each memory vector
    2. convert scores into a softmax distribution
    3. use the weights for prompt summarization or later evaluation
    """

    if not memory_vectors:
        return []

    query = np.array(query_vector, dtype=float)
    scores = []
    for vector in memory_vectors:
        memory = np.array(vector, dtype=float)
        scores.append(float(np.dot(query, memory)))
    return softmax(scores, beta=beta)


def summarize_memory_for_prompt(
    question: str,
    memory_items: list[MemoryItemPayload],
    max_items: int = 3,
) -> str:
    """Build a short weighted memory summary for prompt assembly."""

    if not memory_items:
        return "No stored user memory yet."

    query_vector = embedder.embed(question)
    memory_vectors = [embedder.embed(item.text) for item in memory_items]
    weights = associative_read(query_vector=query_vector, memory_vectors=memory_vectors)

    ranked_items = sorted(
        zip(weights, memory_items, strict=True),
        key=lambda item: item[0],
        reverse=True,
    )[:max_items]

    summary_lines = []
    for weight, item in ranked_items:
        # Rounded weights make the ranking inspectable in prompts and logs.
        summary_lines.append(f"- weight={weight:.3f} [{item.category}] {item.text}")
    return "\n".join(summary_lines)
