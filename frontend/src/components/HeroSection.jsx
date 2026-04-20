import { useAppStore } from "../stores/AppStore";
import { useCorpusStore } from "../stores/CorpusStore";

export function HeroSection() {
  const { route, navigate } = useAppStore();
  const { selectedCorpus } = useCorpusStore();

  return (
    <header className="hero panel">
      <div>
        <p className="eyebrow">Safe Conversational RAG</p>
        <div>Document Q&amp;A assistant for grounded follow-up answers.</div>
        <p className="lede">
          Build a corpus from PDFs or text files, inspect chunks on the admin side, and chat with session-aware
          retrieval on the user side.
        </p>
      </div>
      <nav className="nav-tabs">
        <button className={route === "chat" ? "tab active" : "tab"} onClick={() => navigate("chat")} type="button">
          User Chat
        </button>
        <button className={route === "admin" ? "tab active" : "tab"} onClick={() => navigate("admin")} type="button">
          Admin Monitor
        </button>
      </nav>
    </header>
  );
}
