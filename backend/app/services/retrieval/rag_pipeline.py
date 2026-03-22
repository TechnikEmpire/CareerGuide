"""Dense ANN retrieval over the tracked ESCO source layer.

Reranking remains available only for explicit ablations and is disabled by
default in runtime configuration.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.config import settings
from backend.app.services.generation.schemas import MemoryItemPayload, RetrievedChunk
from backend.app.services.memory.hopfield_memory import summarize_memory_for_prompt
from backend.app.services.retrieval.faiss_hnsw import get_faiss_hnsw_retrieval_service
from backend.app.services.retrieval.rerank import get_reranker_provider


@dataclass(frozen=True)
class RetrievalContext:
    chunks: list[RetrievedChunk]
    memory_summary: str

def build_retrieval_context(
    question: str,
    memory_items: list[MemoryItemPayload],
    top_k: int | None = None,
    use_reranker: bool | None = None,
) -> RetrievalContext:
    """Build ranked retrieval context for the assistant.

    The active path is dense-only retrieval unless reranking is explicitly
    requested.
    """

    retrieval_service = get_faiss_hnsw_retrieval_service()
    result_count = top_k or settings.default_top_k
    candidate_count = max(result_count, settings.retrieval_candidate_pool_size)
    candidates = retrieval_service.search(question, candidate_count)
    reranker_enabled = settings.retrieval_enable_reranker if use_reranker is None else use_reranker
    if reranker_enabled:
        selected_chunks = rerank_chunks(question=question, candidates=candidates, top_k=result_count)
    else:
        selected_chunks = candidates[:result_count]
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
