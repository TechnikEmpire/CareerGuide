"""Train a lightweight BiLSTM sentence classifier for memory extraction."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
import random

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from tooling.memory_extraction.classifier import (
    BiLSTMMemoryClassifier,
    MemorySentenceDataset,
    build_vocabulary,
    collate_memory_batch,
    default_label_to_id,
    save_classifier_bundle,
)
from tooling.memory_extraction.common import read_jsonl, write_json
from tooling.memory_extraction.labels import SUPPORTED_TASKS
from tooling.memory_extraction.metrics import compute_classification_report
from tooling.memory_extraction.paths import (
    model_paths_for_task,
    split_paths_for_task,
)


@dataclass(frozen=True)
class TrainingConfig:
    task: str
    train_input: str
    dev_input: str
    output_bundle: str
    output_report: str
    embedding_dim: int
    hidden_dim: int
    dropout: float
    batch_size: int
    epochs: int
    learning_rate: float
    min_frequency: int
    seed: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a BiLSTM memory-extraction sentence classifier."
    )
    parser.add_argument(
        "--task",
        default="binary",
        choices=SUPPORTED_TASKS,
        help="Classifier task to train: binary MEMORY-vs-NO_MEMORY or multiclass.",
    )
    parser.add_argument("--train-input", default=None)
    parser.add_argument("--dev-input", default=None)
    parser.add_argument("--output-bundle", default=None)
    parser.add_argument("--output-report", default=None)
    parser.add_argument("--embedding-dim", type=int, default=128)
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--min-frequency", type=int, default=1)
    parser.add_argument("--seed", type=int, default=17)
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _evaluate(
    *,
    model: BiLSTMMemoryClassifier,
    data_loader: DataLoader,
    loss_fn: nn.Module,
    id_to_label: dict[int, str],
    device: torch.device,
) -> dict[str, object]:
    model.eval()
    gold_labels: list[str] = []
    predicted_labels: list[str] = []
    total_loss = 0.0
    batch_count = 0

    with torch.no_grad():
        for batch in data_loader:
            token_ids = batch["token_ids"].to(device)
            lengths = batch["lengths"].to(device)
            label_ids = batch["label_ids"].to(device)
            logits = model(token_ids, lengths)
            loss = loss_fn(logits, label_ids)
            predictions = logits.argmax(dim=1).detach().cpu().tolist()

            batch_count += 1
            total_loss += float(loss.item())
            gold_labels.extend(batch["labels"])
            predicted_labels.extend(id_to_label[index] for index in predictions)

    report = compute_classification_report(
        gold_labels=gold_labels,
        predicted_labels=predicted_labels,
        label_order=list(id_to_label.values()),
    )
    report["loss"] = total_loss / batch_count if batch_count else 0.0
    return report


def main() -> None:
    args = parse_args()
    split_paths = split_paths_for_task(args.task)
    model_paths = model_paths_for_task(args.task)
    config = TrainingConfig(
        task=args.task,
        train_input=args.train_input or str(split_paths["train"]),
        dev_input=args.dev_input or str(split_paths["dev"]),
        output_bundle=args.output_bundle or str(model_paths["bundle"]),
        output_report=args.output_report or str(model_paths["train_report"]),
        embedding_dim=args.embedding_dim,
        hidden_dim=args.hidden_dim,
        dropout=args.dropout,
        batch_size=args.batch_size,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        min_frequency=args.min_frequency,
        seed=args.seed,
    )

    set_seed(config.seed)
    train_records = read_jsonl(Path(config.train_input))
    dev_records = read_jsonl(Path(config.dev_input))
    token_to_id = build_vocabulary(train_records, min_frequency=config.min_frequency)
    label_to_id = default_label_to_id(task=config.task)
    id_to_label = {index: label for label, index in label_to_id.items()}

    train_dataset = MemorySentenceDataset(train_records, token_to_id, label_to_id)
    dev_dataset = MemorySentenceDataset(dev_records, token_to_id, label_to_id)
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        shuffle=True,
        collate_fn=collate_memory_batch,
    )
    dev_loader = DataLoader(
        dev_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        collate_fn=collate_memory_batch,
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = BiLSTMMemoryClassifier(
        vocab_size=len(token_to_id),
        embedding_dim=config.embedding_dim,
        hidden_dim=config.hidden_dim,
        label_count=len(label_to_id),
        dropout=config.dropout,
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    loss_fn = nn.CrossEntropyLoss()

    history: list[dict[str, object]] = []
    best_macro_f1 = -1.0
    best_state = None

    for epoch in range(1, config.epochs + 1):
        model.train()
        running_loss = 0.0
        progress = tqdm(train_loader, desc=f"epoch {epoch}", unit="batch")
        try:
            for batch in progress:
                optimizer.zero_grad()
                token_ids = batch["token_ids"].to(device)
                lengths = batch["lengths"].to(device)
                label_ids = batch["label_ids"].to(device)
                logits = model(token_ids, lengths)
                loss = loss_fn(logits, label_ids)
                loss.backward()
                optimizer.step()

                running_loss += float(loss.item())
                progress.set_postfix(loss=f"{loss.item():.4f}")
        finally:
            progress.close()

        dev_report = _evaluate(
            model=model,
            data_loader=dev_loader,
            loss_fn=loss_fn,
            id_to_label=id_to_label,
            device=device,
        )
        epoch_record = {
            "epoch": epoch,
            "train_loss": running_loss / max(len(train_loader), 1),
            "dev": dev_report,
        }
        history.append(epoch_record)

        if float(dev_report["macro_f1"]) > best_macro_f1:
            best_macro_f1 = float(dev_report["macro_f1"])
            best_state = {key: value.detach().cpu() for key, value in model.state_dict().items()}

    if best_state is None:
        raise RuntimeError("Training did not produce a model state.")

    model.load_state_dict(best_state)
    save_classifier_bundle(
        path=config.output_bundle,
        model=model.cpu(),
        token_to_id=token_to_id,
        label_to_id=label_to_id,
        config={
            "vocab_size": len(token_to_id),
            "embedding_dim": config.embedding_dim,
            "hidden_dim": config.hidden_dim,
            "dropout": config.dropout,
            "labels": list(label_to_id.keys()),
            "seed": config.seed,
            "task": config.task,
            "problem_type": "memory_extraction_sentence_classification",
        },
    )

    write_json(
        Path(config.output_report),
        {
            "config": asdict(config),
            "best_macro_f1": best_macro_f1,
            "history": history,
            "device": str(device),
            "vocab_size": len(token_to_id),
            "train_example_count": len(train_records),
            "dev_example_count": len(dev_records),
        },
    )
    print(f"Saved classifier bundle to: {config.output_bundle}")
    print(f"Saved training report to: {config.output_report}")


if __name__ == "__main__":
    main()
