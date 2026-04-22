import { useCorpusStore } from "../stores/CorpusStore";

export function DocumentsPanel() {
  const { documents } = useCorpusStore();

  return (
    <div className="panel stack panel-shell">
      <div className="panel-heading">
        <p className="label">Documents</p>
        <h2>Loaded sample content</h2>
      </div>
      <div className="card-list tall">
        {documents.map((doc) => (
          <div className="data-card" key={doc.doc_id}>
            <div className="card-meta">
              <strong>{doc.source_name}</strong>
              <span>{doc.page ? `p. ${doc.page}` : doc.source_type}</span>
            </div>
            <p>{doc.sample_content}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
