"""Prompt assembly helpers."""

from __future__ import annotations

from backend.app.services.retrieval.rag_pipeline import RetrievalContext


def build_answer_prompt(question: str, retrieval_context: RetrievalContext) -> str:
    """Build a readable prompt preview for debugging and future model calls."""

    citations = "\n".join(
        f"- {chunk.source_name}: {chunk.title}" for chunk in retrieval_context.chunks
    )
    return (
        "You are a grounded career guidance assistant.\n"
        "Answer using the retrieved evidence and the user memory summary.\n\n"
        f"Question:\n{question}\n\n"
        f"Relevant memory:\n{retrieval_context.memory_summary}\n\n"
        f"Retrieved evidence:\n{citations}"
    )
