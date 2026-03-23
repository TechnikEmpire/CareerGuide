"""Basic API smoke tests."""

from __future__ import annotations

from collections.abc import Iterator
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import create_app
from backend.app.services.generation.generator_client import get_generator_client
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
    previous_generation_runtime = settings.generation_runtime

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
    settings.generation_runtime = "stub"
    configure_database(settings.database_url)
    get_embedding_provider.cache_clear()
    get_reranker_provider.cache_clear()
    get_generator_client.cache_clear()
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
        settings.generation_runtime = previous_generation_runtime
        configure_database(settings.database_url)
        get_embedding_provider.cache_clear()
        get_reranker_provider.cache_clear()
        get_generator_client.cache_clear()
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


def test_answer_flow_extracts_and_persists_memory() -> None:
    """The live answer flow should persist extracted memory across requests."""

    client = TestClient(create_app())
    question = "I prefer remote work and async collaboration."

    first_response = client.post(
        "/chat/answer",
        json={"user_id": "memory-user", "question": question},
    )
    assert first_response.status_code == 200
    first_payload = first_response.json()
    assert "remote work" in first_payload["memory_summary"].lower()

    listed_memory = client.get("/memory/list", params={"user_id": "memory-user"})
    assert listed_memory.status_code == 200
    listed_payload = listed_memory.json()
    assert len(listed_payload) == 1
    assert "remote work" in listed_payload[0]["text"].lower()

    second_response = client.post(
        "/chat/answer",
        json={"user_id": "memory-user", "question": question},
    )
    assert second_response.status_code == 200
    listed_again = client.get("/memory/list", params={"user_id": "memory-user"})
    assert listed_again.status_code == 200
    assert len(listed_again.json()) == 1


def test_answer_flow_supports_hopfield_top1_mode() -> None:
    """The live answer path should expose Hopfield top-1 recall through pytest."""

    previous_mode = settings.memory_hopfield_mode
    previous_top_k = settings.memory_hopfield_top_k
    settings.memory_hopfield_mode = "top1"
    settings.memory_hopfield_top_k = 2
    try:
        client = TestClient(create_app())
        user_id = "hopfield-top1-user"

        first_memory = client.post(
            "/memory/upsert",
            json={
                "item": {
                    "id": "memory-top1-1",
                    "user_id": user_id,
                    "text": "I prefer remote work and async collaboration.",
                    "category": "user_constraint",
                    "importance": 0.9,
                    "confidence": 0.8,
                }
            },
        )
        assert first_memory.status_code == 200

        second_memory = client.post(
            "/memory/upsert",
            json={
                "item": {
                    "id": "memory-top1-2",
                    "user_id": user_id,
                    "text": "I enjoy marine biology documentaries.",
                    "category": "user_constraint",
                    "importance": 0.3,
                    "confidence": 0.7,
                }
            },
        )
        assert second_memory.status_code == 200

        response = client.post(
            "/chat/answer",
            json={"user_id": user_id, "question": "Which roles fit remote async collaboration?"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert "mode=top1" in payload["memory_summary"]
        assert "remote work" in payload["memory_summary"].lower()
        assert "rank=2" not in payload["memory_summary"]
    finally:
        settings.memory_hopfield_mode = previous_mode
        settings.memory_hopfield_top_k = previous_top_k


def test_answer_flow_supports_hopfield_topk_mode() -> None:
    """The live answer path should expose Hopfield top-k recall through pytest."""

    previous_mode = settings.memory_hopfield_mode
    previous_top_k = settings.memory_hopfield_top_k
    settings.memory_hopfield_mode = "topk"
    settings.memory_hopfield_top_k = 2
    try:
        client = TestClient(create_app())
        user_id = "hopfield-topk-user"

        for memory_id, text in [
            ("memory-topk-1", "I prefer remote work."),
            ("memory-topk-2", "I need a low-stress transition into data work."),
            ("memory-topk-3", "I enjoy marine biology documentaries."),
        ]:
            upserted = client.post(
                "/memory/upsert",
                json={
                    "item": {
                        "id": memory_id,
                        "user_id": user_id,
                        "text": text,
                        "category": "user_constraint",
                        "importance": 0.8,
                        "confidence": 0.8,
                    }
                },
            )
            assert upserted.status_code == 200

        response = client.post(
            "/chat/answer",
            json={"user_id": user_id, "question": "Which role fits remote low-stress data work?"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert "mode=topk" in payload["memory_summary"]
        assert "rank=1" in payload["memory_summary"]
        assert "rank=2" in payload["memory_summary"]
        assert "remote work" in payload["memory_summary"].lower()
        assert "low-stress transition" in payload["memory_summary"].lower()
    finally:
        settings.memory_hopfield_mode = previous_mode
        settings.memory_hopfield_top_k = previous_top_k
