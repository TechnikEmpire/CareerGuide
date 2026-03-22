"""Evaluation endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.services.generation.schemas import EvalRunRequest, EvalRunResponse

router = APIRouter(prefix="/eval", tags=["eval"])


@router.post("/run-scenarios", response_model=EvalRunResponse)
def run_scenarios(request: EvalRunRequest) -> EvalRunResponse:
    """Return a placeholder evaluation summary.

    The endpoint exists now so later work can attach a real evaluation harness
    without changing the external API shape.
    """

    return EvalRunResponse(
        scenario_count=len(request.scenarios),
        baseline_names=["rag_only", "rag_plus_memory"],
        status="stubbed",
        notes="The evaluation harness will be wired after retrieval and memory mature.",
    )
