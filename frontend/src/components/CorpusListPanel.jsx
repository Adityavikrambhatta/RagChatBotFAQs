import { useCorpusStore } from "../stores/CorpusStore";
import { formatDate } from "../utils/formatters";

export function CorpusListPanel() {
  const { corpora, selectedCorpus, setSelectedCorpus } = useCorpusStore();

  return (
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
  );
}
