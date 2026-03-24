import type { MemoryItemPayload } from "../api/client";

type MemoryPanelProps = {
  userId: string;
  apiBaseUrl: string;
  items: MemoryItemPayload[];
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
};

function renderConfidence(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function MemoryPanel({
  userId,
  apiBaseUrl,
  items,
  isLoading,
  error,
  onRefresh,
}: MemoryPanelProps) {
  return (
    <aside className="panel side-panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">Associative Memory</p>
          <h3>Stored profile facts</h3>
        </div>
        <button className="ghost-button" type="button" onClick={onRefresh}>
          Refresh
        </button>
      </div>

      <dl className="meta-grid">
        <div>
          <dt>Active user</dt>
          <dd>{userId}</dd>
        </div>
        <div>
          <dt>API</dt>
          <dd>{apiBaseUrl}</dd>
        </div>
      </dl>

      {isLoading ? <p className="status-copy">Loading stored memory…</p> : null}
      {error ? <p className="status-copy error-copy">{error}</p> : null}

      {!isLoading && !error && items.length === 0 ? (
        <p className="status-copy">
          No persisted memory yet. Ask a question that includes a stable preference,
          goal, or constraint and the backend should store it automatically.
        </p>
      ) : null}

      <ul className="memory-list">
        {items.map((item) => (
          <li key={item.id} className="memory-card">
            <div className="memory-card-header">
              <span className="pill">{item.category}</span>
              <span className="metric">{renderConfidence(item.confidence)} confidence</span>
            </div>
            <p>{item.text}</p>
          </li>
        ))}
      </ul>
    </aside>
  );
}
