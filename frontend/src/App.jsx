import { startTransition, useEffect, useState } from "react";

function resolveApiBase() {
  const configuredBase = import.meta.env.VITE_API_BASE_URL;
  if (configuredBase) {
    return configuredBase.replace(/\/$/, "");
  }
  const devPorts = new Set(["5173", "5174", "5175"]);
  if (devPorts.has(window.location.port)) {
    return "http://127.0.0.1:8000";
  }
  return "";
}

const API_BASE = resolveApiBase();

function routeFromHash() {
  return window.location.hash === "#/admin" ? "admin" : "chat";
}

function createSessionId() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return `session-${Date.now()}`;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Request failed");
  }
  return payload;
}

function formatDate(value) {
  if (!value) {
    return "Not available";
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

function SourceBadge({ source }) {
  return (
    <div className="source-card">
      <div className="source-meta">
        <strong>{source.source_name}</strong>
        <span>{source.page ? `p. ${source.page}` : source.source_type}</span>
      </div>
      <p>{source.preview}</p>
    </div>
  );
}

export default function App() {
  const [route, setRoute] = useState(routeFromHash());
  const [health, setHealth] = useState(null);
  const [corpora, setCorpora] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [selectedCorpus, setSelectedCorpus] = useState("");
  const [documents, setDocuments] = useState([]);
  const [chunks, setChunks] = useState([]);
  const [previewHits, setPreviewHits] = useState([]);
  const [previewQuestion, setPreviewQuestion] = useState("What does the support guide recommend for follow-up questions?");
  const [buildCorpusName, setBuildCorpusName] = useState("");
  const [files, setFiles] = useState([]);
  const [forceRebuild, setForceRebuild] = useState(true);
  const [replaceExisting, setReplaceExisting] = useState(true);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [activeSources, setActiveSources] = useState([]);
  const [sessionId, setSessionId] = useState(createSessionId());
  const [status, setStatus] = useState("Ready to ingest a corpus or start chatting.");
  const [loadingAdmin, setLoadingAdmin] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);
  const [adminProgress, setAdminProgress] = useState("");
  const [lastIngestResult, setLastIngestResult] = useState(null);

  useEffect(() => {
    const onHashChange = () => setRoute(routeFromHash());
    window.addEventListener("hashchange", onHashChange);
    if (!window.location.hash) {
      window.location.hash = "#/chat";
    }
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  async function refreshOverview() {
    const [healthPayload, overviewPayload] = await Promise.all([
      fetchJson(`${API_BASE}/api/health`),
      fetchJson(`${API_BASE}/api/admin/overview`)
    ]);

    let nextCorpus = healthPayload.default_corpus || "";

    startTransition(() => {
      setHealth(healthPayload);
      setCorpora(overviewPayload.corpora);
      setSessions(overviewPayload.sessions);
      if (overviewPayload.corpora.length > 0) {
        const defaultCorpus = overviewPayload.corpora.some((item) => item.corpus_name === selectedCorpus)
          ? selectedCorpus
          : overviewPayload.corpora[0].corpus_name;
        nextCorpus = defaultCorpus;
        setSelectedCorpus(defaultCorpus);
      } else {
        nextCorpus = "";
        setSelectedCorpus("");
      }
      if (!buildCorpusName && overviewPayload.corpora.length === 0) {
        setBuildCorpusName("");
      }
    });

    if (nextCorpus) {
      await refreshCorpusDetails(nextCorpus);
    } else {
      startTransition(() => {
        setLastIngestResult(null);
        setDocuments([]);
        setChunks([]);
      });
    }
  }

  async function refreshCorpusDetails(corpusName) {
    if (!corpusName) {
      return;
    }
    const [detailPayload, documentPayload, chunkPayload] = await Promise.all([
      fetchJson(`${API_BASE}/api/admin/corpus-detail?corpus_name=${encodeURIComponent(corpusName)}`),
      fetchJson(`${API_BASE}/api/admin/documents?corpus_name=${encodeURIComponent(corpusName)}`),
      fetchJson(`${API_BASE}/api/admin/chunks?corpus_name=${encodeURIComponent(corpusName)}&limit=40`)
    ]);
    startTransition(() => {
      setLastIngestResult(detailPayload);
      setDocuments(documentPayload);
      setChunks(chunkPayload);
    });
  }

  useEffect(() => {
    refreshOverview().catch((error) => setStatus(error.message));
  }, []);

  useEffect(() => {
    refreshCorpusDetails(selectedCorpus).catch((error) => {
      setLastIngestResult(null);
      setDocuments([]);
      setChunks([]);
      setStatus(error.message);
    });
  }, [selectedCorpus]);

  async function handleBuild(event) {
    event.preventDefault();
    if (files.length === 0) {
      setStatus("Upload at least one PDF or text document.");
      return;
    }

    const formData = new FormData();
    formData.append("corpus_name", buildCorpusName.trim());
    formData.append("force_rebuild", String(forceRebuild));
    formData.append("replace_existing", String(replaceExisting));
    for (const file of files) {
      formData.append("files", file);
    }

    setLoadingAdmin(true);
    setAdminProgress(`Uploading ${files.length} file(s) and preparing the corpus...`);
    setStatus("Upload started. PDF extraction and embedding can take a little while for larger files.");
    try {
      const payload = await fetchJson(`${API_BASE}/api/corpora/upload-build`, {
        method: "POST",
        body: formData
      });
      setSelectedCorpus(payload.corpus_name);
      setBuildCorpusName(payload.corpus_name);
      setLastIngestResult(payload);
      setStatus(
        `Indexed ${payload.input_file_count} file(s) into ${payload.chunk_count} chunks for corpus ${payload.corpus_name}.`
      );
      setAdminProgress("Upload complete. Corpus index refreshed successfully.");
      setFiles([]);
      await refreshOverview();
      await refreshCorpusDetails(payload.corpus_name);
    } catch (error) {
      setAdminProgress("");
      setStatus(error.message);
    } finally {
      setLoadingAdmin(false);
    }
  }

  async function handlePreview(event) {
    event.preventDefault();
    if (!previewQuestion.trim()) {
      setStatus("Ask a preview query to inspect retrieved chunks.");
      return;
    }
    try {
      const payload = await fetchJson(`${API_BASE}/api/admin/retrieve-preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          corpus_name: selectedCorpus,
          question: previewQuestion.trim(),
          top_k: 4
        })
      });
      setPreviewHits(payload);
      setStatus(`Retrieved ${payload.length} chunk(s) for admin preview.`);
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function handleSend(event) {
    event.preventDefault();
    if (!question.trim()) {
      setStatus("Type a question before sending.");
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
          session_id: sessionId
        })
      });
      setSessionId(payload.session_id);
      setMessages(payload.chat_history);
      setActiveSources(payload.sources);
      setQuestion("");
      setStatus(`Answered using ${payload.retrieval_count} supporting chunk(s).`);
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoadingChat(false);
    }
  }

  async function loadSessionHistory(nextSessionId) {
    try {
      const payload = await fetchJson(`${API_BASE}/api/chat/${encodeURIComponent(nextSessionId)}/history`);
      const match = sessions.find((item) => item.session_id === nextSessionId);
      setSessionId(nextSessionId);
      if (match?.corpus_name) {
        setSelectedCorpus(match.corpus_name);
      }
      setMessages(payload);
      setActiveSources([]);
      setStatus(`Loaded session ${nextSessionId}.`);
    } catch (error) {
      setStatus(error.message);
    }
  }

  function startNewChat() {
    const next = createSessionId();
    setSessionId(next);
    setMessages([]);
    setActiveSources([]);
    setStatus("Started a fresh conversation.");
  }

  return (
    <div className="shell">
      <div className="backdrop backdrop-a" />
      <div className="backdrop backdrop-b" />

      <header className="hero panel">
        <div>
          <p className="eyebrow">Safe Conversational RAG</p>
          <div>Document Q&amp;A assistant for grounded follow-up answers.</div>
          <p className="lede">
            Build a corpus from PDFs or text files, inspect chunks on the admin side, and chat with session-aware
            retrieval on the user side.
          </p>
        </div>
        {/* <div className="hero-bar">
          <span>Embeddings: {health?.embedding_provider || "loading"}</span>
          <span>Model: {health?.llm_model || "loading"}</span>
          <span>Corpus: {selectedCorpus || "none"}</span>
        </div> */}
        <nav className="nav-tabs">
          <button
            className={route === "chat" ? "tab active" : "tab"}
            onClick={() => {
              window.location.hash = "#/chat";
            }}
            type="button"
          >
            User Chat
          </button>
          <button
            className={route === "admin" ? "tab active" : "tab"}
            onClick={() => {
              window.location.hash = "#/admin";
            }}
            type="button"
          >
            Admin Monitor
          </button>
        </nav>
      </header>

      <p className="status-banner">{status}</p>

      {route === "admin" ? (
        <section className="workspace admin-grid">
          <form className="panel stack" onSubmit={handleBuild}>
            <div className="panel-heading">
              <p className="label">Ingestion</p>
              <h2>Load and chunk documents</h2>
              <p>Supports `.pdf`, `.txt`, `.text`, and `.md` files through LangChain loaders.</p>
            </div>
            <label className="field">
              <span>Corpus name</span>
              <input
                placeholder="Leave blank to auto-name from the uploaded file"
                value={buildCorpusName}
                onChange={(event) => setBuildCorpusName(event.target.value)}
              />
            </label>
            <label className="upload-zone">
              <input
                type="file"
                accept=".pdf,.txt,.text,.md"
                multiple
                onChange={(event) => setFiles(Array.from(event.target.files || []))}
              />
              <strong>{files.length > 0 ? `${files.length} file(s) selected` : "Choose PDF or text documents"}</strong>
              <span>Large files will be chunked with overlap before embedding.</span>
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
              <span>Always rebuild the vector index</span>
            </label>
            <button className="primary-button" type="submit" disabled={loadingAdmin}>
              {loadingAdmin ? "Indexing..." : "Upload and build"}
            </button>
            <div className={loadingAdmin ? "progress-card active" : "progress-card"}>
              <strong>{loadingAdmin ? "Build in progress" : "Ready to build"}</strong>
              <span>
                {loadingAdmin
                  ? adminProgress || "Uploading files, extracting PDF text, chunking, embedding, and storing in Chroma."
                  : adminProgress || "Choose one or more PDF or text files, then start the corpus build."}
              </span>
            </div>
          </form>

          <section className="panel stack">
            <div className="panel-heading">
              <p className="label">Latest Build</p>
              <h2>Most recent indexing result</h2>
            </div>
            {lastIngestResult ? (
              <div className="build-summary">
                <div className="summary-stat">
                  <strong>Corpus</strong>
                  <span>{lastIngestResult.corpus_name}</span>
                </div>
                <div className="summary-stat">
                  <strong>Uploaded files</strong>
                  <span>{lastIngestResult.uploaded_files?.join(", ") || "None recorded"}</span>
                </div>
                <div className="summary-stat">
                  <strong>Loaded documents</strong>
                  <span>{lastIngestResult.loaded_document_count}</span>
                </div>
                <div className="summary-stat">
                  <strong>Chunks created</strong>
                  <span>{lastIngestResult.chunk_count}</span>
                </div>
                <div className="summary-stat">
                  <strong>Chunk config</strong>
                  <span>
                    {lastIngestResult.chunk_size} / {lastIngestResult.chunk_overlap}
                  </span>
                </div>
                <div className="summary-stat">
                  <strong>Manifest</strong>
                  <span>{lastIngestResult.manifest_path}</span>
                </div>
                <div className="summary-block">
                  <strong>Sample documents</strong>
                  <div className="card-list">
                    {lastIngestResult.sample_documents?.map((doc) => (
                      <article className="data-card" key={doc.doc_id}>
                        <div className="card-meta">
                          <strong>{doc.source_name}</strong>
                          <span>{doc.page ? `p. ${doc.page}` : doc.source_type}</span>
                        </div>
                        <p>{doc.sample_content}</p>
                      </article>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <p className="empty">Build a corpus to see the latest indexing result here.</p>
            )}
          </section>

          <section className="panel stack">
            <div className="panel-heading">
              <p className="label">Corpora</p>
              <h2>Available RAG indexes</h2>
            </div>
            <div className="card-list">
              {corpora.length === 0 ? <p className="empty">No corpora built yet.</p> : null}
              {corpora.map((corpus) => (
                <button
                  key={corpus.corpus_name}
                  className={corpus.corpus_name === selectedCorpus ? "select-card active" : "select-card"}
                  onClick={() => setSelectedCorpus(corpus.corpus_name)}
                  type="button"
                >
                  <strong>{corpus.corpus_name}</strong>
                  <span>{corpus.input_file_count} files</span>
                  <span>{corpus.loaded_document_count} docs</span>
                  <span>{corpus.chunk_count} chunks</span>
                  <span>{formatDate(corpus.last_ingested_at)}</span>
                </button>
              ))}
            </div>
          </section>

          <section className="panel stack">
            <div className="panel-heading">
              <p className="label">Documents</p>
              <h2>Loaded sample content</h2>
            </div>
            <div className="card-list tall">
              {documents.map((doc) => (
                <article className="data-card" key={doc.doc_id}>
                  <div className="card-meta">
                    <strong>{doc.source_name}</strong>
                    <span>{doc.page ? `p. ${doc.page}` : doc.source_type}</span>
                  </div>
                  <p>{doc.sample_content}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="panel stack">
            <div className="panel-heading">
              <p className="label">Chunk Explorer</p>
              <h2>Stored chunk previews</h2>
            </div>
            <div className="card-list tall">
              {chunks.map((chunk) => (
                <article className="data-card" key={chunk.chunk_id}>
                  <div className="card-meta">
                    <strong>{chunk.chunk_id}</strong>
                    <span>{chunk.source_name}</span>
                  </div>
                  <p>{chunk.preview}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="panel stack">
            <form onSubmit={handlePreview}>
              <div className="panel-heading">
                <p className="label">Retriever Preview</p>
                <h2>Inspect what the RAG sees</h2>
              </div>
              <label className="field">
                <span>Preview query</span>
                <textarea value={previewQuestion} onChange={(event) => setPreviewQuestion(event.target.value)} rows="4" />
              </label>
              <button className="secondary-button" type="submit">
                Run preview
              </button>
            </form>
            <div className="card-list tall">
              {previewHits.map((hit) => (
                <article className="data-card" key={`${hit.chunk_id}-${hit.score}`}>
                  <div className="card-meta">
                    <strong>{hit.source_name}</strong>
                    <span>score {hit.score}</span>
                  </div>
                  <p>{hit.preview}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="panel stack">
            <div className="panel-heading">
              <p className="label">Sessions</p>
              <h2>Recent conversations</h2>
            </div>
            <div className="card-list">
              {sessions.length === 0 ? <p className="empty">No chat sessions yet.</p> : null}
              {sessions.map((session) => (
                <button
                  className="select-card"
                  key={session.session_id}
                  onClick={() => loadSessionHistory(session.session_id)}
                  type="button"
                >
                  <strong>{session.corpus_name}</strong>
                  <span>{session.message_count} messages</span>
                  <span>{formatDate(session.updated_at)}</span>
                  <span>{session.preview || "No assistant reply yet."}</span>
                </button>
              ))}
            </div>
          </section>
        </section>
      ) : (
        <section className="workspace user-grid">
          <aside className="panel stack">
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
            <p className="helper">
              Try follow-ups like “Explain more”, “What about the previous point?”, or “Summarize that section again.”
            </p>
          </aside>

          <div className="chat-column">
            <section className="panel transcript-panel">
              <div className="panel-heading">
                <p className="label">Chat Window</p>
                <h2>User page</h2>
              </div>
              <div className="transcript">
                {messages.length === 0 ? <p className="empty">No messages yet. Ask a grounded question to begin.</p> : null}
                {messages.map((message, index) => (
                  <article className={message.role === "assistant" ? "bubble assistant" : "bubble user"} key={`${message.role}-${index}`}>
                    <span>{message.role === "assistant" ? "Assistant" : "You"}</span>
                    <p>{message.content}</p>
                  </article>
                ))}
              </div>
              <form className="composer" onSubmit={handleSend}>
                <textarea
                  placeholder="Ask from the uploaded documents..."
                  rows="4"
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                />
                <button className="primary-button" type="submit" disabled={loadingChat}>
                  {loadingChat ? "Answering..." : "Send"}
                </button>
              </form>
            </section>

            <section className="panel stack">
              <div className="panel-heading">
                <p className="label">Sources</p>
                <h2>Grounding evidence</h2>
              </div>
              <div className="card-list tall">
                {activeSources.length === 0 ? <p className="empty">Sources appear here after each answer.</p> : null}
                {activeSources.map((source, index) => (
                  <SourceBadge key={`${source.chunk_id}-${index}`} source={source} />
                ))}
              </div>
            </section>
          </div>
        </section>
      )}
    </div>
  );
}
