"""Build or refresh the persisted retrieval corpus and FAISS index."""

from __future__ import annotations

import argparse

from backend.app.config import settings
from backend.app.services.retrieval.embeddings import get_embedding_provider
from backend.app.services.retrieval.faiss_hnsw import build_retrieval_index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build or refresh the SQLite-persisted retrieval chunk store and "
            "the FAISS HNSW index used by the backend."
        )
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild SQLite retrieval rows and the FAISS index even if current artifacts look valid.",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default=None,
        help=(
            "Device for model-backed retrieval embedding during this standalone build. "
            "Use `cuda` to force GPU and fail fast if CUDA is unavailable."
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Optional retrieval embedding batch-size override for this build.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.device is not None:
        settings.retrieval_embedding_device = args.device
    if args.batch_size is not None:
        if args.batch_size < 1:
            raise SystemExit("--batch-size must be at least 1.")
        settings.retrieval_embedding_batch_size = args.batch_size
    get_embedding_provider.cache_clear()
    stats = build_retrieval_index(force=args.force)

    print("Retrieval index build complete.")
    print(f"Chunks indexed: {stats.chunk_count}")
    print(f"Embedding model: {stats.embedding_model}")
    print(f"Embedding device: {settings.retrieval_embedding_device}")
    print(f"Embedding batch size: {settings.retrieval_embedding_batch_size}")
    print(f"Vector size: {stats.vector_size}")
    print(f"Rebuilt SQLite rows: {stats.rebuilt_sqlite}")
    print(f"Rebuilt FAISS index: {stats.rebuilt_faiss}")
    print(f"FAISS index path: {stats.index_path}")
    print(f"Manifest path: {stats.manifest_path}")


if __name__ == "__main__":
    main()
