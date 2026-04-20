import { SourceBadge } from "./SourceBadge";
import { useChatStore } from "../stores/ChatStore";

export function SourcesPanel() {
  const { activeSources } = useChatStore();

  return (
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
  );
}
