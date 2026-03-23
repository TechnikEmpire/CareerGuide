"""Prepare train/dev/test splits for the memory-extraction classifier."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from tooling.memory_extraction.common import read_jsonl, seeded_random, write_json, write_jsonl
from tooling.memory_extraction.labels import SUPPORTED_TASKS, derive_task_label
from tooling.memory_extraction.paths import (
    RAW_SYNTHETIC_DATASET_PATH,
    split_paths_for_task,
)
from tooling.memory_extraction.schema import MemoryExtractionRecord


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare train/dev/test splits for the synthetic memory-extraction corpus."
    )
    parser.add_argument(
        "--task",
        default="binary",
        choices=SUPPORTED_TASKS,
        help="Classifier task to prepare: binary MEMORY-vs-NO_MEMORY or multiclass.",
    )
    parser.add_argument(
        "--input-jsonl",
        default=str(RAW_SYNTHETIC_DATASET_PATH),
        help="Synthetic input dataset.",
    )
    parser.add_argument(
        "--train-output",
        default=None,
        help="Train split JSONL output.",
    )
    parser.add_argument(
        "--dev-output",
        default=None,
        help="Dev split JSONL output.",
    )
    parser.add_argument(
        "--test-output",
        default=None,
        help="Test split JSONL output.",
    )
    parser.add_argument(
        "--manifest-output",
        default=None,
        help="Split manifest JSON output.",
    )
    parser.add_argument("--seed", type=int, default=17, help="Random seed.")
    parser.add_argument("--train-ratio", type=float, default=0.8, help="Train split ratio.")
    parser.add_argument("--dev-ratio", type=float, default=0.1, help="Dev split ratio.")
    return parser.parse_args()


def split_records(
    records: list[MemoryExtractionRecord],
    *,
    seed: int,
    train_ratio: float,
    dev_ratio: float,
) -> dict[str, list[MemoryExtractionRecord]]:
    """Split records while preserving label-language buckets."""

    rng = seeded_random(seed)
    buckets: dict[tuple[str, str], list[MemoryExtractionRecord]] = defaultdict(list)
    for record in records:
        buckets[(record.language, record.label)].append(record)

    splits = {"train": [], "dev": [], "test": []}
    for bucket_records in buckets.values():
        bucket_copy = list(bucket_records)
        rng.shuffle(bucket_copy)
        total = len(bucket_copy)
        train_end = int(total * train_ratio)
        dev_end = train_end + int(total * dev_ratio)
        splits["train"].extend(bucket_copy[:train_end])
        splits["dev"].extend(bucket_copy[train_end:dev_end])
        splits["test"].extend(bucket_copy[dev_end:])
    return splits


def _build_manifest(splits: dict[str, list[MemoryExtractionRecord]]) -> dict[str, object]:
    by_split: dict[str, object] = {}
    for split_name, records in splits.items():
        bucket_counts: dict[str, int] = {}
        for record in records:
            bucket_key = f"{record.language}:{record.label}"
            bucket_counts[bucket_key] = bucket_counts.get(bucket_key, 0) + 1
        by_split[split_name] = {
            "count": len(records),
            "buckets": dict(sorted(bucket_counts.items())),
        }
    return by_split


def project_records_for_task(records: list[MemoryExtractionRecord], *, task: str) -> list[MemoryExtractionRecord]:
    """Project raw fine-grained records into one classifier task label space."""

    projected: list[MemoryExtractionRecord] = []
    for record in records:
        projected.append(
            MemoryExtractionRecord(
                record_id=record.record_id,
                language=record.language,
                label=derive_task_label(record.label, task),
                text=record.text,
                source=record.source,
                source_model=record.source_model,
                prompt_name=record.prompt_name,
            )
        )
    return projected


def main() -> None:
    args = parse_args()
    if args.train_ratio <= 0 or args.dev_ratio < 0 or (args.train_ratio + args.dev_ratio) >= 1:
        raise ValueError("Split ratios must satisfy train_ratio > 0, dev_ratio >= 0, and train_ratio + dev_ratio < 1.")

    default_paths = split_paths_for_task(args.task)
    train_output = Path(args.train_output) if args.train_output else default_paths["train"]
    dev_output = Path(args.dev_output) if args.dev_output else default_paths["dev"]
    test_output = Path(args.test_output) if args.test_output else default_paths["test"]
    manifest_output = Path(args.manifest_output) if args.manifest_output else default_paths["manifest"]

    raw_records = read_jsonl(Path(args.input_jsonl))
    records = project_records_for_task(raw_records, task=args.task)
    splits = split_records(
        records,
        seed=args.seed,
        train_ratio=args.train_ratio,
        dev_ratio=args.dev_ratio,
    )
    write_jsonl(train_output, splits["train"])
    write_jsonl(dev_output, splits["dev"])
    write_jsonl(test_output, splits["test"])
    write_json(
        manifest_output,
        {
            "task": args.task,
            "seed": args.seed,
            "train_ratio": args.train_ratio,
            "dev_ratio": args.dev_ratio,
            "split_stats": _build_manifest(splits),
        },
    )
    print(f"Prepared {args.task} train split: {train_output}")
    print(f"Prepared {args.task} dev split: {dev_output}")
    print(f"Prepared {args.task} test split: {test_output}")
    print(f"Split manifest: {manifest_output}")


if __name__ == "__main__":
    main()
