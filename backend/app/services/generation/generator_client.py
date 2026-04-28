"""Generation client abstraction for stub and local GGUF-server execution."""

from __future__ import annotations

import ast
from difflib import SequenceMatcher
from functools import lru_cache
import json
import re
from typing import Any, Protocol

import httpx

from backend.app.config import settings
from backend.app.services.generation.plan_calendar import finalize_career_plan
from backend.app.services.generation.plan_guardrails import build_fallback_career_plan
from backend.app.services.generation.schemas import (
    AnswerResponse,
    CareerPlanCalendarEvent,
    CareerPlanRequest,
    CareerPlanResponse,
    CareerPlanStep,
    RetrievedChunk,
)
from backend.app.services.generation.skill_enrichment import (
    SkillEnrichment,
    build_skill_enrichment_cache_key,
    build_skill_enrichment_prompt,
    build_skill_enrichment_repair_prompt,
    fallback_skill_enrichment,
    get_cached_skill_enrichment,
    normalize_skill_enrichment_payload,
    skill_enrichment_needs_repair,
    store_cached_skill_enrichment,
)
from backend.app.services.retrieval.rag_pipeline import RetrievalContext

_THINK_TAG_PATTERN = re.compile(r"<think>.*?</think>\s*", flags=re.DOTALL)
_JSON_FENCE_PATTERN = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", flags=re.DOTALL)
_PARTIAL_ANSWER_PATTERN = re.compile(
    r'"(?P<field>direct_answer|answer)"\s*:\s*"(?P<answer>.*?)(?=",\s*"(?:cited_refs|cited_chunk_ids)"|\}\s*$|$)',
    flags=re.DOTALL,
)
_PARTIAL_REFS_PATTERN = re.compile(
    r'"(?P<field>cited_refs|cited_chunk_ids)"\s*:\s*\[(?P<refs>[^\]]*)',
    flags=re.DOTALL,
)
_INLINE_REF_PATTERN = re.compile(r"\[(\d+)\]")
_INLINE_REF_STRIP_PATTERN = re.compile(r"\s*\[\d+\](?=(?:\s|[.,;:!?)]|$))")
_LEADING_SENTENCE_PATTERN = re.compile(r"^\s*(?P<sentence>.+?(?:[.!?](?:\s|$)|$))", flags=re.DOTALL)
_WORD_PATTERN = re.compile(r"\w+", flags=re.UNICODE)


class GenerationClientError(RuntimeError):
    """Raised when the configured generation backend cannot complete a request."""


class GeneratorClient(Protocol):
    """Common interface for generation backends."""

    def generate_skill_enrichment(
        self,
        *,
        occupation: RetrievedChunk,
        target_role: str,
        language_code: str,
        user_goal: str,
    ) -> SkillEnrichment:
        """Generate practical study skills for a supported occupation."""

    def generate_answer(
        self,
        *,
        question: str,
        prompt: str,
        retrieval_context: RetrievalContext,
        memory_items: list[object],
    ) -> AnswerResponse:
        """Generate a grounded answer."""

    def generate_career_plan(
        self,
        *,
        request: CareerPlanRequest,
        prompt: str,
        retrieval_context: RetrievalContext,
        skill_enrichment: SkillEnrichment | None = None,
    ) -> CareerPlanResponse:
        """Generate a grounded structured career plan."""


