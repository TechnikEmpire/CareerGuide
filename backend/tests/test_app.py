"""Basic API smoke tests."""

from __future__ import annotations

from collections.abc import Iterator
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import create_app
from backend.app.services.assistant_service import answer_question as run_answer_question
from backend.app.services.generation.generator_client import get_generator_client
from backend.app.services.generation.schemas import AnswerRequest
from backend.app.services.memory.memory_store import default_memory_store
from backend.app.services.retrieval.embeddings import get_embedding_provider
from backend.app.services.retrieval.faiss_hnsw import (
    RetrievalArtifactsError,
    build_retrieval_index,
    get_faiss_hnsw_retrieval_service,
)
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


def test_healthcheck_includes_local_frontend_cors_headers() -> None:
    """The backend should allow the local frontend dev server to call the API."""

    client = TestClient(create_app())
    response = client.options(
        "/health",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_frontend_dist_root_serves_index_html(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The backend should serve the built SPA shell when a frontend dist exists."""

    dist_path = tmp_path / "frontend-dist"
    assets_path = dist_path / "assets"
    assets_path.mkdir(parents=True)
    (dist_path / "index.html").write_text("<html><body>CareerGuide SPA</body></html>", encoding="utf-8")
    (assets_path / "app.js").write_text("console.log('career');", encoding="utf-8")

    monkeypatch.setattr(settings, "frontend_dist_path", dist_path)
    monkeypatch.setattr(settings, "serve_frontend", True)

    client = TestClient(create_app())

    index_response = client.get("/")
    asset_response = client.get("/assets/app.js")

    assert index_response.status_code == 200
    assert "CareerGuide SPA" in index_response.text
    assert asset_response.status_code == 200
    assert "console.log('career');" in asset_response.text


def test_frontend_dist_does_not_shadow_reserved_api_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The SPA fallback should not silently swallow missing API-like paths."""

    dist_path = tmp_path / "frontend-dist"
    dist_path.mkdir(parents=True)
    (dist_path / "index.html").write_text("<html><body>CareerGuide SPA</body></html>", encoding="utf-8")

    monkeypatch.setattr(settings, "frontend_dist_path", dist_path)
    monkeypatch.setattr(settings, "serve_frontend", True)

    client = TestClient(create_app())
    response = client.get("/chat/not-a-real-route")

    assert response.status_code == 404


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
    question = "I prefer remote work and async collaboration. What skills do data analysts need?"

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
    assert listed_payload[0]["text"] == "I prefer remote work and async collaboration."

    second_response = client.post(
        "/chat/answer",
        json={"user_id": "memory-user", "question": question},
    )
    assert second_response.status_code == 200
    listed_again = client.get("/memory/list", params={"user_id": "memory-user"})
    assert listed_again.status_code == 200
    assert len(listed_again.json()) == 1


def test_answer_flow_extracts_and_persists_russian_memory() -> None:
    """The live answer flow should persist Russian sentence-level memory too."""

    client = TestClient(create_app())
    question = "Я предпочитаю удаленную работу и спокойный график. Какие навыки нужны для аналитики данных?"

    response = client.post(
        "/chat/answer",
        json={"user_id": "memory-user-ru", "question": question},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "удаленную работу" in payload["memory_summary"].lower()

    listed_memory = client.get("/memory/list", params={"user_id": "memory-user-ru"})
    assert listed_memory.status_code == 200
    listed_payload = listed_memory.json()
    assert len(listed_payload) == 1
    assert listed_payload[0]["text"] == "Я предпочитаю удаленную работу и спокойный график."


def test_answer_flow_dedupes_duplicate_memory_sentences_within_one_request() -> None:
    """One user turn should not persist the same memory twice."""

    client = TestClient(create_app())
    question = "I prefer remote work. I prefer remote work."

    response = client.post(
        "/chat/answer",
        json={"user_id": "memory-user-dup", "question": question},
    )
    assert response.status_code == 200

    listed_memory = client.get("/memory/list", params={"user_id": "memory-user-dup"})
    assert listed_memory.status_code == 200
    listed_payload = listed_memory.json()
    assert len(listed_payload) == 1
    assert listed_payload[0]["text"] == "I prefer remote work."


def test_memory_endpoint_deletes_one_persisted_item() -> None:
    """The memory API should delete a stored item for the active user only."""

    client = TestClient(create_app())
    user_id = "memory-delete-user"

    upserted = client.post(
        "/memory/upsert",
        json={
            "item": {
                "id": "memory-delete-1",
                "user_id": user_id,
                "text": "I prefer remote work.",
                "category": "user_constraint",
                "importance": 0.8,
                "confidence": 0.9,
            }
        },
    )
    assert upserted.status_code == 200

    deleted = client.delete("/memory/memory-delete-1", params={"user_id": user_id})
    assert deleted.status_code == 200
    assert deleted.json()["id"] == "memory-delete-1"

    listed_memory = client.get("/memory/list", params={"user_id": user_id})
    assert listed_memory.status_code == 200
    assert listed_memory.json() == []


def test_memory_endpoint_returns_404_for_wrong_user_delete() -> None:
    """Deletion should not expose or remove another user's memory item."""

    client = TestClient(create_app())
    owner_user_id = "memory-delete-owner"

    upserted = client.post(
        "/memory/upsert",
        json={
            "item": {
                "id": "memory-delete-protected",
                "user_id": owner_user_id,
                "text": "I prefer async collaboration.",
                "category": "user_constraint",
                "importance": 0.8,
                "confidence": 0.9,
            }
        },
    )
    assert upserted.status_code == 200

    wrong_delete = client.delete("/memory/memory-delete-protected", params={"user_id": "intruder"})
    assert wrong_delete.status_code == 404

    listed_memory = client.get("/memory/list", params={"user_id": owner_user_id})
    assert listed_memory.status_code == 200
    assert len(listed_memory.json()) == 1


def test_answer_service_can_run_without_memory_and_does_not_persist() -> None:
    """The core answer service should support a RAG-only path without memory writes."""

    response = run_answer_question(
        AnswerRequest(
            user_id="rag-only-user",
            question="I prefer remote work and async collaboration.",
        ),
        include_memory=False,
    )

    assert response.memory_summary == "No stored user memory yet."
    assert default_memory_store.list_items(user_id="rag-only-user") == []


def test_answer_flow_handles_external_resource_requests_honestly() -> None:
    """The answer path should not hallucinate external resources from ESCO-only evidence."""

    client = TestClient(create_app())
    response = client.post(
        "/chat/answer",
        json={
            "user_id": "resource-user",
            "question": "Do you have any external resources you could point me to, to learn more about these?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "external courses or websites" in payload["answer"]
    assert "study plan or a search checklist" in payload["answer"]
    assert "Scaffold answer" not in payload["answer"]


def test_answer_flow_refuses_unsupported_explicit_role_request() -> None:
    """Explicit unsupported role requests should return a grounded refusal, not fake coaching."""

    client = TestClient(create_app())
    user_id = "unsupported-role-user"
    response = client.post(
        "/chat/answer",
        json={"user_id": user_id, "question": "I prefer remote work. How do I become a stripper?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["response_kind"] == "refusal"
    assert "can’t provide grounded career guidance" in payload["answer"]
    assert payload["citations"] == []
    listed_memory = client.get("/memory/list", params={"user_id": user_id})
    assert listed_memory.status_code == 200
    assert listed_memory.json() == []


def test_answer_flow_blocks_exploitative_illegal_request() -> None:
    """Exploitative or illegal work requests should fail through the scope gate."""

    client = TestClient(create_app())
    user_id = "blocked-user"
    response = client.post(
        "/chat/answer",
        json={"user_id": user_id, "question": "I prefer remote work. How do I become a pimp?"},
    )

    assert response.status_code == 400
    assert "exploitative, coercive, or illegal work" in response.json()["detail"]
    listed_memory = client.get("/memory/list", params={"user_id": user_id})
    assert listed_memory.status_code == 200
    assert listed_memory.json() == []


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


def test_career_plan_returns_503_when_retrieval_artifacts_are_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retrieval artifact failures should surface as service errors, not raw 500s."""

    from backend.app.api import assistant as assistant_api

    def fail(_request):
        raise RetrievalArtifactsError("Retrieval artifacts are missing or stale.")

    monkeypatch.setattr(assistant_api, "generate_career_plan_response", fail)

    client = TestClient(create_app())
    response = client.post(
        "/career/plan",
        json={
            "user_id": "memory-user",
            "goal": "Build a transition plan into data analytics",
            "target_role": "Data Analyst",
        },
    )

    assert response.status_code == 503
    assert "Retrieval artifacts are missing or stale." in response.json()["detail"]


def test_career_plan_returns_400_for_unsupported_target_role() -> None:
    """Plan building should refuse unsupported target roles instead of inventing a plan."""

    client = TestClient(create_app())
    response = client.post(
        "/career/plan",
        json={
            "user_id": "unsupported-plan-user",
            "goal": "Build a transition plan into stripping",
            "target_role": "Stripper",
        },
    )

    assert response.status_code == 400
    assert "does not show a strong enough match" in response.json()["detail"]


def test_career_plan_returns_schedule_ready_fields() -> None:
    """The plan endpoint should return workload and calendar data for export/UI rendering."""

    client = TestClient(create_app())
    response = client.post(
        "/career/plan",
        json={
            "user_id": "plan-user",
            "goal": "Build a transition plan into data analytics",
            "target_role": "Data Analyst",
            "study_preferences": {
                "study_start_date": "2026-04-06",
                "preferred_study_time": "evening",
                "study_frequency_per_week": 3,
                "session_duration_minutes": 90,
                "timezone": "America/St_Johns",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["workload_level"] in {"low", "medium", "high"}
    assert payload["estimated_weeks"] >= 1
    assert payload["study_preferences"]["preferred_study_time"] == "evening"
    assert payload["calendar_events"]


def test_career_plan_export_ics_returns_calendar_file() -> None:
    """The plan export endpoint should return a downloadable ICS file."""

    client = TestClient(create_app())
    plan_response = client.post(
        "/career/plan",
        json={
            "user_id": "plan-export-user",
            "goal": "Build a transition plan into project management",
            "target_role": "Project Manager",
            "study_preferences": {
                "study_start_date": "2026-04-06",
                "preferred_study_time": "evening",
                "study_frequency_per_week": 2,
                "session_duration_minutes": 90,
                "timezone": "America/St_Johns",
            },
        },
    )
    assert plan_response.status_code == 200

    export_response = client.post(
        "/career/plan/export-ics",
        json={
            "user_id": "plan-export-user",
            "plan": plan_response.json(),
        },
    )

    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith("text/calendar")
    assert "filename=" in export_response.headers["content-disposition"]
    assert "BEGIN:VCALENDAR" in export_response.text
    assert "BEGIN:VEVENT" in export_response.text


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
