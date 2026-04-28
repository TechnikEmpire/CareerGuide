"""Model-driven practical skill enrichment for supported ESCO occupations."""

from __future__ import annotations

from collections import OrderedDict
from hashlib import sha256
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.app.services.generation.esco_grounding import (
    extract_description,
    extract_label,
    extract_skills,
)
from backend.app.services.generation.schemas import RetrievedChunk

_CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")
_ABSTRACT_SKILL_NAME_PATTERN = re.compile(
    r"\b(?:information|knowledge|documentation|structure|types?|techniques?|processing|"
    r"concepts?|principles?|methods?|systems?|analytics?|engineering|intelligence|"
    r"business\s+\w+|data\s+(?:analytics?|engineering|processing|mining|storage|science))\b"
    r"|информац|знан|документац|структур|тип[ыа]?|техник|метод|принцип|систем",
    flags=re.IGNORECASE,
)
_OBSERVABLE_TASK_PATTERN = re.compile(
    r"\b(?:build|create|write|draft|practice|complete|analy[sz]e|compare|clean|debug|test|"
    r"design|prepare|produce|review|implement|configure|measure|map|interview|present)\b"
    r"|созда|сдел|разобр|напис|подготов|практик|выполн|проанализ|сравн|очист|отлад|тест|спроект|"
    r"реализ|настро|измер|состав|провед|презент",
    flags=re.IGNORECASE,
)
_CACHE_SIZE = 128
_CACHE: OrderedDict[str, "SkillEnrichment"] = OrderedDict()


class EnrichedSkill(BaseModel):
    """One practical study skill suggested for a matched role."""

    name: str = Field(min_length=1)
    rationale: str = ""
    study_order: int = Field(default=1, ge=1)
    effort_level: Literal["low", "medium", "high"] = "medium"
    practice_tasks: list[str] = Field(default_factory=list)
    source: Literal["model", "esco"] = "model"


class SkillEnrichment(BaseModel):
    """Validated model enrichment attached to a supported occupation."""

    role_label: str
    language_code: Literal["en", "ru"] = "en"
    skills: list[EnrichedSkill] = Field(default_factory=list)
    notes: str = ""
    used_model: bool = False

    def skill_names(self, *, limit: int = 8, include_esco: bool = True) -> list[str]:
        skills = self.skills if include_esco else [skill for skill in self.skills if skill.source == "model"]
        return _dedupe([skill.name for skill in sorted(skills, key=lambda skill: skill.study_order)])[:limit]

    def model_skill_names(self, *, limit: int = 8) -> list[str]:
        return self.skill_names(limit=limit, include_esco=False)

    def effort_levels(self) -> dict[str, str]:
        return {skill.name.casefold(): skill.effort_level for skill in self.skills}

    def practice_tasks_by_skill(self) -> dict[str, list[str]]:
        return {
            skill.name.casefold(): skill.practice_tasks
            for skill in self.skills
            if skill.practice_tasks
        }


def language_code_for_text(text: str) -> Literal["en", "ru"]:
    return "ru" if _CYRILLIC_PATTERN.search(text) else "en"


def fallback_skill_enrichment(
    *,
    occupation: RetrievedChunk | None,
    language_code: str,
    target_role: str,
) -> SkillEnrichment:
    """Build an ESCO-only fallback without adding model-invented practical skills."""

    normalized_language: Literal["en", "ru"] = "ru" if language_code == "ru" else "en"
    role_label = extract_label(occupation, normalized_language) or target_role
    skills = [
        EnrichedSkill(
            name=skill,
            rationale="ESCO skill attached to the matched occupation.",
            study_order=index,
            effort_level="medium",
            practice_tasks=[],
            source="esco",
        )
        for index, skill in enumerate(extract_skills(occupation, normalized_language), start=1)
    ]
    return SkillEnrichment(
        role_label=role_label,
        language_code=normalized_language,
        skills=skills,
        notes="ESCO-only fallback; no model practical enrichment was available.",
        used_model=False,
    )


def build_skill_enrichment_prompt(
    *,
    occupation: RetrievedChunk,
    target_role: str,
    language_code: str,
    user_goal: str,
) -> str:
    """Build the JSON-only prompt for model practical-skill enrichment."""

    normalized_language = "ru" if language_code == "ru" else "en"
    role_label = extract_label(occupation, normalized_language) or occupation.title
    description = extract_description(occupation, normalized_language)
    esco_skills = extract_skills(occupation, normalized_language)
    language_name = "Russian" if normalized_language == "ru" else "English"
    return (
        "Target role:\n"
        f"{target_role or role_label}\n\n"
        "User goal or request:\n"
        f"{user_goal or target_role or role_label}\n\n"
        "Required output language:\n"
        f"{language_name} ({normalized_language})\n\n"
        "Matched ESCO occupation evidence:\n"
        f"- Label: {role_label}\n"
        f"- Description: {description or 'No description line available.'}\n"
        f"- ESCO skills: {', '.join(esco_skills) or 'No ESCO skills listed.'}\n\n"
        "Task:\n"
        "- Use the ESCO occupation as the grounded role boundary.\n"
        "- Use your general career and learning knowledge to suggest practical study skills for a beginner transition into this role.\n"
        "- The practical skills are model suggestions, not ESCO facts. Do not claim ESCO lists them unless they appear above.\n"
        "- Prefer concrete study topics, tools, methods, and practice activities that would make a plan actionable.\n"
        "- Keep suggestions conservative and suitable for a first starter plan, not a complete professional retraining syllabus.\n\n"
        "Return valid JSON only with this exact shape:\n"
        '{"role_label":"...","skills":[{"name":"...","rationale":"...","study_order":1,'
        '"effort_level":"low|medium|high","practice_tasks":["...","..."]}],"notes":"..."}'
    )


