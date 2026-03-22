"""Canonical scoring utilities for retrieval and evidence-aware answer evaluation."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import UTC, datetime
import json
from math import log2
from pathlib import Path
from statistics import mean
from typing import Any


def _load_json_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("predictions"), list):
        return payload["predictions"]
    raise ValueError(f"Unsupported JSON payload shape in {path}")


def _group_qrels(qrels: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    grouped: dict[str, dict[str, int]] = defaultdict(dict)
    for record in qrels:
        grouped[record["query_id"]][record["chunk_id"]] = int(record["relevance"])
    return dict(grouped)


def _group_retrieval_predictions(
    predictions: list[dict[str, Any]],
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for record in predictions:
        ranked_chunk_ids = record.get("ranked_chunk_ids", [])
        grouped[record["query_id"]] = list(ranked_chunk_ids)
    return grouped


def _group_answer_predictions(
    predictions: list[dict[str, Any]],
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for record in predictions:
        grouped[record["case_id"]] = list(record.get("cited_chunk_ids", []))
    return grouped


def _recall_at_k(relevance_map: dict[str, int], ranked_chunk_ids: list[str], k: int) -> float:
    relevant = {chunk_id for chunk_id, relevance in relevance_map.items() if relevance > 0}
    if not relevant:
        return 0.0
    retrieved = set(ranked_chunk_ids[:k])
    return len(relevant & retrieved) / len(relevant)


def _mrr_at_k(relevance_map: dict[str, int], ranked_chunk_ids: list[str], k: int) -> float:
    for index, chunk_id in enumerate(ranked_chunk_ids[:k], start=1):
        if relevance_map.get(chunk_id, 0) > 0:
            return 1.0 / index
    return 0.0


def _dcg_at_k(relevance_map: dict[str, int], ranked_chunk_ids: list[str], k: int) -> float:
    score = 0.0
    for index, chunk_id in enumerate(ranked_chunk_ids[:k], start=1):
        relevance = relevance_map.get(chunk_id, 0)
        if relevance <= 0:
            continue
        score += (2**relevance - 1) / log2(index + 1)
    return score


def _ndcg_at_k(relevance_map: dict[str, int], ranked_chunk_ids: list[str], k: int) -> float:
    ideal_chunk_ids = [
        chunk_id
        for chunk_id, _ in sorted(
            relevance_map.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]
    ideal_dcg = _dcg_at_k(relevance_map, ideal_chunk_ids, k)
    if ideal_dcg == 0:
        return 0.0
    return _dcg_at_k(relevance_map, ranked_chunk_ids, k) / ideal_dcg


def score_retrieval_predictions(
    *,
    qrels: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    ks: list[int],
) -> dict[str, Any]:
    """Score retrieval predictions with IR-style metrics."""

    qrels_by_query = _group_qrels(qrels)
    predictions_by_query = _group_retrieval_predictions(predictions)

    per_query: dict[str, dict[str, float]] = {}
    aggregate: dict[str, float] = {}

    for query_id, relevance_map in qrels_by_query.items():
        ranked_chunk_ids = predictions_by_query.get(query_id, [])
        per_query_metrics: dict[str, float] = {}
        for k in ks:
            per_query_metrics[f"recall@{k}"] = round(_recall_at_k(relevance_map, ranked_chunk_ids, k), 4)
            per_query_metrics[f"mrr@{k}"] = round(_mrr_at_k(relevance_map, ranked_chunk_ids, k), 4)
            per_query_metrics[f"ndcg@{k}"] = round(_ndcg_at_k(relevance_map, ranked_chunk_ids, k), 4)
        per_query[query_id] = per_query_metrics

    for k in ks:
        aggregate[f"recall@{k}"] = round(
            mean(metrics[f"recall@{k}"] for metrics in per_query.values()) if per_query else 0.0,
            4,
        )
        aggregate[f"mrr@{k}"] = round(
            mean(metrics[f"mrr@{k}"] for metrics in per_query.values()) if per_query else 0.0,
            4,
        )
        aggregate[f"ndcg@{k}"] = round(
            mean(metrics[f"ndcg@{k}"] for metrics in per_query.values()) if per_query else 0.0,
            4,
        )

    return {
        "query_count": len(qrels_by_query),
        "ks": ks,
        "aggregate": aggregate,
        "per_query": per_query,
    }


def score_answer_evidence_predictions(
    *,
    answer_cases: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Score cited-evidence overlap for answer-level evaluation cases."""

    predictions_by_case = _group_answer_predictions(predictions)
    per_case: dict[str, dict[str, float]] = {}

    for case in answer_cases:
        case_id = case["id"]
        expected = set(case.get("expected_evidence_chunk_ids", []))
        cited = set(predictions_by_case.get(case_id, []))

        hits = len(expected & cited)
        precision = hits / len(cited) if cited else 0.0
        recall = hits / len(expected) if expected else 0.0
        f1 = 0.0 if precision == 0.0 and recall == 0.0 else (2 * precision * recall) / (precision + recall)

        per_case[case_id] = {
            "evidence_precision": round(precision, 4),
            "evidence_recall": round(recall, 4),
            "evidence_f1": round(f1, 4),
        }

    aggregate = {
        "evidence_precision": round(
            mean(metrics["evidence_precision"] for metrics in per_case.values()) if per_case else 0.0,
            4,
        ),
        "evidence_recall": round(
            mean(metrics["evidence_recall"] for metrics in per_case.values()) if per_case else 0.0,
            4,
        ),
        "evidence_f1": round(
            mean(metrics["evidence_f1"] for metrics in per_case.values()) if per_case else 0.0,
            4,
        ),
    }

    return {
        "case_count": len(answer_cases),
        "aggregate": aggregate,
        "per_case": per_case,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Score retrieval predictions with Recall/MRR/nDCG and optionally "
            "score answer evidence overlap against the tracked evaluation fixtures."
        )
    )
    parser.add_argument(
        "--retrieval-predictions",
        type=Path,
        default=None,
        help="JSON file containing ranked retrieval predictions.",
    )
    parser.add_argument(
        "--answer-predictions",
        type=Path,
        default=None,
        help="JSON file containing answer-level cited chunk predictions.",
    )
    parser.add_argument(
        "--qrels",
        type=Path,
        default=Path("eval/retrieval_qrels.json"),
        help="Path to the canonical retrieval qrels JSON file.",
    )
    parser.add_argument(
        "--answer-cases",
        type=Path,
        default=Path("eval/answer_eval_cases.json"),
        help="Path to the canonical answer-evaluation cases JSON file.",
    )
    parser.add_argument(
        "--ks",
        type=int,
        nargs="+",
        default=[1, 3, 5, 10, 20],
        help="Cutoffs to score for retrieval metrics.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional JSON output path for persisted scoring results.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report: dict[str, Any] = {}

    if args.retrieval_predictions is not None:
        qrels = _load_json_records(args.qrels)
        retrieval_predictions = _load_json_records(args.retrieval_predictions)
        report["retrieval"] = score_retrieval_predictions(
            qrels=qrels,
            predictions=retrieval_predictions,
            ks=args.ks,
        )

    if args.answer_predictions is not None:
        answer_cases = _load_json_records(args.answer_cases)
        answer_predictions = _load_json_records(args.answer_predictions)
        report["answer_evidence"] = score_answer_evidence_predictions(
            answer_cases=answer_cases,
            predictions=answer_predictions,
        )

    if not report:
        report = {
            "status": "no_predictions_supplied",
            "next_step": (
                "Provide --retrieval-predictions and/or --answer-predictions "
                "to score against the tracked evaluation fixtures."
            ),
        }

    output_payload = {
        "scored_at": datetime.now(UTC).isoformat(),
        "report": report,
    }

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(output_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(json.dumps(output_payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
