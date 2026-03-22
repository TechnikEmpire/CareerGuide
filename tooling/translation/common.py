"""Common helpers for ESCO preprocessing tooling."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any


def read_csv_rows(path: Path) -> Iterator[dict[str, str]]:
    """Yield rows from a UTF-8 CSV file with newline-safe parsing."""

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield {key: (value or "") for key, value in row.items()}


def clean_text(value: str) -> str | None:
    """Normalize whitespace and collapse blank strings to `None`."""

    normalized = " ".join(value.split())
    return normalized or None


def split_multivalue_field(value: str) -> list[str]:
    """Split ESCO multiline text fields into clean lists.

    ESCO uses quoted cells that contain embedded newlines for fields such as
    `altLabels` and `inScheme`. We preserve order and drop empty values.
    """

    values = []
    seen = set()
    for item in value.splitlines():
        cleaned = clean_text(item)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            values.append(cleaned)
    return values


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    """Write JSON Lines records with UTF-8 encoding."""

    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")


def append_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    """Append JSON Lines records with UTF-8 encoding."""

    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """Yield parsed records from a JSONL file."""

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                yield json.loads(stripped)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write formatted JSON with UTF-8 encoding."""

    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
