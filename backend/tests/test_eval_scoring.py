from __future__ import annotations

from eval.score_eval import score_answer_evidence_predictions
from eval.score_eval import score_retrieval_predictions


def test_retrieval_scoring_reports_perfect_rank_for_exact_hit() -> None:
    qrels = [
        {"query_id": "q1", "chunk_id": "c1", "relevance": 3},
        {"query_id": "q1", "chunk_id": "c2", "relevance": 1},
    ]
    predictions = [
        {"query_id": "q1", "ranked_chunk_ids": ["c1", "c2", "c9"]},
    ]

    report = score_retrieval_predictions(qrels=qrels, predictions=predictions, ks=[1, 3])

    assert report["aggregate"]["recall@1"] == 0.5
    assert report["aggregate"]["recall@3"] == 1.0
    assert report["aggregate"]["mrr@1"] == 1.0
    assert report["aggregate"]["ndcg@3"] == 1.0


def test_answer_evidence_scoring_tracks_precision_and_recall() -> None:
    answer_cases = [
        {
            "id": "case-1",
            "expected_evidence_chunk_ids": ["c1", "c2"],
        }
    ]
    predictions = [
        {
            "case_id": "case-1",
            "cited_chunk_ids": ["c1", "c9"],
        }
    ]

    report = score_answer_evidence_predictions(
        answer_cases=answer_cases,
        predictions=predictions,
    )

    assert report["aggregate"]["evidence_precision"] == 0.5
    assert report["aggregate"]["evidence_recall"] == 0.5
    assert report["aggregate"]["evidence_f1"] == 0.5
