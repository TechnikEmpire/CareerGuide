"""Transparent reranking logic for the scaffold pipeline."""

from __future__ import annotations


def combine_scores(lexical_score: float, dense_score: float) -> float:
    """Fuse lexical and dense scores.

    The weighting is deliberately explicit. At this stage, readability and easy
    tuning matter more than squeezing out every last point of retrieval quality.
    """

    return (0.45 * lexical_score) + (0.55 * dense_score)