def build_skill_enrichment_repair_prompt(
    *,
    occupation: RetrievedChunk,
    target_role: str,
    language_code: str,
    user_goal: str,
    previous_enrichment: SkillEnrichment,
) -> str:
    """Build a repair prompt when the first enrichment is too abstract."""

    normalized_language = "ru" if language_code == "ru" else "en"
    language_name = "Russian" if normalized_language == "ru" else "English"
    role_label = extract_label(occupation, normalized_language) or occupation.title
    description = extract_description(occupation, normalized_language)
    esco_skills = extract_skills(occupation, normalized_language)
    previous_skills = ", ".join(previous_enrichment.skill_names(limit=8)) or "none"
    return (
        "The previous practical-skill enrichment was too abstract for a learner-facing study plan.\n\n"
        "Target role:\n"
        f"{target_role or role_label}\n\n"
        "User goal or request:\n"
        f"{user_goal or target_role or role_label}\n\n"
        "Required output language:\n"
        f"{language_name} ({normalized_language})\n\n"
        "Matched ESCO occupation evidence:\n"
        f"- Label: {role_label}\n"
        f"- Description: {description or 'No description line available.'}\n"
        f"- ESCO skills: {', '.join(esco_skills) or 'No ESCO skills listed.'}\n\n"
        "Previous abstract skill names:\n"
        f"{previous_skills}\n\n"
        "Rewrite them into concrete beginner study topics and observable practice tasks. "
        "Do not copy ESCO taxonomy labels as skill names unless you make them specific and learner-facing. "
        "Every skill must include at least one practice task a user could do in a study session.\n\n"
        "Return valid JSON only with this exact shape:\n"
        '{"role_label":"...","skills":[{"name":"...","rationale":"...","study_order":1,'
        '"effort_level":"low|medium|high","practice_tasks":["...","..."]}],"notes":"..."}'
    )


def normalize_skill_enrichment_payload(
    payload: dict[str, Any],
    *,
    occupation: RetrievedChunk | None,
    language_code: str,
    target_role: str,
) -> SkillEnrichment:
    """Validate loose model JSON into a bounded enrichment object."""

    fallback = fallback_skill_enrichment(
        occupation=occupation,
        language_code=language_code,
        target_role=target_role,
    )
    raw_skills = payload.get("skills")
    if not isinstance(raw_skills, list):
        return fallback

    normalized_language: Literal["en", "ru"] = "ru" if language_code == "ru" else "en"
    role_label = str(payload.get("role_label") or fallback.role_label or target_role).strip()
    skills: list[EnrichedSkill] = []
    seen: set[str] = set()
    for index, raw_skill in enumerate(raw_skills[:8], start=1):
        if not isinstance(raw_skill, dict):
            continue
        name = _clean_text(raw_skill.get("name"), max_length=80)
        if not name:
            continue
        normalized = name.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        effort_level = str(raw_skill.get("effort_level") or "medium").strip().lower()
        if effort_level not in {"low", "medium", "high"}:
            effort_level = "medium"
        raw_practice_tasks = raw_skill.get("practice_tasks", [])
        if not isinstance(raw_practice_tasks, list):
            raw_practice_tasks = []
        practice_tasks = [
            task
            for task in (_clean_text(item, max_length=140) for item in raw_practice_tasks)
            if task
        ][:4]
        skills.append(
            EnrichedSkill(
                name=name,
                rationale=_clean_text(raw_skill.get("rationale"), max_length=220),
                study_order=_coerce_order(raw_skill.get("study_order"), fallback=index),
                effort_level=effort_level,  # type: ignore[arg-type]
                practice_tasks=practice_tasks,
                source="model",
            )
        )

    if not skills:
        return fallback

    return SkillEnrichment(
        role_label=role_label,
        language_code=normalized_language,
        skills=skills,
        notes=_clean_text(payload.get("notes"), max_length=300),
        used_model=True,
    )


