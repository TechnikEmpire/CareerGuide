"""Assistant-facing endpoints."""

from __future__ import annotations

from urllib.parse import quote

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


def _build_ascii_filename_stem(target_role: str) -> str:
    """Return an ASCII-safe filename stem for Content-Disposition fallback."""

    safe_stem = "".join(
        character.lower() if character.isascii() and character.isalnum() else "-"
        for character in target_role.strip()
    ).strip("-")
    return safe_stem or "career-plan"


def _build_content_disposition(file_name: str, *, ascii_fallback: str) -> str:
    """Build a latin-1-safe attachment header with UTF-8 filename support."""

    return (
        f'attachment; filename="{ascii_fallback}"; '
        f"filename*=UTF-8''{quote(file_name)}"
    )


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
    file_name = f"{request.plan.target_role.strip() or 'career-plan'}.ics"
    ascii_file_name = f"{_build_ascii_filename_stem(request.plan.target_role)}.ics"
    return Response(
        content=ics_body,
        media_type="text/calendar",
        headers={
            "Content-Disposition": _build_content_disposition(
                file_name,
                ascii_fallback=ascii_file_name,
            ),
        },
    )
