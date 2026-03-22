"""Canonical retrieval-stage benchmarks for the repo."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import platform
from statistics import mean
import sys
from time import perf_counter

from backend.app.config import settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark the retrieval stack in explicit stages. The canonical "
            "baseline is CPU-only HNSW search timing over stored query vectors; "
            "heavier dense, rerank, and full-context modes are opt-in."
        )
    )
    parser.add_argument(
        "--queries-file",
        type=Path,
        default=Path("eval/retrieval_benchmark_queries.json"),
        help="Path to the canonical benchmark query JSON file.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=settings.default_top_k,
        help="Final retrieval context size to benchmark.",
    )
    parser.add_argument(
        "--candidate-pool",
        type=int,
        default=settings.retrieval_candidate_pool_size,
        help="Dense candidate pool size to benchmark before reranking.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Limit benchmark workload. In `hnsw` mode this controls how many "
            "stored vectors are sampled from the index. In other modes it "
            "limits benchmark queries loaded from the query file."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("hnsw", "dense", "rerank", "full"),
        default="hnsw",
        help=(
            "Benchmark mode. `hnsw` is the canonical minimal baseline and "
            "does not load the query embedder. "
            "`dense` adds query embedding + ANN retrieval. `rerank` adds "
            "reranker-only timings. `full` benchmarks the full retrieval-context path."
        ),
    )
    parser.add_argument(
        "--rerank-limit",
        type=int,
        default=1,
        help="Number of canonical queries to use for the heavier reranker/full-context modes.",
    )
    device_group = parser.add_mutually_exclusive_group()
    device_group.add_argument(
        "--cpu-only",
        action="store_true",
        dest="cpu_only",
        help="Force model-backed benchmark stages onto CPU. This is also the default behavior.",
    )
    device_group.add_argument(
        "--allow-gpu",
        action="store_false",
        dest="cpu_only",
        help="Allow CUDA for dense, rerank, or full benchmark modes.",
    )
    parser.add_argument(
        "--hf-home",
        type=Path,
        default=None,
        help="Optional writable Hugging Face cache directory for benchmark runs.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional JSON output path for the benchmark report.",
    )
    parser.set_defaults(cpu_only=True)
    return parser.parse_args()


def _load_queries(path: Path, limit: int | None) -> list[dict[str, str]]:
    records = json.loads(path.read_text(encoding="utf-8"))
    if limit is not None:
        records = records[:limit]
    if not records:
        raise ValueError(f"No benchmark queries found in {path}")
    return records


def _configure_hf_cache(hf_home: Path | None) -> None:
    if hf_home is None:
        return
    os.environ["HF_HOME"] = str(hf_home)
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(hf_home / "hub")
    hf_home.mkdir(parents=True, exist_ok=True)


def _summary(values: list[float]) -> dict[str, float]:
    if not values:
        return {"avg_seconds": 0.0, "min_seconds": 0.0, "max_seconds": 0.0}
    return {
        "avg_seconds": round(mean(values), 3),
        "min_seconds": round(min(values), 3),
        "max_seconds": round(max(values), 3),
    }


def _runtime_environment() -> dict[str, object]:
    try:
        import torch

        cuda_available = torch.cuda.is_available()
        device_name = torch.cuda.get_device_name(0) if cuda_available else "cpu"
        torch_version = torch.__version__
    except Exception:
        cuda_available = False
        device_name = "unknown"
        torch_version = "unavailable"

    return {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cuda_available": cuda_available,
        "device_name": device_name,
        "torch_version": torch_version,
    }


def main() -> None:
    args = parse_args()
    if args.cpu_only:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
    _configure_hf_cache(args.hf_home)

    previous_candidate_pool = settings.retrieval_candidate_pool_size
    settings.retrieval_candidate_pool_size = args.candidate_pool

    from backend.app.services.retrieval.faiss_hnsw import get_faiss_hnsw_retrieval_service
    from backend.app.services.retrieval.faiss_hnsw import inspect_retrieval_artifacts

    try:
        artifact_status = inspect_retrieval_artifacts()
        if not artifact_status.sqlite_current or not artifact_status.faiss_current:
            raise RuntimeError(
                "Retrieval artifacts are missing or stale. "
                "Run `python -m backend.scripts.build_retrieval_index` before benchmarking."
            )

        candidate_pool = max(args.top_k, settings.retrieval_candidate_pool_size)
        benchmark_dense = args.mode in {"dense", "rerank", "full"}
        benchmark_rerank = args.mode in {"rerank", "full"}
        benchmark_full = args.mode == "full"
        get_faiss_hnsw_retrieval_service.cache_clear()

        queries: list[dict[str, str]] = []
        rerank_queries: list[dict[str, str]] = []
        cold_hnsw_seconds: float | None = None
        cold_hnsw_title: str | None = None
        cold_dense_seconds: float | None = None
        cold_dense_title: str | None = None
        cold_full_seconds: float | None = None
        cold_full_title: str | None = None

        service = get_faiss_hnsw_retrieval_service()
        vector_samples = []

        embedding_times: list[float] = []
        hnsw_times: list[float] = []
        dense_times: list[float] = []
        rerank_times: list[float] = []
        full_times: list[float] = []
        query_sanity: list[dict[str, object]] = []

        if args.mode == "hnsw":
            vector_samples = service.benchmark_query_vectors(args.limit or 10)
            if not vector_samples:
                raise RuntimeError("No stored vectors are available for HNSW benchmarking.")

            start = perf_counter()
            cold_hnsw_chunks = service.search_with_vector(vector_samples[0].vector, candidate_pool)
            cold_hnsw_seconds = perf_counter() - start
            cold_hnsw_title = cold_hnsw_chunks[0].title if cold_hnsw_chunks else None

            for sample in vector_samples:
                start = perf_counter()
                vector_candidates = service.search_with_vector(sample.vector, candidate_pool)
                hnsw_times.append(perf_counter() - start)
                query_sanity.append(
                    {
                        "chunk_id": sample.chunk_id,
                        "seed_title": sample.title,
                        "hnsw_top_title": vector_candidates[0].title if vector_candidates else None,
                    }
                )
        else:
            from backend.app.services.retrieval.embeddings import get_embedding_provider
            from backend.app.services.retrieval.rag_pipeline import build_retrieval_context
            from backend.app.services.retrieval.rerank import get_reranker_provider

            queries = _load_queries(args.queries_file, args.limit)
            rerank_queries = queries[: max(1, args.rerank_limit)] if benchmark_rerank else []
            cold_query = queries[0]["query"]

            get_embedding_provider.cache_clear()
            get_faiss_hnsw_retrieval_service.cache_clear()
            service = get_faiss_hnsw_retrieval_service()
            embedder = get_embedding_provider()
            cold_query_vector = embedder.embed_query(cold_query)

            start = perf_counter()
            cold_dense_chunks = service.search_with_vector(cold_query_vector, candidate_pool)
            cold_hnsw_seconds = perf_counter() - start
            cold_hnsw_title = cold_dense_chunks[0].title if cold_dense_chunks else None

            start = perf_counter()
            cold_dense_chunks = get_faiss_hnsw_retrieval_service().search(cold_query, candidate_pool)
            cold_dense_seconds = perf_counter() - start
            cold_dense_title = cold_dense_chunks[0].title if cold_dense_chunks else None

            if benchmark_full:
                get_embedding_provider.cache_clear()
                get_faiss_hnsw_retrieval_service.cache_clear()
                get_reranker_provider.cache_clear()
                start = perf_counter()
                cold_context = build_retrieval_context(
                    rerank_queries[0]["query"],
                    [],
                    top_k=args.top_k,
                    use_reranker=True,
                )
                cold_full_seconds = perf_counter() - start
                cold_full_title = cold_context.chunks[0].title if cold_context.chunks else None

            embedder = get_embedding_provider()
            service = get_faiss_hnsw_retrieval_service()
            reranker = get_reranker_provider() if benchmark_rerank else None

            for record in queries:
                query = record["query"]

                start = perf_counter()
                query_vector = embedder.embed_query(query)
                embedding_times.append(perf_counter() - start)

                start = perf_counter()
                vector_candidates = service.search_with_vector(query_vector, candidate_pool)
                hnsw_times.append(perf_counter() - start)

                sanity = {
                    "id": record["id"],
                    "language": record["language"],
                    "query": query,
                    "hnsw_top_title": vector_candidates[0].title if vector_candidates else None,
                }

                dense_candidates = vector_candidates
                if benchmark_dense:
                    start = perf_counter()
                    dense_candidates = service.search(query, candidate_pool)
                    dense_times.append(perf_counter() - start)
                    sanity["dense_top_title"] = dense_candidates[0].title if dense_candidates else None

                if reranker is not None and record in rerank_queries:
                    documents = [f"{chunk.title}\n\n{chunk.text}" for chunk in dense_candidates]

                    start = perf_counter()
                    rerank_scores = reranker.rerank(query, documents)
                    rerank_times.append(perf_counter() - start)

                    if rerank_scores:
                        best_index = max(range(len(rerank_scores)), key=rerank_scores.__getitem__)
                        sanity["rerank_top_title"] = dense_candidates[best_index].title

                    if benchmark_full:
                        start = perf_counter()
                        context = build_retrieval_context(query, [], top_k=args.top_k, use_reranker=True)
                        full_times.append(perf_counter() - start)
                        sanity["full_top_title"] = context.chunks[0].title if context.chunks else None

                query_sanity.append(sanity)

        report = {
            "environment": _runtime_environment(),
            "queries_file": str(args.queries_file) if args.mode != "hnsw" else None,
            "query_source": "stored_index_vectors" if args.mode == "hnsw" else "canonical_query_file",
            "query_count": len(vector_samples) if args.mode == "hnsw" else len(queries),
            "benchmark_mode": args.mode,
            "settings": {
                "top_k": args.top_k,
                "candidate_pool": candidate_pool,
                "embedding_model": artifact_status.embedding_model,
                "reranker_model": settings.retrieval_reranker_model_name if benchmark_rerank else None,
                "faiss_hnsw_m": settings.faiss_hnsw_m,
                "faiss_hnsw_ef_construction": settings.faiss_hnsw_ef_construction,
                "faiss_hnsw_ef_search": settings.faiss_hnsw_ef_search,
                "cpu_only": args.cpu_only,
                "rerank_limit": args.rerank_limit,
            },
            "artifacts": {
                "chunk_count": artifact_status.chunk_count,
                "embedding_model": artifact_status.embedding_model,
                "vector_size": artifact_status.vector_size,
                "sqlite_current": artifact_status.sqlite_current,
                "faiss_current": artifact_status.faiss_current,
                "index_path": str(artifact_status.index_path),
                "manifest_path": str(artifact_status.manifest_path),
            },
            "cold_pipeline": {
                "hnsw_seconds": round(cold_hnsw_seconds, 3) if cold_hnsw_seconds is not None else None,
                "hnsw_top_title": cold_hnsw_title,
                "dense_seconds": round(cold_dense_seconds, 3) if cold_dense_seconds is not None else None,
                "dense_top_title": cold_dense_title,
                "full_seconds": round(cold_full_seconds, 3) if cold_full_seconds is not None else None,
                "full_top_title": cold_full_title,
            },
            "warm_components": {
                "embed_query": _summary(embedding_times) if args.mode != "hnsw" else None,
                "faiss_hnsw_search": _summary(hnsw_times),
                "dense_retrieval": _summary(dense_times) if benchmark_dense else None,
                "rerank_only": _summary(rerank_times) if benchmark_rerank else None,
                "full_context": _summary(full_times) if benchmark_full else None,
            },
            "query_sanity": query_sanity,
        }

        if args.output_json is not None:
            args.output_json.parent.mkdir(parents=True, exist_ok=True)
            args.output_json.write_text(
                json.dumps(report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        settings.retrieval_candidate_pool_size = previous_candidate_pool


if __name__ == "__main__":
    main()
