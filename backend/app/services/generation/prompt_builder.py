"""Prompt assembly helpers for grounded generation."""

from __future__ import annotations

import re

from backend.app.services.retrieval.rag_pipeline import RetrievalContext


_CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")


def _format_memory_summary(retrieval_context: RetrievalContext) -> str:
    summary = retrieval_context.memory_summary.strip()
    return summary if summary else "No stable user memory is currently stored."


def _format_evidence_block(retrieval_context: RetrievalContext) -> str:
    if not retrieval_context.chunks:
        return "No retrieved evidence was available."

    sections: list[str] = []
    for index, chunk in enumerate(retrieval_context.chunks, start=1):
        sections.append(
            "\n".join(
                [
                    f"[{index}] {chunk.title}",
                    f"Source: {chunk.source_name}",
                    f"URL: {chunk.source_url}",
                    f"Chunk ID: {chunk.chunk_id or 'unknown'}",
                    f"Content: {chunk.text}",
                ]
            )
        )
    return "\n\n".join(sections)


def _required_answer_language(question: str) -> tuple[str, str]:
    if _CYRILLIC_PATTERN.search(question):
        return ("Russian", "ru")
    return ("English", "en")


def build_answer_prompt(question: str, retrieval_context: RetrievalContext) -> str:
    """Build the grounded answer prompt sent to the generation backend."""

    language_name, language_code = _required_answer_language(question)
    return (
        "Question:\n"
        f"{question}\n\n"
        "Required answer language:\n"
        f"{language_name} ({language_code})\n\n"
        "User memory summary:\n"
        f"{_format_memory_summary(retrieval_context)}\n\n"
        "Retrieved evidence:\n"
        f"{_format_evidence_block(retrieval_context)}\n\n"
        "Instructions:\n"
        f"- Answer only in {language_name} ({language_code}). Do not switch languages.\n"
        '- Return valid JSON only using exactly this shape: {"direct_answer": "...", "cited_refs": [1, 2]}.\n'
        "- Use only the retrieved evidence and the memory summary.\n"
        "- If the evidence is incomplete, say so explicitly.\n"
        "- Do not repeat, paraphrase, or restate the user's question at the start of the answer.\n"
        "- Start with the actual answer or recommendation, not with a reformulation of the request.\n"
        "- Keep the answer concise, practical, and grounded.\n"
        "- Keep the answer under 140 words.\n"
        "- Finish the answer cleanly. Do not stop mid-sentence.\n"
        "- Prefer one short paragraph followed by 2 to 4 compact bullet points when helpful.\n"
        "- `cited_refs` must contain the numbered evidence references like 1 or 2 from the retrieved evidence block.\n"
        "- Cite only the evidence references that directly support the final answer.\n"
        "- Do not include every retrieved chunk by default.\n"
        "- Prefer 1 to 3 cited references. Use an empty list only if no evidence supports the answer.\n"
    )


def build_career_plan_prompt(
    *,
    goal: str,
    target_role: str,
    retrieval_context: RetrievalContext,
) -> str:
    """Build the structured career-plan prompt for the generation backend."""

    language_name, language_code = _required_answer_language(goal)
    return (
        "Goal:\n"
        f"{goal}\n\n"
        "Target role:\n"
        f"{target_role}\n\n"
        "Required answer language:\n"
        f"{language_name} ({language_code})\n\n"
        "User memory summary:\n"
        f"{_format_memory_summary(retrieval_context)}\n\n"
        "Retrieved evidence:\n"
        f"{_format_evidence_block(retrieval_context)}\n\n"
        "Instructions:\n"
        f"- Write all string values in {language_name} ({language_code}).\n"
        "- Return valid JSON only.\n"
        '- Use exactly this shape: {"goal": "...", "target_role": "...", "steps": [{"title": "...", "description": "..."}]}.\n'
        "- Produce 3 to 5 steps.\n"
        "- Keep every step grounded in the retrieved evidence.\n"
        "- If evidence is limited, reflect that in cautious wording rather than inventing claims.\n"
    )
