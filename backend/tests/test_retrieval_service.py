"""Focused tests for retrieval-service artifact repair behavior."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.app.config import settings
from backend.app.services.retrieval.embeddings import get_embedding_provider
from backend.app.services.retrieval.esco_corpus import load_esco_retrieval_chunks
from backend.app.services.retrieval import faiss_hnsw
from backend.db import session as db_session
from backend.db.models import RetrievalChunkRecord


def test_retrieval_service_rebuilds_stale_artifacts_before_failing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One stale-artifact hit should trigger a lazy rebuild attempt."""

    monkeypatch.setattr(faiss_hnsw.db_session, "init_db", lambda: None)
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

    monkeypatch.setattr(faiss_hnsw.db_session, "init_db", lambda: None)
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


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _write_minimal_esco_fixture(directory: Path) -> None:
    concepts = [
        {
            "record_type": "concept",
            "dataset": "esco",
            "dataset_version": "test",
            "source_language": "en",
            "concept_kind": "occupation",
            "raw_concept_type": "Occupation",
            "concept_uri": "http://data.europa.eu/esco/occupation/data-analyst",
            "status": "released",
            "source_text": {
                "preferred_label": "data analyst",
                "alt_labels": ["analytics specialist"],
                "hidden_labels": [],
                "description": "Data analysts examine datasets and support business decisions.",
                "definition": None,
                "scope_note": None,
                "regulated_profession_note": None,
            },
            "translations": {
                "ru": {
                    "preferred_label": "аналитик данных",
                    "alt_labels": ["специалист по аналитике"],
                    "hidden_labels": [],
                    "description": "Аналитики данных изучают наборы данных и поддерживают бизнес-решения.",
                    "definition": None,
                    "scope_note": None,
                    "regulated_profession_note": None,
                    "translation_meta": {"model_name": "test-fixture"},
                }
            },
            "classification": {"code": "2421", "isco_group": "2421"},
        }
    ]
    _write_jsonl(directory / "esco_concepts.en_ru.jsonl", concepts)
    _write_jsonl(directory / "esco_relations.jsonl", [])


def test_build_retrieval_index_uses_current_reconfigured_database(tmp_path: Path) -> None:
    """Retrieval builds should write rows into the current configured SQLite DB."""

    previous_provider = settings.retrieval_embedding_provider
    previous_model = settings.retrieval_embedding_model_name
    previous_vector_size = settings.retrieval_vector_size
    previous_index_path = settings.retrieval_index_path
    previous_manifest_path = settings.retrieval_index_manifest_path
    previous_bilingual_path = settings.esco_bilingual_concepts_path
    previous_relations_path = settings.esco_relations_path
    previous_database_url = settings.database_url

    test_database_url = f"sqlite:///{tmp_path / 'retrieval-service-test.db'}"
    _write_minimal_esco_fixture(tmp_path)

    settings.retrieval_embedding_provider = "deterministic"
    settings.retrieval_embedding_model_name = "deterministic"
    settings.retrieval_vector_size = 64
    settings.retrieval_index_path = tmp_path / "faiss_hnsw.index"
    settings.retrieval_index_manifest_path = tmp_path / "faiss_hnsw_manifest.json"
    settings.esco_bilingual_concepts_path = tmp_path / "esco_concepts.en_ru.jsonl"
    settings.esco_relations_path = tmp_path / "esco_relations.jsonl"
    settings.database_url = test_database_url

    db_session.configure_database(test_database_url)
    get_embedding_provider.cache_clear()
    load_esco_retrieval_chunks.cache_clear()
    faiss_hnsw.get_faiss_hnsw_retrieval_service.cache_clear()

    try:
        faiss_hnsw.build_retrieval_index(force=True)
        with db_session.SessionLocal() as session:
            stored_rows = session.query(RetrievalChunkRecord).count()
        assert stored_rows == 1
    finally:
        settings.retrieval_embedding_provider = previous_provider
        settings.retrieval_embedding_model_name = previous_model
        settings.retrieval_vector_size = previous_vector_size
        settings.retrieval_index_path = previous_index_path
        settings.retrieval_index_manifest_path = previous_manifest_path
        settings.esco_bilingual_concepts_path = previous_bilingual_path
        settings.esco_relations_path = previous_relations_path
        settings.database_url = previous_database_url
        db_session.configure_database(previous_database_url)
        get_embedding_provider.cache_clear()
        load_esco_retrieval_chunks.cache_clear()
        faiss_hnsw.get_faiss_hnsw_retrieval_service.cache_clear()
