import { createContext, startTransition, useContext, useEffect, useState } from "react";

import { API_BASE, fetchJson } from "../api/client";
import { useAppStore } from "./AppStore";

const CorpusStoreContext = createContext(null);

export function CorpusStoreProvider({ children }) {
  const { setHealth, setStatus } = useAppStore();
  const [corpora, setCorpora] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [selectedCorpus, setSelectedCorpus] = useState("");
  const [documents, setDocuments] = useState([]);
  const [chunks, setChunks] = useState([]);
  const [previewHits, setPreviewHits] = useState([]);
  const [previewQuestion, setPreviewQuestion] = useState(
    "What does the support guide recommend for follow-up questions?"
  );
  const [buildCorpusName, setBuildCorpusName] = useState("");
  const [files, setFiles] = useState([]);
  const [forceRebuild, setForceRebuild] = useState(true);
  const [replaceExisting, setReplaceExisting] = useState(true);
  const [loadingAdmin, setLoadingAdmin] = useState(false);
  const [adminProgress, setAdminProgress] = useState("");
  const [lastIngestResult, setLastIngestResult] = useState(null);

  async function refreshCorpusDetails(corpusName) {
    if (!corpusName) {
      return;
    }
    const [detailPayload, documentPayload, chunkPayload] = await Promise.all([
      fetchJson(`${API_BASE}/api/admin/corpus-detail?corpus_name=${encodeURIComponent(corpusName)}`),
      fetchJson(`${API_BASE}/api/admin/documents?corpus_name=${encodeURIComponent(corpusName)}`),
      fetchJson(`${API_BASE}/api/admin/chunks?corpus_name=${encodeURIComponent(corpusName)}&limit=40`)
    ]);
    startTransition(() => {
      setLastIngestResult(detailPayload);
      setDocuments(documentPayload);
      setChunks(chunkPayload);
    });
  }

  async function refreshOverview() {
    const [healthPayload, overviewPayload] = await Promise.all([
      fetchJson(`${API_BASE}/api/health`),
      fetchJson(`${API_BASE}/api/admin/overview`)
    ]);

    let nextCorpus = healthPayload.default_corpus || "";

    startTransition(() => {
      setHealth(healthPayload);
      setCorpora(overviewPayload.corpora);
      setSessions(overviewPayload.sessions);
      if (overviewPayload.corpora.length > 0) {
        const defaultCorpus = overviewPayload.corpora.some((item) => item.corpus_name === selectedCorpus)
          ? selectedCorpus
          : overviewPayload.corpora[0].corpus_name;
        nextCorpus = defaultCorpus;
        setSelectedCorpus(defaultCorpus);
      } else {
        nextCorpus = "";
        setSelectedCorpus("");
      }
      if (!buildCorpusName && overviewPayload.corpora.length === 0) {
        setBuildCorpusName("");
      }
    });

    if (nextCorpus) {
      await refreshCorpusDetails(nextCorpus);
    } else {
      startTransition(() => {
        setLastIngestResult(null);
        setDocuments([]);
        setChunks([]);
      });
    }
  }

  useEffect(() => {
    refreshOverview().catch((error) => setStatus(error.message));
  }, []);

  useEffect(() => {
    refreshCorpusDetails(selectedCorpus).catch((error) => {
      setLastIngestResult(null);
      setDocuments([]);
      setChunks([]);
      setStatus(error.message);
    });
  }, [selectedCorpus]);

  async function submitBuild() {
    if (files.length === 0) {
      setStatus("Upload at least one PDF or text document.");
      return null;
    }

    const formData = new FormData();
    formData.append("corpus_name", buildCorpusName.trim());
    formData.append("force_rebuild", String(forceRebuild));
    formData.append("replace_existing", String(replaceExisting));
    for (const file of files) {
      formData.append("files", file);
    }

    setLoadingAdmin(true);
    setAdminProgress(`Uploading ${files.length} file(s) and preparing the corpus...`);
    setStatus("Upload started. PDF extraction and embedding can take a little while for larger files.");

    try {
      const payload = await fetchJson(`${API_BASE}/api/corpora/upload-build`, {
        method: "POST",
        body: formData
      });
      setSelectedCorpus(payload.corpus_name);
      setBuildCorpusName(payload.corpus_name);
      setLastIngestResult(payload);
      setStatus(
        `Indexed ${payload.input_file_count} file(s) into ${payload.chunk_count} chunks for corpus ${payload.corpus_name}.`
      );
      setAdminProgress("Upload complete. Corpus index refreshed successfully.");
      setFiles([]);
      await refreshOverview();
      await refreshCorpusDetails(payload.corpus_name);
      return payload;
    } catch (error) {
      setAdminProgress("");
      setStatus(error.message);
      throw error;
    } finally {
      setLoadingAdmin(false);
    }
  }

  async function runPreview() {
    if (!previewQuestion.trim()) {
      setStatus("Ask a preview query to inspect retrieved chunks.");
      return null;
    }

    try {
      const payload = await fetchJson(`${API_BASE}/api/admin/retrieve-preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          corpus_name: selectedCorpus,
          question: previewQuestion.trim(),
          top_k: 4
        })
      });
      setPreviewHits(payload);
      setStatus(`Retrieved ${payload.length} chunk(s) for admin preview.`);
      return payload;
    } catch (error) {
      setStatus(error.message);
      throw error;
    }
  }

  const value = {
    corpora,
    sessions,
    selectedCorpus,
    setSelectedCorpus,
    documents,
    chunks,
    previewHits,
    previewQuestion,
    setPreviewQuestion,
    buildCorpusName,
    setBuildCorpusName,
    files,
    setFiles,
    forceRebuild,
    setForceRebuild,
    replaceExisting,
    setReplaceExisting,
    loadingAdmin,
    adminProgress,
    lastIngestResult,
    refreshOverview,
    submitBuild,
    runPreview
  };

  return <CorpusStoreContext.Provider value={value}>{children}</CorpusStoreContext.Provider>;
}

export function useCorpusStore() {
  const value = useContext(CorpusStoreContext);
  if (!value) {
    throw new Error("useCorpusStore must be used within CorpusStoreProvider");
  }
  return value;
}
