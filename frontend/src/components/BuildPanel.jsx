import { useCorpusStore } from "../stores/CorpusStore";

export function BuildPanel() {
  const {
    buildCorpusName,
    setBuildCorpusName,
    files,
    setFiles,
    replaceExisting,
    setReplaceExisting,
    forceRebuild,
    setForceRebuild,
    loadingAdmin,
    adminProgress,
    submitBuild
  } = useCorpusStore();

  async function handleSubmit(event) {
    event.preventDefault();
    try {
      await submitBuild();
    } catch {
      // Status is managed in the store.
    }
  }

  return (
    <div className="panel stack panel-shell">
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
        <input type="file" accept=".pdf,.txt,.text,.md" multiple onChange={(event) => setFiles(Array.from(event.target.files || []))} />
        <strong>{files.length > 0 ? `${files.length} file(s) selected` : "Choose PDF or text documents"}</strong>
        <span>Large files will be chunked with overlap before embedding.</span>
      </label>
      <label className="toggle">
        <input type="checkbox" checked={replaceExisting} onChange={(event) => setReplaceExisting(event.target.checked)} />
        <span>Replace existing uploaded files for this corpus</span>
      </label>
      <label className="toggle">
        <input type="checkbox" checked={forceRebuild} onChange={(event) => setForceRebuild(event.target.checked)} />
        <span>Always rebuild the vector index</span>
      </label>
      <button className="primary-button" type="button" onClick={handleSubmit} disabled={loadingAdmin}>
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
    </div>
  );
}
