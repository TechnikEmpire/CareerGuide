"""Sentence-like segmentation helpers for runtime memory extraction."""

from __future__ import annotations

from functools import lru_cache
import re
import warnings

from backend.app.config import settings

_CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")
_LATIN_PATTERN = re.compile(r"[A-Za-z]")
_LINE_SPLIT_PATTERN = re.compile(r"(?:\r?\n)+")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_BULLET_PREFIX_PATTERN = re.compile(r"^\s*(?:[-*•]+|\d+[\.\)])\s*")
_FALLBACK_SENTENCE_BOUNDARY_PATTERN = re.compile(r"(?<=[.!?…])\s+")


def normalize_segment_text(text: str) -> str:
    """Collapse whitespace for stable sentence-like segments."""

    return _WHITESPACE_PATTERN.sub(" ", text.strip())


def detect_text_language(text: str) -> str:
    """Detect whether a short user segment looks more Russian or English."""

    cyrillic_count = len(_CYRILLIC_PATTERN.findall(text))
    latin_count = len(_LATIN_PATTERN.findall(text))
    return "ru" if cyrillic_count > latin_count else "en"


def _segment_with_regex(text: str) -> list[str]:
    return [segment for segment in _FALLBACK_SENTENCE_BOUNDARY_PATTERN.split(text) if segment.strip()]


@lru_cache(maxsize=4)
def _get_pysbd_segmenter(language: str):
    try:
        import pysbd
    except ModuleNotFoundError:
        warnings.warn(
            "pysbd is not installed in the current app environment; "
            "falling back to regex sentence splitting for memory extraction.",
            stacklevel=2,
        )
        return None
    return pysbd.Segmenter(language=language, clean=False)


def _segment_block(text: str, language: str) -> list[str]:
    if settings.memory_extraction_sentence_splitter.strip().lower() == "pysbd":
        segmenter = _get_pysbd_segmenter(language)
        if segmenter is not None:
            return [segment for segment in segmenter.segment(text) if segment.strip()]
    return _segment_with_regex(text)


def clear_sentence_splitter_cache() -> None:
    """Reset cached sentence-segmentation helpers for tests."""

    _get_pysbd_segmenter.cache_clear()


def split_text_into_sentence_like_segments(text: str) -> list[str]:
    """Split one user turn into short sentence-like segments for classification."""

    segments: list[str] = []
    for block in _LINE_SPLIT_PATTERN.split(text):
        cleaned_block = normalize_segment_text(_BULLET_PREFIX_PATTERN.sub("", block))
        if not cleaned_block:
            continue

        language = detect_text_language(cleaned_block)
        for segment in _segment_block(cleaned_block, language):
            cleaned_segment = normalize_segment_text(_BULLET_PREFIX_PATTERN.sub("", segment))
            if cleaned_segment:
                segments.append(cleaned_segment)
    return segments
