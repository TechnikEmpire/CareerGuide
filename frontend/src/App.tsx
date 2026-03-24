import { FormEvent, useEffect, useRef, useState } from "react";

import {
  deleteMemory,
  exportCareerPlanIcs,
  fetchMemories,
  requestAnswer,
  requestCareerPlan,
  type CareerPlanResponse,
  type MemoryItemPayload,
  type StudyPreferences,
} from "./api/client";
import { CitationList } from "./components/CitationList";
import { MemoryPanel } from "./components/MemoryPanel";
import { MessageCard, type ConversationMessage } from "./components/MessageCard";

const MOBILE_SIDEBAR_BREAKPOINT = 980;

const CHAT_PROMPTS = [
  "Я хочу перейти в аналитику данных, но мне нужен спокойный темп работы.",
  "I prefer remote work and async collaboration. What career paths fit me?",
  "Я могу уделять обучению только 5 часов в неделю. С чего начать путь в UX?",
  "Мне нужна работа без постоянных созвонов. Какие роли стоит рассмотреть?",
];

const PLAN_PROMPTS = [
  {
    goal: "Build a realistic transition plan into data analytics in 6 months",
    targetRole: "Data Analyst",
  },
  {
    goal: "Составить спокойный план перехода в product management без выгорания",
    targetRole: "Product Manager",
  },
];

const INITIAL_MESSAGE: ConversationMessage = {
  id: "assistant-welcome",
  role: "assistant",
  text:
    "Расскажите, какой формат работы вам подходит, чего вы хотите избежать и куда хотите двигаться. " +
    "Я помогу сузить варианты и продолжить разговор по шагам.",
};

type AppView = "chat" | "plan" | "memory";

type ConversationSession = {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ConversationMessage[];
};

type SavedPlanBundle = {
  plan: CareerPlanResponse;
  goal: string;
  targetRole: string;
  savedAt: string;
};

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
    normalized.includes("can’t provide grounded career guidance") ||
    normalized.includes("can't provide grounded career guidance") ||
    normalized.includes("not a crisis-response system") ||
    normalized.includes("не могу надежно дать карьерную рекомендацию") ||
    normalized.includes("не могу построить надежный план")
  );
}

