"""Schedule-aware plan enrichment and ICS export helpers."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from math import ceil
import re
from uuid import NAMESPACE_URL, uuid5
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
from backend.app.services.generation.skill_enrichment import (
    SkillEnrichment,
    filter_learner_facing_topic_names,
    learner_facing_skill_names,
    merge_skill_names,
)
from backend.app.services.generation.study_cadence import estimate_study_cadence
from backend.app.services.retrieval.rag_pipeline import RetrievalContext

_CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")
_INTERNAL_SCAFFOLD_PATTERN = re.compile(
    r"\b(work directly on|tie the practice back|finish with a small checkable result|"
    r"pin down which version|core work:|keep the study focus|review retrieved career evidence|"
    r"identify the most relevant role signals)\b"
    r"|суть роли:|держите фокус|работайте именно над|практическое задание:",
    flags=re.IGNORECASE,
)
_EMPTY_OR_MALFORMED_PATTERN = re.compile(r"^\s*(?:n/?a|none|null|todo|tbd|\\.\\.\\.)\s*$", flags=re.IGNORECASE)
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

def finalize_career_plan(
    *,
    request: CareerPlanRequest,
    retrieval_context: RetrievalContext,
    goal: str,
    target_role: str,
    steps: list[CareerPlanStep],
    citations=None,
    skill_enrichment: SkillEnrichment | None = None,
) -> CareerPlanResponse:
    """Normalize a raw plan into a richer response with schedule metadata."""

    language_code = "ru" if _CYRILLIC_PATTERN.search(f"{goal}\n{target_role}") else "en"
    primary_chunk = first_occupation_or_chunk(retrieval_context)
    role_label = extract_label(primary_chunk, language_code) or target_role
    role_description = extract_description(primary_chunk, language_code)
    role_summary = summarize_description(role_description, language_code)
    grounded_focus_topics = extract_focus_topics(retrieval_context, language_code, limit=4)
    enriched_focus_topics = learner_facing_skill_names(skill_enrichment, limit=8)
    grounded_plan_topics = filter_learner_facing_topic_names(grounded_focus_topics)
    focus_topics = merge_skill_names(
        enriched_focus_topics,
        grounded_plan_topics if not enriched_focus_topics else [],
        limit=10,
    )
    workload_level = estimate_workload_level(
        focus_topics=focus_topics,
        skill_enrichment=skill_enrichment,
    )
    preferences = normalize_study_preferences(request.study_preferences)
    cadence = estimate_study_cadence(
        role_label=role_label,
        focus_topics=focus_topics,
        workload_level=workload_level,
        study_preferences=preferences,
        availability_text=f"{goal}\n{target_role}\n{retrieval_context.memory_summary}",
        effort_levels=skill_enrichment.effort_levels() if skill_enrichment is not None else {},
    )
    enriched_steps = enrich_plan_steps(
        steps=steps,
        language_code=language_code,
        role_label=role_label,
        role_description=role_summary,
        focus_topics=focus_topics,
        total_hours=cadence.total_hours,
        skill_enrichment=skill_enrichment,
    )
    calendar_events = build_calendar_events(
        target_role=target_role,
        language_code=language_code,
        steps=enriched_steps,
        preferences=preferences,
        skill_practice_tasks=skill_enrichment.practice_tasks_by_skill() if skill_enrichment is not None else {},
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
    focus_topics: list[str],
    skill_enrichment: SkillEnrichment | None = None,
) -> str:
    """Approximate a study workload tier from skill breadth and model effort levels."""

    effort_levels = skill_enrichment.effort_levels() if skill_enrichment is not None else {}
    high_effort_count = sum(1 for topic in focus_topics if effort_levels.get(topic.casefold()) == "high")
    medium_effort_count = sum(1 for topic in focus_topics if effort_levels.get(topic.casefold()) == "medium")
    if high_effort_count >= 3 or len(focus_topics) >= 9:
        return "high"
    if high_effort_count >= 1 or medium_effort_count >= 3 or len(focus_topics) >= 4:
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
    skill_enrichment: SkillEnrichment | None = None,
) -> list[CareerPlanStep]:
    """Attach grounded focus topics and estimated effort to each step."""

    if not steps:
        return []

    step_hours = _allocated_step_hours(steps, total_hours)
    topics_per_step = 3 if len(focus_topics) >= len(steps) * 3 else 2
    enriched_steps: list[CareerPlanStep] = []
    assigned_topics: set[str] = set()
    for index, step in enumerate(steps):
        focus_slice = _focus_topics_for_step(
            step=step,
            focus_topics=focus_topics,
            assigned_topics=assigned_topics,
            topics_per_step=topics_per_step,
        )
        assigned_topics.update(topic.casefold() for topic in focus_slice)
        estimated_hours = step_hours[index]
        grounded_detail = _grounded_detail_for_step(
            index=index,
            language_code=language_code,
            role_label=role_label,
            role_description=role_description,
            focus_slice=focus_slice,
        )
        should_preserve = _should_preserve_step_description(
            step=step,
            focus_slice=focus_slice,
            language_code=language_code,
        )
        description = (
            _clean_visible_description(step.description)
            if should_preserve
            else _rewrite_step_description(
                index=index,
                title=step.title,
                description=step.description,
                language_code=language_code,
                role_label=role_label,
                role_description=role_description,
                focus_slice=focus_slice,
            )
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


def _focus_topics_for_step(
    *,
    step: CareerPlanStep,
    focus_topics: list[str],
    assigned_topics: set[str],
    topics_per_step: int,
) -> list[str]:
    """Choose topics that match the step text before falling back to sequential allocation."""

    selected = _append_unique_topics([], step.focus_skills)
    step_text = " ".join([step.title, step.description, *step.focus_skills])
    matched_topics = [
        topic
        for topic in focus_topics
        if _topic_matches_text(topic, step_text)
    ]
    selected = _append_unique_topics(selected, matched_topics)
    if selected:
        return selected[:topics_per_step]

    remaining = [
        topic
        for topic in focus_topics
        if topic.casefold() not in assigned_topics and topic.casefold() not in {item.casefold() for item in selected}
    ]
    selected = _append_unique_topics(selected, remaining)
    if selected:
        return selected[:topics_per_step]
    return focus_topics[: max(1, min(topics_per_step, len(focus_topics)))]


def _append_unique_topics(existing: list[str], incoming: list[str]) -> list[str]:
    output = [topic for topic in existing if topic.strip()]
    seen = {topic.casefold() for topic in output}
    for topic in incoming:
        cleaned = topic.strip()
        normalized = cleaned.casefold()
        if not cleaned or normalized in seen:
            continue
        seen.add(normalized)
        output.append(cleaned)
    return output


def _topic_matches_text(topic: str, text: str) -> bool:
    topic_tokens = _topic_tokens(topic)
    text_tokens = set(_topic_tokens(text))
    if not topic_tokens:
        return False
    if set(topic_tokens).issubset(text_tokens):
        return True
    if len(topic_tokens) == 1:
        return topic_tokens[0] in text.casefold()
    return any(token in text_tokens for token in topic_tokens if len(token) >= 5)


def _topic_tokens(value: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[A-Za-zА-Яа-яЁё0-9+#]+", value.casefold().replace("ё", "е"))
        if token not in {"and", "with", "the", "for", "basic", "basics", "и", "с", "для", "основы"}
    ]


def build_calendar_events(
    *,
    target_role: str,
    language_code: str,
    steps: list[CareerPlanStep],
    preferences: StudyPreferences,
    skill_practice_tasks: dict[str, list[str]] | None = None,
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
                skill_practice_tasks=skill_practice_tasks or {},
            )
            events.append(
                CareerPlanCalendarEvent(
                    event_id=_build_event_id(
                        event_type="study",
                        title=title,
                        starts_at=start_at.isoformat(),
                        step_index=step_index,
                        session_index=session_index,
                    ),
                    event_type="study",
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


def rebuild_plan_schedule(plan: CareerPlanResponse, *, add_weekly_breaks: bool = False) -> CareerPlanResponse:
    """Rebuild calendar events for an already-grounded plan after preference changes."""

    language_code = "ru" if _CYRILLIC_PATTERN.search(f"{plan.goal}\n{plan.target_role}") else "en"
    preferences = normalize_study_preferences(plan.study_preferences)
    focus_topics = _plan_focus_topics(plan.steps)
    cadence = estimate_study_cadence(
        role_label=plan.target_role,
        focus_topics=focus_topics,
        workload_level=plan.workload_level,
        study_preferences=preferences,
        availability_text=plan.goal,
    )
    steps = _redistribute_step_hours(plan.steps, cadence.total_hours)
    study_events = build_calendar_events(
        target_role=plan.target_role,
        language_code=language_code,
        steps=steps,
        preferences=preferences,
    )
    calendar_events = study_events
    if add_weekly_breaks:
        calendar_events = sorted(
            [*study_events, *_build_weekly_break_events(study_events, preferences, language_code)],
            key=lambda event: event.starts_at,
        )
    estimated_weeks = max((event.week_index for event in calendar_events), default=1)
    return plan.model_copy(
        update={
            "estimated_weeks": estimated_weeks,
            "study_preferences": preferences,
            "steps": steps,
            "calendar_events": calendar_events,
        }
    )


def _plan_focus_topics(steps: list[CareerPlanStep]) -> list[str]:
    topics: list[str] = []
    seen: set[str] = set()
    for step in steps:
        for topic in step.focus_skills:
            cleaned = topic.strip()
            normalized = cleaned.casefold()
            if not cleaned or normalized in seen:
                continue
            seen.add(normalized)
            topics.append(cleaned)
    return topics


def _redistribute_step_hours(steps: list[CareerPlanStep], total_hours: float) -> list[CareerPlanStep]:
    if not steps:
        return []
    allocated_hours = _allocated_step_hours(steps, total_hours)
    return [
        step.model_copy(update={"estimated_hours": allocated_hours[index]})
        for index, step in enumerate(steps)
    ]


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
        uid = f"{event.event_id}@careerguide.local"
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


def _build_event_id(
    *,
    event_type: str,
    title: str,
    starts_at: str,
    step_index: int,
    session_index: int,
) -> str:
    raw_value = f"{event_type}|{title}|{starts_at}|{step_index}|{session_index}"
    return f"evt-{uuid5(NAMESPACE_URL, raw_value)}"


def _build_weekly_break_events(
    study_events: list[CareerPlanCalendarEvent],
    preferences: StudyPreferences,
    language_code: str,
) -> list[CareerPlanCalendarEvent]:
    if not study_events or preferences.study_start_date is None:
        return []

    break_events: list[CareerPlanCalendarEvent] = []
    max_week = max(event.week_index for event in study_events)
    slot_hour, slot_minute = _STUDY_TIME_SLOTS[preferences.preferred_study_time]
    break_start_hour = min(slot_hour + 1, 20)
    for week_index in range(1, max_week + 1):
        week_start = preferences.study_start_date + timedelta(days=(week_index - 1) * 7)
        event_date = _next_weekday_on_or_after(week_start, 6)
        start_at = datetime.combine(event_date, time(hour=break_start_hour, minute=slot_minute))
        end_at = start_at + timedelta(minutes=30)
        if language_code == "ru":
            title = "Перерыв на восстановление"
            description = "Короткий запланированный перерыв: восстановиться, снизить нагрузку и не превращать учебный план в ежедневное давление."
        else:
            title = "Recovery break"
            description = "A short scheduled break: recover, lower pressure, and keep the study plan sustainable."
        break_events.append(
            CareerPlanCalendarEvent(
                event_id=_build_event_id(
                    event_type="break",
                    title=title,
                    starts_at=start_at.isoformat(),
                    step_index=0,
                    session_index=week_index,
                ),
                event_type="break",
                title=title,
                description=description,
                starts_at=start_at.isoformat(),
                ends_at=end_at.isoformat(),
                week_index=week_index,
                step_index=1,
                session_index=week_index,
                total_sessions=max_week,
            )
        )
    return break_events


def _weights_for_step_count(step_count: int) -> list[float]:
    if step_count == len(_DEFAULT_STEP_WEIGHTS):
        return list(_DEFAULT_STEP_WEIGHTS)
    return [1.0 / step_count for _ in range(step_count)]


def _allocated_step_hours(steps: list[CareerPlanStep], total_hours: float) -> list[float]:
    if not steps:
        return []
    raw_hours = [
        float(step.estimated_hours)
        if step.estimated_hours is not None and step.estimated_hours > 0
        else 0.0
        for step in steps
    ]
    if any(value > 0 for value in raw_hours):
        positive_values = [value for value in raw_hours if value > 0]
        default_missing = sum(positive_values) / len(positive_values)
        raw_hours = [value if value > 0 else default_missing for value in raw_hours]
        raw_total = sum(raw_hours)
        return [round(total_hours * value / raw_total, 1) for value in raw_hours]

    weights = _weights_for_step_count(len(steps))
    return [round(total_hours * weights[index], 1) for index, _step in enumerate(steps)]


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
    skill_practice_tasks: dict[str, list[str]],
) -> str:
    description_parts = [
        _build_session_objective(
            step=step,
            language_code=language_code,
            step_index=step_index,
            session_index=session_index,
            total_sessions=total_sessions,
            skill_practice_tasks=skill_practice_tasks,
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
    title_is_scaffold = _is_scaffold_step_title(lowered_title, language_code)

    if not title_is_scaffold and focus_summary:
        return _specific_step_description(
            title=title,
            language_code=language_code,
            role_label=role_label,
            role_description=role_description,
            focus_summary=focus_summary,
        )

    if language_code == "ru":
        if index == 0 or "уточн" in lowered_title:
            return (
                f"Уточните, какой вариант роли {role_label} подходит под ваш срок и формат работы. "
                f"{'Сделайте первый результат по темам ' + focus_summary + '.' if focus_summary else 'Зафиксируйте критерии выбора роли.'}"
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
            f"Clarify which version of {role_label} fits your timeline and preferred work style. "
            f"{'Create a first result around ' + focus_summary + '.' if focus_summary else 'Write down the role criteria you want to use.'}"
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


def _is_scaffold_step_title(lowered_title: str, language_code: str) -> bool:
    if language_code == "ru":
        return re.search(r"уточн|сопостав|проект|доказательств|результат", lowered_title) is not None
    return re.search(r"\b(clarify|map|baseline|practice project|build practice|turn .*proof|proof)\b", lowered_title) is not None


def _specific_step_description(
    *,
    title: str,
    language_code: str,
    role_label: str,
    role_description: str,
    focus_summary: str,
) -> str:
    del title
    del role_description
    if language_code == "ru":
        return (
            f"Сфокусируйтесь на {focus_summary} для роли {role_label}. "
            "Сделайте небольшой результат, который можно проверить: упражнение, мини-кейс, заметки или рабочий артефакт."
        ).strip()
    return (
        f"Focus on {focus_summary} for {role_label}. "
        "Produce a small checkable result such as an exercise, mini-case, notes, or work sample."
    ).strip()


def _should_preserve_step_description(
    *,
    step: CareerPlanStep,
    focus_slice: list[str],
    language_code: str,
) -> bool:
    title = step.title.strip()
    description = step.description.strip()
    if not title or not description:
        return False
    if _EMPTY_OR_MALFORMED_PATTERN.search(description):
        return False
    if _INTERNAL_SCAFFOLD_PATTERN.search(description):
        return False
    if _is_scaffold_step_title(title.casefold(), language_code):
        return False
    if focus_slice and not _text_mentions_all_focus(description, focus_slice):
        return False
    return True


def _text_mentions_all_focus(text: str, focus_slice: list[str]) -> bool:
    return all(_text_mentions_topic(text, topic) for topic in focus_slice)


def _text_mentions_topic(text: str, topic: str) -> bool:
    haystack_tokens = set(_topic_tokens(text))
    topic_tokens = _topic_tokens(topic)
    return bool(topic_tokens and any(_topic_token_in_text(token, haystack_tokens) for token in topic_tokens))


def _topic_token_in_text(token: str, haystack_tokens: set[str]) -> bool:
    if len(token) < 3:
        return False
    singular = token.rstrip("s")
    for candidate in haystack_tokens:
        candidate_singular = candidate.rstrip("s")
        if token == candidate or singular == candidate_singular:
            return True
        if len(singular) >= 5 and candidate_singular.startswith(singular):
            return True
        if len(candidate_singular) >= 5 and singular.startswith(candidate_singular):
            return True
    return False


def _clean_visible_description(description: str) -> str:
    cleaned = " ".join(description.split()).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


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
    skill_practice_tasks: dict[str, list[str]],
) -> str:
    focus_summary = join_human_list(step.focus_skills[:2], language_code)
    practice_task = _practice_task_for_focus(
        step.focus_skills,
        skill_practice_tasks,
        session_index=session_index,
        total_sessions=total_sessions,
        language_code=language_code,
    )
    if practice_task:
        if total_sessions > 1:
            if language_code == "ru":
                return f"Сессия {session_index} из {total_sessions}: {practice_task}"
            return f"Session {session_index} of {total_sessions}: {practice_task}"
        return practice_task

    if focus_summary and not _is_scaffold_step_title(step.title.casefold(), language_code):
        templates = _specific_session_templates(focus_summary, language_code)
        template = _select_session_template(templates, session_index=session_index, language_code=language_code)
        if total_sessions > 1:
            if language_code == "ru":
                return f"Сессия {session_index} из {total_sessions}: {template}"
            return f"Session {session_index} of {total_sessions}: {template}"
        return template

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

    template = _select_session_template(templates, session_index=session_index, language_code=language_code)
    if total_sessions > 1:
        if language_code == "ru":
            return f"Сессия {session_index} из {total_sessions}: {template}"
        return f"Session {session_index} of {total_sessions}: {template}"
    return template


def _practice_task_for_focus(
    focus_skills: list[str],
    skill_practice_tasks: dict[str, list[str]],
    *,
    session_index: int,
    total_sessions: int,
    language_code: str,
) -> str:
    if not skill_practice_tasks:
        return ""
    for skill in focus_skills:
        tasks = skill_practice_tasks.get(skill.casefold(), [])
        if tasks:
            task = tasks[(session_index - 1) % len(tasks)]
            if total_sessions <= len(tasks):
                return task
            return _with_session_phase(task, session_index=session_index, language_code=language_code)
    return ""


def _select_session_template(templates: list[str], *, session_index: int, language_code: str) -> str:
    if session_index <= len(templates):
        return templates[session_index - 1]
    template = templates[(session_index - 1) % len(templates)]
    phase = _continuation_phase(session_index, language_code)
    return f"{phase}: {lower_sentence_start(template)}"


def _with_session_phase(task: str, *, session_index: int, language_code: str) -> str:
    phases_en = (
        "Start",
        "Continue",
        "Apply",
        "Review",
        "Package",
        "Reflect",
        "Extend",
        "Check",
    )
    phases_ru = (
        "Начните",
        "Продолжите",
        "Примените",
        "Проверьте",
        "Оформите",
        "Зафиксируйте",
        "Расширьте",
        "Сверьте",
    )
    phases = phases_ru if language_code == "ru" else phases_en
    phase = phases[(session_index - 1) % len(phases)]
    return f"{phase}: {lower_sentence_start(task.rstrip('.'))}."


def _continuation_phase(session_index: int, language_code: str) -> str:
    phases_ru = ("Продолжение", "Углубление", "Проверка", "Закрепление")
    phases_en = ("Continue", "Deepen", "Check", "Reinforce")
    phases = phases_ru if language_code == "ru" else phases_en
    return phases[(session_index - 1) % len(phases)]


def _specific_session_templates(focus_summary: str, language_code: str) -> list[str]:
    if language_code == "ru":
        return [
            f"Разберите базовые понятия по теме {focus_summary} и выпишите, что нужно применить на практике.",
            f"Сделайте короткое упражнение по теме {focus_summary} на небольшом примере.",
            f"Примените {focus_summary} к маленькой задаче, похожей на рабочую ситуацию.",
            "Проверьте ошибки, повторите слабые места и обновите заметки.",
            "Соберите небольшой артефакт, который показывает прогресс по этой теме.",
            "Кратко зафиксируйте результат, выводы и следующий шаг.",
        ]
    return [
        f"Review the core ideas for {focus_summary} and note what must be practiced.",
        f"Complete a short exercise using {focus_summary} on a small example.",
        f"Apply {focus_summary} to a small task that resembles real role work.",
        "Check mistakes, repeat weak spots, and update your notes.",
        "Create a small artifact that shows progress on this topic.",
        "Record the result, lessons learned, and next step in a short note.",
    ]
