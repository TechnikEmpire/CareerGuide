"""Unit tests for local generator-client parsing helpers."""

from __future__ import annotations

from backend.app.services.generation.generator_client import _extract_answer_payload
from backend.app.services.generation.generator_client import _extract_json_object
from backend.app.services.generation.generator_client import _strip_think_tags
from backend.app.services.generation.generator_client import LlamaCppGeneratorClient
from backend.app.services.generation.schemas import CareerPlanRequest
from backend.app.services.generation.schemas import RetrievedChunk
from backend.app.services.retrieval.rag_pipeline import RetrievalContext


def test_strip_think_tags_removes_reasoning_block() -> None:
    text = "<think>hidden reasoning</think>\nFinal answer"
    assert _strip_think_tags(text) == "Final answer"


def test_extract_json_object_reads_fenced_json() -> None:
    payload = _extract_json_object(
        "```json\n"
        '{"goal":"become a developer","target_role":"software developer","steps":[{"title":"Study","description":"Start small"}]}\n'
        "```"
    )
    assert payload["goal"] == "become a developer"
    assert payload["steps"][0]["title"] == "Study"


def test_extract_json_object_ignores_think_tags() -> None:
    payload = _extract_json_object(
        "<think>do not expose this</think>"
        '{"goal":"grow","target_role":"analyst","steps":[{"title":"Map skills","description":"Compare evidence"}]}'
    )
    assert payload["target_role"] == "analyst"


def test_extract_answer_payload_uses_explicit_cited_chunk_ids() -> None:
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="chunk-1",
                source_name="ESCO",
                source_url="http://example.com/1",
                title="Chunk 1",
                text="First chunk",
                score=0.9,
            ),
            RetrievedChunk(
                chunk_id="chunk-2",
                source_name="ESCO",
                source_url="http://example.com/2",
                title="Chunk 2",
                text="Second chunk",
                score=0.8,
            ),
        ],
        memory_summary="No memory.",
    )

    answer, citations = _extract_answer_payload(
        '{"direct_answer":"Grounded answer","cited_chunk_ids":["chunk-2","chunk-1","chunk-2"]}',
        retrieval_context,
        "What should I do next?",
    )

    assert answer == "Grounded answer"
    assert [chunk.chunk_id for chunk in citations] == ["chunk-2", "chunk-1"]


def test_extract_answer_payload_resolves_numeric_evidence_refs() -> None:
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="chunk-1",
                source_name="ESCO",
                source_url="http://example.com/1",
                title="Chunk 1",
                text="First chunk",
                score=0.9,
            ),
            RetrievedChunk(
                chunk_id="chunk-2",
                source_name="ESCO",
                source_url="http://example.com/2",
                title="Chunk 2",
                text="Second chunk",
                score=0.8,
            ),
        ],
        memory_summary="No memory.",
    )

    answer, citations = _extract_answer_payload(
        '{"direct_answer":"Grounded answer","cited_refs":[2,1,2]}',
        retrieval_context,
        "What should I do next?",
    )

    assert answer == "Grounded answer"
    assert [chunk.chunk_id for chunk in citations] == ["chunk-2", "chunk-1"]


def test_extract_answer_payload_salvages_partial_json_and_refs() -> None:
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="chunk-1",
                source_name="ESCO",
                source_url="http://example.com/1",
                title="Chunk 1",
                text="First chunk",
                score=0.9,
            ),
            RetrievedChunk(
                chunk_id="chunk-2",
                source_name="ESCO",
                source_url="http://example.com/2",
                title="Chunk 2",
                text="Second chunk",
                score=0.8,
            ),
        ],
        memory_summary="No memory.",
    )

    answer, citations = _extract_answer_payload(
        '{"direct_answer":"Grounded answer","cited_refs":[2,1',
        retrieval_context,
        "What should I do next?",
    )

    assert answer == "Grounded answer"
    assert [chunk.chunk_id for chunk in citations] == ["chunk-2", "chunk-1"]


def test_extract_answer_payload_falls_back_to_plain_text_without_fake_citations() -> None:
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="chunk-1",
                source_name="ESCO",
                source_url="http://example.com/1",
                title="Chunk 1",
                text="First chunk",
                score=0.9,
            )
        ],
        memory_summary="No memory.",
    )

    answer, citations = _extract_answer_payload(
        "Plain text answer",
        retrieval_context,
        "What should I do next?",
    )

    assert answer == "Plain text answer"
    assert citations == []


def test_extract_answer_payload_repairs_python_list_like_plain_text() -> None:
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="chunk-1",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/1",
                title="Remote-friendly role",
                text="First chunk",
                score=0.9,
            )
        ],
        memory_summary="No memory.",
    )

    answer, citations = _extract_answer_payload(
        "['Data analyst', 'UX researcher', 'Technical writer']",
        retrieval_context,
        "What career paths fit me?",
    )

    assert answer == "- Data analyst\n- UX researcher\n- Technical writer"
    assert citations == []


def test_extract_answer_payload_reads_inline_citations_from_plain_text() -> None:
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="chunk-1",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/1",
                title="Data analyst",
                text="First chunk",
                score=0.9,
            ),
            RetrievedChunk(
                chunk_id="chunk-2",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/2",
                title="Project coordinator",
                text="Second chunk",
                score=0.8,
            ),
        ],
        memory_summary="No memory.",
    )

    answer, citations = _extract_answer_payload(
        "Data analyst and project coordinator are the strongest current fits [1] [2].",
        retrieval_context,
        "What career paths fit me?",
    )

    assert answer == "Data analyst and project coordinator are the strongest current fits."
    assert [chunk.chunk_id for chunk in citations] == ["chunk-1", "chunk-2"]


def test_extract_answer_payload_strips_leading_question_restatement() -> None:
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="chunk-1",
                source_name="ESCO",
                source_url="http://example.com/1",
                title="Chunk 1",
                text="First chunk",
                score=0.9,
            )
        ],
        memory_summary="No memory.",
    )

    answer, citations = _extract_answer_payload(
        (
            '{"direct_answer":"Я предпочитаю удаленную работу и мне нужен низкострессовый переход '
            'в аналитику данных. Сфокусируйтесь на ролях аналитика данных с удаленным форматом '
            'и начинайте с небольших SQL-задач.","cited_refs":[1]}'
        ),
        retrieval_context,
        "Я предпочитаю удаленную работу и мне нужен низкострессовый переход в аналитику данных.",
    )

    assert answer.startswith("Сфокусируйтесь на ролях аналитика данных")
    assert [chunk.chunk_id for chunk in citations] == ["chunk-1"]


def test_generate_career_plan_falls_back_when_model_returns_invalid_json(
    monkeypatch,
) -> None:
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
    request = CareerPlanRequest(
        user_id="demo-user",
        goal="Build a transition plan into project management",
        target_role="Project Manager",
    )

    client = LlamaCppGeneratorClient()
    monkeypatch.setattr(
        client,
        "_chat_completion",
        lambda **_: "not valid json at all",
    )

    response = client.generate_career_plan(
        request=request,
        prompt="prompt",
        retrieval_context=retrieval_context,
    )

    assert response.goal == request.goal
    assert response.target_role == request.target_role
    assert len(response.steps) == 4
