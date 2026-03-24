"""Unit tests for answer-prompt shaping."""

from __future__ import annotations

from datetime import date

from backend.app.services.generation.prompt_builder import build_answer_prompt, build_career_plan_prompt
from backend.app.services.generation.schemas import RetrievedChunk, StudyPreferences
from backend.app.services.retrieval.rag_pipeline import RetrievalContext


def _retrieval_context() -> RetrievalContext:
    return RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="chunk-1",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/occupation",
                title="data analyst",
                text=(
                    "ESCO concept kind: occupation.\n"
                    "English label: data analyst.\n"
                    "Description (EN): Analyse datasets and prepare reports."
                ),
                score=0.9,
            )
        ],
        memory_summary="Remembered preference: remote work.",
    )


def test_build_answer_prompt_adds_conversational_coaching_rules() -> None:
    prompt = build_answer_prompt(
        "I prefer remote work and async collaboration. What career paths fit me?",
        _retrieval_context(),
    )

    assert "Write like a helpful career coach in conversation" in prompt
    assert "Translate the evidence into normal human language." in prompt
    assert "Do not echo ESCO labels or source titles" in prompt
    assert "If the evidence mostly covers skills rather than occupations" in prompt
    assert "End with one short follow-up question that keeps the dialogue moving." in prompt


def test_build_answer_prompt_skips_forced_follow_up_for_non_exploratory_question() -> None:
    prompt = build_answer_prompt(
        "What skills do data analysts need?",
        _retrieval_context(),
    )

    assert "End with one short follow-up question that keeps the dialogue moving." not in prompt


def test_build_career_plan_prompt_includes_study_preferences_and_richer_shape() -> None:
    prompt = build_career_plan_prompt(
        goal="Build a transition plan into data analytics",
        target_role="Data Analyst",
        study_preferences=StudyPreferences(
            study_start_date=date(2026, 4, 6),
            preferred_study_time="evening",
            study_frequency_per_week=3,
            session_duration_minutes=90,
            timezone="America/St_Johns",
        ),
        retrieval_context=_retrieval_context(),
    )

    assert "Study preferences:" in prompt
    assert "Sessions per week: 3" in prompt
    assert '"focus_skills": ["..."]' in prompt
    assert '"estimated_hours": 4.5' in prompt
