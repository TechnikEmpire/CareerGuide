"""Unit tests for answer-prompt shaping."""

from __future__ import annotations

from backend.app.services.generation.prompt_builder import build_answer_prompt
from backend.app.services.generation.schemas import RetrievedChunk
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
