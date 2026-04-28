"""Conservative study-cadence estimates for chat answers and plan schedules."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
import re

from backend.app.services.generation.schemas import StudyPreferences

_CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")
_HOURS_PER_WEEK_PATTERNS = (
    re.compile(
        r"\b(?P<hours>\d+(?:[.,]\d+)?)\s*(?:hours?|hrs?|h)\s*(?:per|a)\s*week\b",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"(?P<hours>\d+(?:[.,]\d+)?)\s*(?:час|часа|часов|ч)\s*(?:в|на)\s*недел",
        flags=re.IGNORECASE,
    ),
)
_SESSIONS_PER_WEEK_PATTERNS = (
    re.compile(
        r"\b(?P<count>[1-7])\s*(?:sessions?|times?|evenings?|mornings?|afternoons?)\s*(?:per|a)\s*week\b",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"(?P<count>[1-7])\s*(?:занят|сесси|раз|раза|вечер|утр|дн[яеё])\w*\s*(?:в|на)\s*недел",
        flags=re.IGNORECASE,
    ),
)
_WORKLOAD_BASE_HOURS = {
    "low": 14.0,
    "medium": 24.0,
    "high": 34.0,
}


@dataclass(frozen=True)
class TopicCadence:
    """Estimated effort for a concrete study topic."""

    topic: str
    estimated_hours: float
    estimated_weeks: int


@dataclass(frozen=True)
class StudyCadenceEstimate:
    """Starter study-load estimate shared by chat and calendar planning."""

    total_hours: float
    hours_per_week: float
    estimated_weeks: int
    topic_efforts: tuple[TopicCadence, ...]


def estimate_study_cadence(
    *,
    role_label: str,
    focus_topics: list[str],
    workload_level: str,
    study_preferences: StudyPreferences | None = None,
    availability_text: str = "",
    effort_levels: dict[str, str] | None = None,
) -> StudyCadenceEstimate:
    """Estimate a conservative starter cadence for role-specific study topics."""

    del role_label
    topics = _dedupe_topics(focus_topics)[:8]
    hours_per_week = (
        extract_hours_per_week(availability_text)
        or _hours_per_week_from_preferences(study_preferences)
        or 4.5
    )
    hours_per_week = _clamp(hours_per_week, 1.0, 30.0)
    workload = workload_level if workload_level in _WORKLOAD_BASE_HOURS else "medium"
    topic_bonus = min(12.0, max(0, len(topics) - 3) * 2.0)
    effort_bonus = _effort_bonus(topics, effort_levels or {})
    total_hours = round(_WORKLOAD_BASE_HOURS[workload] + topic_bonus + effort_bonus, 1)
    topic_efforts = _allocate_topic_efforts(
        topics,
        total_hours,
        hours_per_week,
        effort_levels=effort_levels or {},
    )
    return StudyCadenceEstimate(
        total_hours=total_hours,
        hours_per_week=hours_per_week,
        estimated_weeks=max(1, ceil(total_hours / hours_per_week)),
        topic_efforts=topic_efforts,
    )


def extract_hours_per_week(text: str) -> float | None:
    """Parse explicit weekly study availability from English or Russian text."""

    for pattern in _HOURS_PER_WEEK_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        return _parse_number(match.group("hours"))

    for pattern in _SESSIONS_PER_WEEK_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        return float(match.group("count")) * 1.5

    return None


def format_cadence_sentence(estimate: StudyCadenceEstimate, language_code: str) -> str:
    """Return one compact coaching sentence for chat answers."""

    topic_names = [topic.topic for topic in estimate.topic_efforts[:3]]
    if not topic_names:
        if language_code == "ru":
            return (
                f"По нагрузке это примерно {estimate.estimated_weeks} нед. при "
                f"{_format_hours(estimate.hours_per_week, language_code)} в неделю."
            )
        return (
            f"As a starter load, expect about {estimate.estimated_weeks} weeks at "
            f"{_format_hours(estimate.hours_per_week, language_code)} per week."
        )

    first_topics = _join_topics(topic_names[:2], language_code)
    next_topic = topic_names[2] if len(topic_names) > 2 else ""
    if language_code == "ru":
        suffix = f", затем добавить {next_topic}" if next_topic else ""
        return (
            f"По темпу заложите около {estimate.estimated_weeks} нед. при "
            f"{_format_hours(estimate.hours_per_week, language_code)} в неделю: сначала {first_topics}{suffix}."
        )
    suffix = f", then add {next_topic}" if next_topic else ""
    return (
        f"At about {_format_hours(estimate.hours_per_week, language_code)} per week, "
        f"treat {first_topics} as the first {estimate.estimated_weeks}-week starter block{suffix}."
    )


def format_cadence_block(estimate: StudyCadenceEstimate, language_code: str) -> str:
    """Return prompt-ready cadence guidance."""

    if language_code == "ru":
        lines = [
            f"Weekly study budget: {_format_hours(estimate.hours_per_week, language_code)}.",
            f"Starter estimate: {estimate.total_hours:g} hours across about {estimate.estimated_weeks} weeks.",
        ]
    else:
        lines = [
            f"Weekly study budget: {_format_hours(estimate.hours_per_week, language_code)}.",
            f"Starter estimate: {estimate.total_hours:g} hours across about {estimate.estimated_weeks} weeks.",
        ]

    if estimate.topic_efforts:
        topic_lines = [
            f"{topic.topic}: about {topic.estimated_hours:g} hours / {topic.estimated_weeks} week(s)"
            for topic in estimate.topic_efforts[:6]
        ]
        lines.append("Topic effort bands: " + "; ".join(topic_lines) + ".")
    return "\n".join(lines)


def _hours_per_week_from_preferences(preferences: StudyPreferences | None) -> float | None:
    if preferences is None:
        return None
    return preferences.study_frequency_per_week * (preferences.session_duration_minutes / 60.0)


def _allocate_topic_efforts(
    topics: list[str],
    total_hours: float,
    hours_per_week: float,
    *,
    effort_levels: dict[str, str],
) -> tuple[TopicCadence, ...]:
    if not topics:
        return ()

    visible_topics = topics[:6]
    normalized_effort_levels = {key.casefold(): value for key, value in effort_levels.items()}
    weights = [
        _topic_weight(topic, index=index, effort_levels=normalized_effort_levels)
        for index, topic in enumerate(visible_topics)
    ]
    weight_total = sum(weights)
    topic_efforts: list[TopicCadence] = []
    for topic, weight in zip(visible_topics, weights, strict=False):
        estimated_hours = max(2.0, round((total_hours * weight / weight_total) * 2) / 2)
        topic_efforts.append(
            TopicCadence(
                topic=topic,
                estimated_hours=estimated_hours,
                estimated_weeks=max(1, ceil(estimated_hours / hours_per_week)),
            )
        )
    return tuple(topic_efforts)


def _effort_bonus(topics: list[str], effort_levels: dict[str, str]) -> float:
    normalized_levels = {key.casefold(): value for key, value in effort_levels.items()}
    high_count = sum(1 for topic in topics if normalized_levels.get(topic.casefold()) == "high")
    medium_count = sum(1 for topic in topics if normalized_levels.get(topic.casefold()) == "medium")
    return min(8.0, high_count * 2.0 + medium_count * 0.75)


def _topic_weight(topic: str, *, index: int, effort_levels: dict[str, str]) -> float:
    effort_level = effort_levels.get(topic.casefold())
    if effort_level == "high":
        return 1.5
    if effort_level == "medium":
        return 1.2
    if effort_level == "low":
        return 0.85
    return 1.15 if index < 2 else 1.0


def _dedupe_topics(topics: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for topic in topics:
        cleaned = topic.strip()
        if not cleaned:
            continue
        normalized = cleaned.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(cleaned)
    return deduped


def _join_topics(topics: list[str], language_code: str) -> str:
    if not topics:
        return ""
    if len(topics) == 1:
        return topics[0]
    conjunction = "и" if language_code == "ru" else "and"
    return f"{topics[0]} {conjunction} {topics[1]}"


def _format_hours(value: float, language_code: str) -> str:
    formatted = f"{value:g}"
    return f"{formatted} ч" if language_code == "ru" else f"{formatted} hours"


def _parse_number(value: str) -> float:
    return float(value.replace(",", "."))


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))
