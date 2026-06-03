"""Unit tests for local generator-client parsing helpers."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.generation.generator_client import _extract_answer_payload
from backend.app.services.generation.generator_client import _extract_json_object
from backend.app.services.generation.generator_client import _strip_think_tags
from backend.app.services.generation.generator_client import LlamaCppGeneratorClient
from backend.app.services.generation.skill_enrichment import clear_skill_enrichment_cache
from backend.app.services.generation.schemas import CareerPlanRequest
from backend.app.services.generation.schemas import RetrievedChunk
from backend.app.services.retrieval.rag_pipeline import RetrievalContext


def test_strip_think_tags_removes_reasoning_block() -> None:
    text = "<think>hidden reasoning</think>\nFinal answer"
    assert _strip_think_tags(text) == "Final answer"


def test_strip_think_tags_keeps_response_after_visible_thinking_leak() -> None:
    text = (
        "Thinking Process:\n\n"
        "1. Analyze the request.\n"
        "*Self-Correction during drafting:* Keep this out of the answer.\n\n"
        "*Drafting response:*\n"
        "Both are excellent hands-on careers, but plumber is the broader target."
    )

    assert (
        _strip_think_tags(text)
        == "Both are excellent hands-on careers, but plumber is the broader target."
    )


def test_strip_think_tags_keeps_final_answer_after_visible_thinking_leak() -> None:
    text = (
        "Thinking Process:\n\n"
        "I should compare the roles briefly.\n\n"
        "Final Answer:\n"
        "Plumber is the stronger long-term career target."
    )

    assert _strip_think_tags(text) == "Plumber is the stronger long-term career target."


def test_strip_think_tags_keeps_revised_draft_after_visible_thinking_leak() -> None:
    text = (
        "Thinking Process:\n\n"
        "1. **Analyze the Request:** compare two trades.\n"
        "2. **Review Evidence:** plumber and drain technician are occupations.\n"
        "7. **Final Polish:** remove scratchpad text.\n\n"
        "Revised Draft:\n"
        "Plumber is the broader beginner target, while drain technician is more specialized."
    )

    assert (
        _strip_think_tags(text)
        == "Plumber is the broader beginner target, while drain technician is more specialized."
    )


def test_strip_think_tags_drops_visible_reasoning_without_final_marker() -> None:
    text = "Thinking Process:\n\n1. Analyze only, but never reach a final answer."

    assert _strip_think_tags(text) == ""


def test_llama_cpp_chat_completion_sends_qwen35_anti_loop_sampling(
    monkeypatch,
) -> None:
    captured_payload: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"choices": [{"message": {"content": "Final answer"}}]}

    class FakeHttpClient:
        def __init__(self, *, timeout: float) -> None:
            self.timeout = timeout

        def __enter__(self) -> "FakeHttpClient":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def post(self, endpoint: str, *, json: dict[str, object]) -> FakeResponse:
            captured_payload.update(json)
            return FakeResponse()

    monkeypatch.setattr("backend.app.services.generation.generator_client.httpx.Client", FakeHttpClient)

    client = LlamaCppGeneratorClient()
    text = client._chat_completion(
        system_prompt="system",
        user_prompt="user",
        max_tokens=settings.generation_answer_max_tokens,
    )

    assert text == "Final answer"
    assert captured_payload["temperature"] == 0.7
    assert captured_payload["top_p"] == 0.95
    assert captured_payload["top_k"] == 20
    assert captured_payload["min_p"] == 0.0
    assert captured_payload["presence_penalty"] == 1.5
    assert captured_payload["repeat_penalty"] == 1.15


def test_llama_cpp_answer_falls_back_when_thinking_cleanup_removes_completion(
    monkeypatch,
) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "choices": [
                    {
                        "message": {
                            "content": "Thinking Process:\n\n1. Analyze only and never provide a final answer."
                        }
                    }
                ]
            }

    class FakeHttpClient:
        def __init__(self, *, timeout: float) -> None:
            self.timeout = timeout

        def __enter__(self) -> "FakeHttpClient":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def post(self, endpoint: str, *, json: dict[str, object]) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr("backend.app.services.generation.generator_client.httpx.Client", FakeHttpClient)

    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="plumber",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/plumber",
                title="plumber",
                text=(
                    "ESCO concept kind: occupation.\n"
                    "English label: plumber.\n"
                    "Description (EN): Plumbers maintain and install water, gas, and sewage systems."
                ),
                score=0.9,
            )
        ],
        memory_summary="No stored user memory yet.",
    )

    response = LlamaCppGeneratorClient().generate_answer(
        question="I want to become a plumber.",
        prompt="Question:\nI want to become a plumber.",
        retrieval_context=retrieval_context,
        memory_items=[],
    )

    assert "plumber" in response.answer.lower()
    assert response.answer.startswith("Plumber is")
    assert "role involves plumbers maintain" not in response.answer.lower()
    assert "Thinking Process" not in response.answer
    assert [citation.chunk_id for citation in response.citations] == ["plumber"]


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
    assert response.calendar_events
    assert response.estimated_weeks >= 1


def test_generate_skill_enrichment_uses_model_json_and_cache(monkeypatch) -> None:
    clear_skill_enrichment_cache()
    occupation = RetrievedChunk(
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
    client = LlamaCppGeneratorClient()
    calls = {"count": 0}

    def fake_chat_completion(**_: object) -> str:
        calls["count"] += 1
        return (
            '{"role_label":"data analyst","skills":[{"name":"Query practice",'
            '"rationale":"Fake model output.","study_order":1,"effort_level":"medium",'
            '"practice_tasks":["Complete one small query exercise."]}],"notes":"Starter list."}'
        )

    monkeypatch.setattr(client, "_chat_completion", fake_chat_completion)

    first = client.generate_skill_enrichment(
        occupation=occupation,
        target_role="data analyst",
        language_code="en",
        user_goal="Build a plan.",
    )
    second = client.generate_skill_enrichment(
        occupation=occupation,
        target_role="data analyst",
        language_code="en",
        user_goal="Build a plan.",
    )

    assert calls["count"] == 1
    assert first == second
    assert first.used_model is True
    assert first.skill_names() == ["Query practice"]


def test_generate_skill_enrichment_repairs_abstract_model_output(monkeypatch) -> None:
    clear_skill_enrichment_cache()
    occupation = RetrievedChunk(
        chunk_id="occupation-repair",
        chunk_type="occupation",
        source_name="ESCO",
        source_url="http://example.com/occupation",
        title="data analyst",
        text=(
            "ESCO concept kind: occupation.\n"
            "English label: data analyst.\n"
            "Description (EN): Data analysts inspect and interpret collections of data.\n"
            "Essential skills (EN): business intelligence, information structure, documentation types."
        ),
        score=0.93,
    )
    client = LlamaCppGeneratorClient()
    responses = iter(
        [
            (
                '{"role_label":"data analyst","skills":[{"name":"business intelligence",'
                '"study_order":1,"effort_level":"medium","practice_tasks":[]},'
                '{"name":"information structure","study_order":2,"effort_level":"medium",'
                '"practice_tasks":[]}],"notes":"Abstract list."}'
            ),
            (
                '{"role_label":"data analyst","skills":[{"name":"Spreadsheet report cleanup",'
                '"rationale":"Concrete beginner practice.","study_order":1,"effort_level":"medium",'
                '"practice_tasks":["Clean a small spreadsheet and write a three-line data quality note."]}],'
                '"notes":"Repaired list."}'
            ),
        ]
    )

    monkeypatch.setattr(client, "_chat_completion", lambda **_: next(responses))

    enrichment = client.generate_skill_enrichment(
        occupation=occupation,
        target_role="data analyst",
        language_code="en",
        user_goal="Build a plan.",
    )

    assert enrichment.used_model is True
    assert enrichment.skill_names() == ["Spreadsheet report cleanup"]
    assert enrichment.practice_tasks_by_skill()["spreadsheet report cleanup"] == [
        "Clean a small spreadsheet and write a three-line data quality note."
    ]
