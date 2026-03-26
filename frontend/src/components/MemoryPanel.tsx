import type { MemoryItemPayload } from "../api/client";
import type { UiText } from "../config/ui";

type MemoryPanelProps = {
  userId: string;
  items: MemoryItemPayload[];
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
  onDelete: (item: MemoryItemPayload) => void;
  deletingMemoryId: string | null;
  isBusy: boolean;
  uiText: UiText;
};

function renderConfidence(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function MemoryPanel({
  userId,
  items,
  isLoading,
  error,
  onRefresh,
  onDelete,
  deletingMemoryId,
  isBusy,
  uiText,
}: MemoryPanelProps) {
  return (
    <section className="content-card memory-surface">
      <div className="content-card-header">
        <div>
          <p className="sidebar-eyebrow">{uiText.memory.eyebrow}</p>
          <h3>{uiText.memory.title}</h3>
        </div>
        <button className="toolbar-button" type="button" onClick={onRefresh} disabled={isBusy}>
          {uiText.memory.refresh}
        </button>
      </div>

      <dl className="meta-grid">
        <div>
          <dt>{uiText.memory.activeUser}</dt>
          <dd>{userId}</dd>
        </div>
        <div>
          <dt>{uiText.memory.storedItems}</dt>
          <dd>{items.length}</dd>
        </div>
      </dl>

      {isLoading ? <p className="panel-copy">{uiText.memory.loading}</p> : null}
      {error ? <p className="panel-error">{error}</p> : null}

      {!isLoading && !error && items.length === 0 ? (
        <div className="empty-panel">
          <h4>{uiText.memory.emptyTitle}</h4>
          <p>{uiText.memory.emptyDescription}</p>
        </div>
      ) : null}

      {items.length > 0 ? (
        <p className="panel-copy">{uiText.memory.description}</p>
      ) : null}

      <ul className="memory-list">
        {items.map((item) => (
          <li key={item.id} className="memory-card">
            <div className="memory-card-header">
              <div className="memory-card-meta">
                <span className="pill">{item.category}</span>
                <span className="metric">
                  {renderConfidence(item.confidence)} {uiText.memory.confidence}
                </span>
              </div>
              <button
                className="toolbar-button secondary memory-delete-button"
                type="button"
                onClick={() => onDelete(item)}
                disabled={deletingMemoryId === item.id}
              >
                {deletingMemoryId === item.id ? uiText.memory.deleting : uiText.memory.delete}
              </button>
            </div>
            <p>{item.text}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
