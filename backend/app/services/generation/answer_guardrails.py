"""Intent-aware answer guardrails for common low-quality chat cases."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re

from backend.app.services.generation.schemas import RetrievedChunk
from backend.app.services.retrieval.rag_pipeline import RetrievalContext

_CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")
_CAREER_FIT_PATTERN = re.compile(
    r"\b(career|careers|role|roles|job|jobs|occupation|occupations|path|paths|fit me|suit me)\b"
    r"|карьер|роль|роли|работ|профес|подход",
    flags=re.IGNORECASE,
)
_SKILL_QUESTION_PATTERN = re.compile(
    r"\b(skill|skills|what do i need|need to work|need for|need to become|qualifications)\b"
    r"|навык|навыки|умени|квалифик|что нужно",
    flags=re.IGNORECASE,
)
_EXTERNAL_RESOURCES_PATTERN = re.compile(
    r"\b(resource|resources|course|courses|learn more|read more|book|books|article|articles|"
    r"website|websites|guide|guides|tutorial|tutorials|certification|certifications|links)\b"
    r"|ресурс|ресурсы|курс|курсы|почитать|книг|стать|сайт|ссыл|гайд|руководств|туториал|сертифик",
    flags=re.IGNORECASE,
)
_META_ROLE_PATTERN = re.compile(
    r"\b(career guidance|career counsell|career counselor|career coach|career advice|"
    r"career counselling|career counseling|advise on career|provide career counselling|"
    r"provide career counseling)\b"
    r"|консульт.*карьер|карьерн.*консульт",
    flags=re.IGNORECASE,
)
_SHORT_WEIRD_SKILL_PATTERN = re.compile(r"\d")
_PM_METHODOLOGY_PATTERN = re.compile(r"\bpm\b|²", flags=re.IGNORECASE)
_EXPLICIT_TARGET_REQUEST_PATTERN = re.compile(
    r"\b(become|be a|be an|work as|transition into|move into|go into|pursue|target role|"
    r"plan into|plan for|how do i become|how can i become|want to be)\b"
    r"|как стать|стать|работать как|перейти в|целевая роль|план перехода|хочу быть",
    flags=re.IGNORECASE,
)
_WORD_PATTERN = re.compile(r"\w+", flags=re.UNICODE)
_ROLE_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "be",
    "become",
    "build",
    "can",
    "career",
    "careers",
    "for",
    "goal",
    "how",
    "i",
    "into",
    "job",
    "jobs",
    "me",
    "move",
    "my",
    "path",
    "paths",
    "plan",
    "role",
    "roles",
    "target",
    "the",
    "to",
    "transition",
    "want",
    "what",
    "work",
    "would",
    "как",
    "кем",
    "мне",
    "моя",
    "мое",
    "мои",
    "переход",
    "план",
    "путь",
    "роль",
    "роли",
    "работа",
    "работать",
    "стать",
    "хочу",
    "целевая",
}


@dataclass(frozen=True)
class GuardrailedAnswer:
    """Deterministic answer returned before free-form generation."""

    text: str
    citations: list[RetrievedChunk]
    response_kind: str = "answer"


class UnsupportedGuidanceRequestError(RuntimeError):
    """Raised when the current corpus cannot support a grounded guidance request."""


def maybe_build_guardrailed_answer(
    *,
    question: str,
    retrieval_context: RetrievalContext,
) -> GuardrailedAnswer | None:
    """Return a deterministic answer for the most failure-prone chat intents."""

    for builder in (
        _build_unsupported_answer,
        _build_external_resources_answer,
        _build_skill_answer,
        _build_career_fit_answer,
    ):
        answer = builder(question=question, retrieval_context=retrieval_context)
        if answer is not None:
            return answer
    return None


def ensure_grounded_plan_support(
    *,
    goal: str,
    target_role: str,
    retrieval_context: RetrievalContext,
) -> None:
    """Reject plans for roles that are not grounded in the current corpus."""

    if _has_supported_role_grounding(target_role, retrieval_context):
        return

    language_code = _language_code(f"{goal}\n{target_role}")
    if language_code == "ru":
        raise UnsupportedGuidanceRequestError(
            "Я не могу построить надежный план для этой цели, потому что текущая база "
            "не дает достаточно уверенного совпадения с поддерживаемой ролью или "
            "переходом. Попробуйте более стандартную должность или соседнюю карьерную область."
        )

    raise UnsupportedGuidanceRequestError(
        "I can’t build a grounded plan for that goal yet, because the current knowledge base "
        "does not show a strong enough match for a supported role or transition. "
        "Try a more standard job title or a nearby career area."
    )


def _build_unsupported_answer(
    *,
    question: str,
    retrieval_context: RetrievalContext,
) -> GuardrailedAnswer | None:
    if not _EXPLICIT_TARGET_REQUEST_PATTERN.search(question):
        return None
    if _has_supported_role_grounding(question, retrieval_context):
        return None

    language_code = _language_code(question)
    if language_code == "ru":
        return GuardrailedAnswer(
            text=(
                "Я не могу надежно дать карьерную рекомендацию по этому запросу, потому что "
                "текущая база не показывает достаточно уверенного совпадения с поддерживаемой "
                "ролью или карьерным переходом. Я могу помогать только там, где запрос "
                "хорошо опирается на доступные карьерные данные. Попробуйте назвать более "
                "стандартную должность или соседнюю карьерную область."
            ),
            citations=[],
            response_kind="refusal",
        )

    return GuardrailedAnswer(
        text=(
            "I can’t provide grounded career guidance for that request yet, because the current "
            "knowledge base does not show a strong enough match for a supported role or career "
            "transition. I can help only where the request maps clearly onto the available "
            "career data. Try a more standard job title or a nearby career area."
        ),
        citations=[],
        response_kind="refusal",
    )


def _build_external_resources_answer(
    *,
    question: str,
    retrieval_context: RetrievalContext,
) -> GuardrailedAnswer | None:
    if _EXTERNAL_RESOURCES_PATTERN.search(question) is None:
        return None

    language_code = _language_code(question)
    occupation = _first_useful_occupation(retrieval_context)
    skills = _extract_skills(occupation, language_code) if occupation else []
    skill_summary = _join_list(skills[:3], language_code)
    citations = [occupation] if occupation is not None else retrieval_context.chunks[:1]

    if language_code == "ru":
        if skill_summary:
            answer = (
                "Я пока не могу честно дать внешние курсы, книги или сайты из текущей базы, "
                "потому что она содержит роли и навыки ESCO, а не каталог учебных ресурсов. "
                f"Зато уже видно, что стоит изучать в первую очередь: {skill_summary}. "
                "Если хотите, я могу сразу превратить это в короткий учебный план или в чеклист для самостоятельного поиска."
            )
        else:
            answer = (
                "Я пока не могу честно дать внешние курсы, книги или сайты из текущей базы, "
                "потому что она содержит роли и навыки ESCO, а не каталог учебных ресурсов. "
                "Если хотите, я могу вместо этого собрать короткий учебный план или чеклист для самостоятельного поиска."
            )
        return GuardrailedAnswer(text=answer, citations=citations)

    if skill_summary:
        answer = (
            "I can’t honestly point you to external courses or websites from the current knowledge base yet, "
            "because it contains ESCO role and skill data rather than a curated learning-resources catalog. "
            f"What it does show clearly is that the next topics to learn are {skill_summary}. "
            "If you want, I can turn that into a short study plan or a search checklist."
        )
    else:
        answer = (
            "I can’t honestly point you to external courses or websites from the current knowledge base yet, "
            "because it contains ESCO role and skill data rather than a curated learning-resources catalog. "
            "If you want, I can turn the relevant skill areas into a short study plan or a search checklist instead."
        )
    return GuardrailedAnswer(text=answer, citations=citations)


def _build_skill_answer(
    *,
    question: str,
    retrieval_context: RetrievalContext,
) -> GuardrailedAnswer | None:
    if _SKILL_QUESTION_PATTERN.search(question) is None:
        return None

    language_code = _language_code(question)
    occupation = _first_useful_occupation(retrieval_context)
    if occupation is not None:
        role_label = _extract_label(occupation, language_code)
        skills = _extract_skills(occupation, language_code)
        if skills:
            skill_summary = _join_list(skills[:4], language_code)
            if language_code == "ru":
                answer = (
                    f"Для роли {role_label} в текущих данных важнее всего {skill_summary}. "
                    "Это хороший базовый набор, с которого стоит начинать. "
                    "Если хотите, я могу дальше разложить это на начальный уровень, практику и портфолио."
                )
            else:
                answer = (
                    f"For {role_label}, the clearest skills in the current data are {skill_summary}. "
                    "That is a solid baseline to start with. "
                    "If you want, I can break these into beginner study, practical exercises, and portfolio work next."
                )
            return GuardrailedAnswer(text=answer, citations=[occupation])

    top_skill_chunks = [chunk for chunk in retrieval_context.chunks if chunk.chunk_type == "skill_concept"]
    top_skill_labels = [
        _extract_label(chunk, language_code)
        for chunk in top_skill_chunks
        if _extract_label(chunk, language_code)
    ]
    if not top_skill_labels:
        return None

    skill_summary = _join_list(_dedupe_strings(top_skill_labels)[:4], language_code)
    if language_code == "ru":
        answer = (
            f"По текущим данным здесь важнее всего такие направления навыков: {skill_summary}. "
            "Если хотите, я могу дальше разложить их по приоритету и предложить порядок изучения."
        )
    else:
        answer = (
            f"The clearest skill areas here are {skill_summary}. "
            "If you want, I can rank them by priority and suggest a sensible learning order."
        )
    return GuardrailedAnswer(text=answer, citations=top_skill_chunks[:2])


def _build_career_fit_answer(
    *,
    question: str,
    retrieval_context: RetrievalContext,
) -> GuardrailedAnswer | None:
    if _CAREER_FIT_PATTERN.search(question) is None:
        return None

    language_code = _language_code(question)
    occupations = _useful_occupations(retrieval_context)
    if len(occupations) >= 2:
        role_labels = [_extract_label(chunk, language_code) for chunk in occupations[:3]]
        role_summary = _join_list(role_labels, language_code)
        if language_code == "ru":
            answer = (
                f"С тем, что я знаю сейчас, я бы в первую очередь рассмотрел такие направления: {role_summary}. "
                "Пока держу это как предварительные варианты, потому что у меня уже есть ваш предпочтительный формат работы, "
                "но еще мало данных о типе задач. "
                "Что вам ближе в повседневной работе: анализ, координация, письмо/документация или исследование?"
            )
        else:
            answer = (
                f"Based on what I know so far, the first paths I would explore are {role_summary}. "
                "I’d still keep that tentative, because I understand your work-style preference but not yet the kind of tasks you enjoy most. "
                "Which sounds closer to you day to day: analysis, coordination, writing/documentation, or research?"
            )
        return GuardrailedAnswer(text=answer, citations=occupations[:2])

    skill_chunks = [chunk for chunk in retrieval_context.chunks if chunk.chunk_type == "skill_concept"]
    skill_labels = [
        _extract_label(chunk, language_code)
        for chunk in skill_chunks
        if _extract_label(chunk, language_code)
    ]
    skill_summary = _join_list(_dedupe_strings(skill_labels)[:2], language_code)
    citations = skill_chunks[:2]

    if language_code == "ru":
        if skill_summary:
            answer = (
                f"Пока у меня есть хороший сигнал о формате работы: вам важны удаленность и async-взаимодействие, "
                f"а текущие данные в основном указывают на навыки вроде {skill_summary}. "
                "Этого еще недостаточно, чтобы уверенно назвать лучшие роли. "
                "Что вам ближе: анализ, координация, письмо/документация или исследование?"
            )
        else:
            answer = (
                "Пока я уверенно вижу только формат работы, который вам подходит: удаленность и async-взаимодействие. "
                "Этого еще недостаточно, чтобы честно назвать лучшие роли. "
                "Что вам ближе: анализ, координация, письмо/документация или исследование?"
            )
        return GuardrailedAnswer(text=answer, citations=citations)

    if skill_summary:
        answer = (
            "What I can say confidently so far is that remote work and async collaboration matter to you, "
            f"and the current evidence mostly points to collaboration skills such as {skill_summary}. "
            "That still is not enough for me to name the best role matches honestly. "
            "Which kind of work sounds closer to you: analysis, coordination, writing/documentation, or research?"
        )
    else:
        answer = (
            "What I can say confidently so far is that remote work and async collaboration matter to you. "
            "That still is not enough for me to name the best role matches honestly. "
            "Which kind of work sounds closer to you: analysis, coordination, writing/documentation, or research?"
        )
    return GuardrailedAnswer(text=answer, citations=citations)


def _has_supported_role_grounding(text: str, retrieval_context: RetrievalContext) -> bool:
    role_tokens = _extract_role_tokens(text)
    if not role_tokens:
        return True

    for occupation in _useful_occupations(retrieval_context):
        if _role_support_score(role_tokens, occupation) >= 0.5:
            return True
    return False


def _extract_role_tokens(text: str) -> list[str]:
    tokens = [token.casefold() for token in _WORD_PATTERN.findall(text)]
    return [
        token
        for token in tokens
        if len(token) >= 2 and token not in _ROLE_STOPWORDS
    ]


def _role_support_score(role_tokens: list[str], chunk: RetrievedChunk) -> float:
    haystack = f"{chunk.title}\n{chunk.text}".casefold()
    chunk_tokens = set(_WORD_PATTERN.findall(haystack))
    overlap_ratio = len(set(role_tokens) & chunk_tokens) / len(set(role_tokens))
    similarity = SequenceMatcher(None, " ".join(role_tokens), haystack[:240]).ratio()
    return max(overlap_ratio, similarity)


def _language_code(question: str) -> str:
    return "ru" if _CYRILLIC_PATTERN.search(question) else "en"


def _useful_occupations(retrieval_context: RetrievalContext) -> list[RetrievedChunk]:
    occupations: list[RetrievedChunk] = []
    for chunk in retrieval_context.chunks:
        if chunk.chunk_type != "occupation":
            continue
        haystack = f"{chunk.title}\n{chunk.text}"
        if _META_ROLE_PATTERN.search(haystack):
            continue
        occupations.append(chunk)
    return occupations


def _first_useful_occupation(retrieval_context: RetrievalContext) -> RetrievedChunk | None:
    occupations = _useful_occupations(retrieval_context)
    return occupations[0] if occupations else None


def _extract_label(chunk: RetrievedChunk, language_code: str) -> str:
    lines = [line.strip() for line in chunk.text.splitlines() if line.strip()]
    prefixes = (
        ("Russian label:", "English label:")
        if language_code == "ru"
        else ("English label:", "Russian label:")
    )
    for prefix in prefixes:
        for line in lines:
            if line.startswith(prefix):
                return line.removeprefix(prefix).strip().strip(".")

    if " / " in chunk.title:
        parts = [part.strip() for part in chunk.title.split(" / ") if part.strip()]
        if len(parts) >= 2:
            return parts[0] if language_code == "ru" else parts[-1]
    return chunk.title.strip()


def _extract_skills(chunk: RetrievedChunk, language_code: str) -> list[str]:
    lines = [line.strip() for line in chunk.text.splitlines() if line.strip()]
    prefixes = (
        ("Essential skills (RU):", "Optional skills (RU):", "Essential skills (EN):")
        if language_code == "ru"
        else ("Essential skills (EN):", "Optional skills (EN):", "Essential skills (RU):")
    )
    skill_blob = ""
    for prefix in prefixes:
        for line in lines:
            if line.startswith(prefix):
                skill_blob = line.removeprefix(prefix).strip().strip(".")
                break
        if skill_blob:
            break

    if not skill_blob:
        return []

    skills: list[str] = []
    seen: set[str] = set()
    for raw_skill in skill_blob.split(","):
        skill = raw_skill.strip().strip(".")
        if not skill:
            continue
        if _PM_METHODOLOGY_PATTERN.search(skill):
            continue
        if _SHORT_WEIRD_SKILL_PATTERN.search(skill) and len(skill) <= 8:
            continue
        normalized = skill.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        skills.append(skill)
    return skills


def _join_list(items: list[str], language_code: str) -> str:
    cleaned = [item for item in items if item]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        joiner = " и " if language_code == "ru" else " and "
        return joiner.join(cleaned)
    separator = ", "
    tail_joiner = " и " if language_code == "ru" else ", and "
    return separator.join(cleaned[:-1]) + tail_joiner + cleaned[-1]


def _dedupe_strings(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue
        normalized = cleaned.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(cleaned)
    return deduped
