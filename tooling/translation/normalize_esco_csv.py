"""Normalize raw ESCO English CSV files into a common bilingual-ready format.

This script intentionally runs before any translation step. The repository
should preserve the original English source fields as canonical and layer
derived Russian translations on top later.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tooling.translation.common import (
    clean_text,
    read_csv_rows,
    split_multivalue_field,
    write_json,
    write_jsonl,
)
from tooling.translation.paths import (
    NORMALIZATION_STATS_PATH,
    NORMALIZED_CONCEPTS_PATH,
    NORMALIZED_RELATIONS_PATH,
    RAW_ESCO_DIR,
    ensure_processed_directories,
)


def build_concept_record(row: dict[str, str], source_file: str, dataset_version: str) -> dict[str, Any]:
    """Map a raw ESCO concept row into the repository's common concept format."""

    raw_type = clean_text(row.get("conceptType", "")) or "Unknown"

    concept_kind_by_file = {
        "occupations_en.csv": "occupation",
        "skills_en.csv": "skill_concept",
        "ISCOGroups_en.csv": "isco_group",
        "skillGroups_en.csv": "skill_group",
    }

    return {
        "record_type": "concept",
        "dataset": "esco",
        "dataset_version": dataset_version,
        "source_language": "en",
        "concept_kind": concept_kind_by_file[source_file],
        "raw_concept_type": raw_type,
        "concept_uri": clean_text(row.get("conceptUri", "")),
        "status": clean_text(row.get("status", "")),
        "source_text": {
            "preferred_label": clean_text(row.get("preferredLabel", "")),
            "alt_labels": split_multivalue_field(row.get("altLabels", "")),
            "hidden_labels": split_multivalue_field(row.get("hiddenLabels", "")),
            "description": clean_text(row.get("description", "")),
            "definition": clean_text(row.get("definition", "")),
            "scope_note": clean_text(row.get("scopeNote", "")),
            "regulated_profession_note": clean_text(row.get("regulatedProfessionNote", "")),
        },
        "translations": {},
        "classification": {
            "isco_group": clean_text(row.get("iscoGroup", "")),
            "skill_type": clean_text(row.get("skillType", "")),
            "reuse_level": clean_text(row.get("reuseLevel", "")),
            "code": clean_text(row.get("code", "")),
            "nace_code": clean_text(row.get("naceCode", "")),
            "in_scheme": split_multivalue_field(row.get("inScheme", "")),
        },
        "audit": {
            "source_file": source_file,
            "modified_date": clean_text(row.get("modifiedDate", "")),
            "normalized_at": datetime.now(UTC).isoformat(),
        },
    }


def build_occupation_skill_relation(row: dict[str, str], dataset_version: str) -> dict[str, Any]:
    """Normalize ESCO occupation-to-skill relation rows."""

    return {
        "record_type": "relation",
        "dataset": "esco",
        "dataset_version": dataset_version,
        "relation_family": "occupation_skill",
        "relation_type": clean_text(row.get("relationType", "")),
        "source_uri": clean_text(row.get("occupationUri", "")),
        "source_kind": "occupation",
        "source_label_en": clean_text(row.get("occupationLabel", "")),
        "target_uri": clean_text(row.get("skillUri", "")),
        "target_kind": "skill_concept",
        "target_subtype": clean_text(row.get("skillType", "")),
        "target_label_en": clean_text(row.get("skillLabel", "")),
        "audit": {"source_file": "occupationSkillRelations_en.csv"},
    }


def build_skill_skill_relation(row: dict[str, str], dataset_version: str) -> dict[str, Any]:
    """Normalize ESCO skill-to-skill relation rows."""

    return {
        "record_type": "relation",
        "dataset": "esco",
        "dataset_version": dataset_version,
        "relation_family": "skill_skill",
        "relation_type": clean_text(row.get("relationType", "")),
        "source_uri": clean_text(row.get("originalSkillUri", "")),
        "source_kind": "skill_concept",
        "source_subtype": clean_text(row.get("originalSkillType", "")),
        "target_uri": clean_text(row.get("relatedSkillUri", "")),
        "target_kind": "skill_concept",
        "target_subtype": clean_text(row.get("relatedSkillType", "")),
        "audit": {"source_file": "skillSkillRelations_en.csv"},
    }


def build_broader_relation(row: dict[str, str], dataset_version: str, source_file: str) -> dict[str, Any]:
    """Normalize ESCO broader-relation rows for occupation or skill hierarchies."""

    return {
        "record_type": "relation",
        "dataset": "esco",
        "dataset_version": dataset_version,
        "relation_family": "broader",
        "relation_type": "broader",
        "source_uri": clean_text(row.get("conceptUri", "")),
        "source_kind": clean_text(row.get("conceptType", "")),
        "source_label_en": clean_text(row.get("conceptLabel", "")),
        "target_uri": clean_text(row.get("broaderUri", "")),
        "target_kind": clean_text(row.get("broaderType", "")),
        "target_label_en": clean_text(row.get("broaderLabel", "")),
        "audit": {"source_file": source_file},
    }