function makeMessageId(prefix: string): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}`;
}

function normalizeUserId(rawUserId: string): string {
  const normalized = rawUserId.trim();
  return normalized.length > 0 ? normalized : "demo-user";
}

function describeError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "The request failed.";
}

function conversationStorageKey(userId: string): string {
  return `careerguide:conversations:${userId}`;
}

function planStorageKey(userId: string): string {
  return `careerguide:plan:${userId}`;
}

function createConversationSession(): ConversationSession {
  const now = new Date().toISOString();
  return {
    id: makeMessageId("conversation"),
    title: "New chat",
    createdAt: now,
    updatedAt: now,
    messages: [INITIAL_MESSAGE],
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

function loadStoredConversations(userId: string): ConversationSession[] {
  const stored = readStorageJson<ConversationSession[]>(conversationStorageKey(userId), []);
  if (!Array.isArray(stored) || stored.length === 0) {
    return [createConversationSession()];
  }
  return [...stored].sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
}

function loadStoredPlan(userId: string): SavedPlanBundle | null {
  return readStorageJson<SavedPlanBundle | null>(planStorageKey(userId), null);
}

function deriveConversationTitle(messages: ConversationMessage[]): string {
  const firstUserMessage = messages.find((message) => message.role === "user");
  if (!firstUserMessage) {
    return "New chat";
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
): ConversationSession[] {
  return sessions
    .map((session) => {
      if (session.id !== conversationId) {
        return session;
      }

      const messages = transform(session.messages);
      return {
        ...session,
        title: deriveConversationTitle(messages),
        updatedAt: new Date().toISOString(),
        messages,
      };
    })
    .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function formatDateValue(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(undefined, {
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
): ConversationSession {
  return (
    conversations.find((conversation) => conversation.id === activeConversationId) ??
    conversations[0] ??
    createConversationSession()
  );
}

function isMobileSidebarViewport(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  return window.innerWidth <= MOBILE_SIDEBAR_BREAKPOINT;
}

export default function App() {
  const [draftUserId, setDraftUserId] = useState("demo-user");
  const [activeUserId, setActiveUserId] = useState("demo-user");
  const [activeView, setActiveView] = useState<AppView>("chat");
  const [isMobileViewport, setIsMobileViewport] = useState(() => isMobileSidebarViewport());
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => isMobileSidebarViewport());
  const [question, setQuestion] = useState("");
  const [conversations, setConversations] = useState<ConversationSession[]>([createConversationSession()]);
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
  const [memories, setMemories] = useState<MemoryItemPayload[]>([]);
  const [isMemoryLoading, setIsMemoryLoading] = useState(false);
  const [memoryError, setMemoryError] = useState<string | null>(null);
  const [deletingMemoryId, setDeletingMemoryId] = useState<string | null>(null);
  const conversationEndRef = useRef<HTMLDivElement | null>(null);

  const activeConversation = findActiveConversation(conversations, activeConversationId);
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
      setMemoryError(describeError(error));
    } finally {
      setIsMemoryLoading(false);
    }
  }

  useEffect(() => {
    const storedConversations = loadStoredConversations(activeUserId);
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
    } else {
      setPlan(null);
      setGoal("");
      setTargetRole("");
      setStudyStartDate(defaultStudyStartDate());
      setPreferredStudyTime("evening");
      setStudyFrequencyPerWeek(3);
      setSavedPlanAt(null);
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
    if (activeView !== "chat") {
      return;
    }
    conversationEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [activeView, messages, isAnswerPending]);

  function handleActivateUser(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const nextUserId = normalizeUserId(draftUserId);
    setDraftUserId(nextUserId);
    setActiveView("chat");
    if (isMobileViewport) {
      setIsSidebarCollapsed(true);
    }
    if (nextUserId === activeUserId) {
      void refreshMemories(nextUserId);
      return;
    }
    setActiveUserId(nextUserId);
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
    const conversation = createConversationSession();
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
    const freshConversation = createConversationSession();
    setConversations([freshConversation]);
    setActiveConversationId(freshConversation.id);
    setActiveView("chat");
    removeStorageKey(conversationStorageKey(activeUserId));
  }

  function reloadSavedPlan(): void {
    const storedPlan = loadStoredPlan(activeUserId);
    if (!storedPlan) {
      setPlanError("No saved plan exists for this profile yet.");
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
  }

  function clearSavedPlan(): void {
    removeStorageKey(planStorageKey(activeUserId));
    setPlan(null);
    setGoal("");
    setTargetRole("");
    setStudyStartDate(defaultStudyStartDate());
    setPreferredStudyTime("evening");
    setStudyFrequencyPerWeek(3);
    setSavedPlanAt(null);
    setPlanError(null);
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

    setQuestion("");
    setIsAnswerPending(true);
    setConversations((previous) =>
      updateConversationMessages(previous, conversationId, (messagesBefore) => [
        ...messagesBefore,
        userMessage,
      ]),
    );

    try {
      const response = await requestAnswer(activeUserId, trimmedQuestion);
      const assistantMessage: ConversationMessage = {
        id: makeMessageId("assistant"),
        role: "assistant",
        text: response.answer,
        citations: response.citations,
        memorySummary: response.memory_summary,
        promptPreview: response.prompt_preview,
        responseKind: response.response_kind === "refusal" ? "refusal" : "answer",
      };
      setConversations((previous) =>
        updateConversationMessages(previous, conversationId, (messagesBefore) => [
          ...messagesBefore,
          assistantMessage,
        ]),
      );
      await refreshMemories(activeUserId);
    } catch (error) {
      const errorText = describeError(error);
      const errorMessage: ConversationMessage = {
        id: makeMessageId("assistant-error"),
        role: "assistant",
        text: errorText,
        isError: !isScopeLimitMessage(errorText),
        responseKind: isScopeLimitMessage(errorText) ? "refusal" : "answer",
      };
      setConversations((previous) =>
        updateConversationMessages(previous, conversationId, (messagesBefore) => [
          ...messagesBefore,
          errorMessage,
        ]),
      );
    } finally {
      setIsAnswerPending(false);
    }
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
      const savedAt = new Date().toISOString();
      setPlan(response);
      setSavedPlanAt(savedAt);
      writeStorageJson<SavedPlanBundle>(planStorageKey(activeUserId), {
        plan: response,
        goal: trimmedGoal,
        targetRole: trimmedRole,
        savedAt,
      });
    } catch (error) {
      setPlanError(describeError(error));
    } finally {
      setIsPlanPending(false);
    }
  }

  async function handleExportPlan(): Promise<void> {
    if (!plan || isPlanExportPending) {
      return;
    }
    if (!plan.calendar_events?.length) {
      setPlanError("Build or reload a scheduled plan before exporting a calendar file.");
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
      setPlanError(describeError(error));
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
      setMemoryError(describeError(error));
    } finally {
      setDeletingMemoryId(null);
    }
  }

  return (
    <div
      className={`shell-root ${isSidebarCollapsed ? "sidebar-collapsed" : ""} ${
        isMobileViewport ? "sidebar-mobile" : ""
      }`}
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
            <div className="brand-mark">CG</div>
            <div className="brand-copy">
              <p className="sidebar-eyebrow">CareerGuide</p>
              <h1 className="sidebar-title">Career coach</h1>
            </div>
          </div>

          <form className="sidebar-profile-form" onSubmit={handleActivateUser}>
            <label className="sidebar-field">
              <span>Profile</span>
              <input
                value={draftUserId}
                onChange={(event) => setDraftUserId(event.target.value)}
                placeholder="demo-user"
              />
            </label>
            <button className="sidebar-primary-button" type="submit">
              Use profile
            </button>
          </form>
        </div>

        <div className="sidebar-actions">
          <button className="sidebar-action-button" type="button" onClick={handleStartNewChat}>
            <span className="sidebar-button-icon" aria-hidden="true">
              +
            </span>
            <span className="sidebar-button-text">New chat</span>
          </button>
          <button
            className="sidebar-action-button secondary"
            type="button"
            onClick={handleDeleteAllChats}
            disabled={!canDeleteAllChats}
          >
            <span className="sidebar-button-icon" aria-hidden="true">
              -
            </span>
            <span className="sidebar-button-text">Delete all</span>
          </button>
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
            <span className="sidebar-button-text">Chat</span>
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
            <span className="sidebar-button-text">Plan</span>
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
            <span className="sidebar-button-text">Memory</span>
          </button>
        </nav>

        <section className="sidebar-history">
          <div className="sidebar-section-header">
            <p className="sidebar-eyebrow">History</p>
            <span>{conversations.length}</span>
          </div>

          <ul className="conversation-list">
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
                  <span className="conversation-time">{formatTimestamp(conversation.updatedAt)}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>

        <div className="sidebar-footer">
          <div>
            <p className="sidebar-eyebrow">Active user</p>
            <strong>{activeUserId}</strong>
          </div>
          {savedPlanAt ? <span className="sidebar-footnote">Plan saved</span> : null}
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
              <span className="sidebar-toggle-text">{isSidebarCollapsed ? "Menu" : "Hide menu"}</span>
            </button>

            <div>
              <p className="workspace-kicker">
                {activeView === "chat"
                  ? "Grounded chat"
                  : activeView === "plan"
                  ? "Structured planning"
                  : "Associative memory"}
              </p>
              <h2 className="workspace-title">
                {activeView === "chat"
                  ? "Career conversation"
                  : activeView === "plan"
                  ? "One active plan per profile"
                  : "Stored user facts"}
              </h2>
            </div>
          </div>
          <div className="workspace-meta">
            <span className="workspace-badge">{activeUserId}</span>
            {savedPlanAt && activeView === "plan" ? (
              <span className="workspace-badge muted">Saved {formatTimestamp(savedPlanAt)}</span>
            ) : null}
          </div>
        </header>

        {activeView === "chat" ? (
          <section className="chat-stage">
            <div className="chat-scroll">
              {!hasUserMessages ? (
                <section className="empty-state">
                  <p className="empty-kicker">Grounded career guidance</p>
                  <h3>What do you want help figuring out?</h3>
                  <p>
                    Ask about role fit, tradeoffs, next steps, constraints, or a safer transition plan.
                  </p>

                  <div className="suggestion-grid">
                    {CHAT_PROMPTS.map((prompt) => (
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
                    <MessageCard key={message.id} message={message} />
                  ))}
                  {isAnswerPending ? (
                    <article className="message message-assistant message-loading">
                      <header className="message-header">
                        <span className="message-role">Coach</span>
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
                    rows={3}
                    placeholder="Describe what fits you, what you want to avoid, or what decision you are trying to make."
                  />
                  <div className="composer-row">
                    <span className="composer-hint">
                      Citations and memory stay available inside each answer.
                    </span>
                    <button className="composer-submit" type="submit" disabled={!isQuestionReady || isAnswerPending}>
                      {isAnswerPending ? "Thinking…" : "Send"}
                    </button>
                  </div>
                </div>
              </div>
            </form>
          </section>
        ) : null}

        {activeView === "plan" ? (
          <section className="content-stack">
            <section className="content-card">
              <div className="content-card-header">
                <div>
                  <p className="sidebar-eyebrow">Planner</p>
                  <h3>Build or reload the current plan</h3>
                </div>
                <div className="toolbar-actions">
                  <button className="toolbar-button" type="button" onClick={reloadSavedPlan} disabled={!hasSavedPlan}>
                    Reload saved
                  </button>
                  <button
                    className="toolbar-button"
                    type="button"
                    onClick={() => void handleExportPlan()}
                    disabled={!plan || isPlanExportPending}
                  >
                    {isPlanExportPending ? "Exporting…" : "Export .ics"}
                  </button>
                  <button
                    className="toolbar-button secondary"
                    type="button"
                    onClick={clearSavedPlan}
                    disabled={!hasSavedPlan}
                  >
                    Clear saved
                  </button>
                </div>
              </div>

              <div className="suggestion-grid compact">
                {PLAN_PROMPTS.map((prompt) => (
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
                  <span>Goal</span>
                  <textarea
                    value={goal}
                    onChange={(event) => {
                      setGoal(event.target.value);
                      setPlanError(null);
                    }}
                    rows={4}
                    placeholder="Describe the transition, timeline, or work-life boundary."
                  />
                </label>
                <label className="sidebar-field">
                  <span>Target role</span>
                  <input
                    value={targetRole}
                    onChange={(event) => {
                      setTargetRole(event.target.value);
                      setPlanError(null);
                    }}
                    placeholder="Data Analyst"
                  />
                </label>
                <div className="plan-settings-grid">
                  <label className="sidebar-field">
                    <span>Study start date</span>
                    <input
                      type="date"
                      value={studyStartDate}
                      onChange={(event) => setStudyStartDate(event.target.value)}
                    />
                  </label>
                  <label className="sidebar-field">
                    <span>Preferred study time</span>
                    <select
                      value={preferredStudyTime}
                      onChange={(event) => setPreferredStudyTime(event.target.value as StudyPreferences["preferred_study_time"])}
                    >
                      <option value="morning">Morning</option>
                      <option value="afternoon">Afternoon</option>
                      <option value="evening">Evening</option>
                    </select>
                  </label>
                  <label className="sidebar-field">
                    <span>Sessions per week</span>
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
                  <span className="composer-hint">
                    Generating a new plan overwrites the saved one for this profile and rebuilds the calendar schedule.
                  </span>
                  <button className="composer-submit" type="submit" disabled={!isPlanReady || isPlanPending}>
                    {isPlanPending ? "Building…" : "Build plan"}
                  </button>
                </div>
              </form>
              {planError ? (
                planErrorIsScopeLimit ? (
                  <div className="empty-panel scope-panel">
                    <h4>Unsupported planning request</h4>
                    <p>{planError}</p>
                  </div>
                ) : (
                  <p className="panel-error">{planError}</p>
                )
              ) : null}
            </section>

            <section className="content-card">
              <div className="content-card-header">
                <div>
                  <p className="sidebar-eyebrow">Saved plan</p>
                  <h3>{plan?.target_role ?? "No plan yet"}</h3>
                </div>
                {savedPlanAt ? <span className="workspace-badge muted">{formatTimestamp(savedPlanAt)}</span> : null}
              </div>

              {plan ? (
                <div className="plan-result">
                  <p className="plan-goal">{plan.goal}</p>
                  <div className="plan-meta-row">
                    <span className="pill">Workload: {plan.workload_level ?? "medium"}</span>
                    <span className="pill">{plan.estimated_weeks ?? 1} week plan</span>
                    <span className="pill">
                      {plan.study_preferences?.study_frequency_per_week ?? 3} sessions/week ·{" "}
                      {plan.study_preferences?.preferred_study_time ?? "evening"}
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
                          <p className="sidebar-eyebrow">Calendar</p>
                          <h4>Scheduled study sessions</h4>
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
                                Step {event.step_index} · Session {event.session_index} of {event.total_sessions} · Week {event.week_index}
                              </p>
                              <p className="metric">{formatDateValue(event.starts_at)}</p>
                            </div>
                          </li>
                        ))}
                      </ol>
                    </div>
                  ) : null}
                  <CitationList citations={plan.citations} title="Plan evidence" />
                </div>
              ) : (
                <div className="empty-panel">
                  <h4>No saved plan for this profile</h4>
                  <p>Build a plan once and it will stay attached to the current profile until you replace it.</p>
                </div>
              )}
            </section>
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
              userId={activeUserId}
            />
          </section>
        ) : null}
      </main>
    </div>
  );
}
