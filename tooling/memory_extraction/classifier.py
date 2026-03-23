"""BiLSTM classifier utilities for sentence-level memory extraction."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import torch
from torch import nn
from torch.utils.data import Dataset

from tooling.memory_extraction.labels import label_order_for_task
from tooling.memory_extraction.schema import MemoryExtractionRecord

PAD_TOKEN = "<pad>"
UNK_TOKEN = "<unk>"
PAD_ID = 0
UNK_ID = 1
_TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", flags=re.UNICODE)


def tokenize_text(text: str) -> list[str]:
    """Tokenize text with a simple Unicode-aware regex."""

    return _TOKEN_PATTERN.findall(text.lower())


def build_vocabulary(records: list[MemoryExtractionRecord], min_frequency: int = 1) -> dict[str, int]:
    """Build a vocabulary from training records."""

    token_counts: Counter[str] = Counter()
    for record in records:
        token_counts.update(tokenize_text(record.text))

    token_to_id = {PAD_TOKEN: PAD_ID, UNK_TOKEN: UNK_ID}
    for token, count in sorted(token_counts.items()):
        if count >= min_frequency:
            token_to_id[token] = len(token_to_id)
    return token_to_id


def encode_text(text: str, token_to_id: dict[str, int]) -> list[int]:
    """Encode tokenized text into vocabulary ids."""

    return [token_to_id.get(token, UNK_ID) for token in tokenize_text(text)] or [UNK_ID]


class MemorySentenceDataset(Dataset[dict[str, Any]]):
    """Torch dataset for sentence-level memory examples."""

    def __init__(
        self,
        records: list[MemoryExtractionRecord],
        token_to_id: dict[str, int],
        label_to_id: dict[str, int],
    ) -> None:
        self._records = records
        self._token_to_id = token_to_id
        self._label_to_id = label_to_id

    def __len__(self) -> int:
        return len(self._records)

    def __getitem__(self, index: int) -> dict[str, Any]:
        record = self._records[index]
        return {
            "record_id": record.record_id,
            "tokens": encode_text(record.text, self._token_to_id),
            "label_id": self._label_to_id[record.label],
            "label": record.label,
            "language": record.language,
            "text": record.text,
        }


def collate_memory_batch(batch: list[dict[str, Any]]) -> dict[str, Any]:
    """Pad a sentence-classification batch."""

    lengths = torch.tensor([len(item["tokens"]) for item in batch], dtype=torch.long)
    max_length = int(lengths.max().item())
    token_ids = torch.full((len(batch), max_length), PAD_ID, dtype=torch.long)
    for row_index, item in enumerate(batch):
        token_tensor = torch.tensor(item["tokens"], dtype=torch.long)
        token_ids[row_index, : token_tensor.shape[0]] = token_tensor

    return {
        "token_ids": token_ids,
        "lengths": lengths,
        "label_ids": torch.tensor([item["label_id"] for item in batch], dtype=torch.long),
        "labels": [item["label"] for item in batch],
        "languages": [item["language"] for item in batch],
        "record_ids": [item["record_id"] for item in batch],
        "texts": [item["text"] for item in batch],
    }


class BiLSTMMemoryClassifier(nn.Module):
    """A lightweight BiLSTM classifier for sentence-level memory extraction."""

    def __init__(
        self,
        *,
        vocab_size: int,
        embedding_dim: int,
        hidden_dim: int,
        label_count: int,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=PAD_ID)
        self.encoder = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_dim,
            batch_first=True,
            bidirectional=True,
        )
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_dim * 2, label_count)

    def forward(self, token_ids: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        embedded = self.embedding(token_ids)
        packed = nn.utils.rnn.pack_padded_sequence(
            embedded,
            lengths.cpu(),
            batch_first=True,
            enforce_sorted=False,
        )
        _, (hidden_state, _) = self.encoder(packed)
        forward_hidden = hidden_state[-2]
        backward_hidden = hidden_state[-1]
        features = torch.cat([forward_hidden, backward_hidden], dim=1)
        features = self.dropout(features)
        return self.classifier(features)


@dataclass(frozen=True)
class LoadedClassifierBundle:
    """In-memory classifier bundle for later runtime integration."""

    model: BiLSTMMemoryClassifier
    token_to_id: dict[str, int]
    label_to_id: dict[str, int]
    id_to_label: dict[int, str]
    config: dict[str, Any]


def save_classifier_bundle(
    *,
    path: str,
    model: BiLSTMMemoryClassifier,
    token_to_id: dict[str, int],
    label_to_id: dict[str, int],
    config: dict[str, Any],
) -> None:
    """Save the classifier bundle to disk."""

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "token_to_id": token_to_id,
            "label_to_id": label_to_id,
            "config": config,
        },
        path,
    )


def load_classifier_bundle(path: str, *, device: str | torch.device = "cpu") -> LoadedClassifierBundle:
    """Load a saved classifier bundle."""

    payload = torch.load(path, map_location=device)
    config = dict(payload["config"])
    label_to_id = dict(payload["label_to_id"])
    token_to_id = dict(payload["token_to_id"])
    model = BiLSTMMemoryClassifier(
        vocab_size=int(config["vocab_size"]),
        embedding_dim=int(config["embedding_dim"]),
        hidden_dim=int(config["hidden_dim"]),
        label_count=len(label_to_id),
        dropout=float(config["dropout"]),
    )
    model.load_state_dict(payload["model_state_dict"])
    model.to(device)
    model.eval()
    return LoadedClassifierBundle(
        model=model,
        token_to_id=token_to_id,
        label_to_id=label_to_id,
        id_to_label={index: label for label, index in label_to_id.items()},
        config=config,
    )


def predict_single_text(
    *,
    bundle: LoadedClassifierBundle,
    text: str,
    device: str | torch.device = "cpu",
) -> dict[str, Any]:
    """Run one text through the trained classifier bundle."""

    token_ids = torch.tensor([encode_text(text, bundle.token_to_id)], dtype=torch.long, device=device)
    lengths = torch.tensor([token_ids.shape[1]], dtype=torch.long, device=device)
    with torch.no_grad():
        logits = bundle.model(token_ids, lengths)
        probabilities = torch.softmax(logits, dim=1)[0].detach().cpu()
    predicted_id = int(probabilities.argmax().item())
    return {
        "label": bundle.id_to_label[predicted_id],
        "confidence": float(probabilities[predicted_id].item()),
        "probabilities": {
            bundle.id_to_label[index]: float(probability.item())
            for index, probability in enumerate(probabilities)
        },
    }


def default_label_to_id(*, task: str = "binary") -> dict[str, int]:
    """Return the canonical label mapping for one classifier task."""

    return {label: index for index, label in enumerate(label_order_for_task(task))}
