"""FAISS HNSW retrieval over SQLite-persisted chunk embeddings."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import faiss
import numpy as np
from sqlalchemy import select

from backend.app.config import settings
from backend.app.services.generation.schemas import RetrievedChunk
from backend.app.services.retrieval.embeddings import get_embedding_provider
from backend.app.services.retrieval.esco_corpus import load_esco_retrieval_chunks
from backend.db.models import RetrievalChunkRecord
from backend.db.session import SessionLocal, init_db


@dataclass(frozen=True)
class IndexedChunk:
    """In-memory retrieval chunk with its persisted identity."""

    chunk_id: str
    source_name: str
    source_url: str
    title: str
    text: str


def _embedding_to_bytes(values: tuple[float, ...]) -> bytes:
    return np.asarray(values, dtype=np.float32).tobytes()


def _bytes_to_embedding(payload: bytes) -> np.ndarray:
    return np.frombuffer(payload, dtype=np.float32)


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

        query_vector = np.asarray([self.embedder.embed_query(query)], dtype=np.float32)
        scores, indices = self._index.search(query_vector, top_k)

        retrieved: list[RetrievedChunk] = []
        for score, chunk_index in zip(scores[0], indices[0], strict=True):
            if chunk_index < 0:
                continue

            chunk = self._chunks[chunk_index]
            retrieved.append(
                RetrievedChunk(
                    source_name=chunk.source_name,
                    source_url=chunk.source_url,
                    title=chunk.title,
                    text=chunk.text,
                    score=round(float(score), 4),
                    dense_score=round(float(score), 4),
                )
            )
        return retrieved

    def _ensure_loaded(self) -> None:
        if self._index is not None and self._chunks:
            return

        self._ensure_sqlite_corpus()

        with SessionLocal() as session:
            rows = list(
                session.scalars(
                    select(RetrievalChunkRecord).order_by(RetrievalChunkRecord.chunk_id)
                )
            )

        if not rows:
            self._index = None
            self._chunks = []
            return

        vectors = np.vstack([_bytes_to_embedding(row.embedding) for row in rows]).astype(np.float32)
        index = faiss.IndexHNSWFlat(self.embedder.vector_size, settings.faiss_hnsw_m, faiss.METRIC_INNER_PRODUCT)
        index.hnsw.efConstruction = settings.faiss_hnsw_ef_construction
        index.hnsw.efSearch = settings.faiss_hnsw_ef_search
        index.add(vectors)

        self._index = index
        self._chunks = [
            IndexedChunk(
                chunk_id=row.chunk_id,
                source_name=row.source_name,
                source_url=row.source_url,
                title=row.title,
                text=row.text,
            )
            for row in rows
        ]

    def _ensure_sqlite_corpus(self) -> None:
        init_db()
        source_chunks = load_esco_retrieval_chunks()
        expected_count = len(source_chunks)

        with SessionLocal() as session:
            existing_count = session.query(RetrievalChunkRecord).count()
            first_row = session.scalars(select(RetrievalChunkRecord).limit(1)).first()
            first_dim = len(_bytes_to_embedding(first_row.embedding)) if first_row else 0
            if (
                existing_count == expected_count
                and existing_count > 0
                and first_dim == self.embedder.vector_size
                and first_row.embedding_model == self.embedder.model_id
            ):
                return

            embeddings = self.embedder.embed_documents([chunk.embedding_text for chunk in source_chunks])
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
                        embedding_model=self.embedder.model_id,
                        embedding=_embedding_to_bytes(tuple(embedding)),
                    )
                    for chunk, embedding in zip(source_chunks, embeddings, strict=True)
                ]
            )
            session.commit()


@lru_cache(maxsize=1)
def get_faiss_hnsw_retrieval_service() -> FaissHnswRetrievalService:
    """Return the singleton retrieval service for the current process."""

    return FaissHnswRetrievalService()
