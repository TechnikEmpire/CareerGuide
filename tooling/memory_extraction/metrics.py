"""Metrics for sentence-classification training and evaluation."""

from __future__ import annotations

from collections import Counter


def compute_classification_report(
    *,
    gold_labels: list[str],
    predicted_labels: list[str],
    label_order: list[str],
) -> dict[str, object]:
    """Compute accuracy and per-label precision/recall/F1."""

    if len(gold_labels) != len(predicted_labels):
        raise ValueError("gold_labels and predicted_labels must have the same length.")

    total = len(gold_labels)
    accuracy = (
        sum(1 for gold, predicted in zip(gold_labels, predicted_labels, strict=True) if gold == predicted)
        / total
        if total
        else 0.0
    )

    per_label: dict[str, dict[str, float]] = {}
    macro_f1_values: list[float] = []
    confusion: dict[str, dict[str, int]] = {
        gold_label: {predicted_label: 0 for predicted_label in label_order}
        for gold_label in label_order
    }

    for gold, predicted in zip(gold_labels, predicted_labels, strict=True):
        confusion[gold][predicted] += 1

    for label in label_order:
        true_positive = confusion[label][label]
        false_positive = sum(confusion[other][label] for other in label_order if other != label)
        false_negative = sum(confusion[label][other] for other in label_order if other != label)
        support = Counter(gold_labels)[label]

        precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) else 0.0
        recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) else 0.0
        f1 = (
            (2 * precision * recall) / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        macro_f1_values.append(f1)
        per_label[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": float(support),
        }

    macro_f1 = sum(macro_f1_values) / len(macro_f1_values) if macro_f1_values else 0.0

    return {
        "example_count": total,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "per_label": per_label,
        "confusion": confusion,
    }

