"""Evaluate dense-only top-k and candidate-pool settings against tracked qrels."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path

from eval.score_eval import score_retrieval_predictions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Score dense-only retrieval configurations against the tracked qrels "
            "without rebuilding retrieval artifacts."
        )
    )
    parser.add_argument(
        "--queries-file",
        type=Path,
        default=Path("eval/retrieval_benchmark_queries.json"),
        help="Path to the canonical retrieval benchmark query file.",
    )
    parser.add_argument(
        "--qrels",
        type=Path,
        default=Path("eval/retrieval_qrels.json"),
        help="Path to the canonical retrieval qrels JSON file.",
    )
    parser.add_argument(
        "--top-k-values",
        type=int,
        nargs="+",
        default=[3, 5, 10, 20],
        help="Top-k values to evaluate for dense-only retrieval.",
    )
    parser.add_argument(
        "--candidate-pool-values",
        type=int,
        nargs="+",
        default=[5, 10, 20],
        help="Candidate-pool values to record for pipeline parity.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("eval/out/dense_retrieval_tuning.json"),
        help="Output path for the dense-only tuning report.",
    )
    device_group = parser.add_mutually_exclusive_group()
    device_group.add_argument(
        "--cpu-only",
        action="store_true",
        dest="cpu_only",
        help="Force CPU-only evaluation. This is the default behavior.",
    )
    device_group.add_argument(
        "--allow-gpu",
        action="store_false",
        dest="cpu_only",
        help="Allow CUDA for query embedding during evaluation.",
    )
    parser.set_defaults(cpu_only=True)
    return parser.parse_args()


def _load_json(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    if args.cpu_only:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    from backend.app.config import settings
    from backend.app.services.retrieval.faiss_hnsw import get_faiss_hnsw_retrieval_service
    from backend.app.services.retrieval.faiss_hnsw import inspect_retrieval_artifacts

    artifact_status = inspect_retrieval_artifacts()
    if not artifact_status.sqlite_current or not artifact_status.faiss_current:
        raise RuntimeError(
            "Retrieval artifacts are missing or stale. "
            "Run `python -m backend.scripts.build_retrieval_index` before tuning dense retrieval, "
            "or use `python -m backend.scripts.run_local_eval_workflow`, which now repairs stale "
            "retrieval artifacts automatically."
        )

    queries = _load_json(args.queries_file)
    qrels = _load_json(args.qrels)
    retrieval_service = get_faiss_hnsw_retrieval_service()

    results: list[dict[str, object]] = []
    for top_k in sorted(set(args.top_k_values)):
        for candidate_pool in sorted(set(args.candidate_pool_values)):
            search_k = max(top_k, candidate_pool)
            predictions = []
            for query_record in queries:
                ranked_chunks = retrieval_service.search(str(query_record["query"]), search_k)
                predictions.append(
                    {
                        "query_id": query_record["id"],
                        "ranked_chunk_ids": [
                            chunk.chunk_id for chunk in ranked_chunks[:top_k] if chunk.chunk_id
                        ],
                    }
                )

            score_report = score_retrieval_predictions(
                qrels=qrels,
                predictions=predictions,
                ks=[top_k],
            )
            aggregate = score_report["aggregate"]
            results.append(
                {
                    "top_k": top_k,
                    "candidate_pool": candidate_pool,
                    "search_k": search_k,
                    "candidate_pool_affects_dense_only_ranking": False,
                    "aggregate": {
                        f"recall@{top_k}": aggregate[f"recall@{top_k}"],
                        f"mrr@{top_k}": aggregate[f"mrr@{top_k}"],
                        f"ndcg@{top_k}": aggregate[f"ndcg@{top_k}"],
                    },
                }
            )

    output_payload = {
        "evaluated_at": datetime.now(UTC).isoformat(),
        "queries_file": str(args.queries_file),
        "qrels_file": str(args.qrels),
        "retrieval_artifacts": {
            "chunk_count": artifact_status.chunk_count,
            "embedding_model": artifact_status.embedding_model,
            "vector_size": artifact_status.vector_size,
            "index_path": str(artifact_status.index_path),
            "manifest_path": str(artifact_status.manifest_path),
            "sqlite_current": artifact_status.sqlite_current,
            "faiss_current": artifact_status.faiss_current,
        },
        "settings": {
            "cpu_only": args.cpu_only,
            "top_k_values": sorted(set(args.top_k_values)),
            "candidate_pool_values": sorted(set(args.candidate_pool_values)),
            "faiss_hnsw_m": settings.faiss_hnsw_m,
            "faiss_hnsw_ef_construction": settings.faiss_hnsw_ef_construction,
            "faiss_hnsw_ef_search": settings.faiss_hnsw_ef_search,
            "note": (
                "When reranking is disabled, candidate_pool does not change the final "
                "ranking because the dense path simply trims the top-k FAISS results."
            ),
        },
        "results": results,
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(output_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote dense-only tuning report to: {args.output_json}")


if __name__ == "__main__":
    main()
