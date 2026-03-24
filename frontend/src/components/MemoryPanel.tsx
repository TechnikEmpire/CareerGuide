import type { MemoryItemPayload } from "../api/client";

type MemoryPanelProps = {
  userId: string;
  items: MemoryItemPayload[];
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
  onDelete: (item: MemoryItemPayload) => void;
  deletingMemoryId: string | null;
  isBusy: boolean;
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
}: MemoryPanelProps) {
  return (
    <section className="content-card memory-surface">
      <div className="content-card-header">
        <div>
          <p className="sidebar-eyebrow">Associative memory</p>
          <h3>Stored profile facts</h3>
        </div>
        <button className="toolbar-button" type="button" onClick={onRefresh} disabled={isBusy}>
          Refresh
        </button>
      </div>

      <dl className="meta-grid">
        <div>
          <dt>Active user</dt>
          <dd>{userId}</dd>
        </div>
        <div>
          <dt>Stored items</dt>
          <dd>{items.length}</dd>
        </div>
      </dl>

      {isLoading ? <p className="panel-copy">Loading stored memory…</p> : null}
      {error ? <p className="panel-error">{error}</p> : null}

      {!isLoading && !error && items.length === 0 ? (
        <div className="empty-panel">
          <h4>No stored memory yet</h4>
          <p>
            Ask a question that includes a stable preference, goal, or constraint and the
            backend should store it automatically.
          </p>
        </div>
      ) : null}

      {items.length > 0 ? (
        <p className="panel-copy">
          This view shows the current long-term facts the backend may reuse in later
          answers.
        </p>
      ) : null}

      <ul className="memory-list">
        {items.map((item) => (
          <li key={item.id} className="memory-card">
            <div className="memory-card-header">
              <div className="memory-card-meta">
                <span className="pill">{item.category}</span>
                <span className="metric">{renderConfidence(item.confidence)} confidence</span>
              </div>
              <button
                className="toolbar-button secondary memory-delete-button"
                type="button"
                onClick={() => onDelete(item)}
                disabled={deletingMemoryId === item.id}
              >
                {deletingMemoryId === item.id ? "Deleting…" : "Delete"}
              </button>
            </div>
            <p>{item.text}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
