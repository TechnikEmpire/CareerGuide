"""Utilities for turning long documents into retrieval-sized chunks."""

from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 40) -> list[str]:
    """Split text into overlapping character windows.

    This is a placeholder strategy that keeps the code easy to follow during the
    scaffold stage. We can replace it with token-aware chunking once the corpus
    ingestion layer is in place.
    """

    if chunk_size <= overlap:
        raise ValueError("chunk_size must be larger than overlap")

    normalized_text = " ".join(text.split())
    if not normalized_text:
        return []

    chunks: list[str] = []
    step = chunk_size - overlap
    for start in range(0, len(normalized_text), step):
        chunks.append(normalized_text[start : start + chunk_size])
    return chunks
