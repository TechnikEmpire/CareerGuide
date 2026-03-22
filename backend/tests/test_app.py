"""Basic API smoke tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import create_app
from backend.app.services.retrieval.embeddings import get_embedding_provider
from backend.app.services.retrieval.faiss_hnsw import get_faiss_hnsw_retrieval_service
from backend.app.services.retrieval.rerank import get_reranker_provider


@pytest.fixture(autouse=True)
def use_deterministic_retrieval_backend() -> Iterator[None]:
    """Keep the API smoke tests fast and independent of model downloads."""

    previous_provider = settings.retrieval_embedding_provider
    previous_model = settings.retrieval_embedding_model_name
    previous_vector_size = settings.retrieval_vector_size
    previous_reranker_provider = settings.retrieval_reranker_provider

    settings.retrieval_embedding_provider = "deterministic"
    settings.retrieval_embedding_model_name = "deterministic"
    settings.retrieval_vector_size = 256
    settings.retrieval_reranker_provider = "deterministic"
    get_embedding_provider.cache_clear()
    get_reranker_provider.cache_clear()
    get_faiss_hnsw_retrieval_service.cache_clear()
    try:
        yield
    finally:
        settings.retrieval_embedding_provider = previous_provider
        settings.retrieval_embedding_model_name = previous_model
        settings.retrieval_vector_size = previous_vector_size
        settings.retrieval_reranker_provider = previous_reranker_provider
        get_embedding_provider.cache_clear()
        get_reranker_provider.cache_clear()
        get_faiss_hnsw_retrieval_service.cache_clear()


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
