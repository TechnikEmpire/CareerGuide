"""Tests for model-driven practical skill enrichment."""

from __future__ import annotations

from pathlib import Path

from backend.app.services.generation.skill_enrichment import (
    build_skill_enrichment_cache_key,
    clear_skill_enrichment_cache,
    fallback_skill_enrichment,
    get_cached_skill_enrichment,
    normalize_skill_enrichment_payload,
    skill_enrichment_needs_repair,
    store_cached_skill_enrichment,
)
from backend.app.services.generation.schemas import RetrievedChunk


def _occupation() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="occupation-1",
        chunk_type="occupation",
        source_name="ESCO",
        source_url="http://example.com/occupation",
        title="data analyst",
        text=(
            "ESCO concept kind: occupation.\n"
            "English label: data analyst.\n"
            "Description (EN): Data analysts inspect and interpret collections of data.\n"
            "Essential skills (EN): business intelligence, data analytics."
        ),
        score=0.93,
    )


def test_normalize_skill_enrichment_payload_accepts_fake_model_skills() -> None:
    enrichment = normalize_skill_enrichment_payload(
        {
            "role_label": "data analyst",
            "skills": [
                {
                    "name": "Query practice",
                    "rationale": "Useful for preparing role-specific analysis.",
                    "study_order": 1,
                    "effort_level": "high",
                    "practice_tasks": ["Complete one small query exercise."],
                }
            ],
            "notes": "Starter list.",
        },
        occupation=_occupation(),
        language_code="en",
        target_role="data analyst",
    )

    assert enrichment.used_model is True
    assert enrichment.skill_names() == ["Query practice"]
    assert enrichment.effort_levels()["query practice"] == "high"
    assert enrichment.practice_tasks_by_skill()["query practice"] == ["Complete one small query exercise."]


def test_invalid_skill_enrichment_payload_falls_back_to_esco_only() -> None:
    enrichment = normalize_skill_enrichment_payload(
        {"role_label": "data analyst", "skills": "not a list"},
        occupation=_occupation(),
        language_code="en",
        target_role="data analyst",
    )

    assert enrichment.used_model is False
    assert enrichment.skill_names() == ["business intelligence", "data analytics"]
    assert {skill.source for skill in enrichment.skills} == {"esco"}


def test_abstract_model_enrichment_requires_repair() -> None:
    enrichment = normalize_skill_enrichment_payload(
        {
            "role_label": "data analyst",
            "skills": [
                {"name": "business intelligence", "study_order": 1, "practice_tasks": []},
                {"name": "information structure", "study_order": 2, "practice_tasks": []},
            ],
        },
        occupation=_occupation(),
        language_code="en",
        target_role="data analyst",
    )

    assert skill_enrichment_needs_repair(
        enrichment,
        occupation=_occupation(),
        language_code="en",
    )


def test_skill_enrichment_cache_key_includes_model_and_occupation() -> None:
    clear_skill_enrichment_cache()
    occupation = _occupation()
    first_key = build_skill_enrichment_cache_key(
        model_artifact="model-a",
        occupation=occupation,
        language_code="en",
        target_role="data analyst",
    )
    second_key = build_skill_enrichment_cache_key(
        model_artifact="model-b",
        occupation=occupation,
        language_code="en",
        target_role="data analyst",
    )
    enrichment = fallback_skill_enrichment(
        occupation=occupation,
        language_code="en",
        target_role="data analyst",
    )

    store_cached_skill_enrichment(first_key, enrichment)

    assert first_key != second_key
    assert get_cached_skill_enrichment(first_key) == enrichment
    assert get_cached_skill_enrichment(second_key) is None


def test_old_practical_skill_map_is_not_present_in_production_generation_code() -> None:
    generation_dir = Path("backend/app/services/generation")
    assert not (generation_dir / "practical_skills.py").exists()
    production_text = "\n".join(path.read_text(encoding="utf-8") for path in generation_dir.glob("*.py"))
    assert "_EXPANSIONS" not in production_text
    assert "practical_study_topics_for_context" not in production_text
