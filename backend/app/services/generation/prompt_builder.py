"""Prompt assembly helpers for grounded generation."""

from __future__ import annotations

import re

from backend.app.services.generation.esco_grounding import extract_description, extract_label, extract_skills
from backend.app.services.generation.practical_skills import practical_study_topics_for_context
from backend.app.services.generation.schemas import StudyPreferences
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


def _summarize_chunk_for_prompt(chunk, language_code: str) -> str:
    """Compress raw ESCO chunk text into the fields that actually help generation."""

    label = extract_label(chunk, language_code)
    description = extract_description(chunk, language_code)
    skills = extract_skills(chunk, language_code)

    selected_lines = [
        f"Kind: {chunk.chunk_type or 'unknown'}",
        f"Label: {label}" if label else "",
        f"Summary: {description}" if description else "",
    ]
    if chunk.chunk_type == "occupation" and skills:
        selected_lines.append(f"Key skills: {', '.join(skills[:6])}")
    elif chunk.chunk_type == "skill_concept" and skills:
        selected_lines.append(f"Related skills: {', '.join(skills[:4])}")

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


def _format_practical_topics_block(
    retrieval_context: RetrievalContext,
    language_code: str,
    *,
    target_role: str,
) -> str:
    topics = practical_study_topics_for_context(
        retrieval_context,
        language_code,
        target_role=target_role,
    )
    if not topics:
        return "No extra practical study topics were inferred."
    return (
        "These are practical study suggestions inferred from the identifiable role family, "
        "not direct ESCO facts: "
        f"{', '.join(topics)}."
    )


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
        "Practical study topic suggestions:\n"
        f"{_format_practical_topics_block(retrieval_context, language_code, target_role=question)}\n\n"
        "Instructions:\n"
        f"- Answer only in {language_name} ({language_code}). Do not switch languages.\n"
        "- Return plain text only. Do not return JSON, Python lists, or code fences.\n"
        "- Write like a helpful career coach in conversation, not like a search engine or encyclopedia.\n"
        "- Use a natural coaching tone that responds directly to the user, not a textbook or database tone.\n"
        "- Use only the retrieved evidence, practical study topic suggestions, and the memory summary.\n"
        "- You may use the practical study topic suggestions as concrete learning topics, but do not describe them as ESCO facts.\n"
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
    study_preferences: StudyPreferences,
    retrieval_context: RetrievalContext,
) -> str:
    """Build the structured career-plan prompt for the generation backend."""

    language_name, language_code = _required_answer_language(goal)
    return (
        "Goal:\n"
        f"{goal}\n\n"
        "Target role:\n"
        f"{target_role}\n\n"
        "Study preferences:\n"
        f"- Start date: {study_preferences.study_start_date or 'auto'}\n"
        f"- Preferred study time: {study_preferences.preferred_study_time}\n"
        f"- Sessions per week: {study_preferences.study_frequency_per_week}\n"
        f"- Session duration minutes: {study_preferences.session_duration_minutes}\n"
        f"- Timezone: {study_preferences.timezone}\n\n"
        "Required answer language:\n"
        f"{language_name} ({language_code})\n\n"
        "User memory summary:\n"
        f"{_format_memory_summary(retrieval_context)}\n\n"
        "Retrieved evidence:\n"
        f"{_format_evidence_block(retrieval_context, language_code)}\n\n"
        "Practical study topic suggestions:\n"
        f"{_format_practical_topics_block(retrieval_context, language_code, target_role=target_role)}\n\n"
        "Instructions:\n"
        f"- Write all string values in {language_name} ({language_code}).\n"
        "- Return valid JSON only.\n"
        '- Use exactly this shape: {"goal": "...", "target_role": "...", "steps": [{"title": "...", "description": "...", "focus_skills": ["..."], "grounded_detail": "...", "estimated_hours": 4.5}]}.\n'
        "- Produce 3 to 5 steps.\n"
        "- Keep every step grounded in the retrieved evidence.\n"
        "- Pull useful details from role descriptions and ESCO skill lists into the step descriptions naturally.\n"
        "- Use practical study topic suggestions for concrete study progression when they are available, but do not describe them as ESCO facts.\n"
        "- Use the retrieved role description to explain what the work actually involves, not just the role title.\n"
        "- Use focus_skills for the main study topics attached to that step.\n"
        "- estimated_hours should be a realistic small-block study estimate for that step, not full professional training time.\n"
        "- If evidence is limited, reflect that in cautious wording rather than inventing claims.\n"
    )
