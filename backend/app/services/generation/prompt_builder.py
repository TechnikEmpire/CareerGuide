"""Prompt assembly helpers for grounded generation."""

from __future__ import annotations

import re

from backend.app.services.retrieval.rag_pipeline import RetrievalContext


_CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")
_EXPLORATORY_FIT_PATTERN = re.compile(
    r"\b((what|which).{0,40}(career|careers|role|roles|job|jobs|occupation|occupations|path|paths|"
    r"next step|next steps)|fit me|suit me|good for me)\b"
    r"|((какие|какой).{0,40}(карьер|роль|роли|работ|профес|следующ)|подход)",
    flags=re.IGNORECASE,
)


def _format_memory_summary(retrieval_context: RetrievalContext) -> str:
    summary = retrieval_context.memory_summary.strip()
    return summary if summary else "No stable user memory is currently stored."


def _pick_chunk_line(lines: list[str], prefixes: tuple[str, ...]) -> str:
    for prefix in prefixes:
        for line in lines:
            if line.startswith(prefix):
                return line
    return ""


def _summarize_chunk_for_prompt(chunk, language_code: str) -> str:
    """Compress raw ESCO chunk text into the fields that actually help generation."""

    lines = [line.strip() for line in chunk.text.splitlines() if line.strip()]
    label_prefixes = (
        ("Russian label:", "English label:")
        if language_code == "ru"
        else ("English label:", "Russian label:")
    )
    description_prefixes = (
        ("Description (RU):", "Definition (RU):", "Scope note (RU):", "Description (EN):")
        if language_code == "ru"
        else ("Description (EN):", "Definition (EN):", "Scope note (EN):", "Description (RU):")
    )
    skill_prefixes = (
        ("Essential skills (RU):", "Optional skills (RU):", "Essential skills (EN):")
        if language_code == "ru"
        else ("Essential skills (EN):", "Optional skills (EN):", "Essential skills (RU):")
    )

    selected_lines = [
        _pick_chunk_line(lines, ("ESCO concept kind:",)),
        _pick_chunk_line(lines, label_prefixes),
        _pick_chunk_line(lines, description_prefixes),
    ]
    if chunk.chunk_type == "occupation":
        selected_lines.append(_pick_chunk_line(lines, skill_prefixes))

    filtered_lines = [line for line in selected_lines if line]
    return "\n".join(filtered_lines) if filtered_lines else chunk.text


def _format_evidence_block(retrieval_context: RetrievalContext, language_code: str) -> str:
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
                    f"Content: {_summarize_chunk_for_prompt(chunk, language_code)}",
                ]
            )
        )
    return "\n\n".join(sections)


def _required_answer_language(question: str) -> tuple[str, str]:
    if _CYRILLIC_PATTERN.search(question):
        return ("Russian", "ru")
    return ("English", "en")


def _needs_follow_up_question(question: str) -> bool:
    return _EXPLORATORY_FIT_PATTERN.search(question) is not None


def build_answer_prompt(question: str, retrieval_context: RetrievalContext) -> str:
    """Build the grounded answer prompt sent to the generation backend."""

    language_name, language_code = _required_answer_language(question)
    follow_up_instruction = (
        "- End with one short follow-up question that keeps the dialogue moving.\n"
        if _needs_follow_up_question(question)
        else ""
    )
    return (
        "Question:\n"
        f"{question}\n\n"
        "Required answer language:\n"
        f"{language_name} ({language_code})\n\n"
        "User memory summary:\n"
        f"{_format_memory_summary(retrieval_context)}\n\n"
        "Retrieved evidence:\n"
        f"{_format_evidence_block(retrieval_context, language_code)}\n\n"
        "Instructions:\n"
        f"- Answer only in {language_name} ({language_code}). Do not switch languages.\n"
        "- Return plain text only. Do not return JSON, Python lists, or code fences.\n"
        "- Write like a helpful career coach in conversation, not like a search engine or encyclopedia.\n"
        "- Use a natural coaching tone that responds directly to the user, not a textbook or database tone.\n"
        "- Use only the retrieved evidence and the memory summary.\n"
        "- If the evidence is incomplete, say so explicitly.\n"
        "- Do not repeat, paraphrase, or restate the user's question at the start of the answer.\n"
        "- Start with the actual answer or recommendation, not with a reformulation of the request.\n"
        "- Translate the evidence into normal human language. Do not echo ESCO labels or source titles unless the role name itself is useful.\n"
        "- Avoid phrases like 'according to the evidence', 'the retrieved evidence', or 'as per'.\n"
        "- Keep the answer concise, practical, and grounded.\n"
        "- Keep the answer under 170 words.\n"
        "- Finish the answer cleanly. Do not stop mid-sentence.\n"
        "- Prefer one short paragraph followed by 2 to 4 compact bullet points when helpful.\n"
        "- If the user asks which career paths or roles fit them, name 2 to 4 role options instead of echoing evidence titles.\n"
        "- Never present a skill, task, or counseling service as if it were itself a career path.\n"
        "- If the evidence mostly covers skills rather than occupations, say that briefly and pivot to a clarifying question instead of pretending the skill names are job titles.\n"
        "- If the current evidence is too generic to support confident role suggestions, say that briefly and ask one short follow-up question about the user's strengths, interests, or preferred industries.\n"
        "- If you name possible roles, frame them as tentative options worth exploring, not as a final verdict.\n"
        f"{follow_up_instruction}"
        "- Cite supporting evidence inline using bracketed references like [1] or [2].\n"
        "- Cite only the evidence references that directly support the final answer.\n"
        "- Do not include every retrieved chunk by default.\n"
        "- Prefer 1 to 3 cited references. Omit inline citations only if no evidence supports the answer.\n"
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
        f"{_format_evidence_block(retrieval_context, language_code)}\n\n"
        "Instructions:\n"
        f"- Write all string values in {language_name} ({language_code}).\n"
        "- Return valid JSON only.\n"
        '- Use exactly this shape: {"goal": "...", "target_role": "...", "steps": [{"title": "...", "description": "..."}]}.\n'
        "- Produce 3 to 5 steps.\n"
        "- Keep every step grounded in the retrieved evidence.\n"
        "- If evidence is limited, reflect that in cautious wording rather than inventing claims.\n"
    )
