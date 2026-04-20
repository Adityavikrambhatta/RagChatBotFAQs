export function SourceBadge({ source }) {
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
