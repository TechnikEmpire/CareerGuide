"""Build or refresh the persisted retrieval corpus and FAISS index."""

from __future__ import annotations

import argparse

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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stats = build_retrieval_index(force=args.force)

    print("Retrieval index build complete.")
    print(f"Chunks indexed: {stats.chunk_count}")
    print(f"Embedding model: {stats.embedding_model}")
    print(f"Vector size: {stats.vector_size}")
    print(f"Rebuilt SQLite rows: {stats.rebuilt_sqlite}")
    print(f"Rebuilt FAISS index: {stats.rebuilt_faiss}")
    print(f"FAISS index path: {stats.index_path}")
    print(f"Manifest path: {stats.manifest_path}")


if __name__ == "__main__":
    main()
