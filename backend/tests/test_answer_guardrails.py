"""Tests for deterministic answer guardrails."""

from __future__ import annotations

from backend.app.services.generation.answer_guardrails import (
    _find_supported_occupation,
    maybe_build_guardrailed_answer,
)
from backend.app.services.generation.schemas import RetrievedChunk
from backend.app.services.generation.skill_enrichment import EnrichedSkill, SkillEnrichment
from backend.app.services.retrieval.rag_pipeline import RetrievalContext


def test_guardrails_return_clarifying_fit_answer_when_only_skill_evidence_exists() -> None:
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="skill-1",
                chunk_type="skill_concept",
                source_name="ESCO",
                source_url="http://example.com/skill",
                title="use online tools to collaborate",
                text=(
                    "ESCO concept kind: skill_concept.\n"
                    "English label: use online tools to collaborate.\n"
                    "Description (EN): Use online resources to collaborate from remote locations."
                ),
                score=0.91,
            )
        ],
        memory_summary="No memory.",
    )

    response = maybe_build_guardrailed_answer(
        question="I prefer remote work and async collaboration. What career paths fit me?",
        retrieval_context=retrieval_context,
    )

    assert response is not None
    assert "not enough for me to name the best role matches honestly" in response.text
    assert "Which kind of work sounds closer to you" in response.text
    assert [chunk.chunk_id for chunk in response.citations] == ["skill-1"]


def test_guardrails_build_clean_skill_answer_without_pm2_artifact() -> None:
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="occupation-1",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/occupation",
                title="project manager",
                text=(
                    "ESCO concept kind: occupation.\n"
                    "English label: project manager.\n"
                    "Description (EN): Coordinate project delivery.\n"
                    "Essential skills (EN): risk management, stakeholder communication, resource planning, PM² methodologies, conflict resolution."
                ),
                score=0.93,
            )
        ],
        memory_summary="No memory.",
    )

    response = maybe_build_guardrailed_answer(
        question="Can you tell me more about what skills I need to work in project management?",
        retrieval_context=retrieval_context,
    )

    assert response is not None
    assert "risk management" in response.text
    assert "stakeholder communication" in response.text
    assert "resource planning" in response.text
    assert "conflict resolution" in response.text
    assert "PM²" not in response.text
    assert [chunk.chunk_id for chunk in response.citations] == ["occupation-1"]


def test_guardrails_answer_external_resources_honestly() -> None:
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="occupation-1",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/occupation",
                title="project manager",
                text=(
                    "ESCO concept kind: occupation.\n"
                    "English label: project manager.\n"
                    "Description (EN): Coordinate project delivery.\n"
                    "Essential skills (EN): risk management, stakeholder communication, resource planning."
                ),
                score=0.93,
            )
        ],
        memory_summary="No memory.",
    )

    response = maybe_build_guardrailed_answer(
        question="Do you have any external resources you could point me to, to learn more about these?",
        retrieval_context=retrieval_context,
    )

    assert response is not None
    assert "I can’t honestly point you to external courses or websites" in response.text
    assert "study plan or a search checklist" in response.text
    assert [chunk.chunk_id for chunk in response.citations] == ["occupation-1"]


def test_guardrails_limit_explicit_unsupported_role_request() -> None:
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="occupation-1",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/occupation",
                title="career guidance advisor",
                text=(
                    "ESCO concept kind: occupation.\n"
                    "English label: career guidance advisor.\n"
                    "Description (EN): Advise adults and students on career planning."
                ),
                score=0.44,
            )
        ],
        memory_summary="No memory.",
    )

    response = maybe_build_guardrailed_answer(
        question="How do I become a stripper?",
        retrieval_context=retrieval_context,
    )

    assert response is not None
    assert response.response_kind == "limited_unsupported"
    assert "limited guidance rather than a grounded career recommendation" in response.text
    assert "locally regulated" in response.text
    assert "Transferable adjacent areas" in response.text
    assert response.citations == []


def test_guardrails_match_supported_russian_data_analytics_transition() -> None:
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="occupation-data-analyst",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/occupation/data-analyst",
                title="аналитик данных / data analyst",
                text=(
                    "ESCO concept kind: occupation.\n"
                    "Russian label: аналитик данных.\n"
                    "English label: data analyst.\n"
                    "Description (RU): Аналитики данных импортируют, проверяют, очищают, преобразуют и интерпретируют коллекции данных.\n"
                    "Essential skills (RU): анализ данных, визуализация данных, бизнес-аналитика."
                ),
                score=0.93,
            )
        ],
        memory_summary="No memory.",
    )

    question = "Я хочу перейти в аналитику данных, но мне нужен спокойный темп работы."
    skill_enrichment = SkillEnrichment(
        role_label="аналитик данных",
        language_code="ru",
        used_model=True,
        skills=[
            EnrichedSkill(
                name="SQL",
                rationale="Fake model output for this test.",
                study_order=1,
                effort_level="medium",
                practice_tasks=["Сделать короткую практическую выборку."],
            ),
            EnrichedSkill(
                name="Python и pandas",
                rationale="Fake model output for this test.",
                study_order=2,
                effort_level="medium",
                practice_tasks=["Разобрать небольшой набор данных."],
            ),
        ],
    )

    matched_occupation = _find_supported_occupation(question, retrieval_context)
    response = maybe_build_guardrailed_answer(
        question=question,
        retrieval_context=retrieval_context,
        skill_enrichment=skill_enrichment,
    )

    assert matched_occupation is not None
    assert matched_occupation.chunk_id == "occupation-data-analyst"
    assert response is not None
    assert response.response_kind == "answer"
    assert "аналитик данных" in response.text.lower()
    assert "спокойного темпа" in response.text.lower()
    assert "SQL" in response.text
    assert "Python" in response.text
    assert "нед" in response.text
    assert "ч" in response.text
    assert [chunk.chunk_id for chunk in response.citations] == ["occupation-data-analyst"]


def test_guardrails_career_fit_answer_uses_role_descriptions_naturally() -> None:
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="occupation-1",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/occupation/1",
                title="data analyst",
                text=(
                    "ESCO concept kind: occupation.\n"
                    "English label: data analyst.\n"
                    "Description (EN): Analyse datasets and prepare reports."
                ),
                score=0.91,
            ),
            RetrievedChunk(
                chunk_id="occupation-2",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/occupation/2",
                title="project coordinator",
                text=(
                    "ESCO concept kind: occupation.\n"
                    "English label: project coordinator.\n"
                    "Description (EN): Coordinate delivery timelines and stakeholder updates."
                ),
                score=0.87,
            ),
        ],
        memory_summary="No memory.",
    )

    response = maybe_build_guardrailed_answer(
        question="I prefer remote work. What careers fit me?",
        retrieval_context=retrieval_context,
    )

    assert response is not None
    assert "data analyst: work that involves analyse datasets and prepare reports" in response.text.lower()
    assert "project coordinator: work that involves coordinate delivery timelines and stakeholder updates" in response.text.lower()
