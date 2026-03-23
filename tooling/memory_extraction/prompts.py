"""Prompt templates for synthetic memory-extraction corpus generation."""

from __future__ import annotations

from tooling.memory_extraction.labels import MemoryExtractionLabel

PROMPT_NAME = "memory_extraction_synthetic_v4"

LABEL_GUIDANCE = {
    MemoryExtractionLabel.NO_MEMORY.value: (
        "The sentence must NOT express a stable preference, hard constraint, goal, or availability signal."
    ),
    MemoryExtractionLabel.PREFERENCE.value: (
        "The sentence should express a stable personal preference about how the user likes to work, study, live, or organize life."
    ),
    MemoryExtractionLabel.CONSTRAINT.value: (
        "The sentence should express a hard limitation, restriction, or non-negotiable condition."
    ),
    MemoryExtractionLabel.GOAL.value: (
        "The sentence should express a desired future state, target role, transition direction, or objective."
    ),
    MemoryExtractionLabel.AVAILABILITY.value: (
        "The sentence should express time, schedule, budget, energy, or availability constraints."
    ),
}

LANGUAGE_GUIDANCE = {
    "ru": "Output every example in Russian only.",
    "en": "Output every example in English only.",
}

GLOBAL_BOUNDARY_RULES = [
    "Every line must look like a user utterance typed into a chat.",
    "Use a mixture of full sentences, short fragments, and telegraphic chat-style utterances.",
    "Some examples may be first-person, but not all of them should be.",
    "A small minority of examples may contain mild typos or informal wording.",
    "Do not write generic advice, impersonal facts, slogans, definitions, or educational statements.",
    "Do not write sentences like 'It is important to...', 'One should...', 'Важно...', or 'Нужно...'.",
    "Do not explain the label and do not mention classification.",
    "Make the label signal obvious enough that a supervised classifier can learn it.",
    "Avoid overusing the exact same trigger phrase in every example.",
]

