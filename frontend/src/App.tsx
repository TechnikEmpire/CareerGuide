import { FormEvent, type KeyboardEvent, useEffect, useRef, useState } from "react";

import {
  deleteMemory,
  exportCareerPlanIcs,
  fetchMemories,
  requestAnswer,
  requestCareerPlan,
  type ChatContextTurn,
  type CareerPlanResponse,
  type CareerPlanCalendarEvent,
  type MemoryItemPayload,
  type PlanHandoffSuggestion,
  type PlanUpdateSuggestion,
  type StudyPreferences,
} from "./api/client";
import { CitationList } from "./components/CitationList";
import { MemoryPanel } from "./components/MemoryPanel";
import { MessageCard, type ConversationMessage } from "./components/MessageCard";
import { PlanCalendar } from "./components/PlanCalendar";
import { getUiText, persistUiLanguage, readStoredUiLanguage, type ThemeId, type UiLanguage } from "./config/ui";

const MOBILE_SIDEBAR_BREAKPOINT = 980;
const LEGACY_USER_ID = "demo-user";
const LOCAL_PROFILE_STORAGE_KEY = "careerguide:local-profile:v1";
const LOCAL_PROFILE_MIGRATION_KEY = "careerguide:local-profile:migrated-demo-user:v1";
const DEFAULT_PROFILE_LABEL = "My profile";
const THEMES: ThemeId[] = ["slate", "paper", "contrast"];

type AppView = "chat" | "history" | "plan" | "memory";
type PlanTab = "builder" | "calendar" | "details";

type LocalProfile = {
  id: string;
  label: string;
};

type ConversationSession = {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ConversationMessage[];
  pendingPlanHandoff?: PlanHandoffSuggestion | null;
};

type SavedPlanBundle = {
  plan: CareerPlanResponse;
  goal: string;
  targetRole: string;
  savedAt: string;
};

function createInitialMessage(language: UiLanguage): ConversationMessage {
  const uiText = getUiText(language);
  return {
    id: "assistant-welcome",
    role: "assistant",
    text: uiText.chat.initialAssistantMessage,
  };
}

function isScopeLimitMessage(message: string | null | undefined): boolean {
  if (!message) {
    return false;
  }
  const normalized = message.toLowerCase();
  return (
    normalized.includes("can't assist") ||
    normalized.includes("can’t assist") ||
    normalized.includes("can’t build a grounded plan") ||
    normalized.includes("can't build a grounded plan") ||
    normalized.includes("can’t build an exportable study plan") ||
    normalized.includes("can't build an exportable study plan") ||
    normalized.includes("can’t provide grounded career guidance") ||
    normalized.includes("can't provide grounded career guidance") ||
    normalized.includes("not a crisis-response system") ||
    normalized.includes("не могу надежно дать карьерную рекомендацию") ||
    normalized.includes("не могу построить экспортируемый учебный план") ||
    normalized.includes("не могу построить надежный план")
  );
}

function makeMessageId(prefix: string): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}`;
}

function describeError(error: unknown, fallbackMessage: string): string {
  if (error instanceof Error) {
    return error.message;
  }
  return fallbackMessage;
}

function conversationStorageKey(userId: string): string {
  return `careerguide:conversations:${userId}`;
}

function planStorageKey(userId: string): string {
  return `careerguide:plan:${userId}`;
}

function themeStorageKey(profileId: string): string {
  return `careerguide:theme:${profileId}`;
}

function createConversationSession(language: UiLanguage): ConversationSession {
  const uiText = getUiText(language);
  const now = new Date().toISOString();
  return {
    id: makeMessageId("conversation"),
    title: uiText.chat.newConversationTitle,
    createdAt: now,
    updatedAt: now,
    messages: [createInitialMessage(language)],
  };
}

function readStorageJson<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") {
    return fallback;
  }

  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) {
      return fallback;
    }
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function writeStorageJson<T>(key: string, value: T): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(key, JSON.stringify(value));
}

function removeStorageKey(key: string): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(key);
}

function loadStoredConversations(userId: string, language: UiLanguage): ConversationSession[] {
  const stored = readStorageJson<ConversationSession[]>(conversationStorageKey(userId), []);
  if (!Array.isArray(stored) || stored.length === 0) {
    return [createConversationSession(language)];
  }
  return [...stored].sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
}

function loadStoredPlan(userId: string): SavedPlanBundle | null {
  const storedPlan = readStorageJson<SavedPlanBundle | null>(planStorageKey(userId), null);
  if (!storedPlan?.plan) {
    return null;
  }
  return {
    ...storedPlan,
    plan: normalizePlanForStorage(storedPlan.plan),
  };
}

function makeOpaqueProfileId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `cg-${crypto.randomUUID()}`;
  }
  return `cg-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function normalizeProfileLabel(rawLabel: string): string {
  const normalized = rawLabel.trim();
  return normalized.length > 0 ? normalized : DEFAULT_PROFILE_LABEL;
}

function normalizeProfileCode(rawCode: string): string | null {
  const normalized = rawCode.trim();
  if (!normalized || normalized.length > 64) {
    return null;
  }
  return /^[A-Za-z0-9._:-]+$/.test(normalized) ? normalized : null;
}

function migrateLegacyLocalProfile(profileId: string): void {
  if (typeof window === "undefined") {
    return;
  }
  if (window.localStorage.getItem(LOCAL_PROFILE_MIGRATION_KEY) === "true") {
    return;
  }

  const legacyConversationKey = conversationStorageKey(LEGACY_USER_ID);
  const nextConversationKey = conversationStorageKey(profileId);
  if (!window.localStorage.getItem(nextConversationKey)) {
    const legacyConversations = window.localStorage.getItem(legacyConversationKey);
    if (legacyConversations) {
      window.localStorage.setItem(nextConversationKey, legacyConversations);
    }
  }

  const legacyPlanKey = planStorageKey(LEGACY_USER_ID);
  const nextPlanKey = planStorageKey(profileId);
  if (!window.localStorage.getItem(nextPlanKey)) {
    const legacyPlan = window.localStorage.getItem(legacyPlanKey);
    if (legacyPlan) {
      window.localStorage.setItem(nextPlanKey, legacyPlan);
    }
  }

  window.localStorage.setItem(LOCAL_PROFILE_MIGRATION_KEY, "true");
}

