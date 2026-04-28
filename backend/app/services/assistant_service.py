"""Shared assistant orchestration for API routes and evaluation scripts."""

from __future__ import annotations

from backend.app.services.generation.generator_client import get_generator_client
from backend.app.services.generation.answer_guardrails import (
    ensure_grounded_plan_support,
    maybe_build_guardrailed_answer,
)
from backend.app.services.generation.prompt_builder import (
    build_answer_prompt,
    build_career_plan_prompt,
)
from backend.app.services.generation.schemas import (
    AnswerRequest,
    AnswerResponse,
    CareerPlanRequest,
    CareerPlanResponse,
    MemoryItemPayload,
)
from backend.app.services.memory.memory_consolidate import consolidate_memory_items
from backend.app.services.memory.memory_consolidate import normalize_memory_text
from backend.app.services.memory.memory_extract import extract_candidate_memory_items
from backend.app.services.memory.hopfield_memory import summarize_memory_for_prompt
from backend.app.services.memory.memory_store import default_memory_store
from backend.app.services.retrieval.rag_pipeline import build_retrieval_context
from backend.app.services.safety.safety import ensure_request_is_in_scope


def _extract_request_memory_candidates(user_id: str, text: str) -> list[MemoryItemPayload]:
    """Extract request-local memory candidates without persisting them yet."""

    return consolidate_memory_items(extract_candidate_memory_items(user_id=user_id, text=text))


def _persist_memory_candidates(candidates: list[MemoryItemPayload]) -> None:
    """Persist already-approved memory candidates."""

    for candidate in candidates:
        default_memory_store.upsert_item(candidate)


def _merge_memory_preview(
    stored_items: list[MemoryItemPayload],
    candidate_items: list[MemoryItemPayload],
) -> list[MemoryItemPayload]:
    """Preview post-write memory state without mutating the persistent store."""

    merged: dict[str, MemoryItemPayload] = {}
    ordered_keys: list[str] = []

    def record(item: MemoryItemPayload) -> None:
        normalized_text = normalize_memory_text(item.text)
        if not normalized_text:
            return

        existing = merged.get(normalized_text)
        if existing is None:
            merged[normalized_text] = item
            ordered_keys.append(normalized_text)
            return

        merged[normalized_text] = existing.model_copy(
            update={
                "text": item.text.strip(),
                "category": item.category,
                "importance": max(existing.importance, item.importance),
                "confidence": max(existing.confidence, item.confidence),
            }
        )

    for item in stored_items:
        record(item)
    for item in candidate_items:
        record(item)

    return [merged[key] for key in ordered_keys]


def answer_question(
    request: AnswerRequest,
    *,
    top_k: int | None = None,
    use_reranker: bool | None = None,
    include_memory: bool = True,
) -> AnswerResponse:
    """Run the full grounded answer flow for a user question."""

    ensure_request_is_in_scope(request.question)
    if include_memory:
        pending_memory_candidates = _extract_request_memory_candidates(
            user_id=request.user_id,
            text=request.question,
        )
        stored_memory_items = default_memory_store.list_items(user_id=request.user_id)
        memory_items = _merge_memory_preview(stored_memory_items, pending_memory_candidates)
    else:
        pending_memory_candidates = []
        stored_memory_items = []
        memory_items = []
    retrieval_context = build_retrieval_context(
        question=request.question,
        memory_items=memory_items,
        top_k=top_k,
        use_reranker=use_reranker,
    )
    prompt = build_answer_prompt(question=request.question, retrieval_context=retrieval_context)
    guardrailed_answer = maybe_build_guardrailed_answer(
        question=request.question,
        retrieval_context=retrieval_context,
    )
    if guardrailed_answer is not None:
        should_persist_guardrailed_memory = guardrailed_answer.response_kind == "answer"
        response_memory_summary = (
            summarize_memory_for_prompt(question=request.question, memory_items=stored_memory_items)
            if guardrailed_answer.response_kind == "refusal"
            else retrieval_context.memory_summary
        )
        if include_memory and should_persist_guardrailed_memory:
            _persist_memory_candidates(pending_memory_candidates)
        return AnswerResponse(
            answer=guardrailed_answer.text,
            citations=guardrailed_answer.citations,
            prompt_preview=prompt,
            memory_summary=response_memory_summary,
            response_kind=guardrailed_answer.response_kind,
        )
    generator = get_generator_client()
    response = generator.generate_answer(
        question=request.question,
        prompt=prompt,
        retrieval_context=retrieval_context,
        memory_items=memory_items,
    )
    if include_memory:
        _persist_memory_candidates(pending_memory_candidates)
    return response


def build_career_plan(
    request: CareerPlanRequest,
    *,
    top_k: int | None = None,
    use_reranker: bool | None = None,
) -> CareerPlanResponse:
    """Run the grounded structured-plan flow."""

    ensure_request_is_in_scope(request.goal)
    retrieval_context = build_retrieval_context(
        question=f"{request.goal}\n{request.target_role}",
        memory_items=[],
        top_k=top_k,
        use_reranker=use_reranker,
    )
    ensure_grounded_plan_support(
        goal=request.goal,
        target_role=request.target_role,
        retrieval_context=retrieval_context,
    )
    prompt = build_career_plan_prompt(
        goal=request.goal,
        target_role=request.target_role,
        study_preferences=request.study_preferences,
        retrieval_context=retrieval_context,
    )
    generator = get_generator_client()
    return generator.generate_career_plan(
        request=request,
        prompt=prompt,
        retrieval_context=retrieval_context,
    )
