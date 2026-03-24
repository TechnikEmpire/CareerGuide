"""Focused tests for retrieval-service artifact repair behavior."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.app.services.retrieval import faiss_hnsw


def test_retrieval_service_rebuilds_stale_artifacts_before_failing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One stale-artifact hit should trigger a lazy rebuild attempt."""

    monkeypatch.setattr(faiss_hnsw, "init_db", lambda: None)
    monkeypatch.setattr(faiss_hnsw, "_sorted_source_chunks", lambda: [SimpleNamespace(chunk_id="chunk-1")])
    monkeypatch.setattr(
        faiss_hnsw,
        "get_embedding_provider",
        lambda: SimpleNamespace(model_id="deterministic", vector_size=8),
    )

    sqlite_checks = iter([False, True])
    faiss_checks = iter([False, True])
    monkeypatch.setattr(
        faiss_hnsw,
        "_sqlite_corpus_matches",
        lambda expected_count, *, embedding_model, vector_size: next(sqlite_checks),
    )
    monkeypatch.setattr(
        faiss_hnsw,
        "_faiss_artifacts_match",
        lambda expected_count, *, embedding_model, vector_size: next(faiss_checks),
    )

    rebuild_calls: list[bool] = []
    monkeypatch.setattr(
        faiss_hnsw,
        "build_retrieval_index",
        lambda force=False: rebuild_calls.append(force),
    )

    service = faiss_hnsw.FaissHnswRetrievalService()
    service._ensure_built_artifacts()

    assert rebuild_calls == [False]


def test_retrieval_service_raises_clear_error_when_auto_rebuild_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Automatic artifact repair failures should still surface a controlled error."""

    monkeypatch.setattr(faiss_hnsw, "init_db", lambda: None)
    monkeypatch.setattr(faiss_hnsw, "_sorted_source_chunks", lambda: [SimpleNamespace(chunk_id="chunk-1")])
    monkeypatch.setattr(
        faiss_hnsw,
        "get_embedding_provider",
        lambda: SimpleNamespace(model_id="deterministic", vector_size=8),
    )
    monkeypatch.setattr(
        faiss_hnsw,
        "_sqlite_corpus_matches",
        lambda expected_count, *, embedding_model, vector_size: False,
    )
    monkeypatch.setattr(
        faiss_hnsw,
        "_faiss_artifacts_match",
        lambda expected_count, *, embedding_model, vector_size: False,
    )

    def fail_rebuild(force: bool = False) -> None:
        raise RuntimeError("broken index state")

    monkeypatch.setattr(faiss_hnsw, "build_retrieval_index", fail_rebuild)

    service = faiss_hnsw.FaissHnswRetrievalService()

    with pytest.raises(faiss_hnsw.RetrievalArtifactsError) as exc_info:
        service._ensure_built_artifacts()

    assert "automatic rebuild failed" in str(exc_info.value).lower()
