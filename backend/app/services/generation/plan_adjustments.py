"""Deterministic study-plan adjustments from chat feedback."""

from __future__ import annotations

from datetime import date
import re

from backend.app.services.generation.plan_calendar import rebuild_plan_schedule
from backend.app.services.generation.schemas import (
    CareerPlanResponse,
    CareerPlanStep,
    MemoryItemPayload,
    PlanUpdateSuggestion,
)

_CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")
_RELAX_PATTERN = re.compile(
    r"\b(relax|lighter|less intense|less intensive|slow down|slower|overwhelmed|burnout|burned out|"
    r"burnt out|mental health|struggling|too much|exhausted)\b"
    r"|выгоран|перегруж|слишком много|сложно выдерж|психичес|ментальн|устал|устала|спокойнее|легче|сниз.*нагруз",
    flags=re.IGNORECASE,
)
_FREQUENCY_PATTERN = re.compile(
    r"\b(?P<count_en>[1-7])\s*(?:sessions?|times?)\s*(?:per|a)\s*week\b"
    r"|(?P<count_ru>[1-7])\s*(?:занят|сесси|раз[а]?)\s*(?:в|на)\s*недел",
    flags=re.IGNORECASE,
)
_MORNING_PATTERN = re.compile(r"\bmorning\b|утр", flags=re.IGNORECASE)
_AFTERNOON_PATTERN = re.compile(r"\bafternoon\b|дн[её]м|день", flags=re.IGNORECASE)
_EVENING_PATTERN = re.compile(r"\bevening\b|вечер", flags=re.IGNORECASE)
_ADD_TOPIC_PATTERN = re.compile(
    r"\b(?:add|include|emphasize|focus on|more)\s+(?P<topic_en>[A-Za-z][A-Za-z0-9+#./ -]{1,40})"
    r"|(?:добав|включ|усиль|больше)\s+(?P<topic_ru>[A-Za-zА-Яа-яЁё0-9+#./ -]{1,40})",
    flags=re.IGNORECASE,
)
_TOPIC_CUTOFF_PATTERN = re.compile(
    r"\s*(?:to|practice|sessions?|into|in the plan|please|практик|занят|в план|пожалуйста|и)\b.*",
    flags=re.IGNORECASE,
)


def build_lower_intensity_memory(user_id: str, text: str) -> MemoryItemPayload | None:
    """Return a non-clinical memory item for wellbeing-related schedule feedback."""

    if not _RELAX_PATTERN.search(text):
        return None
    language_code = _language_code(text)
    memory_text = (
        "Нужна менее интенсивная учебная нагрузка."
        if language_code == "ru"
        else "Needs a lower-intensity study schedule."
    )
    return MemoryItemPayload(
        id=f"wellbeing-{user_id}",
        user_id=user_id,
        text=memory_text,
        category="user_constraint",
        importance=0.85,
        confidence=0.9,
    )


def maybe_build_plan_update(question: str, current_plan: CareerPlanResponse | None) -> PlanUpdateSuggestion | None:
    """Build a proposed plan update from explicit chat feedback."""

    if current_plan is None:
        return None

    if _RELAX_PATTERN.search(question):
        return _build_relaxed_plan(question, current_plan)

    frequency = _extract_frequency(question)
    study_time = _extract_study_time(question)
    if frequency is not None or study_time is not None:
        return _build_schedule_preference_update(question, current_plan, frequency, study_time)

    topic = _extract_topic(question)
    if topic:
        return _build_focus_topic_update(question, current_plan, topic)

    return None


def _build_relaxed_plan(question: str, plan: CareerPlanResponse) -> PlanUpdateSuggestion:
    language_code = _language_code(question)
    preferences = plan.study_preferences.model_copy(
        update={
            "study_frequency_per_week": min(plan.study_preferences.study_frequency_per_week, 2),
            "session_duration_minutes": min(plan.study_preferences.session_duration_minutes, 60),
        }
    )
    updated_plan = rebuild_plan_schedule(
        plan.model_copy(
            update={
                "workload_level": "low",
                "study_preferences": preferences,
            }
        ),
        add_weekly_breaks=True,
    )
    summary = (
        "Я предлагаю снизить учебную нагрузку, сделать занятия короче и добавить еженедельные восстановительные перерывы."
        if language_code == "ru"
        else "I suggest lowering the study load, shortening sessions, and adding weekly recovery breaks."
    )
    return PlanUpdateSuggestion(
        kind="relax_schedule",
        summary=summary,
        updated_plan=updated_plan,
    )