LABEL_SPECIFICS = {
    MemoryExtractionLabel.NO_MEMORY.value: {
        "must": [
            "Keep the sentence topical, but make it unsuitable for long-term memory persistence.",
            "Good NO_MEMORY examples include questions, temporary wishes, vague exploration, momentary observations, and reflective comments that should not be stored as stable memory.",
            "The sentence may mention career, study, work-life balance, or planning, but it must not contain a stable user profile fact.",
        ],
        "must_not": [
            "Do not turn the sentence into a clear long-term preference, non-negotiable constraint, concrete goal, or concrete availability limit.",
            "Do not make the sentence look like a durable profile fact.",
        ],
        "examples": {
            "ru": [
                "Какие навыки обычно нужны для аналитики данных?",
                "Я пока просто изучаю разные карьерные варианты.",
                "Интересно, какие направления сейчас считаются перспективными.",
                "Хочется что-то поменять, но я еще не поняла что именно.",
                "Сейчас просто смотрю варианты и ничего не решаю.",
                "Не понимаю, с чего вообще начать смену карьерного трека.",
                "Пока читаю про разные роли и пытаюсь понять, что мне ближе.",
                "Что вообще отличает продуктовую аналитику от отчетной аналитики?",
                "Я сегодня просто собираю идеи без окончательного решения.",
                "Пока сравниваю варианты и не готова ничего фиксировать.",
            ],
            "en": [
                "What skills are usually needed for data analytics?",
                "I am still exploring different career options.",
                "I wonder which directions look promising right now.",
                "I feel like changing something, but I do not know what yet.",
                "Just looking at options for now, not deciding anything yet.",
                "I do not really know where to start with a career switch yet.",
                "Right now I am just comparing different paths and taking notes.",
                "What is the actual difference between product analytics and BI?",
                "Today I am only collecting ideas, not making a final choice.",
                "I am still trying to figure out what kind of role fits me.",
            ],
        },
    },
    MemoryExtractionLabel.PREFERENCE.value: {
        "must": [
            "Make the sentence clearly about what the user likes, prefers, enjoys, or tends to choose.",
            "The preference should feel stable rather than momentary.",
            "The sentence may concern work style, learning style, environment, communication, lifestyle, or location.",
        ],
        "must_not": [
            "Do not write generic advice or abstract principles.",
            "Do not turn the sentence into a hard inability or non-negotiable restriction.",
            "Do not make it a future goal such as changing careers.",
        ],
        "examples": {
            "ru": [
                "Мне больше нравится удаленная работа, чем офис.",
                "Я предпочитаю спокойный темп обучения без жесткой конкуренции.",
                "Мне удобнее работать в небольших командах, а не в больших отделах.",
                "Только удаленка, офис меня выматывает.",
                "Лучше гибкий график и меньше созвонов.",
                "Мне комфортнее работать в тихой обстановке, чем в опенспейсе.",
                "Я лучше воспринимаю информацию в небольших группах, а не на больших лекциях.",
                "Мне проще, когда общение в работе больше письменное, чем голосовое.",
                "Мне ближе проекты со спокойным ритмом, а не с постоянным авралом.",
                "Мне удобнее учиться короткими регулярными сессиями.",
            ],
            "en": [
                "I prefer remote work over being in the office every day.",
                "I like a calm learning pace without heavy competition.",
                "I am more comfortable working in small teams than in large departments.",
                "Remote only, office drains me.",
                "Flexible hours and fewer calls work better for me.",
                "I do better in a quiet environment than in an open office.",
                "Written communication works better for me than constant calls.",
                "I prefer projects with a steady rhythm over constant fire drills.",
                "I learn better in short regular sessions than in marathon study days.",
                "Smaller teams with clear roles feel better to me.",
            ],
        },
    },
    MemoryExtractionLabel.CONSTRAINT.value: {
        "must": [
            "Make the sentence clearly about a hard limit, non-negotiable condition, or impossible option.",
            "The sentence should sound like something that blocks or strongly narrows decisions.",
        ],
        "must_not": [
            "Do not make it a soft preference.",
            "Do not make it only a future goal.",
            "Do not make it only a time-availability statement unless the main point is hard availability.",
        ],
        "examples": {
            "ru": [
                "Я не могу переезжать в другой город из-за семьи.",
                "Мне нельзя работать по ночам по состоянию здоровья.",
                "Я не готова к роли, где нужно постоянно ездить в командировки.",
                "Без переезда.",
                "После шести вечера уже никак.",
                "У меня нет возможности ездить в офис пять дней в неделю.",
                "Я не смогу взять работу с постоянными разъездами.",
                "Без официального оформления этот вариант мне не подходит.",
                "Пока не могу работать полный день из-за ухода за ребенком.",
                "Мне нужен вариант без релокации как минимум на ближайший год.",
            ],
            "en": [
                "I cannot relocate to another city because of my family.",
                "I cannot work night shifts for health reasons.",
                "I am not willing to take a role that requires constant travel.",
                "No relocation.",
                "After 6 pm is impossible for me.",
                "I cannot commute to an office five days a week.",
                "A job with constant travel is not an option for me.",
                "I need formal employment, unofficial work does not work for me.",
                "I cannot do full-time hours right now because of caregiving.",
                "Relocation is off the table for at least the next year.",
            ],
        },
    },
    MemoryExtractionLabel.GOAL.value: {
        "must": [
            "Make the sentence clearly about what the user wants to become, achieve, move into, or work toward.",
            "The sentence should point to a desired future outcome.",
        ],
        "must_not": [
            "Do not make it only a preference about style or environment.",
            "Do not make it only a hard limitation.",
            "Do not make it only a time or budget statement.",
        ],
        "examples": {
            "ru": [
                "Я хочу перейти в аналитику данных в течение следующего года.",
                "Моя цель — со временем выйти в продуктовый менеджмент.",
                "Я хочу найти направление, которое приведет меня к роли в кибербезопасности.",
                "Хочу в кибербезопасность, без долгих кругов.",
                "Моя цель на год — сменить трек на аналитику.",
                "В этом году хочу получить первую работу в аналитике данных.",
                "Я хочу перейти из поддержки в автоматизацию тестирования.",
                "Ищу путь в аналитику HR без второго высшего.",
                "Хочу вырасти в роль, где больше стратегии, а не рутины.",
                "План такой: за год собрать портфолио и выйти на роль младшего аналитика.",
            ],
            "en": [
                "I want to move into data analytics within the next year.",
                "My goal is to grow into product management over time.",
                "I want to find a path that leads me into cybersecurity.",
                "Trying to move into cybersecurity without wasting another year.",
                "My one-year goal is to switch into analytics.",
                "I want to land my first data job this year.",
                "I am trying to move from support into QA automation.",
                "I want a path into HR analytics without going back for another degree.",
                "I want to grow into a role with more strategy and less routine work.",
                "The plan is to build a portfolio and apply for junior BI roles this year.",
            ],
        },
    },
    MemoryExtractionLabel.AVAILABILITY.value: {
        "must": [
            "Make the sentence clearly about time, schedule, budget, workload, or energy availability.",
            "The sentence should contain a concrete or at least explicit capacity signal.",
        ],
        "must_not": [
            "Do not make it a general preference.",
            "Do not make it only a future goal.",
            "Do not make it a broad constraint unless the main signal is capacity or availability.",
        ],
        "examples": {
            "ru": [
                "У меня есть только четыре часа в неделю на обучение.",
                "Сейчас я могу тратить на смену карьеры только ограниченный бюджет.",
                "После основной работы у меня остается мало энергии на сложные курсы.",
                "На учебу у меня только пара вечеров в неделю.",
                "Бюджет сейчас очень небольшой.",
                "В будни я свободна только после семи вечера.",
                "До конца месяца у меня почти нет времени на новые задачи.",
                "На переподготовку сейчас могу выделять максимум десять тысяч рублей в месяц.",
                "На этой неделе могу заняться поиском работы только в выходные.",
                "Сейчас тяну максимум одну большую цель одновременно.",
            ],
            "en": [
                "I only have four hours a week for studying.",
                "Right now I can spend only a limited budget on a career change.",
                "After my main job I have very little energy left for intensive courses.",
                "I only have a couple of evenings a week for this.",
                "Budget is tight right now.",
                "On weekdays I am only free after 7 pm.",
                "Until the end of the month I have almost no time for new tasks.",
                "I can spend at most a small monthly budget on retraining right now.",
                "This week I can only work on job search over the weekend.",
                "Right now I can handle only one big goal at a time.",
            ],
        },
    },
}

