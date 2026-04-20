import { useCorpusStore } from "../stores/CorpusStore";

export function PreviewPanel() {
  const { previewQuestion, setPreviewQuestion, previewHits, runPreview } = useCorpusStore();

  async function handleSubmit(event) {
    event.preventDefault();
    try {
      await runPreview();
    } catch {
      // Status is managed in the store.
    }
  }

  return (
    <section className="panel stack">
      <form onSubmit={handleSubmit}>
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
  );
}
