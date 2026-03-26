import { startTransition, useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8010";

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Request failed");
  }
  return payload;
}

function formatTimestamp(value) {
  if (!value) {
    return "Not built yet";
  }
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short"
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export default function App() {
  const [health, setHealth] = useState(null);
  const [corpora, setCorpora] = useState([]);
  const [selectedCorpus, setSelectedCorpus] = useState("product-support");
  const [buildCorpusName, setBuildCorpusName] = useState("product-support");
  const [files, setFiles] = useState([]);
  const [replaceExisting, setReplaceExisting] = useState(true);
  const [forceRebuild, setForceRebuild] = useState(false);
  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState(5);
  const [chatHistory, setChatHistory] = useState([]);
  const [activeAnswer, setActiveAnswer] = useState(null);
  const [status, setStatus] = useState("Connect a corpus and ask your first support question.");
  const [loadingBuild, setLoadingBuild] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);

  async function refreshCorpora() {
    const items = await fetchJson(`${API_BASE}/api/corpora`);
    startTransition(() => {
      setCorpora(items);
      if (items.length > 0) {
        const firstCorpus = items[0].corpus_name;
        setSelectedCorpus((current) =>
          !current || !items.some((corpus) => corpus.corpus_name === current) ? firstCorpus : current
        );
        setBuildCorpusName((current) =>
          !current || !items.some((corpus) => corpus.corpus_name === current) ? firstCorpus : current
        );
      }
    });
  }

  useEffect(() => {
    fetchJson(`${API_BASE}/api/health`)
      .then((payload) => {
        setHealth(payload);
        setSelectedCorpus(payload.default_corpus);
        setBuildCorpusName(payload.default_corpus);
      })
      .catch((error) => setStatus(error.message));

    refreshCorpora().catch((error) => setStatus(error.message));
  }, []);

  async function handleBuild(event) {
    event.preventDefault();
    if (!buildCorpusName.trim()) {
      setStatus("Choose a corpus name before uploading files.");
      return;
    }
    if (files.length === 0) {
      setStatus("Select one or more CSV, Excel, or PDF files to build the corpus.");
      return;
    }

    const formData = new FormData();
    formData.append("corpus_name", buildCorpusName.trim());
    formData.append("replace_existing", String(replaceExisting));
    formData.append("force_rebuild", String(forceRebuild));
    for (const file of files) {
      formData.append("files", file);
    }

    setLoadingBuild(true);
    try {
      const payload = await fetchJson(`${API_BASE}/api/corpora/upload-build`, {
        method: "POST",
        body: formData
      });
      setSelectedCorpus(payload.corpus_name);
      setBuildCorpusName(payload.corpus_name);
      setStatus(
        `Built ${payload.corpus_name} from ${payload.uploaded_files.length} file(s) and indexed ${payload.chunk_count} chunks.`
      );
      setFiles([]);
      await refreshCorpora();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoadingBuild(false);
    }
  }

  async function handleAsk(event) {
    event.preventDefault();
    if (!question.trim()) {
      setStatus("Ask a question so the assistant can retrieve matching FAQ evidence.");
      return;
    }

    setLoadingChat(true);
    try {
      const payload = await fetchJson(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          corpus_name: selectedCorpus,
          question: question.trim(),
          top_k: Number(topK)
        })
      });
      const entry = {
        question: question.trim(),
        answer: payload.answer,
        citations: payload.citations,
        corpusName: payload.corpus_name
      };
      setActiveAnswer(entry);
      startTransition(() => {
        setChatHistory((current) => [entry, ...current].slice(0, 8));
      });
      setQuestion("");
      setStatus(`Retrieved ${payload.retrieval_count} evidence block(s) from ${payload.corpus_name}.`);
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoadingChat(false);
    }
  }

  return (
    <main className="shell">
      <div className="backdrop backdrop-a" />
      <div className="backdrop backdrop-b" />

      <section className="hero panel">
        <div>
          <p className="eyebrow">RAG FAQ Studio</p>
          <h1>Turn support files into a grounded help desk assistant.</h1>
          <p className="lede">
            Upload error spreadsheets and user manuals, build a local corpus, then ask questions with source-backed
            answers instead of tribal-memory guesses.
          </p>
        </div>
        <div className="health-strip">
          <span>API: {health?.status || "connecting"}</span>
          <span>Embeddings: {health?.embedding_backend || "unknown"}</span>
          <span>LLM: {health?.ollama_chat_enabled ? "ollama" : "fallback mode"}</span>
        </div>
      </section>

      <section className="workspace">
        <aside className="rail">
          <form className="panel build-panel" onSubmit={handleBuild}>
            <div className="panel-heading">
              <h2>Build A Corpus</h2>
              <p>Drop the latest support files here and refresh your RAG index in one step.</p>
            </div>

            <label className="field">
              <span>Corpus name</span>
              <input value={buildCorpusName} onChange={(event) => setBuildCorpusName(event.target.value)} />
            </label>

            <label className="upload-zone">
              <input
                type="file"
                accept=".csv,.xlsx,.xls,.pdf,.txt,.md"
                multiple
                onChange={(event) => setFiles(Array.from(event.target.files || []))}
              />
              <strong>{files.length > 0 ? `${files.length} file(s) selected` : "Choose CSV, XLSX, PDF, or notes"}</strong>
              <span>Spreadsheet rows become FAQ records. Manuals become cited retrieval chunks.</span>
            </label>

            <label className="toggle">
              <input
                type="checkbox"
                checked={replaceExisting}
                onChange={(event) => setReplaceExisting(event.target.checked)}
              />
              <span>Replace existing uploaded files for this corpus</span>
            </label>

            <label className="toggle">
              <input type="checkbox" checked={forceRebuild} onChange={(event) => setForceRebuild(event.target.checked)} />
              <span>Force a full rebuild even if the manifest looks unchanged</span>
            </label>

            <button className="primary-button" type="submit" disabled={loadingBuild}>
              {loadingBuild ? "Building corpus..." : "Upload And Build"}
            </button>

            <div className="file-list">
              {files.length === 0 ? <p>No files selected yet.</p> : files.map((file) => <p key={file.name}>{file.name}</p>)}
            </div>
          </form>

          <section className="panel corpus-panel">
            <div className="panel-heading">
              <h2>Available Corpora</h2>
              <p>Switch the active knowledge base before chatting.</p>
            </div>
            <div className="corpus-list">
              {corpora.length === 0 ? <p className="empty">No corpora built yet.</p> : null}
              {corpora.map((corpus) => (
                <button
                  key={corpus.corpus_name}
                  className={corpus.corpus_name === selectedCorpus ? "corpus-card active" : "corpus-card"}
                  onClick={() => setSelectedCorpus(corpus.corpus_name)}
                  type="button"
                >
                  <strong>{corpus.corpus_name}</strong>
                  <span>{corpus.indexed_files} file(s)</span>
                  <span>{corpus.chunk_count} chunks</span>
                  <span>{formatTimestamp(corpus.last_built_at)}</span>
                </button>
              ))}
            </div>
          </section>
        </aside>

        <section className="chat-stack">
          <form className="panel ask-panel" onSubmit={handleAsk}>
            <div className="panel-heading row">
              <div>
                <h2>Ask The Bot</h2>
                <p>Target a corpus, ask naturally, and inspect every cited source chunk.</p>
              </div>
              <label className="field compact">
                <span>Top K</span>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={topK}
                  onChange={(event) => setTopK(event.target.value)}
                />
              </label>
            </div>

            <label className="field">
              <span>Active corpus</span>
              <input value={selectedCorpus} onChange={(event) => setSelectedCorpus(event.target.value)} />
            </label>

            <textarea
              className="question-box"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Example: How do I fix ERR-202 invoice upload timeout?"
            />

            <div className="actions">
              <button className="primary-button" type="submit" disabled={loadingChat}>
                {loadingChat ? "Searching corpus..." : "Ask Question"}
              </button>
              <p className="status">{status}</p>
            </div>
          </form>

          <section className="response-grid">
            <article className="panel answer-panel">
              <div className="panel-heading">
                <h2>Latest Answer</h2>
                <p>{activeAnswer ? `Grounded in ${activeAnswer.corpusName}` : "Your next answer will appear here."}</p>
              </div>
              {activeAnswer ? (
                <>
                  <div className="qa-block">
                    <span className="label">Question</span>
                    <p>{activeAnswer.question}</p>
                  </div>
                  <div className="qa-block">
                    <span className="label">Answer</span>
                    <pre>{activeAnswer.answer}</pre>
                  </div>
                </>
              ) : (
                <p className="empty">
                  Build a corpus, ask a question, and the answer panel will show grounded output with evidence.
                </p>
              )}
            </article>

            <article className="panel citations-panel">
              <div className="panel-heading">
                <h2>Citations</h2>
                <p>Every answer stays anchored to the indexed spreadsheet rows or manual passages.</p>
              </div>
              <div className="citation-list">
                {!activeAnswer || activeAnswer.citations.length === 0 ? <p className="empty">No citations yet.</p> : null}
                {activeAnswer?.citations.map((citation) => (
                  <article className="citation-card" key={citation.chunk_id}>
                    <header>
                      <strong>{citation.source_file}</strong>
                      <span>{citation.source_type}</span>
                    </header>
                    <div className="meta-row">
                      <span>Score {citation.score}</span>
                      {citation.metadata.page_number ? <span>Page {citation.metadata.page_number}</span> : null}
                      {citation.metadata.sheet_name ? <span>Sheet {citation.metadata.sheet_name}</span> : null}
                      {citation.metadata.row_number ? <span>Row {citation.metadata.row_number}</span> : null}
                    </div>
                    <p>{citation.snippet}</p>
                  </article>
                ))}
              </div>
            </article>
          </section>

          <section className="panel history-panel">
            <div className="panel-heading">
              <h2>Recent Questions</h2>
              <p>Quickly revisit what you asked while tuning the corpus.</p>
            </div>
            <div className="history-list">
              {chatHistory.length === 0 ? <p className="empty">No chat history yet.</p> : null}
              {chatHistory.map((entry, index) => (
                <button className="history-card" key={`${entry.question}-${index}`} type="button" onClick={() => setActiveAnswer(entry)}>
                  <strong>{entry.question}</strong>
                  <span>{entry.corpusName}</span>
                </button>
              ))}
            </div>
          </section>
        </section>
      </section>
    </main>
  );
}
