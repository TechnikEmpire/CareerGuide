"""Shared assistant orchestration for API routes and evaluation scripts."""

from __future__ import annotations

import re

from backend.app.services.generation.generator_client import get_generator_client
from backend.app.services.generation.answer_guardrails import ensure_grounded_plan_support
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
    extract_role_tokens,
    find_supported_occupation,
    useful_occupations,
)
from backend.app.services.generation.schemas import (
    AnswerRequest,
    AnswerResponse,
    CareerPlanRequest,
    CareerPlanResponse,
    ChatContextTurn,
    MemoryItemPayload,
    RetrievedChunk,
)
from backend.app.services.generation.skill_enrichment import (
    SkillEnrichment,
    fallback_skill_enrichment,
    language_code_for_text,
)
from backend.app.services.memory.memory_consolidate import consolidate_memory_items
from backend.app.services.memory.memory_extract import extract_candidate_memory_items
from backend.app.services.memory.hopfield_memory import summarize_memory_for_prompt
from backend.app.services.memory.memory_store import default_memory_store
from backend.app.services.retrieval.rag_pipeline import build_retrieval_context
from backend.app.services.safety.safety import ensure_request_is_in_scope

_GENERIC_FOLLOW_UP_PATTERN = re.compile(
    r"\b(that|this|it|those|these|same|one|specific career title|career title|match me|"
    r"plan around|study plan for that|make a study plan|for that|around that|next step|next steps)\b"
    r"|конкретн.*(?:роль|профес|должност)|под это|для этого|план.*(?:для|под)",
    flags=re.IGNORECASE,
)
_TRANSIENT_TASK_MEMORY_PATTERN = re.compile(
    r"^\s*(?:compare|can you|could you|tell me|explain|what|which|how|do you|does|give me|"
    r"make|create|build|draft|show|list)\b"
    r"|^\s*(?:сравни|можешь|расскажи|объясни|что|какие|какой|как|дай|составь|покажи|перечисли)\b",
    flags=re.IGNORECASE,
)


def _extract_request_memory_candidates(user_id: str, text: str) -> list[MemoryItemPayload]:
    """Extract request-local memory candidates without persisting them yet."""

    lower_intensity_memory = build_lower_intensity_memory(user_id, text)
    if lower_intensity_memory is not None:
        return [lower_intensity_memory]

    candidates = extract_candidate_memory_items(user_id=user_id, text=text)
    stable_candidates = [
        candidate
        for candidate in candidates
        if not _TRANSIENT_TASK_MEMORY_PATTERN.search(candidate.text)
    ]
    return consolidate_memory_items(stable_candidates)


def _persist_memory_candidates(candidates: list[MemoryItemPayload]) -> None:
    """Persist already-approved memory candidates."""

    for candidate in candidates:
        default_memory_store.upsert_item(candidate)


def _filter_conflicting_role_goal_memory(
    question: str,
    memory_items: list[MemoryItemPayload],
) -> list[MemoryItemPayload]:
    """Drop old role-goal memories when the user explicitly pivots to another role."""

    current_role = extract_target_role_phrase(question)
    current_tokens = set(extract_role_tokens(current_role))
    if not current_tokens:
        return memory_items

    filtered_items: list[MemoryItemPayload] = []
    for item in memory_items:
        remembered_role = extract_target_role_phrase(item.text)
        remembered_tokens = set(extract_role_tokens(remembered_role))
        if remembered_tokens and current_tokens.isdisjoint(remembered_tokens):
            continue
        filtered_items.append(item)
    return filtered_items


def _recent_user_context_lines(
    conversation_context: list[ChatContextTurn],
    current_question: str,
    *,
    limit: int = 3,
) -> list[str]:
    """Return recent user turns before the current question."""

    current = current_question.strip()
    user_lines = [
        turn.text.strip()
        for turn in conversation_context
        if turn.role == "user" and turn.text.strip()
    ]
    if user_lines and user_lines[-1] == current:
        user_lines = user_lines[:-1]
    return user_lines[-limit:]


def _needs_recent_context(question: str) -> bool:
    """Return whether a question is probably a follow-up needing prior turns."""

    return _GENERIC_FOLLOW_UP_PATTERN.search(question) is not None


def _recent_context_text(conversation_context: list[ChatContextTurn], current_question: str) -> str:
    lines = _recent_user_context_lines(conversation_context, current_question)
    return "\n".join(f"- User previously said: {line}" for line in lines)


def _retrieval_question_for_request(request: AnswerRequest) -> str:
    """Build a retrieval query that preserves obvious follow-up context."""

    lines = _recent_user_context_lines(request.conversation_context, request.question)
    if not lines or not _needs_recent_context(request.question):
        return request.question
    return "\n".join([*lines, request.question])


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
        memory_items = _filter_conflicting_role_goal_memory(request.question, stored_memory_items)
    else:
        pending_memory_candidates = []
        stored_memory_items = []
        memory_items = []
    retrieval_question = _retrieval_question_for_request(request)
    recent_context = _recent_context_text(request.conversation_context, request.question)
    retrieval_context = build_retrieval_context(
        question=retrieval_question,
        memory_items=memory_items,
        top_k=top_k,
        use_reranker=use_reranker,
    )
    skill_enrichment = _skill_enrichment_for_request(
        text=retrieval_question,
        target_role=request.question,
        retrieval_context=retrieval_context,
        user_goal=request.question,
    )
    plan_update = maybe_build_plan_update(request.question, request.current_plan)
    prompt = build_answer_prompt(
        question=request.question,
        retrieval_context=retrieval_context,
        current_plan=request.current_plan,
        skill_enrichment=skill_enrichment,
        recent_conversation_context=recent_context,
        proposed_plan_update_summary=plan_update.summary if plan_update is not None else "",
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
    if plan_update is not None:
        return response.model_copy(update={"plan_update": plan_update})
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
