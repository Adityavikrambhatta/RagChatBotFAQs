import { useCorpusStore } from "../stores/CorpusStore";
import { formatDate } from "../utils/formatters";

export function SessionsPanel() {
  const { sessions } = useCorpusStore();

  return (
    <div className="panel stack panel-shell">
      <div className="panel-heading">
        <p className="label">Sessions</p>
        <h2>Recent conversations</h2>
      </div>
      <div className="card-list">
        {sessions.length === 0 ? <p className="empty">No chat sessions yet.</p> : null}
        {sessions.map((session) => (
          <div className="data-card" key={session.session_id}>
            <div className="card-meta">
              <strong>{session.corpus_name}</strong>
              <span>{formatDate(session.updated_at)}</span>
            </div>
            <p>{session.preview || "No assistant reply yet."}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
