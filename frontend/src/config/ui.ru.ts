import type { UiText } from "./ui.types";

export const uiTextRu = {
  metadata: {
    htmlLang: "ru",
    title: "CareerGuide",
    description: "CareerGuide — веб-интерфейс для карьерных рекомендаций с grounded retrieval и ассоциативной памятью.",
    locale: "ru",
  },
  brand: {
    eyebrow: "CareerGuide",
    title: "Карьерный помощник",
  },
  sidebar: {
    profileLabel: "Профиль",
    profilePlaceholder: "demo-user",
    useProfile: "Выбрать профиль",
    newChat: "Новый чат",
    deleteAll: "Удалить всё",
    chat: "Чат",
    plan: "План",
    memory: "Память",
    history: "История",
    activeUser: "Активный пользователь",
    planSaved: "План сохранён",
    menu: "Меню",
    hideMenu: "Скрыть меню",
    languageLabel: "Язык интерфейса",
  },
  workspace: {
    chatKicker: "Обоснованный чат",
    planKicker: "Структурное планирование",
    memoryKicker: "Ассоциативная память",
    chatTitle: "Карьерный разговор",
    planTitle: "Один активный план на профиль",
    memoryTitle: "Сохранённые факты о пользователе",
    savedPrefix: "Сохранено",
  },
  shared: {
    loading: "Загрузка…",
  },
  chat: {
    prompts: [
      "Я хочу перейти в аналитику данных, но мне нужен спокойный темп работы.",
      "Я предпочитаю удалённую работу и асинхронное взаимодействие. Какие карьерные пути мне подходят?",
      "Я могу уделять обучению только 5 часов в неделю. С чего начать путь в UX?",
      "Мне нужна работа без постоянных созвонов. Какие роли стоит рассмотреть?",
    ],
    initialAssistantMessage:
      "Расскажите, какой формат работы вам подходит, чего вы хотите избежать и куда хотите двигаться. " +
      "Я помогу сузить варианты и продолжить разговор по шагам.",
    newConversationTitle: "Новый чат",
    emptyKicker: "Обоснованная карьерная навигация",
    emptyTitle: "С чем вы хотите разобраться?",
    emptyDescription:
      "Можно спрашивать о подходящих ролях, компромиссах, следующих шагах, ограничениях или более безопасном плане перехода.",
    assistantTypingRole: "Коуч",
    composerPlaceholder:
      "Опишите, что вам подходит, чего вы хотите избежать и какое решение вы сейчас пытаетесь принять.",
    composerHint: "Источники и память доступны внутри каждого ответа.",
    send: "Отправить",
    thinking: "Думаю…",
  },
  plan: {
    prompts: [
      {
        goal: "Составить реалистичный план перехода в аналитику данных за 6 месяцев",
        targetRole: "Аналитик данных",
      },
      {
        goal: "Составить спокойный план перехода в product management без выгорания",
        targetRole: "Product Manager",
      },
    ],
    plannerEyebrow: "Планировщик",
    plannerTitle: "Создать или загрузить текущий план",
    reloadSaved: "Загрузить сохранённый",
    exportIcs: "Экспорт .ics",
    exporting: "Экспорт…",
    clearSaved: "Очистить сохранённый",
    goalLabel: "Цель",
    goalPlaceholder: "Опишите переход, сроки или ограничения по work-life balance.",
    targetRoleLabel: "Целевая роль",
    targetRolePlaceholder: "Аналитик данных",
    studyStartDate: "Дата начала обучения",
    preferredStudyTime: "Предпочтительное время",
    sessionsPerWeek: "Занятий в неделю",
    studyTimeOptions: {
      morning: "Утро",
      afternoon: "День",
      evening: "Вечер",
    },
    generationHint:
      "Если создать новый план, он перезапишет сохранённый план для этого профиля и пересоберёт календарное расписание.",
    buildPlan: "Построить план",
    buildingPlan: "Строю…",
    unsupportedTitle: "Неподдерживаемый запрос на план",
    savedPlanEyebrow: "Сохранённый план",
    noPlanYet: "Плана пока нет",
    noSavedPlanTitle: "Для этого профиля нет сохранённого плана",
    noSavedPlanDescription:
      "Постройте план один раз, и он будет привязан к текущему профилю, пока вы его не замените.",
    calendarEyebrow: "Календарь",
    calendarTitle: "Запланированные учебные сессии",
    planEvidence: "Основания плана",
    workloadPrefix: "Нагрузка",
    weekPlanLabel: (weeks: number) => `${weeks}-недельный план`,
    sessionsPerWeekLabel: (count: number, studyTime: string) =>
      `${count} занятия в неделю · ${studyTime}`,
    stepSessionWeekLabel: (step: number, session: number, total: number, week: number) =>
      `Шаг ${step} · Сессия ${session} из ${total} · Неделя ${week}`,
    workloadLabels: {
      low: "низкая",
      medium: "средняя",
      high: "высокая",
    },
    noSavedPlanError: "Для этого профиля пока нет сохранённого плана.",
    exportRequiresScheduleError:
      "Сначала постройте или загрузите план с расписанием, а потом экспортируйте календарный файл.",
  },
  memory: {
    eyebrow: "Ассоциативная память",
    title: "Сохранённые факты профиля",
    refresh: "Обновить",
    activeUser: "Активный пользователь",
    storedItems: "Сохранённых элементов",
    loading: "Загрузка памяти…",
    emptyTitle: "Сохранённой памяти пока нет",
    emptyDescription:
      "Задайте вопрос со стабильным предпочтением, целью или ограничением, и backend должен сохранить это автоматически.",
    description:
      "В этом разделе показаны долгосрочные факты, которые backend может использовать в следующих ответах.",
    confidence: "уверенность",
    delete: "Удалить",
    deleting: "Удаление…",
  },
  message: {
    scopeNote: "Пояснение по границам",
    coach: "Коуч",
    you: "Вы",
    whyPaused: "Почему я остановился здесь",
    whyAnswer: "Почему такой ответ",
    memoryUsed: "Использованная память",
    developerPromptPreview: "Предпросмотр developer prompt",
  },
  citation: {
    sources: "Источники",
    citedChunksLabel: (count: number) => `${count} цитируемых фрагментов`,
    scorePrefix: "оценка",
    keySkillsPrefix: "Ключевые навыки",
  },
  errors: {
    requestFailed: "Запрос не удалось выполнить.",
  },
} satisfies UiText;