def _build_schedule_preference_update(
    question: str,
    plan: CareerPlanResponse,
    frequency: int | None,
    study_time: str | None,
) -> PlanUpdateSuggestion:
    language_code = _language_code(question)
    updates: dict[str, object] = {}
    if frequency is not None:
        updates["study_frequency_per_week"] = frequency
    if study_time is not None:
        updates["preferred_study_time"] = study_time
    preferences = plan.study_preferences.model_copy(update=updates)
    updated_plan = rebuild_plan_schedule(
        plan.model_copy(update={"study_preferences": preferences}),
        add_weekly_breaks=any(event.event_type == "break" for event in plan.calendar_events),
    )
    summary = (
        "Я предлагаю пересобрать календарь с обновленными предпочтениями по расписанию."
        if language_code == "ru"
        else "I suggest rebuilding the calendar with the updated schedule preferences."
    )
    return PlanUpdateSuggestion(
        kind="schedule_preferences",
        summary=summary,
        updated_plan=updated_plan,
    )


def _build_focus_topic_update(question: str, plan: CareerPlanResponse, topic: str) -> PlanUpdateSuggestion:
    language_code = _language_code(question)
    normalized_topic = topic.strip()
    if not normalized_topic:
        return None  # type: ignore[return-value]

    target_index = _best_step_index_for_topic(plan, normalized_topic)
    updated_steps: list[CareerPlanStep] = []
    for index, step in enumerate(plan.steps):
        if index != target_index:
            updated_steps.append(step)
            continue
        focus_skills = _append_unique(step.focus_skills, normalized_topic)
        description = step.description
        if normalized_topic.casefold() not in description.casefold():
            if language_code == "ru":
                description = f"{description} Добавьте отдельную практику по теме {normalized_topic}."
            else:
                description = f"{description} Add focused practice on {normalized_topic}."
        updated_steps.append(step.model_copy(update={"focus_skills": focus_skills, "description": description}))

    updated_plan = rebuild_plan_schedule(plan.model_copy(update={"steps": updated_steps}))
    summary = (
        f"Я предлагаю добавить {normalized_topic} в фокус плана и обновить описания занятий."
        if language_code == "ru"
        else f"I suggest adding {normalized_topic} to the plan focus and updating the session descriptions."
    )
    return PlanUpdateSuggestion(
        kind="add_focus_topic",
        summary=summary,
        updated_plan=updated_plan,
    )


def _extract_frequency(text: str) -> int | None:
    match = _FREQUENCY_PATTERN.search(text)
    if not match:
        return None
    raw_count = match.group("count_en") or match.group("count_ru")
    return max(1, min(7, int(raw_count)))


def _extract_study_time(text: str) -> str | None:
    if _MORNING_PATTERN.search(text):
        return "morning"
    if _AFTERNOON_PATTERN.search(text):
        return "afternoon"
    if _EVENING_PATTERN.search(text):
        return "evening"
    return None


def _extract_topic(text: str) -> str:
    match = _ADD_TOPIC_PATTERN.search(text)
    if not match:
        return ""
    topic = (match.group("topic_en") or match.group("topic_ru") or "").strip()
    topic = _TOPIC_CUTOFF_PATTERN.sub("", topic).strip(" .,!?:;-")
    topic = re.sub(r"^(?:more|больше)\s+", "", topic, flags=re.IGNORECASE).strip()
    if not topic or len(topic) > 40:
        return ""
    return topic


def _best_step_index_for_topic(plan: CareerPlanResponse, topic: str) -> int:
    normalized_topic = topic.casefold()
    for index, step in enumerate(plan.steps):
        haystack = "\n".join([step.title, step.description, " ".join(step.focus_skills)]).casefold()
        if normalized_topic in haystack:
            return index
    for index, step in enumerate(plan.steps):
        if re.search(r"\b(project|practice|build|case)\b|проект|практик|кейс", step.title, flags=re.IGNORECASE):
            return index
    return min(1, len(plan.steps) - 1) if plan.steps else 0


def _append_unique(items: list[str], value: str) -> list[str]:
    normalized_value = value.casefold()
    output = [item for item in items if item.strip()]
    if all(item.casefold() != normalized_value for item in output):
        output.append(value)
    return output


def _language_code(text: str) -> str:
    return "ru" if _CYRILLIC_PATTERN.search(text) else "en"
