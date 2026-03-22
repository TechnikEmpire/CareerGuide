"""Lexical retrieval primitives."""

from __future__ import annotations

from collections import Counter


def lexical_overlap_score(query: str, text: str) -> float:
    """Compute a simple overlap score between query tokens and text tokens."""

    query_counts = Counter(query.lower().split())
    text_counts = Counter(text.lower().split())
    if not query_counts:
        return 0.0

    matched = 0
    for token, query_frequency in query_counts.items():
        matched += min(query_frequency, text_counts.get(token, 0))
    return matched / sum(query_counts.values())
