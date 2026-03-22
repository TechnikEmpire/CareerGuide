"""Export ranked retrieval predictions for canonical qrels-based scoring."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path

from backend.app.config import settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export ranked retrieval predictions for the tracked benchmark "
            "queries without rebuilding retrieval artifacts."
        )
    )
    parser.add_argument(
        "--queries-file",
        type=Path,
        default=Path("eval/retrieval_benchmark_queries.json"),
        help="Path to the canonical retrieval benchmark query file.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("eval/out/retrieval_predictions.json"),
        help="Output path for ranked retrieval predictions.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=20,
        help="Number of ranked chunk IDs to export per query.",
    )
    parser.add_argument(
        "--candidate-pool",
        type=int,
        default=settings.retrieval_candidate_pool_size,
        help="Dense candidate pool size to use before optional reranking.",
    )
    parser.add_argument(
        "--use-reranker",
        action="store_true",
        help="Enable reranking for export. Off by default.",
    )
    device_group = parser.add_mutually_exclusive_group()
    device_group.add_argument(
        "--cpu-only",
        action="store_true",
        dest="cpu_only",
        help="Force CPU-only export. This is the default behavior.",
    )
    device_group.add_argument(
        "--allow-gpu",
        action="store_false",
        dest="cpu_only",
        help="Allow CUDA for embedding and optional reranking.",
    )
    parser.set_defaults(cpu_only=True)
    return parser.parse_args()


def _load_queries(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    if args.cpu_only:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    previous_candidate_pool = settings.retrieval_candidate_pool_size
    settings.retrieval_candidate_pool_size = args.candidate_pool

    from backend.app.services.retrieval.faiss_hnsw import get_faiss_hnsw_retrieval_service
    from backend.app.services.retrieval.faiss_hnsw import inspect_retrieval_artifacts
    from backend.app.services.retrieval.rag_pipeline import build_retrieval_context

    try:
        artifact_status = inspect_retrieval_artifacts()
        if not artifact_status.sqlite_current or not artifact_status.faiss_current:
            raise RuntimeError(
                "Retrieval artifacts are missing or stale. "
                "Run `python -m backend.scripts.build_retrieval_index` before exporting predictions."
            )

        queries = _load_queries(args.queries_file)
        retrieval_service = get_faiss_hnsw_retrieval_service()

        predictions: list[dict[str, object]] = []
        for record in queries:
            query_id = str(record["id"])
            query = str(record["query"])

            if args.use_reranker:
                ranked_chunks = build_retrieval_context(
                    query,
                    [],
                    top_k=args.top_k,
                    use_reranker=True,
                ).chunks
            else:
                ranked_chunks = retrieval_service.search(query, args.top_k)

            predictions.append(
                {
                    "query_id": query_id,
                    "language": record.get("language"),
                    "query": query,
                    "use_reranker": args.use_reranker,
                    "top_k": args.top_k,
                    "candidate_pool": args.candidate_pool,
                    "ranked_chunk_ids": [chunk.chunk_id for chunk in ranked_chunks if chunk.chunk_id],
                    "ranked_titles": [chunk.title for chunk in ranked_chunks],
                }
            )

        output_payload = {
            "exported_at": datetime.now(UTC).isoformat(),
            "benchmark_queries_file": str(args.queries_file),
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
                "top_k": args.top_k,
                "candidate_pool": args.candidate_pool,
                "use_reranker": args.use_reranker,
                "cpu_only": args.cpu_only,
                "faiss_hnsw_m": settings.faiss_hnsw_m,
                "faiss_hnsw_ef_construction": settings.faiss_hnsw_ef_construction,
                "faiss_hnsw_ef_search": settings.faiss_hnsw_ef_search,
            },
            "predictions": predictions,
        }

        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(output_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Wrote {len(predictions)} retrieval predictions to: {args.output_json}")
    finally:
        settings.retrieval_candidate_pool_size = previous_candidate_pool


if __name__ == "__main__":
    main()
