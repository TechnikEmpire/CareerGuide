"""Basic API smoke tests."""

from __future__ import annotations

from collections.abc import Iterator
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import create_app
from backend.app.services.retrieval.embeddings import get_embedding_provider
from backend.app.services.retrieval.faiss_hnsw import build_retrieval_index
from backend.app.services.retrieval.faiss_hnsw import get_faiss_hnsw_retrieval_service
from backend.app.services.retrieval.esco_corpus import load_esco_retrieval_chunks
from backend.app.services.retrieval.rerank import get_reranker_provider
from backend.db.session import configure_database


@pytest.fixture(autouse=True, scope="module")
def use_deterministic_retrieval_backend(tmp_path_factory) -> Iterator[None]:
    """Keep the API smoke tests fast and independent of model downloads."""

    previous_provider = settings.retrieval_embedding_provider
    previous_model = settings.retrieval_embedding_model_name
    previous_vector_size = settings.retrieval_vector_size
    previous_reranker_provider = settings.retrieval_reranker_provider
    previous_index_path = settings.retrieval_index_path
    previous_manifest_path = settings.retrieval_index_manifest_path
    previous_bilingual_path = settings.esco_bilingual_concepts_path
    previous_relations_path = settings.esco_relations_path
    previous_database_url = settings.database_url

    tmp_path = tmp_path_factory.mktemp("retrieval-index")
    _write_test_esco_fixture(tmp_path)
    test_database_path = tmp_path / "careerguide-test.db"

    settings.retrieval_embedding_provider = "deterministic"
    settings.retrieval_embedding_model_name = "deterministic"
    settings.retrieval_vector_size = 256
    settings.retrieval_reranker_provider = "deterministic"
    settings.retrieval_index_path = tmp_path / "faiss_hnsw.index"
    settings.retrieval_index_manifest_path = tmp_path / "faiss_hnsw_manifest.json"
    settings.esco_bilingual_concepts_path = tmp_path / "esco_concepts.en_ru.jsonl"
    settings.esco_relations_path = tmp_path / "esco_relations.jsonl"
    settings.database_url = f"sqlite:///{test_database_path}"
    configure_database(settings.database_url)
    get_embedding_provider.cache_clear()
    get_reranker_provider.cache_clear()
    get_faiss_hnsw_retrieval_service.cache_clear()
    load_esco_retrieval_chunks.cache_clear()
    build_retrieval_index(force=True)
    try:
        yield
    finally:
        settings.retrieval_embedding_provider = previous_provider
        settings.retrieval_embedding_model_name = previous_model
        settings.retrieval_vector_size = previous_vector_size
        settings.retrieval_reranker_provider = previous_reranker_provider
        settings.retrieval_index_path = previous_index_path
        settings.retrieval_index_manifest_path = previous_manifest_path
        settings.esco_bilingual_concepts_path = previous_bilingual_path
        settings.esco_relations_path = previous_relations_path
        settings.database_url = previous_database_url
        configure_database(settings.database_url)
        get_embedding_provider.cache_clear()
        get_reranker_provider.cache_clear()
        get_faiss_hnsw_retrieval_service.cache_clear()
        load_esco_retrieval_chunks.cache_clear()


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _write_test_esco_fixture(directory: Path) -> None:
    concepts = [
        {
            "record_type": "concept",
            "dataset": "esco",
            "dataset_version": "test",
            "source_language": "en",
            "concept_kind": "occupation",
            "raw_concept_type": "Occupation",
            "concept_uri": "http://data.europa.eu/esco/occupation/software-developer",
            "status": "released",
            "source_text": {
                "preferred_label": "software developer",
                "alt_labels": ["software engineer", "application developer"],
                "hidden_labels": [],
                "description": "Software developers design, build, test, and maintain software systems.",
                "definition": None,
                "scope_note": None,
                "regulated_profession_note": None,
            },
            "translations": {
                "ru": {
                    "preferred_label": "разработчик программного обеспечения",
                    "alt_labels": ["инженер-программист"],
                    "hidden_labels": [],
                    "description": "Разработчики программного обеспечения проектируют, создают, тестируют и поддерживают программные системы.",
                    "definition": None,
                    "scope_note": None,
                    "regulated_profession_note": None,
                    "translation_meta": {"model_name": "test-fixture"},
                }
            },
            "classification": {"code": "2512", "isco_group": "2512"},
        },
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
                "description": "Data analysts examine datasets, prepare reports, and support business decision-making.",
                "definition": None,
                "scope_note": None,
                "regulated_profession_note": None,
            },
            "translations": {
                "ru": {
                    "preferred_label": "аналитик данных",
                    "alt_labels": ["специалист по аналитике"],
                    "hidden_labels": [],
                    "description": "Аналитики данных изучают наборы данных, готовят отчеты и поддерживают принятие бизнес-решений.",
                    "definition": None,
                    "scope_note": None,
                    "regulated_profession_note": None,
                    "translation_meta": {"model_name": "test-fixture"},
                }
            },
            "classification": {"code": "2421", "isco_group": "2421"},
        },
        {
            "record_type": "concept",
            "dataset": "esco",
            "dataset_version": "test",
            "source_language": "en",
            "concept_kind": "occupation",
            "raw_concept_type": "Occupation",
            "concept_uri": "http://data.europa.eu/esco/occupation/project-manager",
            "status": "released",
            "source_text": {
                "preferred_label": "project manager",
                "alt_labels": ["delivery manager"],
                "hidden_labels": [],
                "description": "Project managers coordinate planning, delivery, and stakeholder communication.",
                "definition": None,
                "scope_note": None,
                "regulated_profession_note": None,
            },
            "translations": {
                "ru": {
                    "preferred_label": "руководитель проекта",
                    "alt_labels": ["менеджер проекта"],
                    "hidden_labels": [],
                    "description": "Руководители проектов координируют планирование, поставку и взаимодействие со стейкхолдерами.",
                    "definition": None,
                    "scope_note": None,
                    "regulated_profession_note": None,
                    "translation_meta": {"model_name": "test-fixture"},
                }
            },
            "classification": {"code": "1219", "isco_group": "1219"},
        },
    ]
    _write_jsonl(directory / "esco_concepts.en_ru.jsonl", concepts)
    _write_jsonl(directory / "esco_relations.jsonl", [])


def test_healthcheck_returns_ok() -> None:
    """The backend should expose a simple health endpoint immediately."""

    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_retrieval_preview_returns_ranked_chunks() -> None:
    """The retrieval endpoint should return real ESCO-backed chunks."""

    client = TestClient(create_app())
    response = client.post("/retrieval/preview", json={"query": "software developer"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["chunks"]
    assert payload["chunks"][0]["source_name"] == "ESCO"
    assert any("software developer" in chunk["title"].lower() for chunk in payload["chunks"][:3])


def test_retrieval_preview_accepts_russian_queries() -> None:
    """The retrieval endpoint should handle Russian queries against ESCO data."""

    client = TestClient(create_app())
    response = client.post(
        "/retrieval/preview",
        json={"query": "разработчик программного обеспечения"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["chunks"]
    assert payload["chunks"][0]["source_name"] == "ESCO"
    assert any(
        "разработчик программного обеспечения" in chunk["title"].lower()
        or "software developer" in chunk["title"].lower()
        for chunk in payload["chunks"][:3]
    )
