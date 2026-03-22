"""Hybrid retrieval scaffold.

The demo chunks below are bilingual scaffold summaries written for repository
development only. They are not the final authoritative corpus. Their purpose is
to keep the early retrieval path inspectable in both English and Russian while
the real ingestion pipeline is still being implemented.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.config import settings
from backend.app.services.generation.schemas import MemoryItemPayload, RetrievedChunk
from backend.app.services.memory.hopfield_memory import summarize_memory_for_prompt
from backend.app.services.retrieval.dense_search import dense_similarity_score
from backend.app.services.retrieval.embeddings import DeterministicHashEmbeddingProvider
from backend.app.services.retrieval.lexical_search import lexical_overlap_score
from backend.app.services.retrieval.rerank import combine_scores


@dataclass(frozen=True)
class DemoChunk:
    source_name: str
    source_url: str
    title: str
    text: str


@dataclass(frozen=True)
class RetrievalContext:
    chunks: list[RetrievedChunk]
    memory_summary: str


DEMO_CHUNKS = [
    DemoChunk(
        source_name="O*NET",
        source_url="https://www.onetonline.org/",
        title="Software Developers",
        text=(
            "Software developers design and modify computer applications. "
            "The role typically requires programming, systems thinking, and collaboration. "
            "Разработчики программного обеспечения проектируют и изменяют компьютерные приложения. "
            "Эта роль обычно требует программирования, системного мышления и сотрудничества."
        ),
    ),
    DemoChunk(
        source_name="ESCO",
        source_url="https://esco.ec.europa.eu/",
        title="Data Analyst Skills",
        text=(
            "Data analysts interpret structured information, communicate findings clearly, "
            "and translate business questions into analytical tasks. "
            "Аналитики данных интерпретируют структурированную информацию, ясно объясняют выводы "
            "и переводят бизнес-вопросы в аналитические задачи."
        ),
    ),
    DemoChunk(
        source_name="WHO",
        source_url="https://www.who.int/",
        title="Mental Health at Work",
        text=(
            "Healthy work design includes manageable workload, role clarity, and supportive "
            "work environments that reduce chronic stress. "
            "Здоровая организация труда включает управляемую нагрузку, ясность роли "
            "и поддерживающую рабочую среду, снижающую хронический стресс."
        ),
    ),
]


embedder = DeterministicHashEmbeddingProvider(vector_size=settings.memory_vector_size)


def build_retrieval_context(
    question: str,
    memory_items: list[MemoryItemPayload],
    top_k: int | None = None,
) -> RetrievalContext:
    """Build ranked retrieval context for the assistant.

    The scaffold uses a tiny in-memory corpus so the surrounding pipeline can be
    exercised immediately. The shape of the returned object is intentionally close
    to what the real retrieval stack will need later.
    """

    ranked_chunks: list[tuple[float, RetrievedChunk]] = []
    for chunk in DEMO_CHUNKS:
        lexical = lexical_overlap_score(question, chunk.text)
        dense = dense_similarity_score(question, chunk.text, embedder=embedder)
        combined_score = combine_scores(lexical_score=lexical, dense_score=dense)

        ranked_chunks.append(
            (
                combined_score,
                RetrievedChunk(
                    source_name=chunk.source_name,
                    source_url=chunk.source_url,
                    title=chunk.title,
                    text=chunk.text,
                    score=round(combined_score, 4),
                ),
            )
        )

    ranked_chunks.sort(key=lambda item: item[0], reverse=True)
    selected_chunks = [item[1] for item in ranked_chunks[: top_k or settings.default_top_k]]
    memory_summary = summarize_memory_for_prompt(question=question, memory_items=memory_items)
    return RetrievalContext(chunks=selected_chunks, memory_summary=memory_summary)