function readStoredLocalProfile(): LocalProfile {
  const stored = readStorageJson<Partial<LocalProfile> | null>(LOCAL_PROFILE_STORAGE_KEY, null);
  if (
    stored &&
    typeof stored.id === "string" &&
    normalizeProfileCode(stored.id) &&
    typeof stored.label === "string"
  ) {
    return {
      id: stored.id,
      label: normalizeProfileLabel(stored.label),
    };
  }

  const profile = {
    id: makeOpaqueProfileId(),
    label: DEFAULT_PROFILE_LABEL,
  };
  writeStorageJson(LOCAL_PROFILE_STORAGE_KEY, profile);
  migrateLegacyLocalProfile(profile.id);
  return profile;
}

function isThemeId(value: string | null | undefined): value is ThemeId {
  return value === "slate" || value === "paper" || value === "contrast";
}

function readStoredTheme(profileId: string): ThemeId {
  if (typeof window === "undefined") {
    return "slate";
  }
  const stored = window.localStorage.getItem(themeStorageKey(profileId));
  return isThemeId(stored) ? stored : "slate";
}

function makeEventId(event: CareerPlanCalendarEvent, index: number): string {
  if (event.event_id) {
    return event.event_id;
  }
  return `evt-local-${index}-${event.starts_at}-${event.title}`.replace(/[^A-Za-z0-9._:-]+/g, "-");
}

function normalizePlanForStorage(rawPlan: CareerPlanResponse): CareerPlanResponse {
  return {
    ...rawPlan,
    calendar_events: (rawPlan.calendar_events ?? []).map((event, index) => ({
      ...event,
      event_id: makeEventId(event, index),
      event_type: event.event_type === "break" ? "break" : "study",
    })),
  };
}

function deriveConversationTitle(messages: ConversationMessage[], language: UiLanguage): string {
  const uiText = getUiText(language);
  const firstUserMessage = messages.find((message) => message.role === "user");
  if (!firstUserMessage) {
    return uiText.chat.newConversationTitle;
  }

  const normalized = firstUserMessage.text.replace(/\s+/g, " ").trim();
  if (normalized.length <= 48) {
    return normalized;
  }
  return `${normalized.slice(0, 45)}…`;
}

function updateConversationMessages(
  sessions: ConversationSession[],
  conversationId: string,
  transform: (messages: ConversationMessage[]) => ConversationMessage[],
  language: UiLanguage,
  pendingPlanHandoff?: PlanHandoffSuggestion | null,
): ConversationSession[] {
  return sessions
    .map((session) => {
      if (session.id !== conversationId) {
        return session;
      }

      const messages = transform(session.messages);
      return {
        ...session,
        title: deriveConversationTitle(messages, language),
        updatedAt: new Date().toISOString(),
        messages,
        pendingPlanHandoff:
          pendingPlanHandoff === undefined ? session.pendingPlanHandoff ?? null : pendingPlanHandoff,
      };
    })
    .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
}

function buildChatContext(messages: ConversationMessage[], nextMessage: ConversationMessage): ChatContextTurn[] {
  return [...messages, nextMessage]
    .filter((message) => !message.isError)
    .slice(-8)
    .map((message) => ({
      role: message.role,
      text: message.text.slice(0, 1000),
    }));
}