class StubGeneratorClient:
    """Deterministic generation client used during scaffold and test runs."""

    def generate_skill_enrichment(
        self,
        *,
        occupation: RetrievedChunk,
        target_role: str,
        language_code: str,
        user_goal: str,
    ) -> SkillEnrichment:
        """Return ESCO-only skills in stub mode without hidden role maps."""

        del user_goal
        return fallback_skill_enrichment(
            occupation=occupation,
            language_code=language_code,
            target_role=target_role,
        )

    def generate_answer(
        self,
        *,
        question: str,
        prompt: str,
        retrieval_context: RetrievalContext,
        memory_items: list[object],
    ) -> AnswerResponse:
        """Build a transparent answer from retrieved evidence."""

        supporting_titles = ", ".join(chunk.title for chunk in retrieval_context.chunks[:2])
        answer_text = (
            f"Scaffold answer for: {question}\n\n"
            f"Top supporting context: {supporting_titles or 'no sources yet'}.\n"
            f"Stored memory used: {len(memory_items)} item(s).\n"
            "This will later be replaced by a grounded local GGUF generation step."
        )

        return AnswerResponse(
            answer=answer_text,
            citations=retrieval_context.chunks[:2],
            prompt_preview=prompt,
            memory_summary=retrieval_context.memory_summary,
        )

    def generate_career_plan(
        self,
        *,
        request: CareerPlanRequest,
        prompt: str,
        retrieval_context: RetrievalContext,
        skill_enrichment: SkillEnrichment | None = None,
    ) -> CareerPlanResponse:
        """Return a small structured plan placeholder."""

        del prompt

        return finalize_career_plan(
            request=request,
            retrieval_context=retrieval_context,
            goal=request.goal,
            target_role=request.target_role,
            steps=[
                CareerPlanStep(
                    title="Clarify target role expectations",
                    description="Review retrieved career evidence and identify the most relevant role signals.",
                ),
                CareerPlanStep(
                    title="Map current skills to the target role",
                    description="List existing strengths, missing capabilities, and business-context gaps.",
                ),
                CareerPlanStep(
                    title="Create a 30-day learning slice",
                    description="Choose one compact learning sprint that can be defended and measured.",
                ),
            ],
            citations=retrieval_context.chunks,
            skill_enrichment=skill_enrichment,
        )


