import type { StudyPreferences } from "../api/client";

export type UiLanguage = "en" | "ru";
export type ThemeId = "graphite" | "harbor" | "meadow";

export type UiText = {
  metadata: {
    htmlLang: string;
    title: string;
    description: string;
    locale: string;
  };
  brand: {
    eyebrow: string;
    title: string;
  };
  sidebar: {
    profileLabel: string;
    profilePlaceholder: string;
    useProfile: string;
    profileCodeLabel: string;
    copyProfileCode: string;
    importProfileCode: string;
    importProfilePlaceholder: string;
    importProfile: string;
    profileCodeCopied: string;
    profileImported: string;
    profileSaved: string;
    profileImportInvalid: string;
    themeLabel: string;
    themeOptions: Record<ThemeId, string>;
    newChat: string;
    deleteAll: string;
    chat: string;
    plan: string;
    memory: string;
    history: string;
    activeUser: string;
    planSaved: string;
    menu: string;
    hideMenu: string;
    languageLabel: string;
  };
  workspace: {
    chatKicker: string;
    planKicker: string;
    memoryKicker: string;
    chatTitle: string;
    planTitle: string;
    memoryTitle: string;
    savedPrefix: string;
  };
  shared: {
    loading: string;
  };
  chat: {
    prompts: string[];
    initialAssistantMessage: string;
    newConversationTitle: string;
    emptyKicker: string;
    emptyTitle: string;
    emptyDescription: string;
    assistantTypingRole: string;
    composerPlaceholder: string;
    composerHint: string;
    send: string;
    thinking: string;
  };
  plan: {
    prompts: Array<{
      goal: string;
      targetRole: string;
    }>;
    plannerEyebrow: string;
    plannerTitle: string;
    reloadSaved: string;
    exportIcs: string;
    exporting: string;
    clearSaved: string;
    goalLabel: string;
    goalPlaceholder: string;
    targetRoleLabel: string;
    targetRolePlaceholder: string;
    studyStartDate: string;
    preferredStudyTime: string;
    sessionsPerWeek: string;
    studyTimeOptions: Record<StudyPreferences["preferred_study_time"], string>;
    generationHint: string;
    buildPlan: string;
    buildingPlan: string;
    unsupportedTitle: string;
    savedPlanEyebrow: string;
    noPlanYet: string;
    noSavedPlanTitle: string;
    noSavedPlanDescription: string;
    calendarEyebrow: string;
    calendarTitle: string;
    planEvidence: string;
    workloadPrefix: string;
    weekPlanLabel: (weeks: number) => string;
    sessionsPerWeekLabel: (count: number, studyTime: string) => string;
    stepSessionWeekLabel: (step: number, session: number, total: number, week: number) => string;
    workloadLabels: Record<"low" | "medium" | "high", string>;
    noSavedPlanError: string;
    exportRequiresScheduleError: string;
  };
  memory: {
    eyebrow: string;
    title: string;
    refresh: string;
    activeUser: string;
    storedItems: string;
    loading: string;
    emptyTitle: string;
    emptyDescription: string;
    description: string;
    confidence: string;
    delete: string;
    deleting: string;
  };
  message: {
    scopeNote: string;
    coach: string;
    you: string;
    whyPaused: string;
    whyAnswer: string;
    memoryUsed: string;
    developerPromptPreview: string;
  };
  citation: {
    sources: string;
    citedChunksLabel: (count: number) => string;
    scorePrefix: string;
    keySkillsPrefix: string;
  };
  errors: {
    requestFailed: string;
  };
};
