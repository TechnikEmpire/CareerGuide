"""Generation client abstraction for stub and local GGUF-server execution."""

from __future__ import annotations

from functools import lru_cache
import json
import re
from typing import Any, Protocol

import httpx

from backend.app.config import settings
from backend.app.services.generation.schemas import (
    AnswerResponse,
    CareerPlanRequest,
    CareerPlanResponse,
    CareerPlanStep,
    RetrievedChunk,
)
from backend.app.services.retrieval.rag_pipeline import RetrievalContext

_THINK_TAG_PATTERN = re.compile(r"<think>.*?</think>\s*", flags=re.DOTALL)
_JSON_FENCE_PATTERN = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", flags=re.DOTALL)
_PARTIAL_ANSWER_PATTERN = re.compile(
    r'"answer"\s*:\s*"(?P<answer>.*?)(?=",\s*"(?:cited_refs|cited_chunk_ids)"|\}\s*$|$)',
    flags=re.DOTALL,
)
_PARTIAL_REFS_PATTERN = re.compile(
    r'"(?P<field>cited_refs|cited_chunk_ids)"\s*:\s*\[(?P<refs>[^\]]*)',
    flags=re.DOTALL,
)
_INLINE_REF_PATTERN = re.compile(r"\[(\d+)\]")


class GenerationClientError(RuntimeError):
    """Raised when the configured generation backend cannot complete a request."""


class GeneratorClient(Protocol):
    """Common interface for generation backends."""

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
    ) -> CareerPlanResponse:
        """Generate a grounded structured career plan."""


class StubGeneratorClient:
    """Deterministic generation client used during scaffold and test runs."""

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
    ) -> CareerPlanResponse:
        """Return a small structured plan placeholder."""

        return CareerPlanResponse(
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
        )


class LlamaCppGeneratorClient:
    """OpenAI-compatible client for a llama.cpp-backed GGUF server runtime."""

    def __init__(self) -> None:
        self.base_url = settings.generation_base_url.rstrip("/")
        self.model_ref = settings.generation_model_artifact
        self.timeout = settings.generation_request_timeout_seconds

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
            "Answer only from the supplied evidence and memory summary. "
            "Return only valid JSON with keys answer and cited_refs. "
            "If the evidence is insufficient, say so plainly. "
            "Do not reveal chain-of-thought or thinking tags. "
            "Follow the requested answer language exactly. "
            "Return a complete final answer and do not stop mid-sentence. "
            "Use cited_refs to name the numbered evidence items like 1 or 2. "
            "Cite only evidence references that directly support the final answer."
        )
        raw_text = self._chat_completion(
            system_prompt=system_prompt,
            user_prompt=prompt,
            max_tokens=settings.generation_answer_max_tokens,
        )
        answer_text, citations = _extract_answer_payload(raw_text, retrieval_context)
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
    ) -> CareerPlanResponse:
        """Generate a grounded structured career plan from the generation server."""

        del request  # The prompt already carries the plan request fields.

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
        payload = _extract_json_object(raw_text)

        try:
            goal = str(payload["goal"])
            target_role = str(payload["target_role"])
            steps_payload = list(payload["steps"])
        except (KeyError, TypeError, ValueError) as exc:
            raise GenerationClientError(
                "The generation server returned invalid career-plan JSON payload."
            ) from exc

        steps = [
            CareerPlanStep(
                title=str(step["title"]),
                description=str(step["description"]),
            )
            for step in steps_payload
        ]
        if not steps:
            raise GenerationClientError("The generation server returned an empty career plan.")

        return CareerPlanResponse(
            goal=goal,
            target_role=target_role,
            steps=steps,
            citations=retrieval_context.chunks,
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
            citations = _resolve_citation_refs(partial_refs, retrieval_context)
            return partial_answer, citations
        citations = _resolve_citation_refs(_INLINE_REF_PATTERN.findall(cleaned), retrieval_context)
        return cleaned, citations

    answer = str(payload.get("answer", "")).strip()
    if not answer:
        raise GenerationClientError("The generation server returned an empty answer payload.")

    cited_refs_raw = payload.get("cited_refs")
    if cited_refs_raw is None:
        cited_refs_raw = payload.get("cited_chunk_ids", [])
    if not isinstance(cited_refs_raw, list):
        raise GenerationClientError("The generation server returned invalid cited_refs.")

    citations = _resolve_citation_refs(cited_refs_raw, retrieval_context)
    return answer, citations


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
