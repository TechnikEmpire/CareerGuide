"""Schedule-aware plan enrichment and ICS export helpers."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from math import ceil
import re
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from backend.app.services.generation.esco_grounding import (
    extract_description,
    extract_focus_topics,
    extract_label,
    first_occupation_or_chunk,
    join_human_list,
    lower_sentence_start,
    summarize_description,
)
from backend.app.services.generation.schemas import (
    CareerPlanCalendarEvent,
    CareerPlanRequest,
    CareerPlanResponse,
    CareerPlanStep,
    StudyPreferences,
)
from backend.app.services.retrieval.rag_pipeline import RetrievalContext

_CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")
_HIGH_WORKLOAD_PATTERN = re.compile(
    r"\b(engineer|engineering|developer|scientist|scientific|architect|cyber|security|"
    r"machine learning|data science|software|backend|frontend|full[- ]stack)\b"
    r"|инженер|разработ|архитект|кибер|безопас|машинн|дата[- ]сайенс",
    flags=re.IGNORECASE,
)
_MEDIUM_WORKLOAD_PATTERN = re.compile(
    r"\b(manager|management|analyst|analytics|specialist|coordinator|product|operations|"
    r"marketing|researcher|designer|consultant)\b"
    r"|менедж|аналит|специалист|координатор|продукт|операц|маркет|исслед|дизайн|консульт",
    flags=re.IGNORECASE,
)
_HIGH_SIGNAL_TOPIC_PATTERN = re.compile(
    r"\b(analysis|analytical|data|sql|statistics?|statistical|business intelligence|"
    r"visuali[sz]ation|engineering|mining|modelling|modeling|research|planning|"
    r"stakeholder|communication|risk|resource|conflict)\b"
    r"|аналит|данн|статист|визуализ|инженер|майнинг|исслед|планир|стейкхолдер|коммуник|риск|ресурс|конфликт",
    flags=re.IGNORECASE,
)
_DEFAULT_STEP_WEIGHTS = (0.2, 0.25, 0.35, 0.2)
_STUDY_TIME_SLOTS: dict[str, tuple[int, int]] = {
    "morning": (8, 0),
    "afternoon": (13, 0),
    "evening": (19, 0),
}
_WEEKDAY_PATTERNS: dict[int, tuple[int, ...]] = {
    1: (1,),
    2: (1, 3),
    3: (0, 2, 4),
    4: (0, 1, 3, 5),
    5: (0, 1, 2, 4, 5),
    6: (0, 1, 2, 3, 4, 6),
    7: (0, 1, 2, 3, 4, 5, 6),
}
_WORKLOAD_TOTAL_HOURS = {
    "low": 9.0,
    "medium": 14.0,
    "high": 18.0,
}


def finalize_career_plan(
    *,
    request: CareerPlanRequest,
    retrieval_context: RetrievalContext,
    goal: str,
    target_role: str,
    steps: list[CareerPlanStep],
    citations=None,
) -> CareerPlanResponse:
    """Normalize a raw plan into a richer response with schedule metadata."""

    language_code = "ru" if _CYRILLIC_PATTERN.search(f"{goal}\n{target_role}") else "en"
    primary_chunk = first_occupation_or_chunk(retrieval_context)
    role_label = extract_label(primary_chunk, language_code) or target_role
    role_description = extract_description(primary_chunk, language_code)
    role_summary = summarize_description(role_description, language_code)
    focus_topics = extract_focus_topics(retrieval_context, language_code, limit=8)
    workload_level = estimate_workload_level(
        target_role=target_role,
        role_label=role_label,
        role_description=role_summary,
        focus_topics=focus_topics,
    )
    preferences = normalize_study_preferences(request.study_preferences)
    total_hours = _WORKLOAD_TOTAL_HOURS[workload_level]
    enriched_steps = enrich_plan_steps(
        steps=steps,
        language_code=language_code,
        role_label=role_label,
        role_description=role_summary,
        focus_topics=focus_topics,
        total_hours=total_hours,
    )
    calendar_events = build_calendar_events(
        target_role=target_role,
        language_code=language_code,
        steps=enriched_steps,
        preferences=preferences,
    )
    estimated_weeks = max((event.week_index for event in calendar_events), default=1)
    return CareerPlanResponse(
        goal=goal,
        target_role=target_role,
        workload_level=workload_level,
        estimated_weeks=estimated_weeks,
        study_preferences=preferences,
        steps=enriched_steps,
        calendar_events=calendar_events,
        citations=list(citations if citations is not None else retrieval_context.chunks[:3]),
    )


def normalize_study_preferences(preferences: StudyPreferences) -> StudyPreferences:
    """Fill defaults and coerce invalid timezone/time-slot values into safe values."""

    timezone = preferences.timezone.strip() if preferences.timezone.strip() else "UTC"
    try:
        zone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        timezone = "UTC"
        zone = ZoneInfo("UTC")

    preferred_study_time = preferences.preferred_study_time.strip().lower()
    if preferred_study_time not in _STUDY_TIME_SLOTS:
        preferred_study_time = "evening"

    study_start_date = preferences.study_start_date or _next_monday(datetime.now(zone).date())
    return preferences.model_copy(
        update={
            "study_start_date": study_start_date,
            "preferred_study_time": preferred_study_time,
            "timezone": timezone,
        }
    )


def estimate_workload_level(
    *,
    target_role: str,
    role_label: str,
    role_description: str,
    focus_topics: list[str],
) -> str:
    """Approximate a study workload tier from grounded role text and skill breadth."""

    role_haystack = "\n".join([target_role, role_label, role_description])
    high_signal_topic_count = sum(1 for topic in focus_topics if _HIGH_SIGNAL_TOPIC_PATTERN.search(topic))
    if _HIGH_WORKLOAD_PATTERN.search(role_haystack) or high_signal_topic_count >= 7:
        return "high"
    if high_signal_topic_count >= 4 or _MEDIUM_WORKLOAD_PATTERN.search(role_haystack):
        return "medium"
    return "low"


def enrich_plan_steps(
    *,
    steps: list[CareerPlanStep],
    language_code: str,
    role_label: str,
    role_description: str,
    focus_topics: list[str],
    total_hours: float,
) -> list[CareerPlanStep]:
    """Attach grounded focus topics and estimated effort to each step."""

    if not steps:
        return []

    weights = _weights_for_step_count(len(steps))
    enriched_steps: list[CareerPlanStep] = []
    for index, step in enumerate(steps):
        start = index * 2
        focus_slice = focus_topics[start : start + 2] or focus_topics[:1]
        estimated_hours = round(total_hours * weights[index], 1)
        grounded_detail = _grounded_detail_for_step(
            index=index,
            language_code=language_code,
            role_label=role_label,
            role_description=role_description,
            focus_slice=focus_slice,
        )
        description = _rewrite_step_description(
            index=index,
            title=step.title,
            description=step.description,
            language_code=language_code,
            role_label=role_label,
            role_description=role_description,
            focus_slice=focus_slice,
        )
        enriched_steps.append(
            step.model_copy(
                update={
                    "description": description,
                    "focus_skills": focus_slice,
                    "grounded_detail": grounded_detail or None,
                    "estimated_hours": estimated_hours,
                }
            )
        )
    return enriched_steps


def build_calendar_events(
    *,
    target_role: str,
    language_code: str,
    steps: list[CareerPlanStep],
    preferences: StudyPreferences,
) -> list[CareerPlanCalendarEvent]:
    """Expand a structured plan into dated calendar sessions."""

    if not steps:
        return []

    slot_hour, slot_minute = _STUDY_TIME_SLOTS[preferences.preferred_study_time]
    session_duration = timedelta(minutes=preferences.session_duration_minutes)
    weekday_pattern = _WEEKDAY_PATTERNS[preferences.study_frequency_per_week]
    schedule_start = preferences.study_start_date
    cursor_date = schedule_start
    events: list[CareerPlanCalendarEvent] = []

    for step_index, step in enumerate(steps, start=1):
        session_count = max(
            1,
            ceil((step.estimated_hours or 0.0) / (preferences.session_duration_minutes / 60.0)),
        )
        for session_number in range(session_count):
            weekday_index = weekday_pattern[session_number % len(weekday_pattern)]
            event_date = _next_weekday_on_or_after(cursor_date, weekday_index)
            start_at = datetime.combine(event_date, time(hour=slot_hour, minute=slot_minute))
            end_at = start_at + session_duration
            week_index = ((event_date - schedule_start).days // 7) + 1
            title = _build_event_title(
                target_role=target_role,
                step=step,
                language_code=language_code,
            )
            session_index = session_number + 1
            description = _build_event_description(
                step=step,
                language_code=language_code,
                step_index=step_index,
                session_index=session_index,
                total_sessions=session_count,
            )
            events.append(
                CareerPlanCalendarEvent(
                    title=title,
                    description=description,
                    starts_at=start_at.isoformat(),
                    ends_at=end_at.isoformat(),
                    week_index=week_index,
                    step_index=step_index,
                    session_index=session_index,
                    total_sessions=session_count,
                )
            )
            cursor_date = event_date + timedelta(days=1)

    return events


def build_plan_ics(plan: CareerPlanResponse, *, user_id: str) -> str:
    """Serialize a generated plan schedule into a minimal ICS calendar."""

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//CareerGuide//Career Plan//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape_ics_text(plan.target_role)} study plan",
        f"X-WR-TIMEZONE:{_escape_ics_text(plan.study_preferences.timezone)}",
    ]
    created_at = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    timezone = plan.study_preferences.timezone or "UTC"

    for event in plan.calendar_events:
        starts_at = datetime.fromisoformat(event.starts_at)
        ends_at = datetime.fromisoformat(event.ends_at)
        uid = f"{uuid4()}@careerguide.local"
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{created_at}",
                f"DTSTART;TZID={timezone}:{starts_at.strftime('%Y%m%dT%H%M%S')}",
                f"DTEND;TZID={timezone}:{ends_at.strftime('%Y%m%dT%H%M%S')}",
                f"SUMMARY:{_escape_ics_text(event.title)}",
                f"DESCRIPTION:{_escape_ics_text(event.description)}",
                "STATUS:CONFIRMED",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def _weights_for_step_count(step_count: int) -> list[float]:
    if step_count == len(_DEFAULT_STEP_WEIGHTS):
        return list(_DEFAULT_STEP_WEIGHTS)
    return [1.0 / step_count for _ in range(step_count)]


def _grounded_detail_for_step(
    *,
    index: int,
    language_code: str,
    role_label: str,
    role_description: str,
    focus_slice: list[str],
) -> str:
    if language_code == "ru":
        if index == 0 and role_description:
            return f"Суть роли: {lower_sentence_start(role_description)}."
        if focus_slice:
            return f"Сфокусируйтесь на темах {join_human_list(focus_slice, language_code)}."
        return f"Держите фокус на требованиях роли {role_label}."

    if index == 0 and role_description:
        return f"Core work: {lower_sentence_start(role_description)}."
    if focus_slice:
        return f"Keep the study focus on {join_human_list(focus_slice, language_code)}."
    return f"Keep the work tied to the practical expectations of {role_label}."


def _build_event_title(
    *,
    target_role: str,
    step: CareerPlanStep,
    language_code: str,
) -> str:
    del language_code
    return f"{target_role}: {step.title}"


def _build_event_description(
    *,
    step: CareerPlanStep,
    language_code: str,
    step_index: int,
    session_index: int,
    total_sessions: int,
) -> str:
    description_parts = [
        _build_session_objective(
            step=step,
            language_code=language_code,
            step_index=step_index,
            session_index=session_index,
            total_sessions=total_sessions,
        )
    ]
    if step.focus_skills:
        if language_code == "ru":
            description_parts.append(
                f"Темы занятия: {join_human_list(step.focus_skills, language_code)}."
            )
        else:
            description_parts.append(
                f"Focus topics: {join_human_list(step.focus_skills, language_code)}."
            )
    return " ".join(part for part in description_parts if part).strip()


def _next_monday(today: date) -> date:
    days_ahead = (7 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)


def _next_weekday_on_or_after(start_date: date, weekday: int) -> date:
    days_ahead = (weekday - start_date.weekday()) % 7
    return start_date + timedelta(days=days_ahead)


def _escape_ics_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", r"\;")
        .replace(",", r"\,")
        .replace("\n", r"\n")
    )


def _rewrite_step_description(
    *,
    index: int,
    title: str,
    description: str,
    language_code: str,
    role_label: str,
    role_description: str,
    focus_slice: list[str],
) -> str:
    focus_summary = join_human_list(focus_slice, language_code)
    lowered_title = title.casefold()

    if language_code == "ru":
        if index == 0 or "уточн" in lowered_title:
            return (
                f"Определите, какой вариант роли {role_label} лучше всего подходит под ваш срок и формат работы. "
                f"{_grounded_detail_for_step(index=index, language_code=language_code, role_label=role_label, role_description=role_description, focus_slice=focus_slice)}"
            ).strip()
        if index == 1 or "сопостав" in lowered_title:
            return (
                f"Сравните свой текущий опыт с ключевыми направлениями для старта: {focus_summary or role_label}. "
                "Отметьте, что уже есть, а что нужно подтянуть в первую очередь."
            ).strip()
        if index == 2 or "проект" in lowered_title:
            return (
                f"Соберите один небольшой практический кейс, где вы примените {focus_summary or 'основные навыки роли'} "
                "и получите понятный результат."
            ).strip()
        return (
            f"Оформите результат в короткое доказательство прогресса: что вы сделали, чему научились и какой следующий шаг возьмете дальше. "
            f"{'Держите упор на ' + focus_summary + '.' if focus_summary else ''}"
        ).strip()

    if index == 0 or "clarify" in lowered_title:
        return (
            f"Pin down which version of {role_label} best matches your timeline and preferred work style. "
            f"{_grounded_detail_for_step(index=index, language_code=language_code, role_label=role_label, role_description=role_description, focus_slice=focus_slice)}"
        ).strip()
    if index == 1 or "map" in lowered_title:
        return (
            f"Compare your current background against the most important skill areas for starting out: {focus_summary or role_label}. "
            "Mark what you already have and what needs focused study first."
        ).strip()
    if index == 2 or "project" in lowered_title or "build" in lowered_title:
        return (
            f"Build one small practical project that uses {focus_summary or 'the core target skills'} "
            "and ends with a visible result you can explain."
        ).strip()
    return (
        f"Turn the work into proof with a short write-up, a sample deliverable, and a next-step list. "
        f"{'Keep the emphasis on ' + focus_summary + '.' if focus_summary else ''}"
    ).strip()


def _compact_event_summary(description: str, language_code: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", description.strip())
    primary = sentences[0].strip() if sentences and sentences[0].strip() else description.strip()
    return summarize_description(primary, language_code, max_words=20).rstrip(".") + "."


def _build_session_objective(
    *,
    step: CareerPlanStep,
    language_code: str,
    step_index: int,
    session_index: int,
    total_sessions: int,
) -> str:
    focus_summary = join_human_list(step.focus_skills[:2], language_code)

    if language_code == "ru":
        if step_index == 1:
            templates = [
                f"Просмотрите тип роли и выпишите, что именно вас в ней привлекает.",
                f"Сравните 2-3 близких варианта роли и отметьте, какой ближе вам по формату работы.",
                f"Зафиксируйте короткие критерии выбора роли и итоговый фокус на ближайшие недели.",
            ]
        elif step_index == 2:
            templates = [
                f"Оцените текущий уровень по темам {focus_summary or 'ключевых навыков роли'}.",
                "Отметьте основные пробелы и выберите, что нужно подтянуть в первую очередь.",
                "Составьте короткий список навыков, которые вы будете тренировать в ближайшем спринте.",
            ]
        elif step_index == 3:
            templates = [
                "Определите маленький практический кейс и зафиксируйте результат, который хотите показать.",
                f"Настройте рабочую основу и начните применять {focus_summary or 'ключевые навыки'} на практике.",
                "Доведите проект до понятного чернового результата.",
                "Улучшите итог и убедитесь, что его можно коротко показать другому человеку.",
            ]
        else:
            templates = [
                "Оформите, что вы сделали и какой результат получили.",
                "Соберите краткие доказательства прогресса: заметки, артефакт или мини-кейс.",
                "Запишите, чему вы научились и что стоит улучшить дальше.",
                "Определите следующий шаг на ближайшие 1-2 недели.",
            ]
    else:
        if step_index == 1:
            templates = [
                "Review the role shape and note what specifically attracts you to it.",
                "Compare 2 or 3 nearby versions of the role and note which one best fits your preferred work style.",
                "Write down a short decision rule for the role direction you want to commit to next.",
            ]
        elif step_index == 2:
            templates = [
                f"Assess your current baseline across {focus_summary or 'the key starting skills for the role'}.",
                "Mark the biggest gaps and choose what needs focused study first.",
                "Turn that gap list into a short skills-priority list for the next sprint.",
            ]
        elif step_index == 3:
            templates = [
                "Define one small practical project and the concrete result you want to show.",
                f"Set up the working materials and start applying {focus_summary or 'the target skills'} in practice.",
                "Push the project to a clear first draft.",
                "Polish the result so you can explain it quickly and confidently.",
            ]
        else:
            templates = [
                "Write down what you built and what outcome it produced.",
                "Collect a few pieces of proof: notes, a deliverable, or a short case summary.",
                "Capture what you learned and what still needs work.",
                "Choose the next step for the following 1 to 2 weeks.",
            ]

    template = templates[min(session_index - 1, len(templates) - 1)]
    if total_sessions > 1:
        if language_code == "ru":
            return f"Сессия {session_index} из {total_sessions}: {template}"
        return f"Session {session_index} of {total_sessions}: {template}"
    return template
