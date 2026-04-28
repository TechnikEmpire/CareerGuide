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
from backend.app.services.generation.plan_handoff import (
    answer_pending_plan_handoff,
    maybe_offer_plan_handoff,
)
from backend.app.services.generation.plan_adjustments import (
    build_lower_intensity_memory,
    maybe_build_plan_update,
)
from backend.app.services.generation.role_matcher import (
    extract_target_role_phrase,
    find_supported_occupation,
    useful_occupations,
)
from backend.app.services.generation.schemas import (
    AnswerRequest,
    AnswerResponse,
    CareerPlanRequest,
    CareerPlanResponse,
    MemoryItemPayload,
    RetrievedChunk,
)
from backend.app.services.generation.skill_enrichment import (
    SkillEnrichment,
    fallback_skill_enrichment,
    language_code_for_text,
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

    lower_intensity_memory = build_lower_intensity_memory(user_id, text)
    if lower_intensity_memory is not None:
        return [lower_intensity_memory]

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


def _skill_enrichment_for_request(
    *,
    text: str,
    target_role: str,
    retrieval_context,
    user_goal: str,
) -> SkillEnrichment | None:
    """Build model skill enrichment only when there is a supported occupation."""

    occupation: RetrievedChunk | None = find_supported_occupation(text, retrieval_context)
    if occupation is None:
        if extract_target_role_phrase(text):
            return None
        occupations = useful_occupations(retrieval_context)
        occupation = occupations[0] if len(occupations) == 1 else None
    if occupation is None:
        return None

    language_code = language_code_for_text(text)
    generator = get_generator_client()
    try:
        return generator.generate_skill_enrichment(
            occupation=occupation,
            target_role=target_role,
            language_code=language_code,
            user_goal=user_goal,
        )
    except (RuntimeError, TypeError, ValueError):
        return fallback_skill_enrichment(
            occupation=occupation,
            language_code=language_code,
            target_role=target_role,
        )


def answer_question(
    request: AnswerRequest,
    *,
    top_k: int | None = None,
    use_reranker: bool | None = None,
    include_memory: bool = True,
) -> AnswerResponse:
    """Run the full grounded answer flow for a user question."""

    ensure_request_is_in_scope(request.question)
    pending_handoff_answer = answer_pending_plan_handoff(
        request.question,
        request.pending_plan_handoff,
    )
    if pending_handoff_answer is not None:
        answer_text, plan_handoff = pending_handoff_answer
        stored_memory_items = (
            default_memory_store.list_items(user_id=request.user_id)
            if include_memory
            else []
        )
        return AnswerResponse(
            answer=answer_text,
            citations=[],
            prompt_preview="",
            memory_summary=summarize_memory_for_prompt(
                question=request.question,
                memory_items=stored_memory_items,
            ),
            response_kind="answer",
            plan_handoff=plan_handoff,
        )

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
    skill_enrichment = _skill_enrichment_for_request(
        text=request.question,
        target_role=request.question,
        retrieval_context=retrieval_context,
        user_goal=request.question,
    )
    prompt = build_answer_prompt(
        question=request.question,
        retrieval_context=retrieval_context,
        current_plan=request.current_plan,
        skill_enrichment=skill_enrichment,
    )
    plan_update = maybe_build_plan_update(request.question, request.current_plan)
    if plan_update is not None:
        if include_memory:
            _persist_memory_candidates(pending_memory_candidates)
        return AnswerResponse(
            answer=plan_update.summary,
            citations=[],
            prompt_preview=prompt,
            memory_summary=retrieval_context.memory_summary,
            response_kind="answer",
            plan_update=plan_update,
        )
    guardrailed_answer = maybe_build_guardrailed_answer(
        question=request.question,
        retrieval_context=retrieval_context,
        skill_enrichment=skill_enrichment,
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
        answer_text = guardrailed_answer.text
        plan_handoff = None
        if guardrailed_answer.response_kind == "answer":
            offered_handoff = maybe_offer_plan_handoff(
                question=request.question,
                retrieval_context=retrieval_context,
                conversation_context=request.conversation_context,
                current_answer=answer_text,
            )
            if offered_handoff is not None:
                answer_text, plan_handoff = offered_handoff
        return AnswerResponse(
            answer=answer_text,
            citations=guardrailed_answer.citations,
            prompt_preview=prompt,
            memory_summary=response_memory_summary,
            response_kind=guardrailed_answer.response_kind,
            plan_handoff=plan_handoff,
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
    offered_handoff = maybe_offer_plan_handoff(
        question=request.question,
        retrieval_context=retrieval_context,
        conversation_context=request.conversation_context,
        current_answer=response.answer,
    )
    if offered_handoff is not None:
        answer_text, plan_handoff = offered_handoff
        response = response.model_copy(
            update={"answer": answer_text, "plan_handoff": plan_handoff}
        )
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
    skill_enrichment = _skill_enrichment_for_request(
        text=f"{request.goal}\n{request.target_role}",
        target_role=request.target_role,
        retrieval_context=retrieval_context,
        user_goal=request.goal,
    )
    prompt = build_career_plan_prompt(
        goal=request.goal,
        target_role=request.target_role,
        study_preferences=request.study_preferences,
        retrieval_context=retrieval_context,
        skill_enrichment=skill_enrichment,
    )
    generator = get_generator_client()
    return generator.generate_career_plan(
        request=request,
        prompt=prompt,
        retrieval_context=retrieval_context,
        skill_enrichment=skill_enrichment,
    )
