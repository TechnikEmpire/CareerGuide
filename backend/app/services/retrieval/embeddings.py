"""Embedding helpers for dense retrieval and later memory indexing."""

from __future__ import annotations

from functools import lru_cache
import hashlib
from math import sqrt
import re
from typing import Protocol

import numpy as np

from backend.app.config import settings


class EmbeddingProvider(Protocol):
    """Common interface for dense retrieval encoders."""

    model_id: str
    vector_size: int

    def embed_query(self, text: str) -> list[float]:
        """Embed a retrieval query."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed retrieval documents."""


class DeterministicHashEmbeddingProvider:
    """Small deterministic fallback used for tests and offline scaffolding."""

    def __init__(self, vector_size: int = 256) -> None:
        self.vector_size = vector_size
        self.model_id = f"deterministic-hash-v3-{vector_size}"

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def embed(self, text: str) -> list[float]:
        """Backward-compatible single-text embedding helper."""

        return self._embed(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        buckets = [0.0] * self.vector_size
        for token in re.findall(r"\w+", text.lower(), flags=re.UNICODE):
            self._accumulate_feature(buckets, f"tok:{token}", weight=2.0)

            for ngram_size in (3, 4, 5):
                if len(token) < ngram_size:
                    continue
                for index in range(len(token) - ngram_size + 1):
                    ngram = token[index : index + ngram_size]
                    self._accumulate_feature(buckets, f"ng:{ngram_size}:{ngram}", weight=0.35)

        norm = sqrt(sum(value * value for value in buckets))
        if norm == 0:
            return buckets

        return [value / norm for value in buckets]

    def _accumulate_feature(self, buckets: list[float], feature: str, weight: float) -> None:
        digest = hashlib.sha256(feature.encode("utf-8")).hexdigest()
        index = int(digest[:8], 16) % self.vector_size
        buckets[index] += weight


class Qwen3EmbeddingProvider:
    """Sentence-Transformers wrapper for the Qwen3 embedding series."""

    def __init__(self, model_name: str, batch_size: int = 32) -> None:
        self.model_id = model_name
        self.vector_size = settings.retrieval_vector_size
        self.batch_size = batch_size
        self._model = None

    def embed_query(self, text: str) -> list[float]:
        query_prompt = f"Instruct: {settings.retrieval_query_instruction}\nQuery:"
        return self._encode([text], prompt=query_prompt)[0].tolist()

    def embed(self, text: str) -> list[float]:
        """Backward-compatible single-text embedding helper."""

        return self.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._encode(texts).tolist()

    def _encode(self, texts: list[str], prompt: str | None = None) -> np.ndarray:
        if not texts:
            return np.empty((0, self.vector_size), dtype=np.float32)

        model = self._get_model()
        encode_kwargs = {
            "batch_size": self.batch_size,
            "convert_to_numpy": True,
            "show_progress_bar": False,
        }
        if prompt is not None:
            encode_kwargs["prompt"] = prompt

        embeddings = model.encode(texts, **encode_kwargs)
        embeddings = np.asarray(embeddings, dtype=np.float32)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return embeddings / norms

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_id)
        return self._model


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    """Return the configured embedding provider."""

    provider_name = settings.retrieval_embedding_provider.lower()
    if provider_name == "deterministic":
        return DeterministicHashEmbeddingProvider(vector_size=settings.retrieval_vector_size)
    if provider_name == "qwen3":
        return Qwen3EmbeddingProvider(
            model_name=settings.retrieval_embedding_model_name,
            batch_size=settings.retrieval_embedding_batch_size,
        )
    raise ValueError(f"Unsupported retrieval embedding provider: {settings.retrieval_embedding_provider}")
