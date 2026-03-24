"""Assistant-facing endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.app.services.assistant_service import (
    answer_question as generate_answer_response,
    build_career_plan as generate_career_plan_response,
)
from backend.app.services.generation.answer_guardrails import UnsupportedGuidanceRequestError
from backend.app.services.generation.generator_client import GenerationClientError
from backend.app.services.generation.plan_calendar import build_plan_ics
from backend.app.services.generation.schemas import (
    AnswerRequest,
    AnswerResponse,
    CareerPlanExportRequest,
    CareerPlanRequest,
    CareerPlanResponse,
)
from backend.app.services.retrieval.faiss_hnsw import RetrievalArtifactsError

router = APIRouter(prefix="", tags=["assistant"])


@router.post("/chat/answer", response_model=AnswerResponse)
def answer_question(request: AnswerRequest) -> AnswerResponse:
    """Return a grounded answer using the configured generation backend."""

    try:
        return generate_answer_response(request)
    except UnsupportedGuidanceRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (GenerationClientError, RetrievalArtifactsError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/career/plan", response_model=CareerPlanResponse)
def build_career_plan(request: CareerPlanRequest) -> CareerPlanResponse:
    """Return a grounded structured plan using the configured generation backend."""

    try:
        return generate_career_plan_response(request)
    except UnsupportedGuidanceRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (GenerationClientError, RetrievalArtifactsError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/career/plan/export-ics")
def export_career_plan_ics(request: CareerPlanExportRequest) -> Response:
    """Export a saved grounded plan as an iCalendar file."""

    ics_body = build_plan_ics(request.plan, user_id=request.user_id)
    safe_role = "".join(character if character.isalnum() else "-" for character in request.plan.target_role).strip("-")
    file_stem = safe_role or "career-plan"
    return Response(
        content=ics_body,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f'attachment; filename="{file_stem}.ics"',
        },
    )
