"""Deterministic fallback plan generation when small-model JSON fails."""

from __future__ import annotations

import re

from backend.app.services.generation.schemas import CareerPlanRequest, CareerPlanResponse, CareerPlanStep
from backend.app.services.retrieval.rag_pipeline import RetrievalContext

_CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")
_PM_METHODOLOGY_PATTERN = re.compile(r"\bpm\b|²", flags=re.IGNORECASE)


def build_fallback_career_plan(
    *,
    request: CareerPlanRequest,
    retrieval_context: RetrievalContext,
) -> CareerPlanResponse:
    """Build a small grounded plan without relying on model-structured JSON."""

    language_code = "ru" if _CYRILLIC_PATTERN.search(request.goal) else "en"
    primary_chunk = _first_occupation_or_chunk(retrieval_context)
    role_label = _extract_label(primary_chunk, language_code) if primary_chunk else request.target_role
    skill_summary = _join_list(_extract_skills(primary_chunk, language_code)[:4], language_code)

    if language_code == "ru":
        steps = [
            CareerPlanStep(
                title="Уточнить целевую роль",
                description=(
                    f"Опираясь на текущие данные по роли {role_label}, зафиксируйте, какой именно вариант "
                    f"{request.target_role} соответствует вашей цели и временным ограничениям."
                ),
            ),
            CareerPlanStep(
                title="Сопоставить текущую базу навыков",
                description=(
                    f"Сравните свой текущий опыт с ключевыми направлениями навыков: {skill_summary or 'основные профессиональные навыки из найденных evidence'}."
                ),
            ),
            CareerPlanStep(
                title="Сделать один маленький практический проект",
                description=(
                    "Выберите небольшой, завершимый кейс, в котором можно применить 2-3 целевых навыка и показать реальный результат."
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
                    "best matches your goal and timeline."
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

    return CareerPlanResponse(
        goal=request.goal,
        target_role=request.target_role,
        steps=steps,
        citations=retrieval_context.chunks[:3],
    )


def _first_occupation_or_chunk(retrieval_context: RetrievalContext):
    for chunk in retrieval_context.chunks:
        if chunk.chunk_type == "occupation":
            return chunk
    return retrieval_context.chunks[0] if retrieval_context.chunks else None


def _extract_label(chunk, language_code: str) -> str:
    if chunk is None:
        return ""

    lines = [line.strip() for line in chunk.text.splitlines() if line.strip()]
    prefixes = (
        ("Russian label:", "English label:")
        if language_code == "ru"
        else ("English label:", "Russian label:")
    )
    for prefix in prefixes:
        for line in lines:
            if line.startswith(prefix):
                return line.removeprefix(prefix).strip().strip(".")

    if " / " in chunk.title:
        parts = [part.strip() for part in chunk.title.split(" / ") if part.strip()]
        if len(parts) >= 2:
            return parts[0] if language_code == "ru" else parts[-1]
    return chunk.title.strip()


def _extract_skills(chunk, language_code: str) -> list[str]:
    if chunk is None:
        return []

    lines = [line.strip() for line in chunk.text.splitlines() if line.strip()]
    prefixes = (
        ("Essential skills (RU):", "Optional skills (RU):", "Essential skills (EN):")
        if language_code == "ru"
        else ("Essential skills (EN):", "Optional skills (EN):", "Essential skills (RU):")
    )
    skill_blob = ""
    for prefix in prefixes:
        for line in lines:
            if line.startswith(prefix):
                skill_blob = line.removeprefix(prefix).strip().strip(".")
                break
        if skill_blob:
            break

    if not skill_blob:
        return []

    skills: list[str] = []
    seen: set[str] = set()
    for raw_skill in skill_blob.split(","):
        skill = raw_skill.strip().strip(".")
        if not skill:
            continue
        if _PM_METHODOLOGY_PATTERN.search(skill):
            continue
        normalized = skill.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        skills.append(skill)
    return skills


def _join_list(items: list[str], language_code: str) -> str:
    cleaned = [item for item in items if item]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        joiner = " и " if language_code == "ru" else " and "
        return joiner.join(cleaned)
    separator = ", "
    tail_joiner = " и " if language_code == "ru" else ", and "
    return separator.join(cleaned[:-1]) + tail_joiner + cleaned[-1]
