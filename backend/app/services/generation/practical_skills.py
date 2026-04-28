"""Practical study-topic expansion for identifiable career families.

ESCO is the grounded career source, but some ESCO occupation records are too
generic for an actionable study plan. This module adds conservative, inspectable
study topics for common role families without treating them as ESCO claims.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from backend.app.services.generation.schemas import RetrievedChunk
from backend.app.services.retrieval.rag_pipeline import RetrievalContext


@dataclass(frozen=True)
class PracticalSkillExpansion:
    """Role-family mapping from text patterns to concrete study topics."""

    pattern: re.Pattern[str]
    topics_en: tuple[str, ...]
    topics_ru: tuple[str, ...]


_EXPANSIONS: tuple[PracticalSkillExpansion, ...] = (
    PracticalSkillExpansion(
        pattern=re.compile(
            r"\b(data analyst|data analytics|business intelligence analyst|bi analyst)\b"
            r"|аналитик данных|аналитика данных|бизнес[- ]аналитик данных",
            flags=re.IGNORECASE,
        ),
        topics_en=(
            "SQL",
            "spreadsheet analysis",
            "Python with pandas",
            "data visualization",
            "basic statistics",
            "dashboard storytelling",
        ),
        topics_ru=(
            "SQL",
            "анализ таблиц",
            "Python и pandas",
            "визуализация данных",
            "базовая статистика",
            "дашборды и объяснение выводов",
        ),
    ),
    PracticalSkillExpansion(
        pattern=re.compile(
            r"\b(front[- ]?end developer|frontend developer|web developer|react developer|ui developer)\b"
            r"|frontend|front-end|веб[- ]разработчик|фронтенд|фронт[- ]?енд",
            flags=re.IGNORECASE,
        ),
        topics_en=(
            "HTML and CSS fundamentals",
            "JavaScript",
            "TypeScript basics",
            "React",
            "browser debugging",
            "Git",
        ),
        topics_ru=(
            "основы HTML и CSS",
            "JavaScript",
            "основы TypeScript",
            "React",
            "отладка в браузере",
            "Git",
        ),
    ),
    PracticalSkillExpansion(
        pattern=re.compile(
            r"\b(back[- ]?end developer|backend developer|server-side developer|api developer)\b"
            r"|backend|back-end|бэкенд|бекенд|серверн.*разработ",
            flags=re.IGNORECASE,
        ),
        topics_en=(
            "server-side programming",
            "REST APIs",
            "SQL databases",
            "authentication basics",
            "automated testing",
            "deployment basics",
        ),
        topics_ru=(
            "серверное программирование",
            "REST API",
            "SQL-базы данных",
            "основы аутентификации",
            "автоматизированное тестирование",
            "основы deployment",
        ),
    ),
    PracticalSkillExpansion(
        pattern=re.compile(
            r"\b(software developer|software engineer|application developer|full[- ]stack developer|programmer)\b"
            r"|разработчик программ|software engineer|программист|full[- ]?stack|фулл[- ]?стек",
            flags=re.IGNORECASE,
        ),
        topics_en=(
            "programming fundamentals",
            "Git",
            "SQL basics",
            "automated testing",
            "debugging",
            "deployment basics",
        ),
        topics_ru=(
            "основы программирования",
            "Git",
            "основы SQL",
            "автоматизированное тестирование",
            "отладка",
            "основы deployment",
        ),
    ),
    PracticalSkillExpansion(
        pattern=re.compile(
            r"\b(qa tester|quality assurance|software tester|test engineer)\b"
            r"|тестировщик|qa|quality assurance|инженер.*тест",
            flags=re.IGNORECASE,
        ),
        topics_en=(
            "test case design",
            "bug reporting",
            "exploratory testing",
            "automated tests",
            "API testing",
            "Git basics",
        ),
        topics_ru=(
            "проектирование тест-кейсов",
            "описание багов",
            "исследовательское тестирование",
            "автоматизированные тесты",
            "тестирование API",
            "основы Git",
        ),
    ),
    PracticalSkillExpansion(
        pattern=re.compile(
            r"\b(cybersecurity analyst|security analyst|information security analyst|soc analyst)\b"
            r"|кибербезопас|информационн.*безопас|soc[- ]аналитик",
            flags=re.IGNORECASE,
        ),
        topics_en=(
            "networking basics",
            "Linux command line",
            "security fundamentals",
            "threat modeling",
            "log analysis",
            "incident response basics",
        ),
        topics_ru=(
            "основы сетей",
            "командная строка Linux",
            "основы безопасности",
            "моделирование угроз",
            "анализ логов",
            "основы реагирования на инциденты",
        ),
    ),
    PracticalSkillExpansion(
        pattern=re.compile(
            r"\b(ux designer|ui designer|ux/ui designer|product designer|user experience designer)\b"
            r"|ux|ui[- ]дизайн|продуктов.*дизайн|дизайн.*интерфейс",
            flags=re.IGNORECASE,
        ),
        topics_en=(
            "user research",
            "wireframing",
            "Figma",
            "usability testing",
            "interaction design",
            "portfolio case studies",
        ),
        topics_ru=(
            "user research",
            "вайрфреймы",
            "Figma",
            "usability testing",
            "interaction design",
            "портфолио-кейсы",
        ),
    ),
    PracticalSkillExpansion(
        pattern=re.compile(
            r"\b(business analyst|requirements analyst|systems analyst)\b"
            r"|бизнес[- ]аналитик|системн.*аналитик|аналитик требований",
            flags=re.IGNORECASE,
        ),
        topics_en=(
            "requirements discovery",
            "process mapping",
            "SQL basics",
            "stakeholder interviews",
            "acceptance criteria",
            "business metrics",
        ),
        topics_ru=(
            "выявление требований",
            "моделирование процессов",
            "основы SQL",
            "интервью со стейкхолдерами",
            "критерии приемки",
            "бизнес-метрики",
        ),
    ),
    PracticalSkillExpansion(
        pattern=re.compile(
            r"\b(product manager|product owner|product management)\b"
            r"|product manager|product owner|продуктов.*менедж|менеджер продукта",
            flags=re.IGNORECASE,
        ),
        topics_en=(
            "user discovery",
            "prioritization",
            "roadmapping",
            "analytics basics",
            "stakeholder communication",
            "experiment design",
        ),
        topics_ru=(
            "user discovery",
            "приоритизация",
            "roadmapping",
            "основы аналитики",
            "коммуникация со стейкхолдерами",
            "дизайн экспериментов",
        ),
    ),
    PracticalSkillExpansion(
        pattern=re.compile(
            r"\b(project manager|project coordinator|project management)\b"
            r"|проектн.*менедж|менеджер проекта|координатор проекта",
            flags=re.IGNORECASE,
        ),
        topics_en=(
            "scope planning",
            "risk management",
            "stakeholder communication",
            "timeline planning",
            "Agile/Kanban basics",
            "status reporting",
        ),
        topics_ru=(
            "планирование scope",
            "управление рисками",
            "коммуникация со стейкхолдерами",
            "планирование сроков",
            "основы Agile/Kanban",
            "статус-репортинг",
        ),
    ),
)


def practical_study_topics_for_context(
    retrieval_context: RetrievalContext,
    language_code: str,
    *,
    target_role: str = "",
    limit: int = 8,
) -> list[str]:
    """Return concrete study topics inferred from identifiable role evidence."""

    haystack_parts = [target_role]
    for chunk in retrieval_context.chunks:
        if chunk.chunk_type == "occupation":
            haystack_parts.append(_chunk_role_text(chunk))
    return practical_study_topics_for_text(
        "\n".join(part for part in haystack_parts if part),
        language_code,
        limit=limit,
    )


def practical_study_topics_for_chunk(
    chunk: RetrievedChunk,
    language_code: str,
    *,
    target_role: str = "",
    limit: int = 8,
) -> list[str]:
    """Return concrete study topics inferred from one retrieved occupation."""

    return practical_study_topics_for_text(
        "\n".join(part for part in (target_role, _chunk_role_text(chunk)) if part),
        language_code,
        limit=limit,
    )


def practical_study_topics_for_text(text: str, language_code: str, *, limit: int = 8) -> list[str]:
    """Return concrete study topics for matching role-family text."""

    topics: list[str] = []
    for expansion in _EXPANSIONS:
        if expansion.pattern.search(text):
            topics.extend(expansion.topics_ru if language_code == "ru" else expansion.topics_en)
    return _dedupe(topics)[:limit]


def merge_study_topics(
    grounded_topics: list[str],
    practical_topics: list[str],
    *,
    limit: int = 8,
) -> list[str]:
    """Merge ESCO-grounded topics with practical study topics, preserving order."""

    return _dedupe([*grounded_topics, *practical_topics])[:limit]


def _chunk_role_text(chunk: RetrievedChunk) -> str:
    return f"{chunk.title}\n{chunk.text}"


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        cleaned = " ".join(item.split()).strip()
        if not cleaned:
            continue
        normalized = cleaned.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(cleaned)
    return deduped
