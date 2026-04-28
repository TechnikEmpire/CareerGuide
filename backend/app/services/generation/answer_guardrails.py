"""Intent-aware answer guardrails for common low-quality chat cases."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re

from backend.app.services.generation.esco_grounding import (
    extract_description,
    extract_label as extract_grounded_label,
    extract_skills as extract_grounded_skills,
    join_human_list,
    lower_sentence_start,
)
from backend.app.services.generation.practical_skills import (
    merge_study_topics,
    practical_study_topics_for_chunk,
)
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
_EXPLICIT_TARGET_REQUEST_PATTERN = re.compile(
    r"\b(become|be a|be an|work as|transition into|move into|go into|pursue|target role|"
    r"plan into|plan for|how do i become|how can i become|want to be)\b"
    r"|как стать|стать|работать как|перейти в|целевая роль|план перехода|хочу быть",
    flags=re.IGNORECASE,
)
_ADULT_ENTERTAINMENT_ROLE_PATTERN = re.compile(
    r"\b(stripper|exotic dancer|adult entertainer|adult entertainment|dancer in a strip club)\b"
    r"|стриптиз|стриптизер|стриптизёр|adult entertainment",
    flags=re.IGNORECASE,
)
_CALM_PACE_PATTERN = re.compile(
    r"\b(calm|steady|low[- ]stress|slower|manageable|reasonable pace)\b"
    r"|спокойн|размеренн|без выгоран|низк.*стресс|темп",
    flags=re.IGNORECASE,
)
_ROLE_PHRASE_CUTOFF_PATTERN = re.compile(
    r"\s*(?:[,;]|\b(?:но|при этом|однако|but|while|although|though)\b).*",
    flags=re.IGNORECASE,
)
_TARGET_ROLE_PATTERNS = (
    re.compile(r"(?:перейти|переходить|уйти|войти)\s+в\s+([^.!?]+)", flags=re.IGNORECASE),
    re.compile(r"(?:переход|план перехода)\s+в\s+([^.!?]+)", flags=re.IGNORECASE),
    re.compile(r"(?:стать|хочу быть|работать как|работать в роли)\s+([^.!?]+)", flags=re.IGNORECASE),
    re.compile(r"\b(?:transition|move|go)\s+into\s+([^.!?]+)", flags=re.IGNORECASE),
    re.compile(r"\b(?:become|be a|be an|work as|pursue)\s+([^.!?]+)", flags=re.IGNORECASE),
    re.compile(r"\b(?:target role|plan into|plan for)\s+([^.!?]+)", flags=re.IGNORECASE),
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
    "while",
    "work",
    "would",
    "but",
    "need",
    "needs",
    "steady",
    "calm",
    "как",
    "в",
    "и",
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
    "работы",
    "стать",
    "хочу",
    "целевая",
    "но",
    "нужен",
    "нужна",
    "нужно",
    "спокойный",
    "спокойная",
    "спокойное",
    "темп",
    "график",
}
_CYRILLIC_SUFFIXES = (
    "иями",
    "ями",
    "ами",
    "ого",
    "ему",
    "ыми",
    "ими",
    "ая",
    "яя",
    "ую",
    "юю",
    "ый",
    "ий",
    "ой",
    "ые",
    "ие",
    "ых",
    "их",
    "ам",
    "ям",
    "ом",
    "ем",
    "ах",
    "ях",
    "ов",
    "ев",
    "у",
    "ю",
    "а",
    "я",
    "ы",
    "и",
    "е",
    "о",
)


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
        _build_supported_transition_answer,
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
            "Я не могу построить экспортируемый учебный план для этой цели, потому что текущая база "
            "не дает достаточно уверенного совпадения с поддерживаемой ESCO-ролью или переходом. "
            "В чате можно обсудить направление с оговорками, но для плана и календаря укажите более "
            "стандартную должность или соседнюю поддерживаемую карьерную область."
        )

    raise UnsupportedGuidanceRequestError(
        "I can’t build an exportable study plan for that goal yet, because the current knowledge base "
        "does not show a strong enough match for a supported ESCO role or transition. "
        "Chat can discuss the direction with caveats, but plans and calendars need a more standard "
        "job title or nearby supported career area."
    )


def _build_unsupported_answer(
    *,
    question: str,
    retrieval_context: RetrievalContext,
) -> GuardrailedAnswer | None:
    if not _EXPLICIT_TARGET_REQUEST_PATTERN.search(question):
        return None
    if _find_supported_occupation(question, retrieval_context) is not None:
        return None

    language_code = _language_code(question)
    if language_code == "ru":
        if _ADULT_ENTERTAINMENT_ROLE_PATTERN.search(question):
            return GuardrailedAnswer(
                text=(
                    "В текущей базе нет надежного ESCO-совпадения для такой роли, поэтому это ограниченная проверка здравого смысла, "
                    "а не grounded карьерная рекомендация. Если речь о работе в adult entertainment, относитесь к ней как к локально регулируемому и рискованному виду занятости: "
                    "проверьте законность и правила площадки, заранее определите личные границы и правила consent, оцените нестабильность дохода, налоги и план выхода, "
                    "поддерживайте физическую форму и сценическое присутствие, тренируйте коммуникацию с клиентами и деэскалацию конфликтов. "
                    "Более переносимые соседние направления для сравнения: performance, hospitality/customer service, фитнес-инструкторство или event work."
                ),
                citations=[],
                response_kind="limited_unsupported",
            )

        return GuardrailedAnswer(
            text=(
                "Текущая база не дает надежного совпадения с поддерживаемой ESCO-ролью, поэтому это ограниченная проверка направления, "
                "а не grounded карьерная рекомендация. Я могу помочь разобрать, что работа реально включает, какие есть правовые или квалификационные ограничения, "
                "какие риски и требования к безопасности нужно учитывать, насколько стабилен доход, какие навыки переносимы и какие соседние поддерживаемые роли стоит сравнить. "
                "Для экспортируемого учебного плана лучше указать более стандартную должность или близкую ESCO-поддерживаемую область."
            ),
            citations=[],
            response_kind="limited_unsupported",
        )

    if _ADULT_ENTERTAINMENT_ROLE_PATTERN.search(question):
        return GuardrailedAnswer(
            text=(
                "I do not have a strong ESCO-grounded occupation match for that role, so this is limited guidance rather than a grounded career recommendation. "
                "If you mean adult entertainment, treat it as a locally regulated, higher-risk work decision rather than a generic arts path: "
                "check local legal requirements and venue safety practices, set clear boundaries and consent rules, understand income volatility, taxes, and exit options, "
                "maintain physical conditioning and performance presence, and build customer communication plus conflict-de-escalation skills. "
                "Transferable adjacent areas to compare include performance, hospitality/customer service, fitness instruction, and event work."
            ),
            citations=[],
            response_kind="limited_unsupported",
        )

    return GuardrailedAnswer(
        text=(
            "I do not have a strong ESCO-grounded occupation match for that role, so this is limited guidance rather than a grounded career recommendation. "
            "I can still help you sanity-check the direction: define what the work actually involves, local legal or credential constraints, safety risks, income stability, "
            "transferable skills, and nearby supported roles worth comparing. For an exportable study plan, use a more standard job title or a nearby ESCO-supported role."
        ),
        citations=[],
        response_kind="limited_unsupported",
    )


def _build_supported_transition_answer(
    *,
    question: str,
    retrieval_context: RetrievalContext,
) -> GuardrailedAnswer | None:
    if not _EXPLICIT_TARGET_REQUEST_PATTERN.search(question):
        return None
    if _ADULT_ENTERTAINMENT_ROLE_PATTERN.search(question):
        return None

    occupation = _find_supported_occupation(question, retrieval_context)
    if occupation is None:
        return None

    language_code = _language_code(question)
    role_label = _extract_label(occupation, language_code)
    role_description = extract_description(occupation, language_code)
    practical_topics = practical_study_topics_for_chunk(
        occupation,
        language_code,
        target_role=question,
        limit=6,
    )
    study_topics = merge_study_topics(
        _extract_skills(occupation, language_code),
        practical_topics,
        limit=8,
    )
    study_summary = _join_list(study_topics[:6], language_code)
    practical_summary = _join_list(practical_topics[:5], language_code)
    calm_pace = _CALM_PACE_PATTERN.search(question) is not None

    if language_code == "ru":
        description_sentence = (
            f"По ESCO эта работа включает: {lower_sentence_start(role_description)}. "
            if role_description
            else ""
        )
        pace_sentence = (
            "С учетом спокойного темпа лучше искать команды с плановой отчетностью, BI-дашбордами, "
            "очисткой данных и внутренней аналитикой, а не роли с срочными on-call задачами или агрессивными дедлайнами. "
            if calm_pace
            else "Чтобы темп был устойчивым, заранее уточняйте регулярность отчетности, дедлайны и ожидания по срочным запросам. "
        )
        topic_sentence = (
            f"Практически начать стоит с таких тем: {practical_summary or study_summary}. "
            if practical_summary or study_summary
            else ""
        )
        return GuardrailedAnswer(
            text=(
                f"Да, это поддерживаемое направление: {role_label}. "
                f"{description_sentence}"
                f"{pace_sentence}"
                f"{topic_sentence}"
                "Хороший следующий шаг — собрать небольшой учебный план вокруг одной спокойной аналитической задачи: взять датасет, очистить его, сделать SQL-выборки, собрать простой dashboard и кратко объяснить выводы."
            ),
            citations=[occupation],
        )

    description_sentence = (
        f"ESCO describes this role as work that involves {lower_sentence_start(role_description)}. "
        if role_description
        else ""
    )
    pace_sentence = (
        "For a calmer pace, look for planned reporting, BI dashboards, data cleaning, and internal analytics rather than urgent on-call analysis or aggressive deadline-driven roles. "
        if calm_pace
        else "For a sustainable pace, ask about reporting cadence, deadline pressure, and expectations for urgent requests. "
    )
    topic_sentence = (
        f"The most practical study topics to start with are {practical_summary or study_summary}. "
        if practical_summary or study_summary
        else ""
    )
    return GuardrailedAnswer(
        text=(
            f"Yes, that is a supported direction: {role_label}. "
            f"{description_sentence}"
            f"{pace_sentence}"
            f"{topic_sentence}"
            "A good next step is to build one calm analytics project: clean a dataset, query it with SQL, make a simple dashboard, and explain the findings briefly."
        ),
        citations=[occupation],
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
        role_description = extract_description(occupation, language_code)
        skills = merge_study_topics(
            _extract_skills(occupation, language_code),
            practical_study_topics_for_chunk(
                occupation,
                language_code,
                target_role=question,
                limit=4,
            ),
            limit=8,
        )
        if skills:
            skill_summary = _join_list(skills[:6], language_code)
            if language_code == "ru":
                answer = (
                    f"Для роли {role_label} текущие данные описывают работу так: {lower_sentence_start(role_description) if role_description else role_label}. "
                    f"Из этого наиболее явно следуют такие навыки: {skill_summary}. "
                    "Это хороший базовый набор, с которого стоит начинать. "
                    "Если хотите, я могу дальше разложить это на начальный уровень, практику и портфолио."
                )
            else:
                answer = (
                    f"For {role_label}, the current role data points to work that involves {lower_sentence_start(role_description) if role_description else role_label}. "
                    f"That makes the clearest skills to build {skill_summary}. "
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
        role_options = _build_role_fit_options(occupations[:3], language_code)
        role_lines = "\n".join(f"- {option}" for option in role_options[:3])
        if language_code == "ru":
            answer = (
                "С тем, что я знаю сейчас, я бы в первую очередь рассмотрел такие направления:\n"
                f"{role_lines}\n"
                "Пока держу это как предварительные варианты, потому что у меня уже есть ваш предпочтительный формат работы, "
                "но еще мало данных о типе задач. "
                "Что вам ближе в повседневной работе: анализ, координация, письмо/документация или исследование?"
            )
        else:
            answer = (
                "Based on what I know so far, the first paths I would explore are:\n"
                f"{role_lines}\n"
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
    role_text = _extract_target_role_phrase(text) or text
    role_tokens = _extract_role_tokens(role_text)
    return True if not role_tokens else _find_supported_occupation(text, retrieval_context) is not None


def _find_supported_occupation(text: str, retrieval_context: RetrievalContext) -> RetrievedChunk | None:
    role_text = _extract_target_role_phrase(text) or text
    role_tokens = _extract_role_tokens(role_text)
    if not role_tokens:
        return None

    best_occupation: RetrievedChunk | None = None
    best_score = 0.0
    for occupation in _useful_occupations(retrieval_context):
        score = _role_support_score(role_tokens, occupation)
        if score > best_score:
            best_score = score
            best_occupation = occupation

    return best_occupation if best_score >= 0.5 else None


def _extract_target_role_phrase(text: str) -> str:
    for pattern in _TARGET_ROLE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        return _trim_role_phrase(match.group(1))
    return ""


def _trim_role_phrase(text: str) -> str:
    trimmed = _ROLE_PHRASE_CUTOFF_PATTERN.sub("", text).strip()
    return re.sub(r"^(?:a|an|the)\s+", "", trimmed, flags=re.IGNORECASE)


def _extract_role_tokens(text: str) -> list[str]:
    tokens = [_normalize_role_token(token) for token in _WORD_PATTERN.findall(text)]
    return [
        token
        for token in tokens
        if len(token) >= 2 and token not in _ROLE_STOPWORDS
    ]


def _role_support_score(role_tokens: list[str], chunk: RetrievedChunk) -> float:
    haystack = f"{chunk.title}\n{chunk.text}".casefold()
    chunk_tokens = {_normalize_role_token(token) for token in _WORD_PATTERN.findall(haystack)}
    overlap_ratio = len(set(role_tokens) & chunk_tokens) / len(set(role_tokens))
    similarity = SequenceMatcher(None, " ".join(role_tokens), haystack[:240]).ratio()
    return max(overlap_ratio, similarity)


def _normalize_role_token(token: str) -> str:
    normalized = token.casefold().replace("ё", "е")
    if not _CYRILLIC_PATTERN.search(normalized):
        return normalized
    for suffix in _CYRILLIC_SUFFIXES:
        if normalized.endswith(suffix) and len(normalized) > len(suffix) + 3:
            return normalized[: -len(suffix)]
    return normalized


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
    return extract_grounded_label(chunk, language_code)


def _extract_skills(chunk: RetrievedChunk, language_code: str) -> list[str]:
    skills = extract_grounded_skills(chunk, language_code)
    return [skill for skill in skills if not (_SHORT_WEIRD_SKILL_PATTERN.search(skill) and len(skill) <= 8)]


def _join_list(items: list[str], language_code: str) -> str:
    return join_human_list(items, language_code)


def _build_role_fit_options(occupations: list[RetrievedChunk], language_code: str) -> list[str]:
    options: list[str] = []
    for chunk in occupations:
        label = _extract_label(chunk, language_code)
        description = extract_description(chunk, language_code)
        if description:
            if language_code == "ru":
                options.append(f"{label}: работа, где нужно {lower_sentence_start(description)}")
            else:
                options.append(f"{label}: work that involves {lower_sentence_start(description)}")
        elif label:
            options.append(label)
    return options


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
