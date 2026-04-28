import type { PlanUpdateSuggestion, RetrievedChunk } from "../api/client";
import type { UiText } from "../config/ui";
import { CitationList } from "./CitationList";

const SHOW_DEBUG_PANELS = import.meta.env.VITE_SHOW_DEBUG_PANELS === "true";

export type ConversationMessage = {
  id: string;
  role: "assistant" | "user";
  text: string;
  citations?: RetrievedChunk[];
  memorySummary?: string;
  promptPreview?: string;
  isError?: boolean;
  responseKind?: "answer" | "refusal" | "limited_unsupported";
  planUpdate?: PlanUpdateSuggestion | null;
};

type MessageCardProps = {
  message: ConversationMessage;
  uiText: UiText;
  onApplyPlanUpdate?: (update: PlanUpdateSuggestion) => void;
};

export function MessageCard({ message, uiText, onApplyPlanUpdate }: MessageCardProps) {
  const isScopeNote =
    message.responseKind === "refusal" || message.responseKind === "limited_unsupported";
  const toneClass =
    message.role === "assistant"
      ? message.isError
        ? "message message-assistant message-error"
        : isScopeNote
          ? "message message-assistant message-refusal"
        : "message message-assistant"
      : "message message-user";
  const roleLabel =
    message.role === "assistant"
      ? isScopeNote
        ? uiText.message.scopeNote
        : uiText.message.coach
      : uiText.message.you;
  const detailSummary = isScopeNote ? uiText.message.whyPaused : uiText.message.whyAnswer;

  return (
    <article className={toneClass}>
      <header className="message-header">
        <span className="message-role">{roleLabel}</span>
      </header>

      <div className="message-copy">
        <p>{message.text}</p>
      </div>

      {message.role === "assistant" && message.planUpdate ? (
        <div className="plan-update-callout">
          <p className="sidebar-eyebrow">{uiText.message.planUpdateSuggested}</p>
          <p>{message.planUpdate.summary}</p>
          <button className="toolbar-button" type="button" onClick={() => onApplyPlanUpdate?.(message.planUpdate!)}>
            {uiText.message.applyPlanUpdate}
          </button>
        </div>
      ) : null}

      {message.role === "assistant" &&
      (message.memorySummary || message.citations?.length || (SHOW_DEBUG_PANELS && message.promptPreview)) ? (
        <details className="prompt-preview">
          <summary>{detailSummary}</summary>

          {message.memorySummary ? (
            <section className="message-detail-block">
              <div className="message-detail-header">
                <h4>{uiText.message.memoryUsed}</h4>
              </div>
              <p className="detail-copy">{message.memorySummary}</p>
            </section>
          ) : null}

          {message.citations?.length ? <CitationList citations={message.citations} uiText={uiText} /> : null}

          {SHOW_DEBUG_PANELS && message.promptPreview ? (
            <details className="prompt-preview">
              <summary>{uiText.message.developerPromptPreview}</summary>
              <pre>{message.promptPreview}</pre>
            </details>
          ) : null}
        </details>
      ) : null}
    </article>
  );
}