def choose_latest_record(existing: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Return the preferred record for a duplicate concept URI.

    ESCO v1.2.1 English CSV contains a small number of exact duplicate concept
    rows where only `modifiedDate` differs. We keep the newer source row and
    defensively merge list-like fields in case future dumps diverge more.
    """

    existing_modified = existing["audit"].get("modified_date") or ""
    candidate_modified = candidate["audit"].get("modified_date") or ""

    if candidate_modified >= existing_modified:
        preferred = deepcopy(candidate)
        fallback = existing
    else:
        preferred = deepcopy(existing)
        fallback = candidate

    for field_name in ("alt_labels", "hidden_labels"):
        merged_values: list[str] = []
        seen = set()
        for source_record in (preferred, fallback):
            for value in source_record["source_text"].get(field_name, []):
                if value and value not in seen:
                    seen.add(value)
                    merged_values.append(value)
        preferred["source_text"][field_name] = merged_values

    for field_name in ("preferred_label", "description", "definition", "scope_note", "regulated_profession_note"):
        if not preferred["source_text"].get(field_name):
            preferred["source_text"][field_name] = fallback["source_text"].get(field_name)

    in_scheme_values: list[str] = []
    seen = set()
    for source_record in (preferred, fallback):
        for value in source_record["classification"].get("in_scheme", []):
            if value and value not in seen:
                seen.add(value)
                in_scheme_values.append(value)
    preferred["classification"]["in_scheme"] = in_scheme_values

    for field_name in ("isco_group", "skill_type", "reuse_level", "code", "nace_code"):
        if not preferred["classification"].get(field_name):
            preferred["classification"][field_name] = fallback["classification"].get(field_name)

    preferred["audit"]["modified_date"] = max(existing_modified, candidate_modified)
    return preferred


def normalize_esco(raw_dir: Path, dataset_version: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Normalize the ESCO CSV dump into concept and relation records."""

    concept_files = [
        "occupations_en.csv",
        "skills_en.csv",
        "ISCOGroups_en.csv",
        "skillGroups_en.csv",
    ]
    relation_files = [
        "occupationSkillRelations_en.csv",
        "skillSkillRelations_en.csv",
        "broaderRelationsOccPillar_en.csv",
        "broaderRelationsSkillPillar_en.csv",
    ]

    concepts_by_uri: dict[str, dict[str, Any]] = {}
    concept_uri_order: list[str] = []
    relations: list[dict[str, Any]] = []

    concept_counter: Counter[str] = Counter()
    relation_counter: Counter[str] = Counter()
    duplicate_concept_counter: Counter[str] = Counter()
    duplicate_concept_uris: set[str] = set()
    concept_source_row_count = 0

    for source_file in concept_files:
        for row in read_csv_rows(raw_dir / source_file):
            record = build_concept_record(row=row, source_file=source_file, dataset_version=dataset_version)
            concept_source_row_count += 1
            concept_uri = record["concept_uri"]
            if concept_uri in concepts_by_uri:
                concepts_by_uri[concept_uri] = choose_latest_record(concepts_by_uri[concept_uri], record)
                duplicate_concept_counter[record["concept_kind"]] += 1
                duplicate_concept_uris.add(concept_uri)
                continue
            concepts_by_uri[concept_uri] = record
            concept_uri_order.append(concept_uri)
            concept_counter[record["concept_kind"]] += 1

    concepts = [concepts_by_uri[concept_uri] for concept_uri in concept_uri_order]

    for row in read_csv_rows(raw_dir / "occupationSkillRelations_en.csv"):
        relations.append(build_occupation_skill_relation(row=row, dataset_version=dataset_version))
        relation_counter["occupation_skill"] += 1

    for row in read_csv_rows(raw_dir / "skillSkillRelations_en.csv"):
        relations.append(build_skill_skill_relation(row=row, dataset_version=dataset_version))
        relation_counter["skill_skill"] += 1

    for source_file in ("broaderRelationsOccPillar_en.csv", "broaderRelationsSkillPillar_en.csv"):
        for row in read_csv_rows(raw_dir / source_file):
            relations.append(build_broader_relation(row=row, dataset_version=dataset_version, source_file=source_file))
            relation_counter["broader"] += 1

    stats = {
        "dataset": "esco",
        "dataset_version": dataset_version,
        "raw_dir": str(raw_dir),
        "generated_at": datetime.now(UTC).isoformat(),
        "concept_source_row_count": concept_source_row_count,
        "concept_count": len(concepts),
        "relation_count": len(relations),
        "counts_by_concept_kind": dict(concept_counter),
        "duplicate_concept_groups": len(duplicate_concept_uris),
        "duplicate_concept_rows_removed": sum(duplicate_concept_counter.values()),
        "duplicate_concepts_by_kind": dict(duplicate_concept_counter),
        "counts_by_relation_family": dict(relation_counter),
        "concept_source_files": concept_files,
        "relation_source_files": relation_files,
    }
    return concepts, relations, stats


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Normalize ESCO English CSV files into common JSONL records.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_ESCO_DIR)
    parser.add_argument("--dataset-version", default="1.2.1")
    return parser.parse_args()


def main() -> None:
    """Run the ESCO normalization pipeline."""

    args = parse_args()
    ensure_processed_directories()

    concepts, relations, stats = normalize_esco(
        raw_dir=args.raw_dir,
        dataset_version=args.dataset_version,
    )

    write_jsonl(NORMALIZED_CONCEPTS_PATH, concepts)
    write_jsonl(NORMALIZED_RELATIONS_PATH, relations)
    write_json(NORMALIZATION_STATS_PATH, stats)

    print(f"Wrote normalized concepts to: {NORMALIZED_CONCEPTS_PATH}")
    print(f"Wrote normalized relations to: {NORMALIZED_RELATIONS_PATH}")
    print(f"Wrote normalization stats to: {NORMALIZATION_STATS_PATH}")
    print(f"Concepts: {stats['concept_count']}")
    print(f"Relations: {stats['relation_count']}")


if __name__ == "__main__":
    main()
