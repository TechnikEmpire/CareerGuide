"""Load retrieval chunks from the tracked ESCO preprocessing artifacts."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path

from backend.app.config import settings
@dataclass(frozen=True)
class EscoRetrievalChunk:
    """Retrieval-ready ESCO chunk before embedding."""

    chunk_id: str
    concept_uri: str
    concept_kind: str
    source_name: str
    source_url: str
    title: str
    text: str
    chunk_type: str
    embedding_text: str


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def _clean_text(value: object) -> str:
    if not value or not isinstance(value, str):
        return ""
    return " ".join(value.split())


def _list_text(values: object, limit: int = 8) -> str:
    if not isinstance(values, list):
        return ""

    cleaned = []
    seen: set[str] = set()
    for raw in values:
        text = _clean_text(raw)
        if not text:
            continue
        lowered = text.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return ", ".join(cleaned)


def _preferred_label(record: dict[str, object], language: str) -> str:
    if language == "ru":
        return _clean_text(
            record.get("translations", {}).get("ru", {}).get("preferred_label")  # type: ignore[union-attr]
        )
    return _clean_text(record.get("source_text", {}).get("preferred_label"))  # type: ignore[union-attr]


def _field_text(record: dict[str, object], language: str, field_name: str) -> str:
    if language == "ru":
        return _clean_text(
            record.get("translations", {}).get("ru", {}).get(field_name)  # type: ignore[union-attr]
        )
    return _clean_text(record.get("source_text", {}).get(field_name))  # type: ignore[union-attr]


def _source_url_for_concept(record: dict[str, object]) -> str:
    concept_uri = _clean_text(record.get("concept_uri"))
    if concept_uri:
        return concept_uri
    return "https://esco.ec.europa.eu/"


def _build_title(record: dict[str, object]) -> str:
    label_ru = _preferred_label(record, "ru")
    label_en = _preferred_label(record, "en")
    if label_ru and label_en and label_ru.lower() != label_en.lower():
        return f"{label_ru} / {label_en}"
    return label_ru or label_en or "ESCO concept"


def _build_skill_label_list(
    skill_uris: list[str],
    concepts_by_uri: dict[str, dict[str, object]],
    *,
    language: str,
    limit: int,
) -> str:
    labels: list[str] = []
    seen: set[str] = set()
    for uri in skill_uris:
        concept = concepts_by_uri.get(uri)
        if not concept:
            continue
        label = _preferred_label(concept, language) or _preferred_label(concept, "en")
        if not label:
            continue
        lowered = label.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        labels.append(label)
        if len(labels) >= limit:
            break
    return ", ".join(labels)


def _compose_chunk_text(
    record: dict[str, object],
    concepts_by_uri: dict[str, dict[str, object]],
    essential_skill_uris: list[str],
    optional_skill_uris: list[str],
) -> str:
    concept_kind = _clean_text(record.get("concept_kind"))
    source_text = record.get("source_text", {})
    classification = record.get("classification", {})

    parts = [
        f"ESCO concept kind: {concept_kind}.",
        f"Russian label: {_preferred_label(record, 'ru')}.",
        f"English label: {_preferred_label(record, 'en')}.",
    ]

    alt_labels_ru = _list_text(
        record.get("translations", {}).get("ru", {}).get("alt_labels", [])  # type: ignore[union-attr]
    )
    alt_labels_en = _list_text(source_text.get("alt_labels", []))  # type: ignore[union-attr]
    if alt_labels_ru:
        parts.append(f"Russian alternate labels: {alt_labels_ru}.")
    if alt_labels_en:
        parts.append(f"English alternate labels: {alt_labels_en}.")

    for field_name, label in (
        ("description", "Description"),
        ("definition", "Definition"),
        ("scope_note", "Scope note"),
    ):
        russian_text = _field_text(record, "ru", field_name)
        english_text = _field_text(record, "en", field_name)
        if russian_text:
            parts.append(f"{label} (RU): {russian_text}")
        if english_text:
            parts.append(f"{label} (EN): {english_text}")

    if concept_kind == "occupation":
        essential_ru = _build_skill_label_list(
            essential_skill_uris,
            concepts_by_uri,
            language="ru",
            limit=settings.esco_skill_limit_per_occupation,
        )
        essential_en = _build_skill_label_list(
            essential_skill_uris,
            concepts_by_uri,
            language="en",
            limit=settings.esco_skill_limit_per_occupation,
        )
        optional_ru = _build_skill_label_list(
            optional_skill_uris,
            concepts_by_uri,
            language="ru",
            limit=5,
        )
        optional_en = _build_skill_label_list(
            optional_skill_uris,
            concepts_by_uri,
            language="en",
            limit=5,
        )
        if essential_ru:
            parts.append(f"Essential skills (RU): {essential_ru}.")
        if essential_en:
            parts.append(f"Essential skills (EN): {essential_en}.")
        if optional_ru:
            parts.append(f"Optional skills (RU): {optional_ru}.")
        if optional_en:
            parts.append(f"Optional skills (EN): {optional_en}.")

    code = _clean_text(classification.get("code"))  # type: ignore[union-attr]
    isco_group = _clean_text(classification.get("isco_group"))  # type: ignore[union-attr]
    if code:
        parts.append(f"ESCO code: {code}.")
    if isco_group:
        parts.append(f"ISCO group: {isco_group}.")

    return "\n".join(part for part in parts if part and part.strip())


def _build_embedding_text(title: str, text: str) -> str:
    """Create the dense-retrieval representation for a chunk.

    We deliberately overweight titles and the opening summary because exact role
    and skill labels matter heavily in this corpus.
    """

    headline = f"{title} {title} {title}"
    body_lines = text.splitlines()
    summary = " ".join(body_lines[:6])
    return f"{headline}\n{summary}\n{text}"


def _build_relation_maps(
    relation_records: list[dict[str, object]],
    concepts_by_uri: dict[str, dict[str, object]],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    essential_skills: dict[str, list[str]] = defaultdict(list)
    optional_skills: dict[str, list[str]] = defaultdict(list)

    for relation in relation_records:
        if relation.get("relation_family") != "occupation_skill":
            continue

        source_uri = _clean_text(relation.get("source_uri"))
        target_uri = _clean_text(relation.get("target_uri"))
        relation_type = _clean_text(relation.get("relation_type"))
        if not source_uri or not target_uri:
            continue
        if source_uri not in concepts_by_uri or target_uri not in concepts_by_uri:
            continue

        if relation_type == "essential":
            essential_skills[source_uri].append(target_uri)
        elif relation_type == "optional":
            optional_skills[source_uri].append(target_uri)

    return essential_skills, optional_skills


@lru_cache(maxsize=1)
def load_esco_retrieval_chunks() -> list[EscoRetrievalChunk]:
    """Load retrieval chunks from tracked ESCO artifacts.

    This stays intentionally transparent: the chunk synthesis is deterministic,
    while the dense encoder is selected later by the retrieval service.
    """

    bilingual_records = _load_jsonl(settings.esco_bilingual_concepts_path)
    relation_records = _load_jsonl(settings.esco_relations_path)

    concepts_by_uri = {
        _clean_text(record.get("concept_uri")): record
        for record in bilingual_records
        if _clean_text(record.get("concept_uri"))
        and _clean_text(record.get("concept_kind")) in {"occupation", "skill_concept"}
    }

    essential_skills, optional_skills = _build_relation_maps(relation_records, concepts_by_uri)

    chunks: list[EscoRetrievalChunk] = []
    for concept_uri, record in concepts_by_uri.items():
        text = _compose_chunk_text(
            record,
            concepts_by_uri,
            essential_skill_uris=essential_skills.get(concept_uri, []),
            optional_skill_uris=optional_skills.get(concept_uri, []),
        )
        title = _build_title(record)
        chunks.append(
            EscoRetrievalChunk(
                chunk_id=f"esco:{concept_uri}",
                concept_uri=concept_uri,
                concept_kind=_clean_text(record.get("concept_kind")),
                source_name="ESCO",
                source_url=_source_url_for_concept(record),
                title=title,
                text=text,
                chunk_type=_clean_text(record.get("concept_kind")),
                embedding_text=_build_embedding_text(title, text),
            )
        )

    return chunks
