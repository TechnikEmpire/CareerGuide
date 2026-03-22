"""Assistant-facing endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.services.generation.generator_client import StubGeneratorClient
from backend.app.services.generation.prompt_builder import build_answer_prompt
from backend.app.services.generation.schemas import (
    AnswerRequest,
    AnswerResponse,
    CareerPlanRequest,
    CareerPlanResponse,
)
from backend.app.services.memory.memory_store import default_memory_store
from backend.app.services.retrieval.rag_pipeline import build_retrieval_context
from backend.app.services.safety.safety import ensure_request_is_in_scope

router = APIRouter(prefix="", tags=["assistant"])

generator = StubGeneratorClient()


@router.post("/chat/answer", response_model=AnswerResponse)
def answer_question(request: AnswerRequest) -> AnswerResponse:
    """Return a grounded answer using the current scaffold pipeline."""

    ensure_request_is_in_scope(request.question)
    memory_items = default_memory_store.list_items(user_id=request.user_id)
    retrieval_context = build_retrieval_context(question=request.question, memory_items=memory_items)
    prompt = build_answer_prompt(question=request.question, retrieval_context=retrieval_context)
    return generator.generate_answer(
        question=request.question,
        prompt=prompt,
        retrieval_context=retrieval_context,
        memory_items=memory_items,
    )


@router.post("/career/plan", response_model=CareerPlanResponse)
def build_career_plan(request: CareerPlanRequest) -> CareerPlanResponse:
    """Return a simple structured plan response.

    This is intentionally bounded and transparent. Early in the project, it is
    better to return a simple inspectable structure than to hide logic behind a
    larger model call before the grounding pipeline is ready.
    """

    ensure_request_is_in_scope(request.goal)
    retrieval_context = build_retrieval_context(question=request.goal, memory_items=[])
    return generator.generate_career_plan(request=request, retrieval_context=retrieval_context)
