"""Evaluate a trained BiLSTM memory-extraction classifier."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from tooling.memory_extraction.classifier import (
    MemorySentenceDataset,
    collate_memory_batch,
    load_classifier_bundle,
)
from tooling.memory_extraction.common import read_jsonl, write_json
from tooling.memory_extraction.labels import SUPPORTED_TASKS
from tooling.memory_extraction.metrics import compute_classification_report
from tooling.memory_extraction.paths import (
    model_paths_for_task,
    split_paths_for_task,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a trained BiLSTM memory-extraction classifier."
    )
    parser.add_argument(
        "--task",
        default="binary",
        choices=SUPPORTED_TASKS,
        help="Classifier task to evaluate: binary MEMORY-vs-NO_MEMORY or multiclass.",
    )
    parser.add_argument("--model-bundle", default=None)
    parser.add_argument("--input-jsonl", default=None)
    parser.add_argument("--output-report", default=None)
    parser.add_argument("--batch-size", type=int, default=128)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    split_paths = split_paths_for_task(args.task)
    model_paths = model_paths_for_task(args.task)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_bundle = args.model_bundle or str(model_paths["bundle"])
    input_jsonl = args.input_jsonl or str(split_paths["test"])
    output_report = args.output_report or str(model_paths["eval_report"])
    bundle = load_classifier_bundle(model_bundle, device=device)
    records = read_jsonl(Path(input_jsonl))
    dataset = MemorySentenceDataset(records, bundle.token_to_id, bundle.label_to_id)
    data_loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=collate_memory_batch,
    )

    gold_labels: list[str] = []
    predicted_labels: list[str] = []
    per_language_gold: dict[str, list[str]] = {"ru": [], "en": []}
    per_language_predicted: dict[str, list[str]] = {"ru": [], "en": []}

    with torch.no_grad():
        for batch in data_loader:
            token_ids = batch["token_ids"].to(device)
            lengths = batch["lengths"].to(device)
            logits = bundle.model(token_ids, lengths)
            predictions = logits.argmax(dim=1).detach().cpu().tolist()
            predicted = [bundle.id_to_label[index] for index in predictions]

            gold_labels.extend(batch["labels"])
            predicted_labels.extend(predicted)
            for language, gold, predicted_label in zip(
                batch["languages"],
                batch["labels"],
                predicted,
                strict=True,
            ):
                per_language_gold[language].append(gold)
                per_language_predicted[language].append(predicted_label)

    report = compute_classification_report(
        gold_labels=gold_labels,
        predicted_labels=predicted_labels,
        label_order=list(bundle.label_to_id.keys()),
    )
    report["per_language"] = {
        language: compute_classification_report(
            gold_labels=per_language_gold[language],
            predicted_labels=per_language_predicted[language],
            label_order=list(bundle.label_to_id.keys()),
        )
        for language in sorted(per_language_gold)
        if per_language_gold[language]
    }
    report["task"] = args.task
    report["model_bundle"] = model_bundle
    report["input_jsonl"] = input_jsonl
    write_json(Path(output_report), report)
    print(f"Saved {args.task} evaluation report to: {output_report}")


if __name__ == "__main__":
    main()
