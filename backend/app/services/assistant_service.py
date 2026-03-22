"""Shared assistant orchestration for API routes and evaluation scripts."""

from __future__ import annotations

from backend.app.services.generation.generator_client import get_generator_client
from backend.app.services.generation.prompt_builder import (
    build_answer_prompt,
    build_career_plan_prompt,
)
from backend.app.services.generation.schemas import (
    AnswerRequest,
    AnswerResponse,
    CareerPlanRequest,
    CareerPlanResponse,
)
from backend.app.services.memory.memory_store import default_memory_store
from backend.app.services.retrieval.rag_pipeline import build_retrieval_context
from backend.app.services.safety.safety import ensure_request_is_in_scope


def answer_question(
    request: AnswerRequest,
    *,
    top_k: int | None = None,
    use_reranker: bool | None = None,
    include_memory: bool = True,
) -> AnswerResponse:
    """Run the full grounded answer flow for a user question."""

    ensure_request_is_in_scope(request.question)
    memory_items = default_memory_store.list_items(user_id=request.user_id) if include_memory else []
    retrieval_context = build_retrieval_context(
        question=request.question,
        memory_items=memory_items,
        top_k=top_k,
        use_reranker=use_reranker,
    )
    prompt = build_answer_prompt(question=request.question, retrieval_context=retrieval_context)
    generator = get_generator_client()
    return generator.generate_answer(
        question=request.question,
        prompt=prompt,
        retrieval_context=retrieval_context,
        memory_items=memory_items,
    )


def build_career_plan(
    request: CareerPlanRequest,
    *,
    top_k: int | None = None,
    use_reranker: bool | None = None,
) -> CareerPlanResponse:
    """Run the grounded structured-plan flow."""

    ensure_request_is_in_scope(request.goal)
    retrieval_context = build_retrieval_context(
        question=request.goal,
        memory_items=[],
        top_k=top_k,
        use_reranker=use_reranker,
    )
    prompt = build_career_plan_prompt(
        goal=request.goal,
        target_role=request.target_role,
        retrieval_context=retrieval_context,
    )
    generator = get_generator_client()
    return generator.generate_career_plan(
        request=request,
        prompt=prompt,
        retrieval_context=retrieval_context,
    )
