"""Tests for deterministic career-plan fallbacks."""

from __future__ import annotations

from backend.app.services.generation.plan_guardrails import build_fallback_career_plan
from backend.app.services.generation.schemas import CareerPlanRequest, RetrievedChunk
from backend.app.services.retrieval.rag_pipeline import RetrievalContext


def test_build_fallback_career_plan_uses_grounded_role_and_skills() -> None:
    request = CareerPlanRequest(
        user_id="demo-user",
        goal="Build a transition plan into project management",
        target_role="Project Manager",
    )
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="occupation-1",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/occupation",
                title="project manager",
                text=(
                    "ESCO concept kind: occupation.\n"
                    "English label: project manager.\n"
                    "Description (EN): Coordinate project delivery.\n"
                    "Essential skills (EN): risk management, stakeholder communication, resource planning, conflict resolution."
                ),
                score=0.93,
            )
        ],
        memory_summary="No memory.",
    )

    response = build_fallback_career_plan(
        request=request,
        retrieval_context=retrieval_context,
    )

    assert response.goal == request.goal
    assert response.target_role == request.target_role
    assert len(response.steps) == 4
    assert "project manager" in response.steps[0].description.lower()
    assert "risk management" in response.steps[1].description.lower()
