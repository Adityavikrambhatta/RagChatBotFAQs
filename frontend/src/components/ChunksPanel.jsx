import { useCorpusStore } from "../stores/CorpusStore";

export function ChunksPanel() {
  const { chunks } = useCorpusStore();

  return (
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
  );
}