class LlamaCppGeneratorClient:
    """OpenAI-compatible client for a llama.cpp-backed GGUF server runtime."""

    def __init__(self) -> None:
        self.base_url = settings.generation_base_url.rstrip("/")
        self.model_ref = settings.generation_model_artifact
        self.timeout = settings.generation_request_timeout_seconds

    def generate_skill_enrichment(
        self,
        *,
        occupation: RetrievedChunk,
        target_role: str,
        language_code: str,
        user_goal: str,
    ) -> SkillEnrichment:
        """Ask the local model for practical skills, with ESCO-only fallback."""

        cache_key = build_skill_enrichment_cache_key(
            model_artifact=self.model_ref,
            occupation=occupation,
            language_code=language_code,
            target_role=target_role,
        )
        cached = get_cached_skill_enrichment(cache_key)
        if cached is not None:
            return cached

        fallback = fallback_skill_enrichment(
            occupation=occupation,
            language_code=language_code,
            target_role=target_role,
        )
        prompt = build_skill_enrichment_prompt(
            occupation=occupation,
            target_role=target_role,
            language_code=language_code,
            user_goal=user_goal,
        )
        system_prompt = (
            "You enrich ESCO-grounded career evidence with practical beginner study skills. "
            "Return valid JSON only. Do not include markdown fences or commentary. "
            "Practical skills are model suggestions, not ESCO facts."
        )
        try:
            raw_text = self._chat_completion(
                system_prompt=system_prompt,
                user_prompt=prompt,
                max_tokens=settings.generation_skill_enrichment_max_tokens,
            )
            payload = _extract_json_object(raw_text)
            enrichment = normalize_skill_enrichment_payload(
                payload,
                occupation=occupation,
                language_code=language_code,
                target_role=target_role,
            )
            if skill_enrichment_needs_repair(
                enrichment,
                occupation=occupation,
                language_code=language_code,
            ):
                repair_prompt = build_skill_enrichment_repair_prompt(
                    occupation=occupation,
                    target_role=target_role,
                    language_code=language_code,
                    user_goal=user_goal,
                    previous_enrichment=enrichment,
                )
                repaired_text = self._chat_completion(
                    system_prompt=system_prompt,
                    user_prompt=repair_prompt,
                    max_tokens=settings.generation_skill_enrichment_max_tokens,
                )
                repaired_payload = _extract_json_object(repaired_text)
                repaired_enrichment = normalize_skill_enrichment_payload(
                    repaired_payload,
                    occupation=occupation,
                    language_code=language_code,
                    target_role=target_role,
                )
                enrichment = (
                    fallback
                    if skill_enrichment_needs_repair(
                        repaired_enrichment,
                        occupation=occupation,
                        language_code=language_code,
                    )
                    else repaired_enrichment
                )
        except GenerationClientError:
            enrichment = fallback

        store_cached_skill_enrichment(cache_key, enrichment)
        return enrichment

    def generate_answer(
        self,
        *,
        question: str,
        prompt: str,
        retrieval_context: RetrievalContext,
        memory_items: list[object],
    ) -> AnswerResponse:
        """Generate a grounded answer from the configured generation server."""

        del memory_items  # The prompt already contains the memory summary.

        system_prompt = (
            "You are a grounded career guidance assistant. "
            "Answer only from the supplied evidence, model-enriched practical skill suggestions, and memory summary. "
            "Return plain text only, not JSON. "
            "Sound like a thoughtful career coach in a normal conversation, not a database search result. "
            "Translate evidence into plain human advice rather than echoing source labels. "
            "If the evidence is insufficient, say so plainly. "
            "Do not reveal chain-of-thought or thinking tags. "
            "Follow the requested answer language exactly. "
            "Return a complete final answer and do not stop mid-sentence. "
            "Start immediately with the real answer or recommendation. "
            "Do not repeat or paraphrase the user's request. "
            "Avoid phrases like 'according to the evidence', 'the retrieved evidence', or 'as per'. "
            "Never present a skill, task, or counseling service as if it were itself a career path. "
            "If the evidence mostly covers skills rather than occupations, say that briefly and ask a short clarifying question instead of pretending the skills are jobs. "
            "If the evidence is too generic for confident role suggestions, ask one short follow-up question about strengths, interests, or preferred industries. "
            "Use inline citations like [1] or [2] for evidence references. "
            "Cite only evidence references that directly support the final answer."
        )
        raw_text = self._chat_completion(
            system_prompt=system_prompt,
            user_prompt=prompt,
            max_tokens=settings.generation_answer_max_tokens,
        )
        answer_text, citations = _extract_answer_payload(raw_text, retrieval_context, question)
        return AnswerResponse(
            answer=answer_text,
            citations=citations,
            prompt_preview=prompt,
            memory_summary=retrieval_context.memory_summary,
        )

    def generate_career_plan(
        self,
        *,
        request: CareerPlanRequest,
        prompt: str,
        retrieval_context: RetrievalContext,
        skill_enrichment: SkillEnrichment | None = None,
    ) -> CareerPlanResponse:
        """Generate a grounded structured career plan from the generation server."""

        system_prompt = (
            "You are a grounded career guidance assistant. "
            "Return only valid JSON with keys goal, target_role, and steps. "
            "Each step must contain title and description. "
            "Do not include markdown fences or commentary. "
            "Follow the requested answer language exactly for every string value."
        )
        raw_text = self._chat_completion(
            system_prompt=system_prompt,
            user_prompt=prompt,
            max_tokens=settings.generation_plan_max_tokens,
        )
        try:
            payload = _extract_json_object(raw_text)
        except GenerationClientError:
            return build_fallback_career_plan(
                request=request,
                retrieval_context=retrieval_context,
                skill_enrichment=skill_enrichment,
            )

        try:
            goal = str(payload["goal"])
            target_role = str(payload["target_role"])
            steps_payload = list(payload["steps"])
        except (KeyError, TypeError, ValueError) as exc:
            return build_fallback_career_plan(
                request=request,
                retrieval_context=retrieval_context,
                skill_enrichment=skill_enrichment,
            )

        try:
            steps = [
                CareerPlanStep(
                    title=str(step["title"]),
                    description=str(step["description"]),
                    focus_skills=[str(skill) for skill in step.get("focus_skills", []) if str(skill).strip()]
                    if isinstance(step, dict)
                    else [],
                    grounded_detail=str(step.get("grounded_detail")).strip()
                    if isinstance(step, dict) and step.get("grounded_detail") is not None
                    else None,
                    estimated_hours=float(step.get("estimated_hours"))
                    if isinstance(step, dict) and step.get("estimated_hours") is not None
                    else None,
                )
                for step in steps_payload
            ]
        except (KeyError, TypeError, ValueError):
            return build_fallback_career_plan(
                request=request,
                retrieval_context=retrieval_context,
                skill_enrichment=skill_enrichment,
            )
        if not steps:
            return build_fallback_career_plan(
                request=request,
                retrieval_context=retrieval_context,
                skill_enrichment=skill_enrichment,
            )

        raw_response = CareerPlanResponse(
            goal=goal,
            target_role=target_role,
            workload_level=str(payload.get("workload_level") or "medium"),
            estimated_weeks=int(payload.get("estimated_weeks") or 1),
            study_preferences=request.study_preferences,
            steps=steps,
            calendar_events=[
                CareerPlanCalendarEvent(
                    title=str(event["title"]),
                    description=str(event["description"]),
                    starts_at=str(event["starts_at"]),
                    ends_at=str(event["ends_at"]),
                    week_index=int(event["week_index"]),
                    step_index=int(event["step_index"]),
                    session_index=int(event.get("session_index") or 1),
                    total_sessions=int(event.get("total_sessions") or 1),
                )
                for event in payload.get("calendar_events", [])
                if isinstance(event, dict)
            ],
            citations=retrieval_context.chunks,
        )
        return finalize_career_plan(
            request=request,
            retrieval_context=retrieval_context,
            goal=raw_response.goal,
            target_role=raw_response.target_role,
            steps=raw_response.steps,
            citations=raw_response.citations,
            skill_enrichment=skill_enrichment,
        )

    def _chat_completion(self, *, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        payload = {
            "model": self.model_ref,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": settings.generation_temperature,
            "top_p": settings.generation_top_p,
            "max_tokens": max_tokens,
            "stream": False,
        }

        endpoint = f"{self.base_url}/v1/chat/completions"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(endpoint, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GenerationClientError(
                f"Could not reach the configured generation server at {endpoint}."
            ) from exc

        try:
            response_payload = response.json()
        except ValueError as exc:
            raise GenerationClientError("The generation server returned a non-JSON response.") from exc

        try:
            content = response_payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GenerationClientError(
                "The generation server returned an unexpected response payload."
            ) from exc

        if isinstance(content, list):
            content = "".join(
                str(item.get("text", ""))
                for item in content
                if isinstance(item, dict)
            )

        text = _strip_think_tags(str(content)).strip()
        if not text:
            raise GenerationClientError("The generation server returned an empty completion.")
        return text


def _strip_think_tags(text: str) -> str:
    """Remove reasoning tags that may leak from some local GGUF server configurations."""

    return _THINK_TAG_PATTERN.sub("", text).strip()


def _extract_json_object(text: str) -> dict[str, Any]:
    """Extract and parse a JSON object from a model response."""

    cleaned = _strip_think_tags(text).strip()
    for candidate in (cleaned, *_json_candidates(cleaned)):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    raise GenerationClientError("Could not parse a JSON object from the model response.")


def _extract_answer_payload(
    text: str,
    retrieval_context: RetrievalContext,
    question: str,
) -> tuple[str, list[RetrievedChunk]]:
    """Extract a grounded answer plus explicit cited chunk IDs.

    The active answer-evaluation path relies on model-selected citation IDs, not
    the full retrieved context list. If the model fails to return valid JSON, we
    preserve the raw answer text but do not pretend that every retrieved chunk
    was cited.
    """

    cleaned = _strip_think_tags(text).strip()
    try:
        payload = _extract_json_object(cleaned)
    except GenerationClientError:
        partial_answer, partial_refs = _extract_partial_answer_fields(cleaned)
        if partial_answer is not None:
            inline_refs = _INLINE_REF_PATTERN.findall(partial_answer)
            citations = _resolve_citation_refs(partial_refs or inline_refs, retrieval_context)
            cleaned_answer = _normalize_answer_text(_strip_question_restatement(partial_answer, question))
            return _strip_inline_refs(cleaned_answer), citations
        citations = _resolve_citation_refs(_INLINE_REF_PATTERN.findall(cleaned), retrieval_context)
        cleaned_answer = _normalize_answer_text(_strip_question_restatement(cleaned, question))
        return _strip_inline_refs(cleaned_answer), citations

    answer = _normalize_answer_value(payload.get("direct_answer") or payload.get("answer") or "").strip()
    if not answer:
        raise GenerationClientError("The generation server returned an empty answer payload.")

    cited_refs_raw = payload.get("cited_refs")
    if cited_refs_raw is None:
        cited_refs_raw = payload.get("cited_chunk_ids", [])
    if not isinstance(cited_refs_raw, list):
        raise GenerationClientError("The generation server returned invalid cited_refs.")

    citations = _resolve_citation_refs(cited_refs_raw, retrieval_context)
    return _strip_inline_refs(_strip_question_restatement(answer, question)), citations


def _normalize_answer_value(value: Any) -> str:
    """Convert odd model payloads into a displayable answer string."""

    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return "\n".join(f"- {item}" for item in items)
    return _normalize_answer_text(str(value))


def _normalize_answer_text(text: str) -> str:
    """Repair common small-model answer formatting failures."""

    cleaned = text.strip()
    if not cleaned:
        return cleaned

    if cleaned.startswith("[") and cleaned.endswith("]"):
        try:
            parsed = ast.literal_eval(cleaned)
        except (SyntaxError, ValueError):
            return cleaned
        if isinstance(parsed, (list, tuple)):
            items = [str(item).strip() for item in parsed if str(item).strip()]
            if items:
                return "\n".join(f"- {item}" for item in items)

    return cleaned


def _strip_inline_refs(answer: str) -> str:
    """Remove inline citation markers from the displayed answer text."""

    stripped = _INLINE_REF_STRIP_PATTERN.sub("", answer)
    stripped = re.sub(r"\s+([.,;:!?])", r"\1", stripped)
    stripped = re.sub(r"[ \t]{2,}", " ", stripped)
    stripped = re.sub(r"\n{3,}", "\n\n", stripped)
    return stripped.strip()


def _extract_partial_answer_fields(text: str) -> tuple[str | None, list[str]]:
    """Recover answer payload fields from malformed or truncated JSON-like output."""

    answer_match = _PARTIAL_ANSWER_PATTERN.search(text)
    refs_match = _PARTIAL_REFS_PATTERN.search(text)

    answer: str | None = None
    if answer_match:
        answer = answer_match.group("answer").strip()
        answer = answer.replace('\\"', '"').replace("\\n", "\n").strip()
        if not answer:
            answer = None

    raw_refs: list[str] = []
    if refs_match:
        refs_blob = refs_match.group("refs")
        raw_refs.extend(_extract_ref_tokens(refs_blob))

    return answer, raw_refs


def _extract_ref_tokens(refs_blob: str) -> list[str]:
    """Extract citation tokens from a partially formatted JSON array body."""

    tokens: list[str] = []
    for quoted in re.findall(r'"([^"]+)"', refs_blob):
        cleaned = quoted.strip()
        if cleaned:
            tokens.append(cleaned)
    for numeric in re.findall(r"\b\d+\b", refs_blob):
        if numeric not in tokens:
            tokens.append(numeric)
    return tokens


def _normalize_for_similarity(text: str) -> str:
    """Normalize text for conservative paraphrase detection."""

    return " ".join(_WORD_PATTERN.findall(text.casefold()))


def _strip_question_restatement(answer: str, question: str) -> str:
    """Remove a leading sentence that merely restates the user's question."""

    cleaned_answer = answer.strip()
    if not cleaned_answer:
        return cleaned_answer

    match = _LEADING_SENTENCE_PATTERN.match(cleaned_answer)
    if match is None:
        return cleaned_answer

    first_sentence = match.group("sentence").strip()
    normalized_question = _normalize_for_similarity(question)
    normalized_sentence = _normalize_for_similarity(first_sentence)
    if not normalized_question or not normalized_sentence:
        return cleaned_answer

    question_tokens = set(normalized_question.split())
    sentence_tokens = set(normalized_sentence.split())
    if len(question_tokens) < 4 or len(sentence_tokens) < 4:
        return cleaned_answer

    overlap_ratio = len(question_tokens & sentence_tokens) / max(len(question_tokens), 1)
    similarity_ratio = SequenceMatcher(
        None,
        normalized_question,
        normalized_sentence,
    ).ratio()

    if overlap_ratio < 0.7 and similarity_ratio < 0.82:
        return cleaned_answer

    stripped = cleaned_answer[match.end():].lstrip(" \n\t-:;,.")
    return stripped or cleaned_answer


def _resolve_citation_refs(
    cited_refs_raw: list[Any],
    retrieval_context: RetrievalContext,
) -> list[RetrievedChunk]:
    """Map model-selected citation refs back to canonical retrieved chunks."""

    chunk_by_id = {
        chunk.chunk_id: chunk
        for chunk in retrieval_context.chunks
        if chunk.chunk_id is not None
    }
    chunk_by_ref = {
        str(index): chunk
        for index, chunk in enumerate(retrieval_context.chunks, start=1)
    }
    citations: list[RetrievedChunk] = []
    seen_ids: set[str] = set()
    for raw_ref in cited_refs_raw:
        chunk = _resolve_single_citation_ref(raw_ref, chunk_by_ref, chunk_by_id)
        if chunk is None or chunk.chunk_id is None:
            continue
        if chunk.chunk_id in seen_ids:
            continue
        citations.append(chunk)
        seen_ids.add(chunk.chunk_id)
    return citations


def _resolve_single_citation_ref(
    raw_ref: Any,
    chunk_by_ref: dict[str, RetrievedChunk],
    chunk_by_id: dict[str, RetrievedChunk],
) -> RetrievedChunk | None:
    """Resolve one citation token to a retrieved chunk."""

    ref = str(raw_ref).strip()
    if not ref:
        return None

    normalized_ref = ref.strip("[]() ")
    if normalized_ref.isdigit():
        return chunk_by_ref.get(normalized_ref)

    return chunk_by_id.get(ref) or chunk_by_id.get(normalized_ref)


def _json_candidates(text: str) -> list[str]:
    """Return progressively looser JSON candidates from a free-form response."""

    candidates: list[str] = []
    fence_match = _JSON_FENCE_PATTERN.search(text)
    if fence_match:
        candidates.append(fence_match.group(1))

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(text[start : end + 1])
    return candidates


@lru_cache(maxsize=1)
def get_generator_client() -> GeneratorClient:
    """Return the configured generation backend."""

    runtime = settings.generation_runtime.lower()
    if runtime == "stub":
        return StubGeneratorClient()
    if runtime in {
        "llama.cpp",
        "llama_cpp",
        "llama-cpp-python",
        "llama_cpp_python",
        "openai-compatible",
        "openai_compatible",
    }:
        return LlamaCppGeneratorClient()
    raise ValueError(f"Unsupported generation runtime: {settings.generation_runtime}")
