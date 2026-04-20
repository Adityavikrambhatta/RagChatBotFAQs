import { createContext, useContext, useState } from "react";

import { API_BASE, fetchJson } from "../api/client";
import { createSessionId } from "../utils/appRuntime";
import { useAppStore } from "./AppStore";
import { useCorpusStore } from "./CorpusStore";

const ChatStoreContext = createContext(null);

export function ChatStoreProvider({ children }) {
  const { setStatus } = useAppStore();
  const { selectedCorpus, setSelectedCorpus, sessions } = useCorpusStore();
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [activeSources, setActiveSources] = useState([]);
  const [sessionId, setSessionId] = useState(createSessionId());
  const [loadingChat, setLoadingChat] = useState(false);

  async function submitQuestion() {
    if (!question.trim()) {
      setStatus("Type a question before sending.");
      return null;
    }
    setLoadingChat(true);
    try {
      const payload = await fetchJson(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          corpus_name: selectedCorpus,
          question: question.trim(),
          session_id: sessionId
        })
      });
      setSessionId(payload.session_id);
      setMessages(payload.chat_history);
      setActiveSources(payload.sources);
      setQuestion("");
      setStatus(`Answered using ${payload.retrieval_count} supporting chunk(s).`);
      return payload;
    } catch (error) {
      setStatus(error.message);
      throw error;
    } finally {
      setLoadingChat(false);
    }
  }

  async function loadSessionHistory(nextSessionId) {
    try {
      const payload = await fetchJson(`${API_BASE}/api/chat/${encodeURIComponent(nextSessionId)}/history`);
      const match = sessions.find((item) => item.session_id === nextSessionId);
      if (match?.corpus_name) {
        setSelectedCorpus(match.corpus_name);
      }
      setSessionId(nextSessionId);
      setMessages(payload);
      setActiveSources([]);
      setStatus(`Loaded session ${nextSessionId}.`);
      return payload;
    } catch (error) {
      setStatus(error.message);
      throw error;
    }
  }

  function startNewChat() {
    const next = createSessionId();
    setSessionId(next);
    setMessages([]);
    setActiveSources([]);
    setStatus("Started a fresh conversation.");
  }

  const value = {
    question,
    setQuestion,
    messages,
    activeSources,
    sessionId,
    setSessionId,
    loadingChat,
    submitQuestion,
    loadSessionHistory,
    startNewChat
  };

  return <ChatStoreContext.Provider value={value}>{children}</ChatStoreContext.Provider>;
}

export function useChatStore() {
  const value = useContext(ChatStoreContext);
  if (!value) {
    throw new Error("useChatStore must be used within ChatStoreProvider");
  }
  return value;
}
