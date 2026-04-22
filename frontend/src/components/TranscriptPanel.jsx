import { useChatStore } from "../stores/ChatStore";

export function TranscriptPanel() {
  const { messages, question, setQuestion, loadingChat, submitQuestion } = useChatStore();

  async function handleSubmit(event) {
    event.preventDefault();
    try {
      await submitQuestion();
    } catch {
      // Status is managed in the store.
    }
  }

  return (
    <div className="panel transcript-panel panel-shell">
      <div className="panel-heading">
        <p className="label">Chat Window</p>
        <h2>User page</h2>
      </div>
      <div className="transcript">
        {messages.length === 0 ? <p className="empty">No messages yet. Ask a grounded question to begin.</p> : null}
        {messages.map((message, index) => (
          <div className={message.role === "assistant" ? "bubble assistant" : "bubble user"} key={`${message.role}-${index}`}>
            <span>{message.role === "assistant" ? "Assistant" : "You"}</span>
            <p>{message.content}</p>
          </div>
        ))}
      </div>
      <div className="composer panel-inset">
        <textarea
          placeholder="Ask from the uploaded documents..."
          rows="4"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
        />
        <button className="primary-button" type="button" onClick={handleSubmit} disabled={loadingChat}>
          {loadingChat ? "Answering..." : "Send"}
        </button>
      </div>
    </div>
  );
}
