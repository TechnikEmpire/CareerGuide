"""Shared paths for ESCO preprocessing and translation tooling."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_ESCO_DIR = REPO_ROOT / "data" / "raw" / "ESCO" / "ESCO_dataset_v1.2.1_classification_en_csv"
PROCESSED_ESCO_DIR = REPO_ROOT / "data" / "processed" / "esco"
NORMALIZED_DIR = PROCESSED_ESCO_DIR / "normalized"
BILINGUAL_DIR = PROCESSED_ESCO_DIR / "bilingual"
MANIFESTS_DIR = PROCESSED_ESCO_DIR / "manifests"

NORMALIZED_CONCEPTS_PATH = NORMALIZED_DIR / "esco_concepts.en.jsonl"
NORMALIZED_RELATIONS_PATH = NORMALIZED_DIR / "esco_relations.jsonl"
NORMALIZATION_STATS_PATH = MANIFESTS_DIR / "esco_normalization_stats.json"

BILINGUAL_CONCEPTS_PATH = BILINGUAL_DIR / "esco_concepts.en_ru.jsonl"
TRANSLATION_MANIFEST_PATH = MANIFESTS_DIR / "esco_translation_manifest.json"


def ensure_processed_directories() -> None:
    """Create the output directory layout used by the preprocessing workflow."""

    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    BILINGUAL_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
