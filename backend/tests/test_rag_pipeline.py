"""Unit tests for retrieval-context shaping heuristics."""

from __future__ import annotations

from backend.app.services.generation.schemas import RetrievedChunk
from backend.app.services.retrieval import rag_pipeline


def test_prepare_search_query_for_career_fit_keeps_preference_clause() -> None:
    prepared = rag_pipeline._prepare_search_query(
        "I prefer remote work and async collaboration. What career paths fit me?"
    )

    assert prepared == "I prefer remote work and async collaboration."


def test_prioritize_chunks_for_career_fit_questions_prefers_occupations() -> None:
    chunks = [
        RetrievedChunk(
            chunk_id="skill-1",
            chunk_type="skill_concept",
            source_name="ESCO",
            source_url="http://example.com/skill",
            title="use online tools to collaborate",
            text="ESCO concept kind: skill_concept.\nDescription (EN): Remote collaboration skill.",
            score=0.98,
            dense_score=0.98,
        ),
        RetrievedChunk(
            chunk_id="occupation-1",
            chunk_type="occupation",
            source_name="ESCO",
            source_url="http://example.com/occupation",
            title="data analyst",
            text="ESCO concept kind: occupation.\nDescription (EN): Analyse datasets and prepare reports.",
            score=0.73,
            dense_score=0.73,
        ),
    ]

    prioritized = rag_pipeline._prioritize_chunks_for_question(
        "What career paths fit me if I prefer remote async work?",
        chunks,
    )

    assert [chunk.chunk_id for chunk in prioritized] == ["occupation-1", "skill-1"]


def test_prioritize_chunks_for_career_fit_demotes_meta_career_helper_roles() -> None:
    chunks = [
        RetrievedChunk(
            chunk_id="skill-1",
            chunk_type="skill_concept",
            source_name="ESCO",
            source_url="http://example.com/skill",
            title="use online tools to collaborate",
            text="ESCO concept kind: skill_concept.\nDescription (EN): Remote collaboration skill.",
            score=0.98,
            dense_score=0.98,
        ),
        RetrievedChunk(
            chunk_id="occupation-1",
            chunk_type="occupation",
            source_name="ESCO",
            source_url="http://example.com/occupation",
            title="career guidance advisor",
            text=(
                "ESCO concept kind: occupation.\n"
                "Description (EN): Provide career guidance and counseling."
            ),
            score=0.99,
            dense_score=0.99,
        ),
    ]

    prioritized = rag_pipeline._prioritize_chunks_for_question(
        "I prefer remote work and async collaboration. What career paths fit me?",
        chunks,
    )

    assert [chunk.chunk_id for chunk in prioritized] == ["skill-1", "occupation-1"]


def test_prioritize_chunks_for_non_career_questions_keeps_dense_order() -> None:
    chunks = [
        RetrievedChunk(
            chunk_id="skill-1",
            chunk_type="skill_concept",
            source_name="ESCO",
            source_url="http://example.com/skill",
            title="use online tools to collaborate",
            text="ESCO concept kind: skill_concept.\nDescription (EN): Remote collaboration skill.",
            score=0.98,
            dense_score=0.98,
        ),
        RetrievedChunk(
            chunk_id="occupation-1",
            chunk_type="occupation",
            source_name="ESCO",
            source_url="http://example.com/occupation",
            title="data analyst",
            text="ESCO concept kind: occupation.\nDescription (EN): Analyse datasets and prepare reports.",
            score=0.73,
            dense_score=0.73,
        ),
    ]

    prioritized = rag_pipeline._prioritize_chunks_for_question(
        "What skills do data analysts need?",
        chunks,
    )

    assert [chunk.chunk_id for chunk in prioritized] == ["skill-1", "occupation-1"]
