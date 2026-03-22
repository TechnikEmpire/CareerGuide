"""Basic API smoke tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_healthcheck_returns_ok() -> None:
    """The backend should expose a simple health endpoint immediately."""

    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_retrieval_preview_returns_ranked_chunks() -> None:
    """The scaffold retrieval endpoint should return at least one chunk."""

    client = TestClient(create_app())
    response = client.post("/retrieval/preview", json={"query": "career planning for software work"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["chunks"]


def test_retrieval_preview_accepts_russian_queries() -> None:
    """The scaffold should handle a basic Russian retrieval query."""

    client = TestClient(create_app())
    response = client.post(
        "/retrieval/preview",
        json={"query": "хочу роль в разработке программного обеспечения"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["chunks"]
    assert payload["chunks"][0]["title"] == "Software Developers"
