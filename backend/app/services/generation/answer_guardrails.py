"""Grounding checks for chat and structured plan boundaries."""

from __future__ import annotations

from dataclasses import dataclass
import re

from backend.app.services.generation.role_matcher import (
    find_supported_occupation as shared_find_supported_occupation,
    has_supported_role_grounding as shared_has_supported_role_grounding,
)
from backend.app.services.generation.schemas import RetrievedChunk
from backend.app.services.generation.skill_enrichment import SkillEnrichment
from backend.app.services.retrieval.rag_pipeline import RetrievalContext

_CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")


@dataclass(frozen=True)
class GuardrailedAnswer:
    """Legacy answer shape kept for compatibility with older tests/imports."""

    text: str
    citations: list[RetrievedChunk]
    response_kind: str = "answer"


class UnsupportedGuidanceRequestError(RuntimeError):
    """Raised when the current corpus cannot support a grounded plan request."""


def maybe_build_guardrailed_answer(
    *,
    question: str,
    retrieval_context: RetrievalContext,
    skill_enrichment: SkillEnrichment | None = None,
) -> GuardrailedAnswer | None:
    """Return no deterministic chat answer in the model-led chat path.

    Hard request blocking and exportable-plan support checks still happen in
    the safety and plan-guardrail paths. Normal chat wording should come from
    the configured generation model so the conversation remains natural.
    """

    del question, retrieval_context, skill_enrichment
    return None


def ensure_grounded_plan_support(
    *,
    goal: str,
    target_role: str,
    retrieval_context: RetrievalContext,
) -> None:
    """Reject plans for roles that are not grounded in the current corpus."""

    if _has_supported_role_grounding(target_role, retrieval_context):
        return

    language_code = _language_code(f"{goal}\n{target_role}")
    if language_code == "ru":
        raise UnsupportedGuidanceRequestError(
            "Я не могу построить экспортируемый учебный план для этой цели, потому что текущая база "
            "не дает достаточно уверенного совпадения с поддерживаемой ESCO-ролью или переходом. "
            "В чате можно обсудить направление с оговорками, но для плана и календаря укажите более "
            "стандартную должность или соседнюю поддерживаемую карьерную область."
        )

    raise UnsupportedGuidanceRequestError(
        "I can’t build an exportable study plan for that goal yet, because the current knowledge base "
        "does not show a strong enough match for a supported ESCO role or transition. "
        "Chat can discuss the direction with caveats, but plans and calendars need a more standard "
        "job title or nearby supported career area."
    )


def _has_supported_role_grounding(text: str, retrieval_context: RetrievalContext) -> bool:
    return shared_has_supported_role_grounding(text, retrieval_context)


def _find_supported_occupation(text: str, retrieval_context: RetrievalContext) -> RetrievedChunk | None:
    return shared_find_supported_occupation(text, retrieval_context)


def _language_code(text: str) -> str:
    return "ru" if _CYRILLIC_PATTERN.search(text) else "en"
