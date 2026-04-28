"""Chat-to-plan handoff decisions."""

from __future__ import annotations

import re

from backend.app.services.generation.esco_grounding import extract_label
from backend.app.services.generation.role_matcher import find_singular_supported_occupation
from backend.app.services.generation.schemas import (
    ChatContextTurn,
    PlanHandoffSuggestion,
    RetrievedChunk,
)
from backend.app.services.retrieval.rag_pipeline import RetrievalContext

_CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")
_AFFIRMATIVE_PATTERN = re.compile(
    r"^\s*(yes|yeah|yep|sure|ok|okay|please|do it|let'?s do it|sounds good|go ahead|"
    r"that works|start planning)\b|^\s*(да|ага|угу|ок|окей|хорошо|давай|давайте|соглас|можно)\b",
    flags=re.IGNORECASE,
)
_NEGATIVE_PATTERN = re.compile(
    r"^\s*(no|nope|not now|later|keep chatting|continue chatting|don'?t|do not)\b"
    r"|^\s*(нет|не сейчас|потом|позже|не надо|продолжим|оставим)\b",
    flags=re.IGNORECASE,
)


def answer_pending_plan_handoff(
    question: str,
    pending_handoff: PlanHandoffSuggestion | None,
) -> tuple[str, PlanHandoffSuggestion] | None:
    """Resolve an already-offered handoff from the user's next message."""

    if pending_handoff is None or pending_handoff.status != "offered":
        return None

    language_code = _language_code(question)
    if _AFFIRMATIVE_PATTERN.search(question):
        accepted = pending_handoff.model_copy(update={"status": "accepted"})
        if language_code == "ru":
            return (
                f"Хорошо. Открою конструктор плана с ролью {accepted.target_role}. "
                "Проверьте цель и настройки, затем постройте план.",
                accepted,
            )
        return (
            f"Okay. I’ll open the plan builder with {accepted.target_role} filled in. "
            "Review the goal and settings, then build the plan when you’re ready.",
            accepted,
        )

    if _NEGATIVE_PATTERN.search(question):
        declined = pending_handoff.model_copy(update={"status": "declined"})
        if language_code == "ru":
            return ("Хорошо, продолжим разбирать это в чате без перехода к плану.", declined)
        return ("Okay, we can keep narrowing this in chat without moving to a plan yet.", declined)

    if language_code == "ru":
        return (
            f"Могу перенести это в конструктор плана для роли {pending_handoff.target_role}, "
            "но мне нужен явный ответ. Открыть план?",
            pending_handoff,
        )
    return (
        f"I can move this into the plan builder for {pending_handoff.target_role}, "
        "but I need a clear yes first. Should I open the plan?",
        pending_handoff,
    )


def maybe_offer_plan_handoff(
    *,
    question: str,
    retrieval_context: RetrievalContext,
    conversation_context: list[ChatContextTurn],
    current_answer: str,
) -> tuple[str, PlanHandoffSuggestion] | None:
    """Append a natural plan-handoff question when a single supported role is clear."""

    combined_context = _build_context_text(question, conversation_context)
    occupation = find_singular_supported_occupation(combined_context, retrieval_context)
    if occupation is None:
        occupation = find_singular_supported_occupation(question, retrieval_context)
    if occupation is None:
        return None

    language_code = _language_code(f"{question}\n{current_answer}")
    role_label = _role_label(occupation, language_code)
    goal = _build_goal(role_label, language_code)
    handoff = PlanHandoffSuggestion(
        status="offered",
        target_role=role_label,
        goal=goal,
        source="supported_role_match",
    )
    if language_code == "ru":
        question_text = f" Хотите, я перенесу это в учебный план для роли {role_label}?"
    else:
        question_text = f" Would you like me to move this into a study plan for {role_label}?"
    return (current_answer.rstrip() + question_text, handoff)


def _build_context_text(question: str, conversation_context: list[ChatContextTurn]) -> str:
    recent_user_turns = [
        turn.text.strip()
        for turn in conversation_context[-6:]
        if turn.role == "user" and turn.text.strip()
    ]
    return "\n".join([*recent_user_turns, question])


def _role_label(occupation: RetrievedChunk, language_code: str) -> str:
    return extract_label(occupation, language_code) or occupation.title


def _build_goal(role_label: str, language_code: str) -> str:
    if language_code == "ru":
        return f"Составить реалистичный учебный план перехода в роль {role_label}"
    return f"Build a realistic transition study plan for {role_label}"


def _language_code(text: str) -> str:
    return "ru" if _CYRILLIC_PATTERN.search(text) else "en"
