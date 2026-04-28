"""Shared role matching for grounded chat, planning, and handoff flows."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re

from backend.app.services.generation.schemas import RetrievedChunk
from backend.app.services.retrieval.rag_pipeline import RetrievalContext

_CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")
_META_ROLE_PATTERN = re.compile(
    r"\b(career guidance|career counsell|career counselor|career coach|career advice|"
    r"career counselling|career counseling|advise on career|provide career counselling|"
    r"provide career counseling)\b"
    r"|консульт.*карьер|карьерн.*консульт",
    flags=re.IGNORECASE,
)
_ROLE_PHRASE_CUTOFF_PATTERN = re.compile(
    r"\s*(?:[,;]|\b(?:но|при этом|однако|but|while|although|though)\b).*",
    flags=re.IGNORECASE,
)
_TARGET_ROLE_PATTERNS = (
    re.compile(r"(?:перейти|переходить|уйти|войти)\s+в\s+([^.!?]+)", flags=re.IGNORECASE),
    re.compile(r"(?:переход|план перехода)\s+в\s+([^.!?]+)", flags=re.IGNORECASE),
    re.compile(r"(?:стать|хочу быть|работать как|работать в роли)\s+([^.!?]+)", flags=re.IGNORECASE),
    re.compile(r"\b(?:transition|move|go)\s+into\s+([^.!?]+)", flags=re.IGNORECASE),
    re.compile(r"\b(?:become|be a|be an|work as|pursue)\s+([^.!?]+)", flags=re.IGNORECASE),
    re.compile(r"\b(?:target role|plan into|plan for)\s+([^.!?]+)", flags=re.IGNORECASE),
)
_WORD_PATTERN = re.compile(r"\w+", flags=re.UNICODE)
_ROLE_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "be",
    "become",
    "build",
    "can",
    "career",
    "careers",
    "for",
    "goal",
    "how",
    "i",
    "into",
    "job",
    "jobs",
    "me",
    "move",
    "my",
    "path",
    "paths",
    "plan",
    "role",
    "roles",
    "target",
    "the",
    "to",
    "transition",
    "want",
    "what",
    "while",
    "work",
    "would",
    "but",
    "need",
    "needs",
    "steady",
    "calm",
    "как",
    "в",
    "и",
    "кем",
    "мне",
    "моя",
    "мое",
    "мои",
    "переход",
    "план",
    "путь",
    "роль",
    "роли",
    "работа",
    "работать",
    "работы",
    "стать",
    "хочу",
    "целевая",
    "но",
    "нужен",
    "нужна",
    "нужно",
    "спокойный",
    "спокойная",
    "спокойное",
    "темп",
    "график",
}
_CYRILLIC_SUFFIXES = (
    "иями",
    "ями",
    "ами",
    "ого",
    "ему",
    "ыми",
    "ими",
    "ая",
    "яя",
    "ую",
    "юю",
    "ый",
    "ий",
    "ой",
    "ые",
    "ие",
    "ых",
    "их",
    "ам",
    "ям",
    "ом",
    "ем",
    "ах",
    "ях",
    "ов",
    "ев",
    "у",
    "ю",
    "а",
    "я",
    "ы",
    "и",
    "е",
    "о",
)


@dataclass(frozen=True)
class SupportedOccupationMatch:
    """Best supported occupation match and its confidence score."""

    occupation: RetrievedChunk
    score: float


def has_supported_role_grounding(text: str, retrieval_context: RetrievalContext) -> bool:
    """Return whether text has a supported occupation match in retrieved evidence."""

    role_text = extract_target_role_phrase(text) or text
    role_tokens = extract_role_tokens(role_text)
    return True if not role_tokens else find_supported_occupation(text, retrieval_context) is not None


def find_supported_occupation(text: str, retrieval_context: RetrievalContext) -> RetrievedChunk | None:
    """Return the best supported occupation when the match is strong enough."""

    match = find_supported_occupation_match(text, retrieval_context)
    return match.occupation if match is not None else None


def find_supported_occupation_match(
    text: str,
    retrieval_context: RetrievalContext,
    *,
    minimum_score: float = 0.5,
) -> SupportedOccupationMatch | None:
    """Return the best supported occupation match with score metadata."""

    role_text = extract_target_role_phrase(text) or text
    role_tokens = extract_role_tokens(role_text)
    if not role_tokens:
        return None

    best_occupation: RetrievedChunk | None = None
    best_score = 0.0
    for occupation in useful_occupations(retrieval_context):
        score = role_support_score(role_tokens, occupation)
        if score > best_score:
            best_score = score
            best_occupation = occupation

    if best_occupation is None or best_score < minimum_score:
        return None
    return SupportedOccupationMatch(occupation=best_occupation, score=best_score)


def find_singular_supported_occupation(
    text: str,
    retrieval_context: RetrievalContext,
    *,
    minimum_score: float = 0.5,
    margin: float = 0.18,
) -> RetrievedChunk | None:
    """Return a supported occupation only when one role clearly dominates."""

    role_text = extract_target_role_phrase(text) or text
    role_tokens = extract_role_tokens(role_text)
    if not role_tokens:
        return None

    scored = sorted(
        (
            (role_support_score(role_tokens, occupation), occupation)
            for occupation in useful_occupations(retrieval_context)
        ),
        key=lambda item: item[0],
        reverse=True,
    )
    if not scored or scored[0][0] < minimum_score:
        return None
    if len(scored) == 1:
        return scored[0][1]

    top_score, top_occupation = scored[0]
    second_score, second_occupation = scored[1]
    if top_occupation.chunk_id and top_occupation.chunk_id == second_occupation.chunk_id:
        return top_occupation
    if top_score - second_score >= margin:
        return top_occupation
    return None


def extract_target_role_phrase(text: str) -> str:
    """Extract a likely role phrase from explicit transition language."""

    for pattern in _TARGET_ROLE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        return _trim_role_phrase(match.group(1))
    return ""


def extract_role_tokens(text: str) -> list[str]:
    """Normalize tokens used for role support scoring."""

    tokens = [_normalize_role_token(token) for token in _WORD_PATTERN.findall(text)]
    return [
        token
        for token in tokens
        if len(token) >= 2 and token not in _ROLE_STOPWORDS
    ]


def useful_occupations(retrieval_context: RetrievalContext) -> list[RetrievedChunk]:
    """Return retrieved occupation chunks, excluding career-advisor meta roles."""

    occupations: list[RetrievedChunk] = []
    for chunk in retrieval_context.chunks:
        if chunk.chunk_type != "occupation":
            continue
        haystack = f"{chunk.title}\n{chunk.text}"
        if _META_ROLE_PATTERN.search(haystack):
            continue
        occupations.append(chunk)
    return occupations


def first_useful_occupation(retrieval_context: RetrievalContext) -> RetrievedChunk | None:
    """Return the top useful occupation chunk, if present."""

    occupations = useful_occupations(retrieval_context)
    return occupations[0] if occupations else None


def role_support_score(role_tokens: list[str], chunk: RetrievedChunk) -> float:
    """Score normalized role tokens against occupation title and text."""

    haystack = f"{chunk.title}\n{chunk.text}".casefold()
    chunk_tokens = {_normalize_role_token(token) for token in _WORD_PATTERN.findall(haystack)}
    overlap_ratio = len(set(role_tokens) & chunk_tokens) / len(set(role_tokens))
    similarity = SequenceMatcher(None, " ".join(role_tokens), haystack[:240]).ratio()
    return max(overlap_ratio, similarity)


def _trim_role_phrase(text: str) -> str:
    trimmed = _ROLE_PHRASE_CUTOFF_PATTERN.sub("", text).strip()
    return re.sub(r"^(?:a|an|the)\s+", "", trimmed, flags=re.IGNORECASE)


def _normalize_role_token(token: str) -> str:
    normalized = token.casefold().replace("ё", "е")
    if not _CYRILLIC_PATTERN.search(normalized):
        return normalized
    for suffix in _CYRILLIC_SUFFIXES:
        if normalized.endswith(suffix) and len(normalized) > len(suffix) + 3:
            return normalized[: -len(suffix)]
    return normalized
