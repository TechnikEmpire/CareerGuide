"""Tests for legacy answer guardrail boundaries."""

from __future__ import annotations

from backend.app.services.generation.answer_guardrails import (
    _find_supported_occupation,
    maybe_build_guardrailed_answer,
)
from backend.app.services.generation.schemas import RetrievedChunk
from backend.app.services.retrieval.rag_pipeline import RetrievalContext


def test_guardrails_do_not_intercept_normal_career_fit_chat() -> None:
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

    assert response is None


def test_guardrails_do_not_intercept_normal_skill_chat() -> None:
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

    assert response is None


def test_guardrails_do_not_intercept_external_resource_chat() -> None:
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

    assert response is None


def test_guardrails_do_not_intercept_explicit_unsupported_role_chat() -> None:
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

    assert response is None


def test_guardrails_match_supported_russian_data_analytics_without_intercepting() -> None:
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
    matched_occupation = _find_supported_occupation(question, retrieval_context)
    response = maybe_build_guardrailed_answer(
        question=question,
        retrieval_context=retrieval_context,
    )

    assert matched_occupation is not None
    assert matched_occupation.chunk_id == "occupation-data-analyst"
    assert response is None


def test_supported_role_matching_prefers_exact_alternate_label() -> None:
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="occupation-piano-maker",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/occupation/piano-maker",
                title="piano maker",
                text=(
                    "ESCO concept kind: occupation.\n"
                    "English label: piano maker.\n"
                    "English alternate labels: piano technician, piano builder.\n"
                    "Description (EN): Piano makers create and assemble parts to make pianos."
                ),
                score=0.93,
            ),
            RetrievedChunk(
                chunk_id="occupation-musician",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/occupation/musician",
                title="musician",
                text=(
                    "ESCO concept kind: occupation.\n"
                    "English label: musician.\n"
                    "English alternate labels: orchestra musician, guitarist, pianist, violinist.\n"
                    "Description (EN): Musicians perform music for audiences or recordings."
                ),
                score=0.88,
            ),
        ],
        memory_summary="No memory.",
    )

    matched_occupation = _find_supported_occupation(
        "So, what about being a pianist?",
        retrieval_context,
    )

    assert matched_occupation is not None
    assert matched_occupation.chunk_id == "occupation-musician"


def test_guardrails_do_not_intercept_career_fit_chat() -> None:
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

    assert response is None
