"""Shared helpers for memory-extraction tooling."""

from __future__ import annotations

import json
from pathlib import Path
import random
import re
from typing import Iterable

from tooling.memory_extraction.schema import MemoryExtractionRecord, record_from_dict

_WHITESPACE_PATTERN = re.compile(r"\s+")
_CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")
_LATIN_PATTERN = re.compile(r"[A-Za-z]")
_WORD_PATTERN = re.compile(r"\b[\w-]+\b", flags=re.UNICODE)

_RU_META_MARKERS = (
    "например",
    "перевод",
    "метка",
    "label",
    "контекст",
    "требован",
    "пример",
    "нужно убед",
    "давайте",
    "сначала",
    "еще один",
    "подходит",
    "классифика",
    "долгосрочной памяти",
    "сохранить это в",
    "сохранять это в",
)
_EN_META_MARKERS = (
    "for example",
    "another one",
    "the sentence",
    "the label",
    "the context",
    "classification",
    "requirements",
    "let me",
    "wait,",
    "wait ",
    "first,",
    "first ",
    "that translates to",
    "long-term memory",
    "save this in memory",
    "persist this",
)

_RU_INCOMPLETE_STARTS = ("когда ", "если ", "хотя ")
_EN_INCOMPLETE_STARTS = ("when ", "if ", "although ")
_RU_SYNTHETIC_ARTIFACT_PATTERNS = (
    re.compile(r"\bвчерасал\w*\b"),
    re.compile(r"\bтелепратек\w*\b"),
    re.compile(r"\bрабоч(?:ую|ая|ее|ей|ем)\s+работ\w*\b"),
    re.compile(r"\bпредпочита\w*\s+сделать\b"),
    re.compile(r"\bплавн(?:ую|ый|ое|ые)\s+работ\w*\b"),
    re.compile(r"\bплавн(?:ую|ый|ое|ые)\s+времен\w*\b"),
)
_EN_SYNTHETIC_ARTIFACT_PATTERNS = (
    re.compile(r"\bwork(?:ing)?\s+work\b"),
    re.compile(r"\bprefer\s+to\s+do\s+the\s+work\b"),
)



def ensure_parent(path: Path) -> None:
    """Create the parent directory for a file if needed."""

    path.parent.mkdir(parents=True, exist_ok=True)


def normalize_text(text: str) -> str:
    """Normalize whitespace for dedupe and validation."""

    return _WHITESPACE_PATTERN.sub(" ", text.strip())


def normalize_text_key(text: str) -> str:
    """Create a stable dedupe key."""

    return normalize_text(text).casefold()


def tokenize_text(text: str) -> list[str]:
    """Tokenize text with the same lightweight regex used elsewhere."""

    return _WORD_PATTERN.findall(normalize_text(text).casefold())


def looks_like_language(text: str, language: str) -> bool:
    """Apply a light heuristic language check for synthetic quality control."""

    if language == "ru":
        return bool(_CYRILLIC_PATTERN.search(text))
    if language == "en":
        return bool(_LATIN_PATTERN.search(text)) and not bool(_CYRILLIC_PATTERN.search(text))
    raise ValueError(f"Unsupported language: {language!r}")


def is_plausible_memory_example(text: str, language: str, label: str) -> bool:
    """Reject obvious synthetic junk without leaking the class definition.

    This gate is intentionally label-agnostic in practice. It is here to filter
    prompt-following chatter, malformed fragments, and other low-quality output.
    It is not here to enforce that one class contains one keyword list and the
    other class does not.
    """

    normalized = normalize_text(text)
    lowered = normalized.casefold()
    tokens = tokenize_text(lowered)

    if not normalized:
        return False
    if len(tokens) < 4 or len(tokens) > 28:
        return False
    if "\n" in text or "{" in text or "}" in text or "[" in text or "]" in text:
        return False

    meta_markers = _RU_META_MARKERS if language == "ru" else _EN_META_MARKERS
    if any(marker in lowered for marker in meta_markers):
        return False

    incomplete_starts = _RU_INCOMPLETE_STARTS if language == "ru" else _EN_INCOMPLETE_STARTS
    if lowered.startswith(incomplete_starts) and "?" not in normalized and "," not in normalized:
        return False

    artifact_patterns = (
        _RU_SYNTHETIC_ARTIFACT_PATTERNS if language == "ru" else _EN_SYNTHETIC_ARTIFACT_PATTERNS
    )
    if any(pattern.search(lowered) for pattern in artifact_patterns):
        return False

    if language == "ru":
        latin_characters = len(_LATIN_PATTERN.findall(normalized))
        if latin_characters > max(3, len(normalized) // 8):
            return False
    if "  " in text:
        return False

    return True


def write_jsonl(path: Path, records: Iterable[MemoryExtractionRecord]) -> None:
    """Write JSONL records to disk."""

    ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


def append_jsonl(path: Path, records: Iterable[MemoryExtractionRecord]) -> None:
    """Append JSONL records to disk."""

    ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[MemoryExtractionRecord]:
    """Read JSONL records from disk."""

    with path.open("r", encoding="utf-8") as handle:
        return [record_from_dict(json.loads(line)) for line in handle if line.strip()]


def write_json(path: Path, payload: dict[str, object]) -> None:
    """Write a JSON dictionary to disk."""

    ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def seeded_random(seed: int) -> random.Random:
    """Create a deterministic random generator."""

    return random.Random(seed)
