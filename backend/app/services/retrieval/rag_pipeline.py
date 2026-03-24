"""Dense ANN retrieval over the tracked ESCO source layer.

Reranking remains available only for explicit ablations and is disabled by
default in runtime configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from backend.app.config import settings
from backend.app.services.generation.schemas import MemoryItemPayload, RetrievedChunk
from backend.app.services.memory.hopfield_memory import summarize_memory_for_prompt
from backend.app.services.retrieval.faiss_hnsw import get_faiss_hnsw_retrieval_service
from backend.app.services.retrieval.rerank import get_reranker_provider

_CAREER_FIT_PATTERN = re.compile(
    r"\b(career|careers|role|roles|job|jobs|occupation|occupations|path|paths|fit me|transition|switch)\b"
    r"|карьер|роль|роли|работ|профес|переход",
    flags=re.IGNORECASE,
)
_PREFERENCE_SIGNAL_PATTERN = re.compile(
    r"\b(prefer|preferences|want|need|enjoy|like|strength|strengths|interests|interested|good at|"
    r"remote|async|asynchronous|hybrid|flexible|part[- ]time|full[- ]time|low[- ]stress|stress|salary|"
    r"writing|analysis|analytical|design|research|operations|management|people)\b"
    r"|предпоч|хочу|нужн|интерес|сильн|удален|гибк|стресс|аналит|дизайн|исслед|операц|менедж|люд",
    flags=re.IGNORECASE,
)
_HELPING_ROLE_SIGNAL_PATTERN = re.compile(
    r"\b(help|advise|advisor|coach|counsel|counsell|mentor|teach|teaching|guidance|guiding|therapy)\b"
    r"|помог|консульт|настав|обуч|коуч|психолог",
    flags=re.IGNORECASE,
)
_META_CAREER_ROLE_PATTERN = re.compile(
    r"\b(career guidance|career counsell|career counselor|career coach|career advice|"
    r"provide career counselling|provide career counseling|advise on career|job market offers|"
    r"labour market|labor market)\b"
    r"|консульт.*карьер|карьерн.*консульт|рынок труда",
    flags=re.IGNORECASE,
)
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?…])\s+|\n+")


@dataclass(frozen=True)
class RetrievalContext:
    chunks: list[RetrievedChunk]
    memory_summary: str


def _is_career_fit_question(question: str) -> bool:
    return _CAREER_FIT_PATTERN.search(question) is not None


def _has_preference_signal(text: str) -> bool:
    return _PREFERENCE_SIGNAL_PATTERN.search(text) is not None


def _prepare_search_query(question: str) -> str:
    """Strip generic "what career fits me" wording and keep the actual user signals."""

    if not _is_career_fit_question(question):
        return question

    segments = [
        segment.strip()
        for segment in _SENTENCE_SPLIT_PATTERN.split(question)
        if segment.strip()
    ]
    if not segments:
        return question

    focused_segments = [
        segment
        for segment in segments
        if not (_is_career_fit_question(segment) and not _has_preference_signal(segment))
    ]
    prepared = " ".join(focused_segments).strip()
    return prepared or question


def _chunk_kind_rank(question: str, chunk: RetrievedChunk) -> int:
    haystack = f"{chunk.title}\n{chunk.text}"
    if (
        _is_career_fit_question(question)
        and not _HELPING_ROLE_SIGNAL_PATTERN.search(question)
        and _META_CAREER_ROLE_PATTERN.search(haystack)
    ):
        # Treat meta-career helper roles as a worse fit than normal occupations
        # or skills when the user is asking about their own fit.
        return 2

    if chunk.chunk_type == "occupation":
        return 0
    if chunk.text.lower().startswith("esco concept kind: occupation"):
        return 0
    return 1


def _chunk_score(chunk: RetrievedChunk) -> float:
    return chunk.rerank_score or chunk.dense_score or chunk.score


def _prioritize_chunks_for_question(question: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Apply a small career-intent heuristic on top of dense ANN search."""

    if not _is_career_fit_question(question):
        return chunks

    return sorted(
        chunks,
        key=lambda chunk: (_chunk_kind_rank(question, chunk), -_chunk_score(chunk)),
    )


def build_retrieval_context(
    question: str,
    memory_items: list[MemoryItemPayload],
    top_k: int | None = None,
    use_reranker: bool | None = None,
) -> RetrievalContext:
    """Build ranked retrieval context for the assistant.

    The active path is dense-only retrieval unless reranking is explicitly
    requested. While reranking is off, the live path retrieves exactly `top_k`
    chunks and does not use `candidate_pool` as a separate runtime lever.
    """

    retrieval_service = get_faiss_hnsw_retrieval_service()
    result_count = top_k or settings.default_top_k
    reranker_enabled = settings.retrieval_enable_reranker if use_reranker is None else use_reranker
    career_fit_question = _is_career_fit_question(question)
    candidate_count = (
        max(result_count, settings.retrieval_candidate_pool_size)
        if reranker_enabled
        else max(result_count * 2, settings.retrieval_candidate_pool_size)
        if career_fit_question
        else result_count
    )
    search_query = _prepare_search_query(question)
    candidates = retrieval_service.search(search_query, candidate_count)
    if reranker_enabled:
        selected_chunks = rerank_chunks(question=question, candidates=candidates, top_k=result_count)
    else:
        selected_chunks = _prioritize_chunks_for_question(question, candidates)[:result_count]
    memory_summary = summarize_memory_for_prompt(question=question, memory_items=memory_items)
    return RetrievalContext(chunks=selected_chunks, memory_summary=memory_summary)


def rerank_chunks(question: str, candidates: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    """Rerank dense ANN candidates for explicit ablation or comparison runs."""

    if not candidates:
        return []

    reranker = get_reranker_provider()
    documents = [f"{chunk.title}\n\n{chunk.text}" for chunk in candidates]
    rerank_scores = reranker.rerank(question, documents)

    reranked = [
        RetrievedChunk(
            chunk_id=chunk.chunk_id,
            chunk_type=chunk.chunk_type,
            source_name=chunk.source_name,
            source_url=chunk.source_url,
            title=chunk.title,
            text=chunk.text,
            score=round(float(rerank_score), 4),
            dense_score=chunk.dense_score,
            rerank_score=round(float(rerank_score), 4),
        )
        for chunk, rerank_score in zip(candidates, rerank_scores, strict=True)
    ]
    reranked.sort(
        key=lambda chunk: (
            chunk.rerank_score if chunk.rerank_score is not None else float("-inf"),
            chunk.dense_score if chunk.dense_score is not None else float("-inf"),
        ),
        reverse=True,
    )
    return reranked[:top_k]
