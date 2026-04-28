"""Deterministic fallback plan generation when small-model JSON fails."""

from __future__ import annotations

import re

from backend.app.services.generation.esco_grounding import (
    extract_description,
    extract_label,
    extract_skills,
    first_occupation_or_chunk,
    join_human_list,
    lower_sentence_start,
)
from backend.app.services.generation.plan_calendar import finalize_career_plan
from backend.app.services.generation.schemas import CareerPlanRequest, CareerPlanResponse, CareerPlanStep
from backend.app.services.generation.skill_enrichment import SkillEnrichment
from backend.app.services.retrieval.rag_pipeline import RetrievalContext

_CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")


def build_fallback_career_plan(
    *,
    request: CareerPlanRequest,
    retrieval_context: RetrievalContext,
    skill_enrichment: SkillEnrichment | None = None,
) -> CareerPlanResponse:
    """Build a small grounded plan without relying on model-structured JSON."""

    language_code = "ru" if _CYRILLIC_PATTERN.search(request.goal) else "en"
    primary_chunk = first_occupation_or_chunk(retrieval_context)
    role_label = extract_label(primary_chunk, language_code) if primary_chunk else request.target_role
    role_description = extract_description(primary_chunk, language_code)
    skills = extract_skills(primary_chunk, language_code)[:4]
    skill_summary = join_human_list(skills, language_code)
    grounded_role_phrase = lower_sentence_start(role_description) if role_description else role_label

    if language_code == "ru":
        steps = [
            CareerPlanStep(
                title="Уточнить целевую роль",
                description=(
                    f"Опираясь на текущие данные по роли {role_label}, зафиксируйте, какой именно вариант "
                    f"{request.target_role} соответствует вашей цели и временным ограничениям. "
                    f"Смотрите на роль как на работу, где нужно {grounded_role_phrase}."
                ),
            ),
            CareerPlanStep(
                title="Сопоставить текущую базу навыков",
                description=(
                    f"Сравните свой текущий опыт с ключевыми направлениями навыков: "
                    f"{skill_summary or 'основные профессиональные навыки из найденных данных'}."
                ),
            ),
            CareerPlanStep(
                title="Сделать один маленький практический проект",
                description=(
                    "Выберите небольшой, завершимый кейс, в котором можно применить 2-3 целевых навыка "
                    "и показать реальный результат в рабочем формате."
                ),
            ),
            CareerPlanStep(
                title="Собрать доказательства прогресса",
                description=(
                    "Оформите результаты в виде краткого кейс-описания, заметок о прогрессе и списка следующего шага на ближайшие 2-4 недели."
                ),
            ),
        ]
    else:
        steps = [
            CareerPlanStep(
                title="Clarify the target role",
                description=(
                    f"Use the current evidence around {role_label} to pin down which version of {request.target_role} "
                    f"best matches your goal and timeline. Treat it as work that involves {grounded_role_phrase}."
                ),
            ),
            CareerPlanStep(
                title="Map your current skills baseline",
                description=(
                    f"Compare your existing background against the main skill areas in the current evidence: {skill_summary or 'the core skills surfaced in retrieval'}."
                ),
            ),
            CareerPlanStep(
                title="Build one small practice project",
                description=(
                    "Choose one compact project that lets you apply 2 or 3 target skills and finish with a concrete result."
                ),
            ),
            CareerPlanStep(
                title="Turn the work into proof",
                description=(
                    "Write up what you built, what skills you used, and what the next 2 to 4 weeks of progress should look like."
                ),
            ),
        ]

    return finalize_career_plan(
        request=request,
        retrieval_context=retrieval_context,
        goal=request.goal,
        target_role=request.target_role,
        steps=steps,
        citations=retrieval_context.chunks[:3],
        skill_enrichment=skill_enrichment,
    )
