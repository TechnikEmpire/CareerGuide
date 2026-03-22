"""Embedding helpers.

The final system will use a real embedding model, but the scaffold starts with a
deterministic hash-based embedder so the pipeline stays testable and explainable
before heavier ML dependencies are added.
"""

from __future__ import annotations

import hashlib
from math import sqrt


class DeterministicHashEmbeddingProvider:
    """Create small deterministic vectors from text.

    This is not semantically strong enough for production use, but it gives us a
    stable interface for retrieval and memory code while the real embedding stack
    is still being integrated.
    """

    def __init__(self, vector_size: int = 32) -> None:
        self.vector_size = vector_size

    def embed(self, text: str) -> list[float]:
        """Map text into a normalized fixed-size vector."""

        buckets = [0.0] * self.vector_size
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            index = int(digest[:8], 16) % self.vector_size
            buckets[index] += 1.0

        norm = sqrt(sum(value * value for value in buckets))
        if norm == 0:
            return buckets

        return [value / norm for value in buckets]
