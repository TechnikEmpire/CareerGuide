"""Shared ESCO grounding helpers for answer and plan generation.

These utilities extract the parts of an ESCO chunk that are useful for
grounded conversational answers and schedule-friendly planning.
"""

from __future__ import annotations

import re

from backend.app.services.generation.schemas import RetrievedChunk
from backend.app.services.retrieval.rag_pipeline import RetrievalContext

_PM_METHODOLOGY_PATTERN = re.compile(r"\bpm\b|²", flags=re.IGNORECASE)
_LOW_SIGNAL_SKILL_PATTERN = re.compile(
    r"\b(information structure|documentation types?|visual presentation techniques?)\b"
    r"|структур[аы] информации|типы документац|техник[аи] визуальн",
    flags=re.IGNORECASE,
)
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")


def first_occupation_or_chunk(retrieval_context: RetrievalContext) -> RetrievedChunk | None:
    """Return the first occupation chunk, or the first chunk if no occupation exists."""

    for chunk in retrieval_context.chunks:
        if chunk.chunk_type == "occupation":
            return chunk
    return retrieval_context.chunks[0] if retrieval_context.chunks else None


def extract_label(chunk: RetrievedChunk | None, language_code: str) -> str:
    """Extract the most relevant ESCO label for the requested language."""

    if chunk is None:
        return ""

    lines = [line.strip() for line in chunk.text.splitlines() if line.strip()]
    prefixes = (
        ("Russian label:", "English label:")
        if language_code == "ru"
        else ("English label:", "Russian label:")
    )
    for prefix in prefixes:
        line = _pick_chunk_line(lines, (prefix,))
        if line:
            return line.removeprefix(prefix).strip().strip(".")

    if " / " in chunk.title:
        parts = [part.strip() for part in chunk.title.split(" / ") if part.strip()]
        if len(parts) >= 2:
            return parts[0] if language_code == "ru" else parts[-1]
    return chunk.title.strip()


def extract_description(chunk: RetrievedChunk | None, language_code: str) -> str:
    """Extract the most useful ESCO description line for the requested language."""

    if chunk is None:
        return ""

    lines = [line.strip() for line in chunk.text.splitlines() if line.strip()]
    prefixes = (
        ("Description (RU):", "Definition (RU):", "Scope note (RU):", "Description (EN):")
        if language_code == "ru"
        else ("Description (EN):", "Definition (EN):", "Scope note (EN):", "Description (RU):")
    )
    for prefix in prefixes:
        line = _pick_chunk_line(lines, (prefix,))
        if line:
            return line.removeprefix(prefix).strip().strip(".")
    return ""


def extract_skills(chunk: RetrievedChunk | None, language_code: str) -> list[str]:
    """Extract a cleaned list of ESCO skill labels from a chunk."""

    if chunk is None:
        return []

    lines = [line.strip() for line in chunk.text.splitlines() if line.strip()]
    prefixes = (
        ("Essential skills (RU):", "Optional skills (RU):", "Essential skills (EN):")
        if language_code == "ru"
        else ("Essential skills (EN):", "Optional skills (EN):", "Essential skills (RU):")
    )
    skill_blob = ""
    for prefix in prefixes:
        line = _pick_chunk_line(lines, (prefix,))
        if line:
            skill_blob = line.removeprefix(prefix).strip().strip(".")
            break

    if not skill_blob:
        return []

    skills: list[str] = []
    seen: set[str] = set()
    for raw_skill in skill_blob.split(","):
        skill = raw_skill.strip().strip(".")
        if not skill:
            continue
        if _PM_METHODOLOGY_PATTERN.search(skill):
            continue
        normalized = skill.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        skills.append(skill)
    return skills


def join_human_list(items: list[str], language_code: str) -> str:
    """Join strings using lightweight English or Russian list punctuation."""

    cleaned = [item for item in items if item]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        joiner = " и " if language_code == "ru" else " and "
        return joiner.join(cleaned)
    separator = ", "
    tail_joiner = " и " if language_code == "ru" else ", and "
    return separator.join(cleaned[:-1]) + tail_joiner + cleaned[-1]


def extract_focus_topics(retrieval_context: RetrievalContext, language_code: str, limit: int = 6) -> list[str]:
    """Build a deduplicated list of plan-worthy focus topics from retrieved evidence."""

    topics: list[str] = []
    seen: set[str] = set()
    for chunk in retrieval_context.chunks:
        candidates = extract_skills(chunk, language_code)
        if chunk.chunk_type == "skill_concept":
            label = extract_label(chunk, language_code)
            if label:
                candidates = [label, *candidates]
        for candidate in candidates:
            normalized = candidate.casefold()
            if normalized in seen:
                continue
            seen.add(normalized)
            topics.append(candidate)
    preferred_topics = [topic for topic in topics if not _LOW_SIGNAL_SKILL_PATTERN.search(topic)]
    fallback_topics = [topic for topic in topics if _LOW_SIGNAL_SKILL_PATTERN.search(topic)]
    return preferred_topics[:limit] if preferred_topics else fallback_topics[:limit]


def lower_sentence_start(text: str) -> str:
    """Lowercase only the first character for smoother sentence embedding."""

    if not text:
        return text
    return text[:1].lower() + text[1:]


def summarize_description(text: str, language_code: str, max_words: int = 18) -> str:
    """Compress a raw ESCO description into one short, readable phrase."""

    cleaned = " ".join(text.split()).strip().strip(".")
    if not cleaned:
        return ""

    first_sentence = _SENTENCE_SPLIT_PATTERN.split(cleaned, maxsplit=1)[0].strip().strip(".")
    words = first_sentence.split()
    if len(words) <= max_words:
        return first_sentence
    truncated = " ".join(words[:max_words]).rstrip(",;:")
    if language_code == "ru":
        return f"{truncated}..."
    return f"{truncated}..."


def _pick_chunk_line(lines: list[str], prefixes: tuple[str, ...]) -> str:
    for prefix in prefixes:
        for line in lines:
            if line.startswith(prefix):
                return line
    return ""