function formatTimestamp(value: string, locale: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat(locale, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function formatDateValue(value: string, locale: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(locale, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function detectBrowserTimeZone(): string {
  if (typeof Intl === "undefined") {
    return "UTC";
  }
  return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
}

function defaultStudyStartDate(): string {
  const date = new Date();
  const day = date.getDay();
  const daysUntilMonday = day === 1 ? 7 : ((8 - day) % 7 || 7);
  date.setDate(date.getDate() + daysUntilMonday);
  return date.toISOString().slice(0, 10);
}

function findActiveConversation(
  conversations: ConversationSession[],
  activeConversationId: string | null,
  language: UiLanguage,
): ConversationSession {
  return (
    conversations.find((conversation) => conversation.id === activeConversationId) ??
    conversations[0] ??
    createConversationSession(language)
  );
}

function isMobileSidebarViewport(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  return window.innerWidth <= MOBILE_SIDEBAR_BREAKPOINT;
}

function getStudyTimeLabel(
  language: UiLanguage,
  value: StudyPreferences["preferred_study_time"] | string,
): string {
  const uiText = getUiText(language);
  if (value === "morning" || value === "afternoon" || value === "evening") {
    return uiText.plan.studyTimeOptions[value];
  }
  return value;
}

function getWorkloadLabel(language: UiLanguage, value: string): string {
  const uiText = getUiText(language);
  if (value === "low" || value === "medium" || value === "high") {
    return uiText.plan.workloadLabels[value];
  }
  return value;
}

function getWorkspaceKicker(activeView: AppView, uiText: ReturnType<typeof getUiText>): string {
  if (activeView === "chat") {
    return uiText.workspace.chatKicker;
  }
  if (activeView === "history") {
    return uiText.workspace.historyKicker;
  }
  if (activeView === "plan") {
    return uiText.workspace.planKicker;
  }
  return uiText.workspace.memoryKicker;
}

function getWorkspaceTitle(activeView: AppView, uiText: ReturnType<typeof getUiText>): string {
  if (activeView === "chat") {
    return uiText.workspace.chatTitle;
  }
  if (activeView === "history") {
    return uiText.workspace.historyTitle;
  }
  if (activeView === "plan") {
    return uiText.workspace.planTitle;
  }
  return uiText.workspace.memoryTitle;
}

export default function App() {
  const [uiLanguage, setUiLanguage] = useState<UiLanguage>(() => readStoredUiLanguage());
  const uiText = getUiText(uiLanguage);
  const [activeProfile, setActiveProfile] = useState<LocalProfile>(() => readStoredLocalProfile());
  const activeUserId = activeProfile.id;
  const [draftProfileLabel, setDraftProfileLabel] = useState(activeProfile.label);
  const [importProfileCode, setImportProfileCode] = useState("");
  const [profileNotice, setProfileNotice] = useState<string | null>(null);
  const [themeId, setThemeId] = useState<ThemeId>(() => readStoredTheme(activeProfile.id));
  const [activeView, setActiveView] = useState<AppView>("chat");
  const [isMobileViewport, setIsMobileViewport] = useState(() => isMobileSidebarViewport());
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => isMobileSidebarViewport());
  const [question, setQuestion] = useState("");
  const [conversations, setConversations] = useState<ConversationSession[]>([
    createConversationSession(uiLanguage),
  ]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [isAnswerPending, setIsAnswerPending] = useState(false);
  const [goal, setGoal] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [studyStartDate, setStudyStartDate] = useState(() => defaultStudyStartDate());
  const [preferredStudyTime, setPreferredStudyTime] = useState<StudyPreferences["preferred_study_time"]>("evening");
  const [studyFrequencyPerWeek, setStudyFrequencyPerWeek] = useState(3);
  const [plan, setPlan] = useState<CareerPlanResponse | null>(null);
  const [savedPlanAt, setSavedPlanAt] = useState<string | null>(null);
  const [planError, setPlanError] = useState<string | null>(null);
  const [isPlanPending, setIsPlanPending] = useState(false);
  const [isPlanExportPending, setIsPlanExportPending] = useState(false);
  const [activePlanTab, setActivePlanTab] = useState<PlanTab>("builder");
  const [memories, setMemories] = useState<MemoryItemPayload[]>([]);
  const [isMemoryLoading, setIsMemoryLoading] = useState(false);
  const [memoryError, setMemoryError] = useState<string | null>(null);
  const [deletingMemoryId, setDeletingMemoryId] = useState<string | null>(null);
  const conversationEndRef = useRef<HTMLDivElement | null>(null);

  const activeConversation = findActiveConversation(conversations, activeConversationId, uiLanguage);
  const messages = activeConversation.messages;
  const hasUserMessages = messages.some((message) => message.role === "user");
  const hasSavedPlan = savedPlanAt !== null;
  const canDeleteAllChats = conversations.length > 1 || hasUserMessages;
  const isQuestionReady = question.trim().length > 0;
  const isPlanReady = goal.trim().length > 0 && targetRole.trim().length > 0;
  const planErrorIsScopeLimit = isScopeLimitMessage(planError);
  const currentStudyPreferences: StudyPreferences = {
    study_start_date: studyStartDate,
    preferred_study_time: preferredStudyTime,
    study_frequency_per_week: studyFrequencyPerWeek,
    session_duration_minutes: 90,
    timezone: detectBrowserTimeZone(),
  };

  async function refreshMemories(userId: string): Promise<void> {
    setIsMemoryLoading(true);
    setMemoryError(null);
    try {
      const items = await fetchMemories(userId);
      setMemories(items);
    } catch (error) {
      setMemoryError(describeError(error, uiText.errors.requestFailed));
    } finally {
      setIsMemoryLoading(false);
    }
  }

  useEffect(() => {
    writeStorageJson(LOCAL_PROFILE_STORAGE_KEY, activeProfile);
    setDraftProfileLabel(activeProfile.label);
  }, [activeProfile]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    window.localStorage.setItem(themeStorageKey(activeUserId), themeId);
  }, [activeUserId, themeId]);

  useEffect(() => {
    persistUiLanguage(uiLanguage);

    if (typeof document === "undefined") {
      return;
    }

    document.documentElement.lang = uiText.metadata.htmlLang;
    document.title = uiText.metadata.title;
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute("content", uiText.metadata.description);
    }
  }, [uiLanguage, uiText]);

  useEffect(() => {
    const storedConversations = loadStoredConversations(activeUserId, uiLanguage);
    setConversations(storedConversations);
    setActiveConversationId(storedConversations[0]?.id ?? null);

    const storedPlan = loadStoredPlan(activeUserId);
    if (storedPlan) {
      setPlan(storedPlan.plan);
      setGoal(storedPlan.goal);
      setTargetRole(storedPlan.targetRole);
      setStudyStartDate(storedPlan.plan.study_preferences?.study_start_date ?? defaultStudyStartDate());
      setPreferredStudyTime(storedPlan.plan.study_preferences?.preferred_study_time ?? "evening");
      setStudyFrequencyPerWeek(storedPlan.plan.study_preferences?.study_frequency_per_week ?? 3);
      setSavedPlanAt(storedPlan.savedAt);
      setActivePlanTab("calendar");
    } else {
      setPlan(null);
      setGoal("");
      setTargetRole("");
      setStudyStartDate(defaultStudyStartDate());
      setPreferredStudyTime("evening");
      setStudyFrequencyPerWeek(3);
      setSavedPlanAt(null);
      setActivePlanTab("builder");
    }

    void refreshMemories(activeUserId);
  }, [activeUserId]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const mediaQuery = window.matchMedia(`(max-width: ${MOBILE_SIDEBAR_BREAKPOINT}px)`);
    const syncLayoutMode = (matches: boolean): void => {
      setIsMobileViewport(matches);
      setIsSidebarCollapsed(matches);
    };

    syncLayoutMode(mediaQuery.matches);

    const handleChange = (event: MediaQueryListEvent): void => {
      syncLayoutMode(event.matches);
    };

    if (typeof mediaQuery.addEventListener === "function") {
      mediaQuery.addEventListener("change", handleChange);
      return () => mediaQuery.removeEventListener("change", handleChange);
    }

    mediaQuery.addListener(handleChange);
    return () => mediaQuery.removeListener(handleChange);
  }, []);

  useEffect(() => {
    writeStorageJson(conversationStorageKey(activeUserId), conversations);
  }, [activeUserId, conversations]);

  useEffect(() => {
    setConversations((previous) => {
      let changed = false;
      const localizedWelcome = createInitialMessage(uiLanguage);
      const nextConversations = previous.map((conversation) => {
        const isDefaultWelcomeConversation =
          conversation.messages.length === 1 &&
          conversation.messages[0]?.id === "assistant-welcome" &&
          conversation.messages[0]?.role === "assistant";

        if (!isDefaultWelcomeConversation) {
          return conversation;
        }

        if (
          conversation.title === uiText.chat.newConversationTitle &&
          conversation.messages[0].text === localizedWelcome.text
        ) {
          return conversation;
        }

        changed = true;
        return {
          ...conversation,
          title: uiText.chat.newConversationTitle,
          messages: [localizedWelcome],
        };
      });

      return changed ? nextConversations : previous;
    });
  }, [uiLanguage, uiText.chat.initialAssistantMessage, uiText.chat.newConversationTitle]);

  useEffect(() => {
    if (activeView !== "chat") {
      return;
    }
    conversationEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [activeView, messages, isAnswerPending]);

  function handleSaveProfile(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const nextLabel = normalizeProfileLabel(draftProfileLabel);
    setActiveProfile((previous) => ({ ...previous, label: nextLabel }));
    setDraftProfileLabel(nextLabel);
    setProfileNotice(uiText.sidebar.profileSaved);
    setActiveView("chat");
    if (isMobileViewport) {
      setIsSidebarCollapsed(true);
    }
  }

  function handleImportProfile(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const nextProfileId = normalizeProfileCode(importProfileCode);
    if (!nextProfileId) {
      setProfileNotice(uiText.sidebar.profileImportInvalid);
      return;
    }

    const nextProfile = {
      id: nextProfileId,
      label: normalizeProfileLabel(draftProfileLabel),
    };
    setActiveProfile(nextProfile);
    setThemeId(readStoredTheme(nextProfile.id));
    setImportProfileCode("");
    setProfileNotice(uiText.sidebar.profileImported);
    setActiveView("chat");
    if (isMobileViewport) {
      setIsSidebarCollapsed(true);
    }
  }

  async function handleCopyProfileCode(): Promise<void> {
    try {
      await navigator.clipboard.writeText(activeUserId);
      setProfileNotice(uiText.sidebar.profileCodeCopied);
    } catch {
      setProfileNotice(activeUserId);
    }
  }

  function applyChatPrompt(prompt: string): void {
    setActiveView("chat");
    setQuestion(prompt);
    if (isMobileViewport) {
      setIsSidebarCollapsed(true);
    }
  }

  function applyPlanPrompt(goalPrompt: string, rolePrompt: string): void {
    setActiveView("plan");
    setActivePlanTab("builder");
    setGoal(goalPrompt);
    setTargetRole(rolePrompt);
    setPlanError(null);
    if (isMobileViewport) {
      setIsSidebarCollapsed(true);
    }
  }

  function handleSelectConversation(conversationId: string): void {
    setActiveConversationId(conversationId);
    setActiveView("chat");
    if (isMobileViewport) {
      setIsSidebarCollapsed(true);
    }
  }

  function handleStartNewChat(): void {
    const conversation = createConversationSession(uiLanguage);
    setConversations((previous) => [conversation, ...previous]);
    setActiveConversationId(conversation.id);
    setActiveView("chat");
    setQuestion("");
    if (isMobileViewport) {
      setIsSidebarCollapsed(true);
    }
  }

  function handleDeleteAllChats(): void {
    if (!canDeleteAllChats) {
      return;
    }
    const freshConversation = createConversationSession(uiLanguage);
    setConversations([freshConversation]);
    setActiveConversationId(freshConversation.id);
    setActiveView(activeView === "history" ? "history" : "chat");
    removeStorageKey(conversationStorageKey(activeUserId));
  }

  function savePlanBundle(nextPlan: CareerPlanResponse, nextGoal: string, nextTargetRole: string): void {
    const normalizedPlan = normalizePlanForStorage(nextPlan);
    const savedAt = new Date().toISOString();
    setPlan(normalizedPlan);
    setGoal(nextGoal);
    setTargetRole(nextTargetRole);
    setStudyStartDate(normalizedPlan.study_preferences?.study_start_date ?? defaultStudyStartDate());
    setPreferredStudyTime(normalizedPlan.study_preferences?.preferred_study_time ?? "evening");
    setStudyFrequencyPerWeek(normalizedPlan.study_preferences?.study_frequency_per_week ?? 3);
    setSavedPlanAt(savedAt);
    setPlanError(null);
    setActivePlanTab("calendar");
    writeStorageJson<SavedPlanBundle>(planStorageKey(activeUserId), {
      plan: normalizedPlan,
      goal: nextGoal,
      targetRole: nextTargetRole,
      savedAt,
    });
  }

  function reloadSavedPlan(): void {
    const storedPlan = loadStoredPlan(activeUserId);
    if (!storedPlan) {
      setPlanError(uiText.plan.noSavedPlanError);
      return;
    }
    setPlan(storedPlan.plan);
    setGoal(storedPlan.goal);
    setTargetRole(storedPlan.targetRole);
    setStudyStartDate(storedPlan.plan.study_preferences?.study_start_date ?? defaultStudyStartDate());
    setPreferredStudyTime(storedPlan.plan.study_preferences?.preferred_study_time ?? "evening");
    setStudyFrequencyPerWeek(storedPlan.plan.study_preferences?.study_frequency_per_week ?? 3);
    setSavedPlanAt(storedPlan.savedAt);
    setPlanError(null);
    setActiveView("plan");
    setActivePlanTab("calendar");
  }

  function clearSavedPlan(): void {
    if (!window.confirm(uiText.plan.confirmClearPlan)) {
      return;
    }
    removeStorageKey(planStorageKey(activeUserId));
    setPlan(null);
    setGoal("");
    setTargetRole("");
    setStudyStartDate(defaultStudyStartDate());
    setPreferredStudyTime("evening");
    setStudyFrequencyPerWeek(3);
    setSavedPlanAt(null);
    setPlanError(null);
    setActivePlanTab("builder");
  }

  function handleDeletePlanEvent(event: CareerPlanCalendarEvent): void {
    if (!plan || !window.confirm(uiText.plan.confirmDeleteSession)) {
      return;
    }
    const eventId = event.event_id ?? `${event.starts_at}-${event.title}`;
    const nextPlan = normalizePlanForStorage({
      ...plan,
      calendar_events: plan.calendar_events.filter((candidate, index) => makeEventId(candidate, index) !== eventId),
    });
    savePlanBundle(nextPlan, goal || nextPlan.goal, targetRole || nextPlan.target_role);
  }

  function applyPlanUpdate(update: PlanUpdateSuggestion): void {
    const updatedPlan = normalizePlanForStorage(update.updated_plan);
    savePlanBundle(updatedPlan, updatedPlan.goal, updatedPlan.target_role);
    setActiveView("plan");
  }

  async function handleAskQuestion(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    const conversationId = activeConversation.id;
    if (!trimmedQuestion || isAnswerPending) {
      return;
    }

    const userMessage: ConversationMessage = {
      id: makeMessageId("user"),
      role: "user",
      text: trimmedQuestion,
    };
    const conversationContext = buildChatContext(messages, userMessage);
    const pendingPlanHandoff = activeConversation.pendingPlanHandoff ?? null;

    setQuestion("");
    setIsAnswerPending(true);
    setConversations((previous) =>
      updateConversationMessages(
        previous,
        conversationId,
        (messagesBefore) => [...messagesBefore, userMessage],
        uiLanguage,
      ),
    );

    try {
      const response = await requestAnswer(
        activeUserId,
        trimmedQuestion,
        plan,
        conversationContext,
        pendingPlanHandoff,
      );
      const assistantMessage: ConversationMessage = {
        id: makeMessageId("assistant"),
        role: "assistant",
        text: response.answer,
        citations: response.citations,
        memorySummary: response.memory_summary,
        promptPreview: response.prompt_preview,
        responseKind:
          response.response_kind === "refusal" || response.response_kind === "limited_unsupported"
            ? response.response_kind
            : "answer",
        planUpdate: response.plan_update ?? null,
      };
      const nextPendingPlanHandoff = response.plan_handoff
        ? response.plan_handoff.status === "offered"
          ? response.plan_handoff
          : null
        : pendingPlanHandoff
          ? null
          : undefined;
      setConversations((previous) =>
        updateConversationMessages(
          previous,
          conversationId,
          (messagesBefore) => [...messagesBefore, assistantMessage],
          uiLanguage,
          nextPendingPlanHandoff,
        ),
      );
      if (response.plan_handoff?.status === "accepted") {
        applyPlanPrompt(response.plan_handoff.goal, response.plan_handoff.target_role);
      }
      await refreshMemories(activeUserId);
    } catch (error) {
      const errorText = describeError(error, uiText.errors.requestFailed);
      const errorMessage: ConversationMessage = {
        id: makeMessageId("assistant-error"),
        role: "assistant",
        text: errorText,
        isError: !isScopeLimitMessage(errorText),
        responseKind: isScopeLimitMessage(errorText) ? "refusal" : "answer",
      };
      setConversations((previous) =>
        updateConversationMessages(
          previous,
          conversationId,
          (messagesBefore) => [...messagesBefore, errorMessage],
          uiLanguage,
        ),
      );
    } finally {
      setIsAnswerPending(false);
    }
  }

  function handleQuestionKeyDown(event: KeyboardEvent<HTMLTextAreaElement>): void {
    if (event.key !== "Enter" || event.shiftKey || event.nativeEvent.isComposing) {
      return;
    }

    event.preventDefault();
    event.currentTarget.form?.requestSubmit();
  }

  async function handleBuildPlan(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const trimmedGoal = goal.trim();
    const trimmedRole = targetRole.trim();
    if (!trimmedGoal || !trimmedRole || isPlanPending) {
      return;
    }

    setIsPlanPending(true);
    setPlanError(null);
    try {
      const response = await requestCareerPlan(activeUserId, trimmedGoal, trimmedRole, currentStudyPreferences);
      savePlanBundle(response, trimmedGoal, trimmedRole);
    } catch (error) {
      setPlanError(describeError(error, uiText.errors.requestFailed));
    } finally {
      setIsPlanPending(false);
    }
  }

  async function handleExportPlan(): Promise<void> {
    if (!plan || isPlanExportPending) {
      return;
    }
    if (!plan.calendar_events?.length) {
      setPlanError(uiText.plan.exportRequiresScheduleError);
      return;
    }

    setIsPlanExportPending(true);
    setPlanError(null);
    try {
      const { blob, fileName } = await exportCareerPlanIcs(activeUserId, plan);
      const objectUrl = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = fileName;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(objectUrl);
    } catch (error) {
      setPlanError(describeError(error, uiText.errors.requestFailed));
    } finally {
      setIsPlanExportPending(false);
    }
  }

  async function handleDeleteMemory(item: MemoryItemPayload): Promise<void> {
    if (deletingMemoryId) {
      return;
    }

    setDeletingMemoryId(item.id);
    setMemoryError(null);
    try {
      await deleteMemory(activeUserId, item.id);
      await refreshMemories(activeUserId);
    } catch (error) {
      setMemoryError(describeError(error, uiText.errors.requestFailed));
    } finally {
      setDeletingMemoryId(null);
    }
  }

  return (
    <div
      className={`shell-root ${isSidebarCollapsed ? "sidebar-collapsed" : ""} ${
        isMobileViewport ? "sidebar-mobile" : ""
      }`}
      data-theme={themeId}
    >
      <button
        aria-hidden={isSidebarCollapsed || !isMobileViewport}
        className={`sidebar-backdrop ${
          !isSidebarCollapsed && isMobileViewport ? "sidebar-backdrop-visible" : ""
        }`}
        onClick={() => setIsSidebarCollapsed(true)}
        tabIndex={isSidebarCollapsed || !isMobileViewport ? -1 : 0}
        type="button"
      />
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-lockup">
            <div className="brand-mark">IN</div>
            <div className="brand-copy">
              <p className="sidebar-eyebrow">{uiText.brand.eyebrow}</p>
              <h1 className="sidebar-title">{uiText.brand.title}</h1>
            </div>
          </div>

          <div className="sidebar-settings">
            <details className="sidebar-disclosure" open>
              <summary>{uiText.sidebar.profileSection}</summary>
              <div className="sidebar-disclosure-body">
                <form className="sidebar-profile-form" onSubmit={handleSaveProfile}>
                  <label className="sidebar-field">
                    <span>{uiText.sidebar.profileLabel}</span>
                    <input
                      value={draftProfileLabel}
                      onChange={(event) => setDraftProfileLabel(event.target.value)}
                      placeholder={uiText.sidebar.profilePlaceholder}
                    />
                  </label>
                  <button className="sidebar-primary-button" type="submit">
                    {uiText.sidebar.useProfile}
                  </button>
                </form>

                <div className="profile-code-panel">
                  <p className="sidebar-eyebrow">{uiText.sidebar.profileCodeLabel}</p>
                  <code>{activeUserId}</code>
                  <button className="toolbar-button secondary" type="button" onClick={() => void handleCopyProfileCode()}>
                    {uiText.sidebar.copyProfileCode}
                  </button>
                </div>

                <form className="profile-import-form" onSubmit={handleImportProfile}>
                  <label className="sidebar-field">
                    <span>{uiText.sidebar.importProfileCode}</span>
                    <input
                      value={importProfileCode}
                      onChange={(event) => setImportProfileCode(event.target.value)}
                      placeholder={uiText.sidebar.importProfilePlaceholder}
                    />
                  </label>
                  <button className="toolbar-button" type="submit">
                    {uiText.sidebar.importProfile}
                  </button>
                </form>

                {profileNotice ? <p className="profile-notice">{profileNotice}</p> : null}
              </div>
            </details>

            <details className="sidebar-disclosure">
              <summary>{uiText.sidebar.appearanceSection}</summary>
              <div className="sidebar-disclosure-body theme-toggle-group">
                <p className="sidebar-eyebrow">{uiText.sidebar.themeLabel}</p>
                <div className="theme-toggle-buttons">
                  {THEMES.map((theme) => (
                    <button
                      key={theme}
                      className={`theme-button ${themeId === theme ? "active" : ""}`}
                      type="button"
                      onClick={() => setThemeId(theme)}
                      aria-pressed={themeId === theme}
                    >
                      <span className={`theme-swatch theme-swatch-${theme}`} aria-hidden="true" />
                      <span>{uiText.sidebar.themeOptions[theme]}</span>
                    </button>
                  ))}
                </div>
              </div>
            </details>

            <details className="sidebar-disclosure">
              <summary>{uiText.sidebar.languageSection}</summary>
              <div className="sidebar-disclosure-body language-toggle-group">
                <p className="sidebar-eyebrow">{uiText.sidebar.languageLabel}</p>
                <div className="language-toggle-buttons">
                  <button
                    className={`toolbar-button ${uiLanguage === "ru" ? "active" : ""}`}
                    type="button"
                    onClick={() => setUiLanguage("ru")}
                  >
                    RU
                  </button>
                  <button
                    className={`toolbar-button ${uiLanguage === "en" ? "active" : ""}`}
                    type="button"
                    onClick={() => setUiLanguage("en")}
                  >
                    EN
                  </button>
                </div>
              </div>
            </details>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button
            className={`sidebar-nav-button ${activeView === "chat" ? "active" : ""}`}
            type="button"
            onClick={() => {
              setActiveView("chat");
              if (isMobileViewport) {
                setIsSidebarCollapsed(true);
              }
            }}
          >
            <span className="sidebar-button-icon" aria-hidden="true">
              C
            </span>
            <span className="sidebar-button-text">{uiText.sidebar.chat}</span>
          </button>
          <button
            className={`sidebar-nav-button ${activeView === "history" ? "active" : ""}`}
            type="button"
            onClick={() => {
              setActiveView("history");
              if (isMobileViewport) {
                setIsSidebarCollapsed(true);
              }
            }}
          >
            <span className="sidebar-button-icon" aria-hidden="true">
              H
            </span>
            <span className="sidebar-button-text">{uiText.sidebar.history}</span>
          </button>
          <button
            className={`sidebar-nav-button ${activeView === "plan" ? "active" : ""}`}
            type="button"
            onClick={() => {
              setActiveView("plan");
              if (isMobileViewport) {
                setIsSidebarCollapsed(true);
              }
            }}
          >
            <span className="sidebar-button-icon" aria-hidden="true">
              P
            </span>
            <span className="sidebar-button-text">{uiText.sidebar.plan}</span>
          </button>
          <button
            className={`sidebar-nav-button ${activeView === "memory" ? "active" : ""}`}
            type="button"
            onClick={() => {
              setActiveView("memory");
              if (isMobileViewport) {
                setIsSidebarCollapsed(true);
              }
            }}
          >
            <span className="sidebar-button-icon" aria-hidden="true">
              M
            </span>
            <span className="sidebar-button-text">{uiText.sidebar.memory}</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div>
            <p className="sidebar-eyebrow">{uiText.sidebar.activeUser}</p>
            <strong>{activeProfile.label}</strong>
            <span className="sidebar-profile-code">{activeUserId}</span>
          </div>
          {savedPlanAt ? <span className="sidebar-footnote">{uiText.sidebar.planSaved}</span> : null}
        </div>
      </aside>

      <main className="workspace">
        <header className="workspace-header">
          <div className="workspace-heading">
            <button
              aria-expanded={!isSidebarCollapsed}
              className="toolbar-button secondary sidebar-toggle-button"
              onClick={() => setIsSidebarCollapsed((previous) => !previous)}
              type="button"
            >
              <span className="sidebar-button-icon" aria-hidden="true">
                {isSidebarCollapsed ? "|||" : "<"}
              </span>
              <span className="sidebar-toggle-text">
                {isSidebarCollapsed ? uiText.sidebar.menu : uiText.sidebar.hideMenu}
              </span>
            </button>

            <div>
              <p className="workspace-kicker">
                {getWorkspaceKicker(activeView, uiText)}
              </p>
              <h2 className="workspace-title">
                {getWorkspaceTitle(activeView, uiText)}
              </h2>
            </div>
          </div>
          <div className="workspace-meta">
            <span className="workspace-badge">{activeProfile.label}</span>
            <span className="workspace-badge muted">{activeUserId}</span>
            {savedPlanAt && activeView === "plan" ? (
              <span className="workspace-badge muted">
                {uiText.workspace.savedPrefix} {formatTimestamp(savedPlanAt, uiText.metadata.locale)}
              </span>
            ) : null}
          </div>
        </header>

        {activeView === "chat" ? (
          <section className="chat-stage">
            <div className="chat-scroll">
              {!hasUserMessages ? (
                <section className="empty-state">
                  <p className="empty-kicker">{uiText.chat.emptyKicker}</p>
                  <h3>{uiText.chat.emptyTitle}</h3>
                  <p>{uiText.chat.emptyDescription}</p>

                  <div className="suggestion-grid">
                    {uiText.chat.prompts.map((prompt) => (
                      <button
                        key={prompt}
                        className="suggestion-card"
                        type="button"
                        onClick={() => applyChatPrompt(prompt)}
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </section>
              ) : (
                <div className="message-feed">
                  {messages.map((message) => (
                    <MessageCard
                      key={message.id}
                      message={message}
                      uiText={uiText}
                      onApplyPlanUpdate={applyPlanUpdate}
                    />
                  ))}
                  {isAnswerPending ? (
                    <article className="message message-assistant message-loading">
                      <header className="message-header">
                        <span className="message-role">{uiText.chat.assistantTypingRole}</span>
                      </header>
                      <div className="typing-copy">
                        <span />
                        <span />
                        <span />
                      </div>
                    </article>
                  ) : null}
                  <div ref={conversationEndRef} />
                </div>
              )}
            </div>

            <form className="chat-composer" onSubmit={handleAskQuestion}>
              <div className="composer-shell">
                <div className="composer-shell-inner">
                  <textarea
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    onKeyDown={handleQuestionKeyDown}
                    rows={3}
                    placeholder={uiText.chat.composerPlaceholder}
                  />
                  <div className="composer-row">
                    <span className="composer-hint">{uiText.chat.composerHint}</span>
                    <button className="composer-submit" type="submit" disabled={!isQuestionReady || isAnswerPending}>
                      {isAnswerPending ? uiText.chat.thinking : uiText.chat.send}
                    </button>
                  </div>
                </div>
              </div>
            </form>
          </section>
        ) : null}

        {activeView === "history" ? (
          <section className="content-stack">
            <section className="content-card history-card">
              <div className="content-card-header">
                <div>
                  <p className="sidebar-eyebrow">{uiText.sidebar.history}</p>
                  <h3>{uiText.workspace.historyTitle}</h3>
                </div>
                <div className="workspace-meta">
                  <span className="workspace-badge muted">{conversations.length}</span>
                </div>
              </div>

              <div className="toolbar-actions history-actions">
                <button className="toolbar-button" type="button" onClick={handleStartNewChat}>
                  {uiText.sidebar.newChat}
                </button>
                <button
                  className="toolbar-button secondary"
                  type="button"
                  onClick={handleDeleteAllChats}
                  disabled={!canDeleteAllChats}
                >
                  {uiText.sidebar.deleteAll}
                </button>
              </div>

              <ul className="conversation-list history-conversation-list">
                {conversations.map((conversation) => (
                  <li key={conversation.id}>
                    <button
                      className={`conversation-item ${
                        conversation.id === activeConversation.id ? "active" : ""
                      }`}
                      type="button"
                      onClick={() => handleSelectConversation(conversation.id)}
                    >
                      <span className="conversation-title">{conversation.title}</span>
                      <span className="conversation-time">
                        {formatTimestamp(conversation.updatedAt, uiText.metadata.locale)}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          </section>
        ) : null}

        {activeView === "plan" ? (
          <section className="content-stack">
            <div className="plan-tab-bar" role="tablist" aria-label={uiText.workspace.planTitle}>
              {(["builder", "calendar", "details"] as PlanTab[]).map((tab) => (
                <button
                  key={tab}
                  className={`plan-tab-button ${activePlanTab === tab ? "active" : ""}`}
                  type="button"
                  role="tab"
                  aria-selected={activePlanTab === tab}
                  onClick={() => setActivePlanTab(tab)}
                >
                  {uiText.plan.planTabs[tab]}
                </button>
              ))}
            </div>

            {activePlanTab === "builder" ? (
            <section className="content-card">
              <div className="content-card-header">
                <div>
                  <p className="sidebar-eyebrow">{uiText.plan.plannerEyebrow}</p>
                  <h3>{uiText.plan.plannerTitle}</h3>
                </div>
                <div className="toolbar-actions">
                  <button className="toolbar-button" type="button" onClick={reloadSavedPlan} disabled={!hasSavedPlan}>
                    {uiText.plan.reloadSaved}
                  </button>
                  <button
                    className="toolbar-button"
                    type="button"
                    onClick={() => void handleExportPlan()}
                    disabled={!plan || isPlanExportPending}
                  >
                    {isPlanExportPending ? uiText.plan.exporting : uiText.plan.exportIcs}
                  </button>
                  <button
                    className="toolbar-button secondary"
                    type="button"
                    onClick={clearSavedPlan}
                    disabled={!hasSavedPlan}
                  >
                    {uiText.plan.clearSaved}
                  </button>
                </div>
              </div>

              <div className="suggestion-grid compact">
                {uiText.plan.prompts.map((prompt) => (
                  <button
                    key={`${prompt.goal}-${prompt.targetRole}`}
                    className="suggestion-card compact"
                    type="button"
                    onClick={() => applyPlanPrompt(prompt.goal, prompt.targetRole)}
                  >
                    <strong>{prompt.targetRole}</strong>
                    <span>{prompt.goal}</span>
                  </button>
                ))}
              </div>

              <form className="plan-builder" onSubmit={handleBuildPlan}>
                <label className="sidebar-field">
                  <span>{uiText.plan.goalLabel}</span>
                  <textarea
                    value={goal}
                    onChange={(event) => {
                      setGoal(event.target.value);
                      setPlanError(null);
                    }}
                    rows={4}
                    placeholder={uiText.plan.goalPlaceholder}
                  />
                </label>
                <label className="sidebar-field">
                  <span>{uiText.plan.targetRoleLabel}</span>
                  <input
                    value={targetRole}
                    onChange={(event) => {
                      setTargetRole(event.target.value);
                      setPlanError(null);
                    }}
                    placeholder={uiText.plan.targetRolePlaceholder}
                  />
                </label>
                <div className="plan-settings-grid">
                  <label className="sidebar-field">
                    <span>{uiText.plan.studyStartDate}</span>
                    <input
                      type="date"
                      value={studyStartDate}
                      onChange={(event) => setStudyStartDate(event.target.value)}
                    />
                  </label>
                  <label className="sidebar-field">
                    <span>{uiText.plan.preferredStudyTime}</span>
                    <select
                      value={preferredStudyTime}
                      onChange={(event) => setPreferredStudyTime(event.target.value as StudyPreferences["preferred_study_time"])}
                    >
                      <option value="morning">{uiText.plan.studyTimeOptions.morning}</option>
                      <option value="afternoon">{uiText.plan.studyTimeOptions.afternoon}</option>
                      <option value="evening">{uiText.plan.studyTimeOptions.evening}</option>
                    </select>
                  </label>
                  <label className="sidebar-field">
                    <span>{uiText.plan.sessionsPerWeek}</span>
                    <select
                      value={studyFrequencyPerWeek}
                      onChange={(event) => setStudyFrequencyPerWeek(Number(event.target.value))}
                    >
                      <option value={1}>1</option>
                      <option value={2}>2</option>
                      <option value={3}>3</option>
                      <option value={4}>4</option>
                      <option value={5}>5</option>
                    </select>
                  </label>
                </div>
                <div className="toolbar-actions">
                  <span className="composer-hint">{uiText.plan.generationHint}</span>
                  <button className="composer-submit" type="submit" disabled={!isPlanReady || isPlanPending}>
                    {isPlanPending ? uiText.plan.buildingPlan : uiText.plan.buildPlan}
                  </button>
                </div>
              </form>
              {planError ? (
                planErrorIsScopeLimit ? (
                  <div className="empty-panel scope-panel">
                    <h4>{uiText.plan.unsupportedTitle}</h4>
                    <p>{planError}</p>
                  </div>
                ) : (
                  <p className="panel-error">{planError}</p>
                )
              ) : null}
            </section>
            ) : null}

            {activePlanTab === "calendar" ? (
              <section className="content-card calendar-card">
                <div className="content-card-header">
                  <div>
                    <p className="sidebar-eyebrow">{uiText.plan.calendarEyebrow}</p>
                    <h3>{plan?.target_role ?? uiText.plan.noPlanYet}</h3>
                  </div>
                  <button
                    className="toolbar-button"
                    type="button"
                    onClick={() => void handleExportPlan()}
                    disabled={!plan || isPlanExportPending}
                  >
                    {isPlanExportPending ? uiText.plan.exporting : uiText.plan.exportIcs}
                  </button>
                </div>
                {plan ? (
                  <PlanCalendar plan={plan} uiText={uiText} onDeleteEvent={handleDeletePlanEvent} />
                ) : (
                  <div className="empty-panel">
                    <h4>{uiText.plan.noSavedPlanTitle}</h4>
                    <p>{uiText.plan.noSavedPlanDescription}</p>
                  </div>
                )}
              </section>
            ) : null}

            {activePlanTab === "details" ? (
            <section className="content-card">
              <div className="content-card-header">
                <div>
                  <p className="sidebar-eyebrow">{uiText.plan.savedPlanEyebrow}</p>
                  <h3>{plan?.target_role ?? uiText.plan.noPlanYet}</h3>
                </div>
                {savedPlanAt ? (
                  <span className="workspace-badge muted">
                    {formatTimestamp(savedPlanAt, uiText.metadata.locale)}
                  </span>
                ) : null}
              </div>

              {plan ? (
                <div className="plan-result">
                  <p className="plan-goal">{plan.goal}</p>
                  <div className="plan-meta-row">
                    <span className="pill">
                      {uiText.plan.workloadPrefix}: {getWorkloadLabel(uiLanguage, plan.workload_level ?? "medium")}
                    </span>
                    <span className="pill">{uiText.plan.weekPlanLabel(plan.estimated_weeks ?? 1)}</span>
                    <span className="pill">
                      {uiText.plan.sessionsPerWeekLabel(
                        plan.study_preferences?.study_frequency_per_week ?? 3,
                        getStudyTimeLabel(uiLanguage, plan.study_preferences?.preferred_study_time ?? "evening"),
                      )}
                    </span>
                  </div>
                  <ol className="plan-step-list">
                    {plan.steps.map((step, index) => (
                      <li key={`${step.title}-${index}`} className="plan-step-card">
                        <span className="step-index">{index + 1}</span>
                        <div>
                          <h4>{step.title}</h4>
                          <p>{step.description}</p>
                          {step.focus_skills?.length ? (
                            <div className="plan-pill-row">
                              {step.focus_skills.map((skill) => (
                                <span key={`${step.title}-${skill}`} className="pill">
                                  {skill}
                                </span>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      </li>
                    ))}
                  </ol>
                  {plan.calendar_events?.length ? (
                    <div className="plan-schedule">
                      <div className="content-card-header">
                        <div>
                          <p className="sidebar-eyebrow">{uiText.plan.calendarEyebrow}</p>
                          <h4>{uiText.plan.calendarTitle}</h4>
                        </div>
                      </div>
                      <ol className="plan-step-list">
                        {plan.calendar_events.map((event, index) => (
                          <li key={`${event.title}-${event.starts_at}-${index}`} className="plan-step-card">
                            <span className="step-index">{`${event.step_index}.${event.session_index}`}</span>
                            <div>
                              <h4>{event.title}</h4>
                              <p>{event.description}</p>
                              <p className="metric">
                                {uiText.plan.stepSessionWeekLabel(
                                  event.step_index,
                                  event.session_index,
                                  event.total_sessions,
                                  event.week_index,
                                )}
                              </p>
                              <p className="metric">{formatDateValue(event.starts_at, uiText.metadata.locale)}</p>
                            </div>
                          </li>
                        ))}
                      </ol>
                    </div>
                  ) : null}
                  <CitationList citations={plan.citations} title={uiText.plan.planEvidence} uiText={uiText} />
                </div>
              ) : (
                <div className="empty-panel">
                  <h4>{uiText.plan.noSavedPlanTitle}</h4>
                  <p>{uiText.plan.noSavedPlanDescription}</p>
                </div>
              )}
            </section>
            ) : null}
          </section>
        ) : null}

        {activeView === "memory" ? (
          <section className="content-stack">
            <MemoryPanel
              deletingMemoryId={deletingMemoryId}
              error={memoryError}
              isBusy={isMemoryLoading || deletingMemoryId !== null}
              isLoading={isMemoryLoading}
              items={memories}
              onDelete={(item) => void handleDeleteMemory(item)}
              onRefresh={() => void refreshMemories(activeUserId)}
              uiText={uiText}
              userId={activeUserId}
            />
          </section>
        ) : null}
      </main>
    </div>
  );
}
