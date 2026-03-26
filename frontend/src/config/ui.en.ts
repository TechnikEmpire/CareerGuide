import type { UiText } from "./ui.types";

export const uiTextEn = {
  metadata: {
    htmlLang: "en",
    title: "CareerGuide",
    description: "CareerGuide web UI for grounded career guidance with retrieval and associative memory.",
    locale: "en",
  },
  brand: {
    eyebrow: "CareerGuide",
    title: "Career coach",
  },
  sidebar: {
    profileLabel: "Profile",
    profilePlaceholder: "demo-user",
    useProfile: "Use profile",
    newChat: "New chat",
    deleteAll: "Delete all",
    chat: "Chat",
    plan: "Plan",
    memory: "Memory",
    history: "History",
    activeUser: "Active user",
    planSaved: "Plan saved",
    menu: "Menu",
    hideMenu: "Hide menu",
    languageLabel: "UI language",
  },
  workspace: {
    chatKicker: "Grounded chat",
    planKicker: "Structured planning",
    memoryKicker: "Associative memory",
    chatTitle: "Career conversation",
    planTitle: "One active plan per profile",
    memoryTitle: "Stored user facts",
    savedPrefix: "Saved",
  },
  shared: {
    loading: "Loading…",
  },
  chat: {
    prompts: [
      "I want to move into data analytics, but I need a calm pace of work.",
      "I prefer remote work and async collaboration. What career paths fit me?",
      "I can only study 5 hours per week. Where should I start if I want to move into UX?",
      "I need a role without constant meetings. Which options should I consider?",
    ],
    initialAssistantMessage:
      "Tell me what work format suits you, what you want to avoid, and where you want to move next. " +
      "I’ll help narrow the options and continue the conversation step by step.",
    newConversationTitle: "New chat",
    emptyKicker: "Grounded career guidance",
    emptyTitle: "What do you want help figuring out?",
    emptyDescription:
      "Ask about role fit, tradeoffs, next steps, constraints, or a safer transition plan.",
    assistantTypingRole: "Coach",
    composerPlaceholder:
      "Describe what fits you, what you want to avoid, or what decision you are trying to make.",
    composerHint: "Citations and memory stay available inside each answer.",
    send: "Send",
    thinking: "Thinking…",
  },
  plan: {
    prompts: [
      {
        goal: "Build a realistic transition plan into data analytics in 6 months",
        targetRole: "Data Analyst",
      },
      {
        goal: "Create a calm transition plan into product management without burnout",
        targetRole: "Product Manager",
      },
    ],
    plannerEyebrow: "Planner",
    plannerTitle: "Build or reload the current plan",
    reloadSaved: "Reload saved",
    exportIcs: "Export .ics",
    exporting: "Exporting…",
    clearSaved: "Clear saved",
    goalLabel: "Goal",
    goalPlaceholder: "Describe the transition, timeline, or work-life boundary.",
    targetRoleLabel: "Target role",
    targetRolePlaceholder: "Data Analyst",
    studyStartDate: "Study start date",
    preferredStudyTime: "Preferred study time",
    sessionsPerWeek: "Sessions per week",
    studyTimeOptions: {
      morning: "Morning",
      afternoon: "Afternoon",
      evening: "Evening",
    },
    generationHint:
      "Generating a new plan overwrites the saved one for this profile and rebuilds the calendar schedule.",
    buildPlan: "Build plan",
    buildingPlan: "Building…",
    unsupportedTitle: "Unsupported planning request",
    savedPlanEyebrow: "Saved plan",
    noPlanYet: "No plan yet",
    noSavedPlanTitle: "No saved plan for this profile",
    noSavedPlanDescription:
      "Build a plan once and it will stay attached to the current profile until you replace it.",
    calendarEyebrow: "Calendar",
    calendarTitle: "Scheduled study sessions",
    planEvidence: "Plan evidence",
    workloadPrefix: "Workload",
    weekPlanLabel: (weeks: number) => `${weeks} week plan`,
    sessionsPerWeekLabel: (count: number, studyTime: string) =>
      `${count} sessions/week · ${studyTime}`,
    stepSessionWeekLabel: (step: number, session: number, total: number, week: number) =>
      `Step ${step} · Session ${session} of ${total} · Week ${week}`,
    workloadLabels: {
      low: "low",
      medium: "medium",
      high: "high",
    },
    noSavedPlanError: "No saved plan exists for this profile yet.",
    exportRequiresScheduleError: "Build or reload a scheduled plan before exporting a calendar file.",
  },
  memory: {
    eyebrow: "Associative memory",
    title: "Stored profile facts",
    refresh: "Refresh",
    activeUser: "Active user",
    storedItems: "Stored items",
    loading: "Loading stored memory…",
    emptyTitle: "No stored memory yet",
    emptyDescription:
      "Ask a question that includes a stable preference, goal, or constraint and the backend should store it automatically.",
    description: "This view shows the current long-term facts the backend may reuse in later answers.",
    confidence: "confidence",
    delete: "Delete",
    deleting: "Deleting…",
  },
  message: {
    scopeNote: "Scope note",
    coach: "Coach",
    you: "You",
    whyPaused: "Why I paused here",
    whyAnswer: "Why this answer",
    memoryUsed: "Memory used",
    developerPromptPreview: "Developer prompt preview",
  },
  citation: {
    sources: "Sources",
    citedChunksLabel: (count: number) => `${count} cited chunks`,
    scorePrefix: "score",
    keySkillsPrefix: "Key skills",
  },
  errors: {
    requestFailed: "The request failed.",
  },
} satisfies UiText;
