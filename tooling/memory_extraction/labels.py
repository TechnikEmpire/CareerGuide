"""Label schema for memory-extraction classification."""

from __future__ import annotations

from enum import StrEnum


class MemoryExtractionLabel(StrEnum):
    """Canonical sentence labels for memory extraction."""

    NO_MEMORY = "NO_MEMORY"
    PREFERENCE = "PREFERENCE"
    CONSTRAINT = "CONSTRAINT"
    GOAL = "GOAL"
    AVAILABILITY = "AVAILABILITY"


class MemoryBinaryLabel(StrEnum):
    """Derived binary labels for the first extraction classifier."""

    NO_MEMORY = "NO_MEMORY"
    MEMORY = "MEMORY"


MEMORY_EXTRACTION_LABELS = [label.value for label in MemoryExtractionLabel]
BINARY_MEMORY_EXTRACTION_LABELS = [label.value for label in MemoryBinaryLabel]
SUPPORTED_TASKS = ("binary", "multiclass")
SUPPORTED_LANGUAGES = ("ru", "en")

# Importance is policy metadata, not a classifier prediction.
DEFAULT_IMPORTANCE_BY_LABEL = {
    MemoryExtractionLabel.NO_MEMORY.value: 0.0,
    MemoryExtractionLabel.PREFERENCE.value: 0.7,
    MemoryExtractionLabel.CONSTRAINT.value: 1.0,
    MemoryExtractionLabel.GOAL.value: 0.9,
    MemoryExtractionLabel.AVAILABILITY.value: 0.8,
}


def is_memorable_label(label: str) -> bool:
    """Return whether a label should become a persisted memory item."""

    return label != MemoryExtractionLabel.NO_MEMORY.value


def to_binary_label(label: str) -> str:
    """Collapse fine-grained labels into the first binary task."""

    return (
        MemoryBinaryLabel.NO_MEMORY.value
        if label == MemoryExtractionLabel.NO_MEMORY.value
        else MemoryBinaryLabel.MEMORY.value
    )


def derive_task_label(label: str, task: str) -> str:
    """Map a raw label into the label space used by one classifier task."""

    if task == "multiclass":
        return label
    if task == "binary":
        return to_binary_label(label)
    raise ValueError(f"Unsupported task: {task!r}")


def label_order_for_task(task: str) -> list[str]:
    """Return the canonical label order for one supported classifier task."""

    if task == "multiclass":
        return list(MEMORY_EXTRACTION_LABELS)
    if task == "binary":
        return list(BINARY_MEMORY_EXTRACTION_LABELS)
    raise ValueError(f"Unsupported task: {task!r}")
