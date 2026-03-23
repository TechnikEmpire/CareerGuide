"""Temporary scaffold for the real Hopfield memory module.

Current state:
- explicit one-step associative read over stored memory vectors
- real semantic base embeddings via the active retrieval embedder
- explicit non-trainable `top1` and `topk` recall modes
- prompt-facing weighted summary for inspection

Target state:
- learned projection(s) into a Hopfield memory space
- differentiable `ksoftmax`-style top-k recall rather than sparse masking
- debug exports for scores, weights, selected memory ids, and recalled state

Do not oversell this file. The current implementation is a readable scaffold for
the intended energy-based memory module, not the final defended novelty claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp

import numpy as np

from backend.app.config import settings
from backend.app.services.generation.schemas import MemoryItemPayload
from backend.app.services.retrieval.embeddings import get_embedding_provider


@dataclass(frozen=True)
class HopfieldMemoryHit:
    """One recalled memory item and its Hopfield diagnostics."""

    rank: int
    item: MemoryItemPayload
    score: float
    weight: float


@dataclass(frozen=True)
class HopfieldMemoryResult:
    """Inspectable output of a non-trainable Hopfield recall step."""

    mode: str
    beta: float
    scores: list[float]
    hits: list[HopfieldMemoryHit]
    recalled_state: list[float]


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


def _normalize_mode(mode: str | None) -> str:
    selected = (mode or settings.memory_hopfield_mode).strip().lower()
    if selected not in {"top1", "topk"}:
        raise ValueError(f"Unsupported Hopfield memory mode: {selected!r}")
    return selected


def _top_k_indices(scores: list[float], count: int) -> list[int]:
    if count <= 0:
        return []
    return sorted(
        range(len(scores)),
        key=lambda index: scores[index],
        reverse=True,
    )[:count]


def recall_memory_items(
    *,
    question: str,
    memory_items: list[MemoryItemPayload],
    mode: str | None = None,
    top_k: int | None = None,
    beta: float | None = None,
) -> HopfieldMemoryResult:
    """Recall memory items with a non-trainable Hopfield read over real embeddings.

    `top1` approximates max-energy recall of the single best memory.
    `topk` returns a sparse superposition over the k highest-scoring memories.

    This first implementation uses exact top-k selection plus renormalization
    over the softmax weights. It is intentionally non-trainable and inspectable.
    A later phase can replace this with a differentiable `ksoftmax` variant.
    """

    selected_mode = _normalize_mode(mode)
    selected_beta = beta if beta is not None else settings.memory_hopfield_beta

    if not memory_items:
        return HopfieldMemoryResult(
            mode=selected_mode,
            beta=selected_beta,
            scores=[],
            hits=[],
            recalled_state=[],
        )

    embedder = get_embedding_provider()
    query_vector = np.asarray(embedder.embed_query(question), dtype=np.float32)
    memory_vectors = np.asarray(
        embedder.embed_documents([item.text for item in memory_items]),
        dtype=np.float32,
    )

    scores = [float(np.dot(query_vector, memory_vector)) for memory_vector in memory_vectors]
    dense_weights = associative_read(
        query_vector=query_vector.tolist(),
        memory_vectors=memory_vectors.tolist(),
        beta=selected_beta,
    )

    if selected_mode == "top1":
        selected_indices = _top_k_indices(scores, 1)
        selected_weights = [1.0] if selected_indices else []
        recalled_state = (
            memory_vectors[selected_indices[0]].tolist() if selected_indices else []
        )
    else:
        hit_count = min(top_k or settings.memory_hopfield_top_k, len(memory_items))
        selected_indices = _top_k_indices(scores, hit_count)
        raw_weights = [dense_weights[index] for index in selected_indices]
        weight_total = sum(raw_weights) or 1.0
        selected_weights = [weight / weight_total for weight in raw_weights]
        recalled_state = (
            np.sum(
                [
                    weight * memory_vectors[index]
                    for index, weight in zip(selected_indices, selected_weights, strict=True)
                ],
                axis=0,
            ).tolist()
            if selected_indices
            else []
        )

    hits = [
        HopfieldMemoryHit(
            rank=rank,
            item=memory_items[index],
            score=scores[index],
            weight=selected_weights[rank - 1],
        )
        for rank, index in enumerate(selected_indices, start=1)
    ]

    return HopfieldMemoryResult(
        mode=selected_mode,
        beta=selected_beta,
        scores=scores,
        hits=hits,
        recalled_state=recalled_state,
    )


def summarize_memory_for_prompt(
    question: str,
    memory_items: list[MemoryItemPayload],
    max_items: int | None = None,
) -> str:
    """Build a short Hopfield-weighted memory summary for prompt assembly."""

    if not memory_items:
        return "No stored user memory yet."

    hit_limit = max_items or settings.memory_hopfield_top_k
    result = recall_memory_items(
        question=question,
        memory_items=memory_items,
        top_k=hit_limit,
    )

    summary_lines = [f"Hopfield memory recall: mode={result.mode} beta={result.beta:.2f}"]
    for hit in result.hits[:hit_limit]:
        summary_lines.append(
            f"- rank={hit.rank} weight={hit.weight:.3f} score={hit.score:.3f} "
            f"[{hit.item.category}] {hit.item.text}"
        )
    return "\n".join(summary_lines)
