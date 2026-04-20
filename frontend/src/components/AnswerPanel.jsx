import { useCorpusStore } from "../stores/CorpusStore";

export function BuildSummaryPanel() {
  const { lastIngestResult } = useCorpusStore();

  return (
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
  );
}
