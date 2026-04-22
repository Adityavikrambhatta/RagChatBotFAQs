import { BuildSummaryPanel } from "./components/AnswerPanel";
import { BuildPanel } from "./components/BuildPanel";
import { ChunksPanel } from "./components/ChunksPanel";
import { CorpusListPanel } from "./components/CorpusListPanel";
import { DocumentsPanel } from "./components/DocumentsPanel";
import { HeroSection } from "./components/HeroSection";
import { PreviewPanel } from "./components/PreviewPanel";
import { SessionsPanel } from "./components/HistoryPanel";
import { SourcesPanel } from "./components/CitationsPanel";
import { TranscriptPanel } from "./components/TranscriptPanel";
import { UserControlsPanel } from "./components/AskPanel";
import { AppStoreProvider, useAppStore } from "./stores/AppStore";
import { ChatStoreProvider } from "./stores/ChatStore";
import { CorpusStoreProvider } from "./stores/CorpusStore";

function AdminView() {
  return (
    <div className="workspace admin-grid">
      <BuildPanel />
      <BuildSummaryPanel />
      <CorpusListPanel />
      <DocumentsPanel />
      <ChunksPanel />
      <PreviewPanel />
      <SessionsPanel />
    </div>
  );
}

function ChatView() {
  return (
    <div className="workspace user-grid">
      <UserControlsPanel />

      <div className="chat-column">
        <TranscriptPanel />
        <SourcesPanel />
      </div>
    </div>
  );
}

function StudioShell() {
  const { route, status } = useAppStore();

  return (
    <div className="shell">
      <div className="backdrop backdrop-a" />
      <div className="backdrop backdrop-b" />

      <HeroSection />

      <p className="status-banner">{status}</p>

      {route === "admin" ? <AdminView /> : <ChatView />}
    </div>
  );
}

export default function App() {
  return (
    <AppStoreProvider>
      <CorpusStoreProvider>
        <ChatStoreProvider>
          <StudioShell />
        </ChatStoreProvider>
      </CorpusStoreProvider>
    </AppStoreProvider>
  );
}
