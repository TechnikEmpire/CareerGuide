"""Data structures for synthetic memory-extraction corpora."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from tooling.memory_extraction.labels import (
    BINARY_MEMORY_EXTRACTION_LABELS,
    MEMORY_EXTRACTION_LABELS,
    SUPPORTED_LANGUAGES,
)

_SUPPORTED_SCHEMA_LABELS = set(MEMORY_EXTRACTION_LABELS) | set(BINARY_MEMORY_EXTRACTION_LABELS)


@dataclass(frozen=True)
class MemoryExtractionRecord:
    """One sentence-level supervision example."""

    record_id: str
    language: str
    label: str
    text: str
    source: str
    source_model: str
    prompt_name: str

    def __post_init__(self) -> None:
        if self.language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {self.language!r}")
        if self.label not in _SUPPORTED_SCHEMA_LABELS:
            raise ValueError(f"Unsupported label: {self.label!r}")
        if not self.text.strip():
            raise ValueError("Text must not be empty.")

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-serializable dictionary."""

        return asdict(self)


def record_from_dict(payload: dict[str, Any]) -> MemoryExtractionRecord:
    """Validate and build a record from JSON data."""

    return MemoryExtractionRecord(
        record_id=str(payload["record_id"]),
        language=str(payload["language"]),
        label=str(payload["label"]),
        text=str(payload["text"]),
        source=str(payload.get("source", "unknown")),
        source_model=str(payload.get("source_model", "unknown")),
        prompt_name=str(payload.get("prompt_name", "unknown")),
    )
