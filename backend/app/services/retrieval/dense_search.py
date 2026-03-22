"""Dense retrieval helpers."""

from __future__ import annotations

from backend.app.services.retrieval.embeddings import DeterministicHashEmbeddingProvider


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity for two equal-length vectors."""

    return sum(l * r for l, r in zip(left, right, strict=True))


def dense_similarity_score(
    query: str,
    text: str,
    embedder: DeterministicHashEmbeddingProvider,
) -> float:
    """Compute a dense similarity score with the configured embedder."""

    query_vector = embedder.embed(query)
    text_vector = embedder.embed(text)
    return cosine_similarity(query_vector, text_vector)
