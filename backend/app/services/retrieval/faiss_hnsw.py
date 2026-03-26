"""FAISS HNSW retrieval over SQLite-persisted chunk embeddings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
import json
from pathlib import Path

import faiss
import numpy as np
from sqlalchemy import select

from backend.app.config import settings
from backend.app.services.generation.schemas import RetrievedChunk
from backend.app.services.retrieval.embeddings import get_embedding_provider
from backend.app.services.retrieval.esco_corpus import load_esco_retrieval_chunks
from backend.db import session as db_session
from backend.db.models import RetrievalChunkRecord


@dataclass(frozen=True)
class IndexedChunk:
    """In-memory retrieval chunk with its persisted identity."""

    chunk_id: str
    chunk_type: str
    source_name: str
    source_url: str
    title: str
    text: str


@dataclass(frozen=True)
class BenchmarkQueryVector:
    """Stored vector sample used for pure HNSW benchmarking."""

    chunk_id: str
    title: str
    vector: np.ndarray


@dataclass(frozen=True)
class RetrievalBuildStats:
    """Summary of a retrieval-index build or refresh run."""

    chunk_count: int
    embedding_model: str
    vector_size: int
    index_path: Path
    manifest_path: Path
    rebuilt_sqlite: bool
    rebuilt_faiss: bool


@dataclass(frozen=True)
class RetrievalArtifactStatus:
    """Current retrieval-artifact validity without mutating local state."""

    chunk_count: int
    embedding_model: str
    vector_size: int
    index_path: Path
    manifest_path: Path
    sqlite_current: bool
    faiss_current: bool


class RetrievalArtifactsError(RuntimeError):
    """Raised when the retrieval index or persisted chunk rows are unavailable."""


def _embedding_to_bytes(values: tuple[float, ...]) -> bytes:
    return np.asarray(values, dtype=np.float32).tobytes()


def _bytes_to_embedding(payload: bytes) -> np.ndarray:
    return np.frombuffer(payload, dtype=np.float32)


def _manifest_payload(*, chunk_count: int, embedding_model: str, vector_size: int) -> dict[str, object]:
    return {
        "built_at": datetime.now(UTC).isoformat(),
        "chunk_count": chunk_count,
        "embedding_model": embedding_model,
        "vector_size": vector_size,
        "faiss_hnsw_m": settings.faiss_hnsw_m,
        "faiss_hnsw_ef_construction": settings.faiss_hnsw_ef_construction,
    }


def _normalize_embedding_model_id(value: str) -> str:
    configured = settings.retrieval_embedding_model_id
    if value == configured:
        return configured

    configured_name = Path(configured).name
    value_name = Path(value).name
    if value_name and value_name == configured_name:
        return configured
    return value


def _read_manifest(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _sorted_source_chunks():
    return sorted(load_esco_retrieval_chunks(), key=lambda chunk: chunk.chunk_id)


def _sqlite_corpus_matches(expected_count: int, *, embedding_model: str, vector_size: int) -> bool:
    with db_session.SessionLocal() as session:
        existing_count = session.query(RetrievalChunkRecord).count()
        first_row = session.scalars(select(RetrievalChunkRecord).limit(1)).first()
        if existing_count != expected_count or existing_count == 0 or first_row is None:
            return False
        first_dim = len(_bytes_to_embedding(first_row.embedding))
        stored_model = _normalize_embedding_model_id(first_row.embedding_model)
        expected_model = _normalize_embedding_model_id(embedding_model)
        return first_dim == vector_size and stored_model == expected_model


def _faiss_artifacts_match(expected_count: int, *, embedding_model: str, vector_size: int) -> bool:
    manifest = _read_manifest(settings.retrieval_index_manifest_path)
    index_path = settings.retrieval_index_path
    if manifest is None or not index_path.exists():
        return False

    expected_manifest = {
        "chunk_count": expected_count,
        "embedding_model": embedding_model,
        "vector_size": vector_size,
        "faiss_hnsw_m": settings.faiss_hnsw_m,
        "faiss_hnsw_ef_construction": settings.faiss_hnsw_ef_construction,
    }
    for key, expected_value in expected_manifest.items():
        actual_value = manifest.get(key)
        if key == "embedding_model":
            actual_value = _normalize_embedding_model_id(str(actual_value))
            expected_value = _normalize_embedding_model_id(str(expected_value))
        if actual_value != expected_value:
            return False

    index = faiss.read_index(str(index_path))
    return index.ntotal == expected_count and index.d == vector_size


def _build_faiss_index(vectors: np.ndarray) -> faiss.IndexHNSWFlat:
    index = faiss.IndexHNSWFlat(vectors.shape[1], settings.faiss_hnsw_m, faiss.METRIC_INNER_PRODUCT)
    index.hnsw.efConstruction = settings.faiss_hnsw_ef_construction
    index.hnsw.efSearch = settings.faiss_hnsw_ef_search
    index.add(vectors)
    return index


def _rewrite_sqlite_rows(
    *,
    source_chunks,
    embedding_model: str,
    embeddings: list[list[float]] | None,
    vector_size: int,
) -> None:
    if embeddings is None:
        zero_payload = _embedding_to_bytes(tuple(np.zeros(vector_size, dtype=np.float32).tolist()))
        payloads = [zero_payload] * len(source_chunks)
    else:
        payloads = [_embedding_to_bytes(tuple(embedding)) for embedding in embeddings]

    with db_session.SessionLocal() as session:
        session.query(RetrievalChunkRecord).delete()
        session.bulk_save_objects(
            [
                RetrievalChunkRecord(
                    chunk_id=chunk.chunk_id,
                    concept_uri=chunk.concept_uri,
                    concept_kind=chunk.concept_kind,
                    source_name=chunk.source_name,
                    source_url=chunk.source_url,
                    title=chunk.title,
                    text=chunk.text,
                    chunk_type=chunk.chunk_type,
                    embedding_model=embedding_model,
                    embedding=payload,
                )
                for chunk, payload in zip(source_chunks, payloads, strict=True)
            ]
        )
        session.commit()


def build_retrieval_index(force: bool = False) -> RetrievalBuildStats:
    """Build or refresh the persisted retrieval corpus and FAISS index."""

    db_session.init_db()
    settings.retrieval_index_path.parent.mkdir(parents=True, exist_ok=True)
    source_chunks = _sorted_source_chunks()
    embedder = get_embedding_provider()
    expected_count = len(source_chunks)

    sqlite_current = _sqlite_corpus_matches(
        expected_count,
        embedding_model=embedder.model_id,
        vector_size=embedder.vector_size,
    )
    faiss_current = _faiss_artifacts_match(
        expected_count,
        embedding_model=embedder.model_id,
        vector_size=embedder.vector_size,
    )

    rebuilt_sqlite = force or not sqlite_current
    rebuilt_faiss = force or not faiss_current

    if rebuilt_sqlite:
        if rebuilt_faiss:
            embeddings = embedder.embed_documents([chunk.embedding_text for chunk in source_chunks])
            _rewrite_sqlite_rows(
                source_chunks=source_chunks,
                embedding_model=embedder.model_id,
                embeddings=embeddings,
                vector_size=embedder.vector_size,
            )
        else:
            # When the tracked FAISS artifact is already current, restoring the
            # SQLite metadata rows should not force a second full embedding pass.
            _rewrite_sqlite_rows(
                source_chunks=source_chunks,
                embedding_model=embedder.model_id,
                embeddings=None,
                vector_size=embedder.vector_size,
            )

    with db_session.SessionLocal() as session:
        rows = list(
            session.scalars(
                select(RetrievalChunkRecord).order_by(RetrievalChunkRecord.chunk_id)
            )
        )

    if rebuilt_faiss:
        vectors = np.vstack([_bytes_to_embedding(row.embedding) for row in rows]).astype(np.float32)
        index = _build_faiss_index(vectors)
        faiss.write_index(index, str(settings.retrieval_index_path))
        with settings.retrieval_index_manifest_path.open("w", encoding="utf-8") as handle:
            json.dump(
                _manifest_payload(
                    chunk_count=len(rows),
                    embedding_model=embedder.model_id,
                    vector_size=embedder.vector_size,
                ),
                handle,
                ensure_ascii=False,
                indent=2,
            )

    get_faiss_hnsw_retrieval_service.cache_clear()
    return RetrievalBuildStats(
        chunk_count=len(rows),
        embedding_model=embedder.model_id,
        vector_size=embedder.vector_size,
        index_path=settings.retrieval_index_path,
        manifest_path=settings.retrieval_index_manifest_path,
        rebuilt_sqlite=rebuilt_sqlite,
        rebuilt_faiss=rebuilt_faiss,
    )


def inspect_retrieval_artifacts() -> RetrievalArtifactStatus:
    """Return the current retrieval-artifact status without rebuilding them."""

    db_session.init_db()
    source_chunks = _sorted_source_chunks()
    embedder = get_embedding_provider()
    expected_count = len(source_chunks)

    sqlite_current = _sqlite_corpus_matches(
        expected_count,
        embedding_model=embedder.model_id,
        vector_size=embedder.vector_size,
    )
    faiss_current = _faiss_artifacts_match(
        expected_count,
        embedding_model=embedder.model_id,
        vector_size=embedder.vector_size,
    )
    return RetrievalArtifactStatus(
        chunk_count=expected_count,
        embedding_model=embedder.model_id,
        vector_size=embedder.vector_size,
        index_path=settings.retrieval_index_path,
        manifest_path=settings.retrieval_index_manifest_path,
        sqlite_current=sqlite_current,
        faiss_current=faiss_current,
    )


class FaissHnswRetrievalService:
    """Dense retrieval service backed by FAISS HNSW.

    SQLite persists the chunk text, provenance, and embedding payloads. FAISS
    builds an in-memory HNSW graph from those persisted vectors for search.
    """

    def __init__(self) -> None:
        self.embedder = get_embedding_provider()
        self._index: faiss.IndexHNSWFlat | None = None
        self._chunks: list[IndexedChunk] = []

    def search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        """Return the top-k chunks using FAISS HNSW dense retrieval."""

        self._ensure_loaded()
        if not self._chunks or self._index is None:
            return []

        return self.search_with_vector(self.embedder.embed_query(query), top_k)

    def search_with_vector(self, query_vector: list[float] | np.ndarray, top_k: int) -> list[RetrievedChunk]:
        """Return the top-k chunks for a precomputed query vector."""

        self._ensure_loaded()
        if not self._chunks or self._index is None:
            return []

        search_vector = np.asarray([query_vector], dtype=np.float32)
        scores, indices = self._index.search(search_vector, top_k)

        retrieved: list[RetrievedChunk] = []
        for score, chunk_index in zip(scores[0], indices[0], strict=True):
            if chunk_index < 0:
                continue

            chunk = self._chunks[chunk_index]
            retrieved.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    chunk_type=chunk.chunk_type,
                    source_name=chunk.source_name,
                    source_url=chunk.source_url,
                    title=chunk.title,
                    text=chunk.text,
                    score=round(float(score), 4),
                    dense_score=round(float(score), 4),
                )
            )
        return retrieved

    def benchmark_query_vectors(self, limit: int) -> list[BenchmarkQueryVector]:
        """Return representative stored vectors for pure ANN benchmarking."""

        self._ensure_loaded()
        if self._index is None or not self._chunks:
            return []

        sample_count = min(limit, len(self._chunks))
        samples: list[BenchmarkQueryVector] = []
        for index in range(sample_count):
            vector = np.asarray(self._index.reconstruct(index), dtype=np.float32)
            chunk = self._chunks[index]
            samples.append(
                BenchmarkQueryVector(
                    chunk_id=chunk.chunk_id,
                    title=chunk.title,
                    vector=vector,
                )
            )
        return samples

    def _ensure_loaded(self) -> None:
        if self._index is not None and self._chunks:
            return

        self._ensure_built_artifacts()

        with db_session.SessionLocal() as session:
            rows = list(
                session.scalars(
                    select(RetrievalChunkRecord).order_by(RetrievalChunkRecord.chunk_id)
                )
            )

        if not rows:
            self._index = None
            self._chunks = []
            return

        index = faiss.read_index(str(settings.retrieval_index_path))
        index.hnsw.efSearch = settings.faiss_hnsw_ef_search

        self._index = index
        self._chunks = [
            IndexedChunk(
                chunk_id=row.chunk_id,
                chunk_type=row.chunk_type,
                source_name=row.source_name,
                source_url=row.source_url,
                title=row.title,
                text=row.text,
            )
            for row in rows
        ]

    def _ensure_built_artifacts(self) -> None:
        db_session.init_db()
        expected_count = len(_sorted_source_chunks())
        sqlite_current = _sqlite_corpus_matches(
            expected_count,
            embedding_model=self.embedder.model_id,
            vector_size=self.embedder.vector_size,
        )
        faiss_current = _faiss_artifacts_match(
            expected_count,
            embedding_model=self.embedder.model_id,
            vector_size=self.embedder.vector_size,
        )
        if sqlite_current and faiss_current:
            return

        try:
            build_retrieval_index(force=False)
        except Exception as exc:
            raise RetrievalArtifactsError(
                "Retrieval artifacts are missing or stale, and automatic rebuild failed. "
                "Run `python -m backend.scripts.build_retrieval_index` before querying the API."
            ) from exc

        sqlite_current = _sqlite_corpus_matches(
            expected_count,
            embedding_model=self.embedder.model_id,
            vector_size=self.embedder.vector_size,
        )
        faiss_current = _faiss_artifacts_match(
            expected_count,
            embedding_model=self.embedder.model_id,
            vector_size=self.embedder.vector_size,
        )
        if sqlite_current and faiss_current:
            return

        raise RetrievalArtifactsError(
            "Retrieval artifacts are missing or stale. "
            "Run `python -m backend.scripts.build_retrieval_index` before querying the API."
        )


@lru_cache(maxsize=1)
def get_faiss_hnsw_retrieval_service() -> FaissHnswRetrievalService:
    """Return the singleton retrieval service for the current process."""

    return FaissHnswRetrievalService()
