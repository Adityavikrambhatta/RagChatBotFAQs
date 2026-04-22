import { useChatStore } from "../stores/ChatStore";
import { useCorpusStore } from "../stores/CorpusStore";

export function UserControlsPanel() {
  const { corpora, selectedCorpus, setSelectedCorpus, sessions } = useCorpusStore();
  const { sessionId, setSessionId, loadSessionHistory, startNewChat } = useChatStore();

  return (
    <div className="panel stack panel-shell">
      <div className="panel-heading">
        <p className="label">Conversation</p>
        <h2>Session-aware chat</h2>
        <p>Chat history is sent through a `MessagesPlaceholder` so follow-up questions stay grounded.</p>
      </div>
      <label className="field">
        <span>Corpus</span>
        <select value={selectedCorpus} onChange={(event) => setSelectedCorpus(event.target.value)}>
          {corpora.length === 0 ? <option value="">No corpora yet</option> : null}
          {corpora.map((corpus) => (
            <option key={corpus.corpus_name} value={corpus.corpus_name}>
              {corpus.corpus_name}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>Session id</span>
        <input value={sessionId} onChange={(event) => setSessionId(event.target.value)} />
      </label>
      <div className="button-row">
        <button className="secondary-button" onClick={startNewChat} type="button">
          New session
        </button>
        <button className="secondary-button" onClick={() => loadSessionHistory(sessionId)} type="button">
          Load history
        </button>
      </div>
      <p className="helper">Try follow-ups like “Explain more”, “What about the previous point?”, or “Summarize that section again.”</p>
      <div className="card-list">
        {sessions.length === 0 ? <p className="empty">No chat sessions yet.</p> : null}
        {sessions.map((session) => (
          <button className="select-card" key={session.session_id} onClick={() => loadSessionHistory(session.session_id)} type="button">
            <strong>{session.corpus_name}</strong>
            <span>{session.message_count} messages</span>
            <span>{session.preview || "No assistant reply yet."}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
