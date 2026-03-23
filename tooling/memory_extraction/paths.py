"""Filesystem paths for standalone memory-extraction tooling."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_ROOT = Path(__file__).resolve().parent
DATA_DIR = MODULE_ROOT / "data"
MODELS_DIR = MODULE_ROOT / "models"
RAW_SYNTHETIC_DATASET_PATH = DATA_DIR / "synthetic_memory_sentences.jsonl"
SPLIT_DIR = DATA_DIR / "splits"
TRAIN_SPLIT_PATH = SPLIT_DIR / "binary" / "train.jsonl"
DEV_SPLIT_PATH = SPLIT_DIR / "binary" / "dev.jsonl"
TEST_SPLIT_PATH = SPLIT_DIR / "binary" / "test.jsonl"
SPLIT_MANIFEST_PATH = DATA_DIR / "split_manifest_binary.json"
DEFAULT_MODEL_BUNDLE_PATH = MODELS_DIR / "bilstm_memory_classifier_binary.pt"
DEFAULT_TRAINING_REPORT_PATH = MODELS_DIR / "bilstm_memory_classifier_binary_train_report.json"
DEFAULT_EVAL_REPORT_PATH = MODELS_DIR / "bilstm_memory_classifier_binary_eval_report.json"


def split_dir_for_task(task: str) -> Path:
    """Return the split directory for one classifier task."""

    return SPLIT_DIR / task


def split_paths_for_task(task: str) -> dict[str, Path]:
    """Return train/dev/test/manifest paths for one classifier task."""

    split_dir = split_dir_for_task(task)
    return {
        "train": split_dir / "train.jsonl",
        "dev": split_dir / "dev.jsonl",
        "test": split_dir / "test.jsonl",
        "manifest": DATA_DIR / f"split_manifest_{task}.json",
    }


def model_paths_for_task(task: str) -> dict[str, Path]:
    """Return model bundle and report paths for one classifier task."""

    return {
        "bundle": MODELS_DIR / f"bilstm_memory_classifier_{task}.pt",
        "train_report": MODELS_DIR / f"bilstm_memory_classifier_{task}_train_report.json",
        "eval_report": MODELS_DIR / f"bilstm_memory_classifier_{task}_eval_report.json",
    }
