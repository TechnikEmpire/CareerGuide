"""Assistant-facing endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.services.assistant_service import (
    answer_question as generate_answer_response,
    build_career_plan as generate_career_plan_response,
)
from backend.app.services.generation.generator_client import GenerationClientError
from backend.app.services.generation.schemas import AnswerRequest, AnswerResponse, CareerPlanRequest, CareerPlanResponse
from backend.app.services.retrieval.faiss_hnsw import RetrievalArtifactsError

router = APIRouter(prefix="", tags=["assistant"])


@router.post("/chat/answer", response_model=AnswerResponse)
def answer_question(request: AnswerRequest) -> AnswerResponse:
    """Return a grounded answer using the configured generation backend."""

    try:
        return generate_answer_response(request)
    except (GenerationClientError, RetrievalArtifactsError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/career/plan", response_model=CareerPlanResponse)
def build_career_plan(request: CareerPlanRequest) -> CareerPlanResponse:
    """Return a grounded structured plan using the configured generation backend."""

    try:
        return generate_career_plan_response(request)
    except (GenerationClientError, RetrievalArtifactsError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