def format_skill_enrichment_block(enrichment: SkillEnrichment | None) -> str:
    """Return prompt-ready practical skill context."""

    if enrichment is None or not enrichment.skills:
        return "No model-enriched practical skill suggestions are available; use ESCO skills only."

    source_label = (
        "Model-suggested practical study skills grounded by the matched ESCO occupation"
        if enrichment.used_model
        else "ESCO-only skills fallback"
    )
    lines = [f"{source_label}. Do not describe model suggestions as ESCO facts."]
    for skill in sorted(enrichment.skills, key=lambda item: item.study_order)[:8]:
        parts = [skill.name, f"effort: {skill.effort_level}"]
        if skill.rationale:
            parts.append(f"why: {skill.rationale}")
        if skill.practice_tasks:
            parts.append(f"practice: {'; '.join(skill.practice_tasks[:2])}")
        lines.append(f"- {' | '.join(parts)}")
    if enrichment.notes:
        lines.append(f"Notes: {enrichment.notes}")
    return "\n".join(lines)


def skill_enrichment_needs_repair(
    enrichment: SkillEnrichment,
    *,
    occupation: RetrievedChunk | None,
    language_code: str,
) -> bool:
    """Return whether model enrichment is too abstract for primary plan topics."""

    if not enrichment.used_model or not enrichment.skills:
        return False

    model_skills = [skill for skill in enrichment.skills if skill.source == "model"]
    if not model_skills:
        return True

    esco_names = {skill.casefold() for skill in extract_skills(occupation, language_code)}
    copied_esco_count = sum(1 for skill in model_skills if skill.name.casefold() in esco_names)
    abstract_count = sum(1 for skill in model_skills if _is_abstract_skill_name(skill.name))
    missing_task_count = sum(1 for skill in model_skills if not _has_observable_practice_task(skill))
    total = len(model_skills)
    return (
        copied_esco_count / total >= 0.5
        or abstract_count / total >= 0.5
        or missing_task_count / total >= 0.5
    )


def merge_skill_names(*groups: list[str], limit: int = 8) -> list[str]:
    merged: list[str] = []
    for group in groups:
        merged.extend(group)
    return _dedupe(merged)[:limit]


def learner_facing_skill_names(enrichment: SkillEnrichment | None, *, limit: int = 8) -> list[str]:
    """Return model skills suitable for visible plan topics."""

    if enrichment is None or not enrichment.used_model:
        return []
    names = [
        skill.name
        for skill in sorted(enrichment.skills, key=lambda item: item.study_order)
        if skill.source == "model"
        and not _is_abstract_skill_name(skill.name)
        and _has_observable_practice_task(skill)
    ]
    return _dedupe(names)[:limit]


def filter_learner_facing_topic_names(topics: list[str], *, limit: int = 8) -> list[str]:
    """Keep only generic, learner-facing topic names for visible plan cards."""

    return _dedupe([topic for topic in topics if not _is_abstract_skill_name(topic)])[:limit]


def build_skill_enrichment_cache_key(
    *,
    model_artifact: str,
    occupation: RetrievedChunk,
    language_code: str,
    target_role: str,
) -> str:
    evidence_hash = sha256(
        "\n".join(
            [
                occupation.chunk_id or "",
                occupation.title,
                occupation.text,
                target_role,
                language_code,
                model_artifact,
            ]
        ).encode("utf-8")
    ).hexdigest()
    return evidence_hash


def get_cached_skill_enrichment(cache_key: str) -> SkillEnrichment | None:
    cached = _CACHE.get(cache_key)
    if cached is None:
        return None
    _CACHE.move_to_end(cache_key)
    return cached


def store_cached_skill_enrichment(cache_key: str, enrichment: SkillEnrichment) -> None:
    _CACHE[cache_key] = enrichment
    _CACHE.move_to_end(cache_key)
    while len(_CACHE) > _CACHE_SIZE:
        _CACHE.popitem(last=False)


def clear_skill_enrichment_cache() -> None:
    _CACHE.clear()


def _clean_text(value: Any, *, max_length: int) -> str:
    cleaned = " ".join(str(value or "").split()).strip()
    return cleaned[:max_length].rstrip()


def _coerce_order(value: Any, *, fallback: int) -> int:
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return fallback


def _is_abstract_skill_name(name: str) -> bool:
    cleaned = " ".join(name.split()).strip()
    if not cleaned:
        return True
    token_count = len(re.findall(r"\w+", cleaned, flags=re.UNICODE))
    return token_count <= 4 and _ABSTRACT_SKILL_NAME_PATTERN.search(cleaned) is not None


def _has_observable_practice_task(skill: EnrichedSkill) -> bool:
    return any(_OBSERVABLE_TASK_PATTERN.search(task) for task in skill.practice_tasks)


def _dedupe(items: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = " ".join(item.split()).strip()
        normalized = cleaned.casefold()
        if not cleaned or normalized in seen:
            continue
        seen.add(normalized)
        output.append(cleaned)
    return output
