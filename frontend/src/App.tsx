import { FormEvent, useEffect, useRef, useState } from "react";

import {
  fetchMemories,
  getApiBaseUrl,
  requestAnswer,
  requestCareerPlan,
  type CareerPlanResponse,
  type MemoryItemPayload,
} from "./api/client";
import { CitationList } from "./components/CitationList";
import { MemoryPanel } from "./components/MemoryPanel";
import { MessageCard, type ConversationMessage } from "./components/MessageCard";

const CHAT_PROMPTS = [
  "Я хочу перейти в аналитику данных, но мне нужен спокойный темп работы.",
  "I prefer remote work and async collaboration. What career paths fit me?",
  "Я могу уделять обучению только 5 часов в неделю. С чего начать путь в UX?",
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

export default function App() {
  const [draftUserId, setDraftUserId] = useState("demo-user");
  const [activeUserId, setActiveUserId] = useState("demo-user");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ConversationMessage[]>([INITIAL_MESSAGE]);
  const [isAnswerPending, setIsAnswerPending] = useState(false);
  const [goal, setGoal] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [plan, setPlan] = useState<CareerPlanResponse | null>(null);
  const [planError, setPlanError] = useState<string | null>(null);
  const [isPlanPending, setIsPlanPending] = useState(false);
  const [memories, setMemories] = useState<MemoryItemPayload[]>([]);
  const [isMemoryLoading, setIsMemoryLoading] = useState(false);
  const [memoryError, setMemoryError] = useState<string | null>(null);
  const conversationEndRef = useRef<HTMLDivElement | null>(null);

  const apiBaseUrl = getApiBaseUrl();

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
    void refreshMemories(activeUserId);
  }, [activeUserId]);

  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isAnswerPending]);

  function handleActivateUser(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const nextUserId = normalizeUserId(draftUserId);
    setDraftUserId(nextUserId);
    if (nextUserId === activeUserId) {
      void refreshMemories(nextUserId);
      return;
    }
    setActiveUserId(nextUserId);
    setMessages([INITIAL_MESSAGE]);
    setPlan(null);
    setPlanError(null);
  }

  function applyChatPrompt(prompt: string): void {
    setQuestion(prompt);
  }

  function applyPlanPrompt(goalPrompt: string, rolePrompt: string): void {
    setGoal(goalPrompt);
    setTargetRole(rolePrompt);
  }

  async function handleAskQuestion(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || isAnswerPending) {
      return;
    }

    setQuestion("");
    setIsAnswerPending(true);
    setMessages((previous) => [
      ...previous,
      {
        id: makeMessageId("user"),
        role: "user",
        text: trimmedQuestion,
      },
    ]);

    try {
      const response = await requestAnswer(activeUserId, trimmedQuestion);
      setMessages((previous) => [
        ...previous,
        {
          id: makeMessageId("assistant"),
          role: "assistant",
          text: response.answer,
          citations: response.citations,
          memorySummary: response.memory_summary,
          promptPreview: response.prompt_preview,
        },
      ]);
      await refreshMemories(activeUserId);
    } catch (error) {
      setMessages((previous) => [
        ...previous,
        {
          id: makeMessageId("assistant-error"),
          role: "assistant",
          text: describeError(error),
          isError: true,
        },
      ]);
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
      const response = await requestCareerPlan(activeUserId, trimmedGoal, trimmedRole);
      setPlan(response);
    } catch (error) {
      setPlanError(describeError(error));
    } finally {
      setIsPlanPending(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="hero panel">
        <div className="hero-copy">
          <p className="eyebrow">CareerGuide</p>
          <h1>Grounded career guidance with associative memory.</h1>
          <p className="hero-text">
            Ask about career direction, constraints, and next steps. The assistant keeps the
            conversation grounded in ESCO while adapting to stored user preferences.
          </p>
        </div>
        <form className="identity-form" onSubmit={handleActivateUser}>
          <label className="field">
            <span>User profile id</span>
            <input
              value={draftUserId}
              onChange={(event) => setDraftUserId(event.target.value)}
              placeholder="demo-user"
            />
          </label>
          <button className="primary-button" type="submit">
            Use profile
          </button>
        </form>
      </header>

      <main className="workspace-grid">
        <section className="panel chat-panel">
          <div className="section-header">
            <div>
              <p className="eyebrow">Chat</p>
              <h2>Ask a grounded question</h2>
            </div>
            <span className="metric">Profile: {activeUserId}</span>
          </div>

          <div className="prompt-strip">
            {CHAT_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                className="prompt-chip"
                type="button"
                onClick={() => applyChatPrompt(prompt)}
              >
                {prompt}
              </button>
            ))}
          </div>

          <div className="chat-log">
            {messages.map((message) => (
              <MessageCard key={message.id} message={message} />
            ))}
            {isAnswerPending ? (
              <article className="message message-assistant message-loading">
                <header className="message-header">
                  <span className="eyebrow">Guide</span>
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

          <form className="composer" onSubmit={handleAskQuestion}>
            <label className="field grow">
              <span>Question</span>
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                rows={4}
                placeholder="Tell the assistant what you want, prefer, or need."
              />
            </label>
            <div className="composer-actions">
              <p className="status-copy">
                Ask about fit, transition paths, or next steps. Grounding details stay available if
                you want to inspect them.
              </p>
              <button className="primary-button" type="submit" disabled={isAnswerPending}>
                {isAnswerPending ? "Answering…" : "Ask"}
              </button>
            </div>
          </form>
        </section>

        <section className="panel plan-panel">
          <div className="section-header">
            <div>
              <p className="eyebrow">Planner</p>
              <h2>Generate a structured career plan</h2>
            </div>
          </div>

          <div className="prompt-strip">
            {PLAN_PROMPTS.map((prompt) => (
              <button
                key={`${prompt.goal}-${prompt.targetRole}`}
                className="prompt-chip"
                type="button"
                onClick={() => applyPlanPrompt(prompt.goal, prompt.targetRole)}
              >
                {prompt.targetRole}
              </button>
            ))}
          </div>

          <form className="plan-form" onSubmit={handleBuildPlan}>
            <label className="field">
              <span>Goal</span>
              <textarea
                value={goal}
                onChange={(event) => setGoal(event.target.value)}
                rows={4}
                placeholder="Describe the transition, timeline, or balance constraint."
              />
            </label>
            <label className="field">
              <span>Target role</span>
              <input
                value={targetRole}
                onChange={(event) => setTargetRole(event.target.value)}
                placeholder="Data Analyst"
              />
            </label>
            <div className="composer-actions">
              <p className="status-copy">
                Use the same profile id if you want the plan to be generated in the context of stored memory.
              </p>
              <button className="primary-button" type="submit" disabled={isPlanPending}>
                {isPlanPending ? "Building…" : "Build plan"}
              </button>
            </div>
          </form>

          {planError ? <p className="status-copy error-copy">{planError}</p> : null}

          {plan ? (
            <section className="plan-result">
              <div className="section-header compact">
                <div>
                  <h3>{plan.target_role}</h3>
                  <p className="status-copy">{plan.goal}</p>
                </div>
              </div>
              <ol className="plan-step-list">
                {plan.steps.map((step, index) => (
                  <li key={`${step.title}-${index}`} className="plan-step-card">
                    <span className="step-index">{index + 1}</span>
                    <div>
                      <h4>{step.title}</h4>
                      <p>{step.description}</p>
                    </div>
                  </li>
                ))}
              </ol>
              <CitationList citations={plan.citations} title="Plan evidence" />
            </section>
          ) : (
            <p className="status-copy">
              Plan output will appear here with explicit citations from the current retrieval stack.
            </p>
          )}
        </section>

        <MemoryPanel
          apiBaseUrl={apiBaseUrl}
          error={memoryError}
          isLoading={isMemoryLoading}
          items={memories}
          onRefresh={() => void refreshMemories(activeUserId)}
          userId={activeUserId}
        />
      </main>
    </div>
  );
}
