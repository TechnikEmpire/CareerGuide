"""Prompt assembly helpers for grounded generation."""

from __future__ import annotations

import re

from backend.app.services.generation.esco_grounding import extract_description, extract_focus_topics, extract_label, extract_skills
from backend.app.services.generation.schemas import CareerPlanResponse, StudyPreferences
from backend.app.services.generation.skill_enrichment import SkillEnrichment, format_skill_enrichment_block, merge_skill_names
from backend.app.services.generation.study_cadence import estimate_study_cadence, format_cadence_block
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


def _format_study_cadence_block(
    retrieval_context: RetrievalContext,
    language_code: str,
    *,
    target_role: str,
    availability_text: str,
    skill_enrichment: SkillEnrichment | None = None,
    study_preferences: StudyPreferences | None = None,
    current_plan: CareerPlanResponse | None = None,
) -> str:
    topics = (
        skill_enrichment.skill_names(limit=8)
        if skill_enrichment is not None
        else extract_focus_topics(retrieval_context, language_code, limit=8)
    )
    effort_levels = skill_enrichment.effort_levels() if skill_enrichment is not None else {}
    workload_level = "medium"
    if current_plan is not None:
        workload_level = current_plan.workload_level
        current_plan_topics = [
            topic
            for step in current_plan.steps
            for topic in step.focus_skills
            if topic
        ]
        topics = merge_skill_names(topics, current_plan_topics, limit=8)
        study_preferences = current_plan.study_preferences

    estimate = estimate_study_cadence(
        role_label=target_role,
        focus_topics=topics,
        workload_level=workload_level,
        study_preferences=study_preferences,
        availability_text=availability_text,
        effort_levels=effort_levels,
    )
    return format_cadence_block(estimate, language_code)


def _format_current_plan_block(current_plan: CareerPlanResponse | None) -> str:
    if current_plan is None:
        return "No active study plan was supplied."

    preferences = current_plan.study_preferences
    focus_topics: list[str] = []
    for step in current_plan.steps:
        for topic in step.focus_skills:
            if topic and topic not in focus_topics:
                focus_topics.append(topic)

    upcoming_events = sorted(
        current_plan.calendar_events,
        key=lambda event: event.starts_at,
    )[:5]
    event_lines = [
        f"- {event.starts_at}: {event.title} ({event.event_type})"
        for event in upcoming_events
    ]
    step_lines = [
        f"- {step.title}: {', '.join(step.focus_skills[:4]) or 'no focus topics'}"
        for step in current_plan.steps[:5]
    ]
    return "\n".join(
        [
            f"Target role: {current_plan.target_role}",
            f"Workload: {current_plan.workload_level}",
            f"Study preferences: {preferences.study_frequency_per_week} sessions/week, "
            f"{preferences.session_duration_minutes} minutes, {preferences.preferred_study_time}, "
            f"timezone {preferences.timezone}",
            f"Focus topics: {', '.join(focus_topics[:8]) or 'none listed'}",
            "Steps:",
            *(step_lines or ["- No steps listed."]),
            "Upcoming sessions:",
            *(event_lines or ["- No calendar sessions listed."]),
        ]
    )


def _required_answer_language(question: str) -> tuple[str, str]:
    if _CYRILLIC_PATTERN.search(question):
        return ("Russian", "ru")
    return ("English", "en")


def _needs_follow_up_question(question: str) -> bool:
    return _EXPLORATORY_FIT_PATTERN.search(question) is not None


def build_answer_prompt(
    question: str,
    retrieval_context: RetrievalContext,
    *,
    current_plan: CareerPlanResponse | None = None,
    skill_enrichment: SkillEnrichment | None = None,
) -> str:
    """Build the grounded answer prompt sent to the generation backend."""

    language_name, language_code = _required_answer_language(question)
    memory_summary = _format_memory_summary(retrieval_context)
    availability_text = f"{question}\n{memory_summary}"
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
        f"{memory_summary}\n\n"
        "Retrieved evidence:\n"
        f"{_format_evidence_block(retrieval_context, language_code)}\n\n"
        "Model-enriched practical skill suggestions:\n"
        f"{format_skill_enrichment_block(skill_enrichment)}\n\n"
        "Study cadence guidance:\n"
        f"{_format_study_cadence_block(retrieval_context, language_code, target_role=question, availability_text=availability_text, current_plan=current_plan, skill_enrichment=skill_enrichment)}\n\n"
        "Current active study plan, if supplied:\n"
        f"{_format_current_plan_block(current_plan)}\n\n"
        "Instructions:\n"
        f"- Answer only in {language_name} ({language_code}). Do not switch languages.\n"
        "- Return plain text only. Do not return JSON, Python lists, or code fences.\n"
        "- Write like a helpful career coach in conversation, not like a search engine or encyclopedia.\n"
        "- Use a natural coaching tone that responds directly to the user, not a textbook or database tone.\n"
        "- Use only the retrieved evidence, model-enriched practical skill suggestions, and the memory summary.\n"
        "- You may use model-enriched practical skill suggestions as concrete learning topics, but do not describe them as ESCO facts.\n"
        "- When concrete learning topics are available, include one light study-cadence estimate using the cadence guidance.\n"
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
        "- If the user asks to modify the active study plan, discuss the requested change against the supplied current plan. "
        "Do not claim it has been saved unless the application presents an explicit apply action.\n"
    )


def build_career_plan_prompt(
    *,
    goal: str,
    target_role: str,
    study_preferences: StudyPreferences,
    retrieval_context: RetrievalContext,
    skill_enrichment: SkillEnrichment | None = None,
) -> str:
    """Build the structured career-plan prompt for the generation backend."""

    language_name, language_code = _required_answer_language(goal)
    memory_summary = _format_memory_summary(retrieval_context)
    availability_text = f"{goal}\n{target_role}\n{memory_summary}"
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
        f"{memory_summary}\n\n"
        "Retrieved evidence:\n"
        f"{_format_evidence_block(retrieval_context, language_code)}\n\n"
        "Model-enriched practical skill suggestions:\n"
        f"{format_skill_enrichment_block(skill_enrichment)}\n\n"
        "Study cadence guidance:\n"
        f"{_format_study_cadence_block(retrieval_context, language_code, target_role=target_role, availability_text=availability_text, study_preferences=study_preferences, skill_enrichment=skill_enrichment)}\n\n"
        "Instructions:\n"
        f"- Write all string values in {language_name} ({language_code}).\n"
        "- Return valid JSON only.\n"
        '- Use exactly this shape: {"goal": "...", "target_role": "...", "steps": [{"title": "...", "description": "...", "focus_skills": ["..."], "grounded_detail": "...", "estimated_hours": 4.5}]}.\n'
        "- Produce 3 to 5 steps.\n"
        "- Keep every step grounded in the retrieved evidence.\n"
        "- Use retrieved role descriptions to keep the plan within the supported occupation boundary.\n"
        "- Do not turn abstract ESCO taxonomy labels into milestone titles or primary focus_skills unless they are rewritten as concrete learner-facing study topics.\n"
        "- Use model-enriched practical skill suggestions for concrete study progression when they are available, but do not describe them as ESCO facts.\n"
        "- Use the study cadence guidance to make estimated_hours realistic and schedule-ready.\n"
        "- Use the retrieved role description to explain what the work actually involves, not just the role title.\n"
        "- Use focus_skills for the main study topics attached to that step.\n"
        "- estimated_hours should be a realistic small-block study estimate for that step, not full professional training time.\n"
        "- If evidence is limited, reflect that in cautious wording rather than inventing claims.\n"
    )