LABEL_TOPIC_HINTS = {
    MemoryExtractionLabel.NO_MEMORY.value: [
        "asking what a role requires",
        "comparing several possible directions",
        "temporary confusion or uncertainty",
        "collecting ideas without deciding",
        "reacting to a course or article right now",
        "asking for explanation before committing",
    ],
    MemoryExtractionLabel.PREFERENCE.value: [
        "work environment and noise level",
        "remote or office format",
        "team size and collaboration style",
        "learning format and study rhythm",
        "communication style",
        "pace of work and interruptions",
    ],
    MemoryExtractionLabel.CONSTRAINT.value: [
        "relocation and commuting limits",
        "health restrictions",
        "caregiving or family obligations",
        "travel requirements",
        "employment-format requirements",
        "non-negotiable schedule limits",
    ],
    MemoryExtractionLabel.GOAL.value: [
        "target field or role",
        "career-transition direction",
        "timeline for a switch",
        "promotion or growth target",
        "portfolio or milestone objective",
        "desired future work domain",
    ],
    MemoryExtractionLabel.AVAILABILITY.value: [
        "hours per week",
        "budget for learning or transition",
        "energy after the main job",
        "days or times that are free",
        "current workload capacity",
        "short-term schedule pressure",
    ],
}


def _rotating_subset(items: list[str], *, size: int, variant_index: int, stride: int = 1) -> list[str]:
    """Pick a deterministic rotating window so prompts do not stay frozen."""

    if not items:
        return []
    if size >= len(items):
        return list(items)

    selected: list[str] = []
    index = (variant_index * max(stride, 1)) % len(items)
    while len(selected) < size:
        candidate = items[index % len(items)]
        if candidate not in selected:
            selected.append(candidate)
        index += 1
    return selected


def build_generation_prompt(
    *,
    language: str,
    label: str,
    count: int,
    variant_index: int = 0,
    avoid_phrases: tuple[str, ...] = (),
) -> str:
    """Build the synthetic-data generation prompt for one label-language bucket."""

    specifics = LABEL_SPECIFICS[label]
    must_lines = "\n".join(f"- {line}" for line in specifics["must"])
    must_not_lines = "\n".join(f"- {line}" for line in specifics["must_not"])
    selected_examples = _rotating_subset(
        specifics["examples"][language],
        size=min(6, len(specifics["examples"][language])),
        variant_index=variant_index,
        stride=2,
    )
    example_lines = "\n".join(f"- {line}" for line in selected_examples)
    global_rule_lines = "\n".join(f"- {line}" for line in GLOBAL_BOUNDARY_RULES)
    selected_topics = _rotating_subset(
        LABEL_TOPIC_HINTS[label],
        size=min(4, len(LABEL_TOPIC_HINTS[label])),
        variant_index=variant_index,
        stride=3,
    )
    topic_lines = "\n".join(f"- {line}" for line in selected_topics)
    avoid_lines = "\n".join(f"- {phrase}" for phrase in avoid_phrases)
    avoid_section = (
        "Avoid sentence openings or phrasings too close to:\n"
        f"{avoid_lines}\n"
        if avoid_phrases
        else ""
    )

    return (
        "Task: generate training examples for a sentence classifier that detects persistent user memory.\n"
        "Generate exactly one example sentence per line.\n"
        f"Return exactly {count} examples.\n"
        "Do not number the lines.\n"
        "Do not use bullets.\n"
        "Do not use quotes around the sentences.\n"
        "Do not include markdown fences, XML tags, JSON, or commentary.\n"
        f"{LANGUAGE_GUIDANCE[language]}\n"
        f"Target label: {label}.\n"
        f"Label rule: {LABEL_GUIDANCE[label]}\n"
        "Context: career guidance, study planning, work-life balance, lifestyle constraints, and personal planning.\n"
        "The goal is to capture stable user intent and profile signals, not only narrow job-specific facts.\n"
        "Natural chat phrasing is better than polished textbook phrasing.\n"
        "Include some hard borderline cases when they still fit the target label.\n"
        "Rotate surface form aggressively so the examples do not all start the same way.\n"
        "Global rules:\n"
        f"{global_rule_lines}\n"
        "Try to cover varied angles such as:\n"
        f"{topic_lines}\n"
        "This label MUST satisfy:\n"
        f"{must_lines}\n"
        "This label MUST NOT drift into:\n"
        f"{must_not_lines}\n"
        "Good examples for this label:\n"
        f"{example_lines}\n"
        f"{avoid_section}"
        "Keep each sentence natural, short to medium length, and varied.\n"
        "Avoid duplicates and near-duplicates.\n"
        "Avoid generic advice, abstract reflections, and impersonal recommendations.\n"
        "Do not make every example clean and polished; realistic chat style is preferred.\n"
    )
