from __future__ import annotations

import json
import logging
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from langchain_core.documents import Document

from app.config import Settings
from app.history import FileBackedChatHistory
from app.langchain_rag import (
    build_conversational_chain,
    build_embeddings,
    get_vector_store,
    load_documents,
    normalize_corpus_name,
    reset_collection,
    retrieval_preview,
    split_documents,
)
from app.schemas import ChunkPreview, CorpusSummary, DocumentPreview, IngestResponse

logger = logging.getLogger(__name__)


class ConversationalRagService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.history = FileBackedChatHistory(settings.sessions_dir, settings.max_history_messages)

    def build_corpus(self, *, corpus_name: str, input_dir: Path, force_rebuild: bool = False) -> IngestResponse:
        normalized_corpus = normalize_corpus_name(corpus_name)
        resolved_input = input_dir.expanduser().resolve()
        if not resolved_input.exists():
            raise FileNotFoundError(f"Input directory does not exist: {resolved_input}")
        logger.info("Starting corpus build for '%s' from %s", normalized_corpus, resolved_input)

        corpus_dir = self.settings.corpora_dir / normalized_corpus
        manifest_path = corpus_dir / "manifest.json"
        documents_path = corpus_dir / "documents.json"
        chunks_path = corpus_dir / "chunks.json"
        corpus_dir.mkdir(parents=True, exist_ok=True)

        raw_documents, source_files = load_documents(resolved_input)
        if not raw_documents:
            raise ValueError("No supported PDF or text documents were found to index.")
        logger.info("Loaded %s source files into %s documents", len(source_files), len(raw_documents))

        chunked_documents = split_documents(raw_documents, self.settings)
        if not chunked_documents:
            raise ValueError("Documents were loaded, but no chunks were created.")
        logger.info(
            "Split corpus '%s' into %s chunks with chunk_size=%s overlap=%s",
            normalized_corpus,
            len(chunked_documents),
            self.settings.chunk_size,
            self.settings.chunk_overlap,
        )

        embeddings = build_embeddings(self.settings)
        logger.info(
            "Embedding provider for '%s': %s (%s)",
            normalized_corpus,
            self.settings.embedding_provider,
            self.settings.active_embedding_model(),
        )
        reset_collection(self.settings, normalized_corpus)
        vector_store = get_vector_store(self.settings, normalized_corpus, embeddings)
        vector_store.add_documents(chunked_documents)
        logger.info("Finished indexing corpus '%s' into Chroma", normalized_corpus)

        document_previews = [self._document_preview(index, doc) for index, doc in enumerate(raw_documents, start=1)]
        chunk_previews = [self._chunk_preview(doc) for doc in chunked_documents]

        manifest = {
            "corpus_name": normalized_corpus,
            "collection_name": self.settings.collection_name_for(normalized_corpus),
            "input_dir": str(resolved_input),
            "input_file_count": len(source_files),
            "loaded_document_count": len(raw_documents),
            "chunk_count": len(chunked_documents),
            "chunk_size": self.settings.chunk_size,
            "chunk_overlap": self.settings.chunk_overlap,
            "last_ingested_at": datetime.now(UTC).isoformat(),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        documents_path.write_text(json.dumps([preview.model_dump() for preview in document_previews], indent=2), encoding="utf-8")
        chunks_path.write_text(json.dumps([preview.model_dump() for preview in chunk_previews], indent=2), encoding="utf-8")

        return IngestResponse(
            corpus_name=normalized_corpus,
            collection_name=manifest["collection_name"],
            input_dir=str(resolved_input),
            input_file_count=len(source_files),
            loaded_document_count=len(raw_documents),
            chunk_count=len(chunked_documents),
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            sample_documents=document_previews[:3],
            manifest_path=str(manifest_path),
        )

    def upload_and_build_corpus(
        self,
        *,
        corpus_name: str,
        files: list[tuple[str, bytes]],
        force_rebuild: bool = False,
        replace_existing: bool = True,
    ) -> IngestResponse:
        if not files:
            raise ValueError("At least one file must be uploaded.")
        normalized_corpus = self._resolve_upload_corpus_name(corpus_name, files)
        logger.info("Received %s uploaded file(s) for corpus '%s'", len(files), normalized_corpus)

        target_dir = self.settings.incoming_dir / normalized_corpus
        if replace_existing and target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        uploaded_files: list[str] = []
        for original_name, content in files:
            safe_name = Path(original_name).name
            if not safe_name or not content:
                continue
            destination = target_dir / safe_name
            destination.write_bytes(content)
            uploaded_files.append(safe_name)

        if not uploaded_files:
            raise ValueError("Uploaded files were empty or invalid.")

        response = self.build_corpus(corpus_name=normalized_corpus, input_dir=target_dir, force_rebuild=force_rebuild)
        payload = response.model_dump()
        payload["uploaded_files"] = uploaded_files
        return IngestResponse(**payload)

    def list_corpora(self) -> list[CorpusSummary]:
        records: list[CorpusSummary] = []
        for manifest_path in sorted(self.settings.corpora_dir.glob("*/manifest.json")):
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            records.append(CorpusSummary(**payload))
        return records

    def list_sessions(self):
        return self.history.list_sessions()

    def get_documents(self, corpus_name: str) -> list[DocumentPreview]:
        path = self.settings.corpora_dir / normalize_corpus_name(corpus_name) / "documents.json"
        if not path.exists():
            raise ValueError(f"Corpus '{corpus_name}' has not been ingested yet.")
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [DocumentPreview(**item) for item in payload]

    def get_corpus_detail(self, corpus_name: str) -> IngestResponse:
        normalized_corpus = normalize_corpus_name(corpus_name)
        manifest_path = self.settings.corpora_dir / normalized_corpus / "manifest.json"
        if not manifest_path.exists():
            raise ValueError(f"Corpus '{corpus_name}' has not been ingested yet.")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        documents = self.get_documents(normalized_corpus)
        incoming_dir = self.settings.incoming_dir / normalized_corpus
        uploaded_files = [path.name for path in sorted(incoming_dir.iterdir()) if path.is_file()] if incoming_dir.exists() else []

        return IngestResponse(
            corpus_name=manifest["corpus_name"],
            collection_name=manifest["collection_name"],
            input_dir=manifest["input_dir"],
            uploaded_files=uploaded_files,
            input_file_count=manifest["input_file_count"],
            loaded_document_count=manifest["loaded_document_count"],
            chunk_count=manifest["chunk_count"],
            chunk_size=manifest["chunk_size"],
            chunk_overlap=manifest["chunk_overlap"],
            sample_documents=documents[:3],
            manifest_path=str(manifest_path),
        )

    def get_chunks(self, corpus_name: str, limit: int = 60) -> list[ChunkPreview]:
        path = self.settings.corpora_dir / normalize_corpus_name(corpus_name) / "chunks.json"
        if not path.exists():
            raise ValueError(f"Corpus '{corpus_name}' has not been ingested yet.")
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [ChunkPreview(**item) for item in payload[:limit]]

    def preview_retrieval(self, *, corpus_name: str, question: str, top_k: int) -> list[ChunkPreview]:
        normalized_corpus = normalize_corpus_name(corpus_name)
        self._ensure_manifest(normalized_corpus)
        hits = retrieval_preview(self.settings, normalized_corpus, question, top_k)
        previews: list[ChunkPreview] = []
        for document, score in hits:
            previews.append(
                ChunkPreview(
                    chunk_id=str(document.metadata.get("chunk_id", "unknown")),
                    source_name=str(document.metadata.get("source_name", "unknown")),
                    source_type=str(document.metadata.get("source_type", "unknown")),
                    page=self._page_number(document.metadata),
                    preview=document.page_content[:360],
                    metadata=document.metadata,
                    score=round(float(score), 4),
                )
            )
        return previews

    def chat(self, *, question: str, corpus_name: str, session_id: str | None, top_k: int) -> dict[str, object]:
        normalized_corpus = normalize_corpus_name(corpus_name)
        self._ensure_manifest(normalized_corpus)
        active_session_id = session_id or uuid4().hex
        existing_messages = self.history.load_messages(active_session_id)
        logger.info(
            "Chat request for corpus '%s' session '%s' using provider '%s'",
            normalized_corpus,
            active_session_id,
            f"{self.settings.llm_provider}:{self.settings.active_llm_model()}",
        )
        if self.settings.llm_provider.lower() == "demo":
            supporting_docs, answer = self._demo_chat(normalized_corpus, question, existing_messages, top_k)
        else:
            chain = build_conversational_chain(self.settings, normalized_corpus, top_k)
            result = chain.invoke({"input": question, "chat_history": existing_messages})
            supporting_docs = result.get("context", [])
            answer = str(result.get("answer", "")).strip()
            if not supporting_docs:
                answer = "I don't know."
        logger.info("Chat response for corpus '%s' used %s supporting documents", normalized_corpus, len(supporting_docs))

        self.history.append_turn(
            session_id=active_session_id,
            corpus_name=normalized_corpus,
            user_message=question,
            assistant_message=answer,
        )

        sources = [self._chunk_preview(doc) for doc in supporting_docs]
        return {
            "answer": answer,
            "corpus_name": normalized_corpus,
            "session_id": active_session_id,
            "retrieval_count": len(sources),
            "sources": sources,
            "chat_history": self.history.turns_for(active_session_id),
        }

    def history_for(self, session_id: str):
        return self.history.turns_for(session_id)

    def _ensure_manifest(self, corpus_name: str) -> None:
        manifest = self.settings.corpora_dir / corpus_name / "manifest.json"
        if not manifest.exists():
            raise ValueError(f"Corpus '{corpus_name}' has not been ingested yet.")

    def _resolve_upload_corpus_name(self, requested_name: str, files: list[tuple[str, bytes]]) -> str:
        trimmed = requested_name.strip()
        if trimmed:
            return normalize_corpus_name(trimmed)

        first_name = Path(files[0][0]).stem if files else "corpus"
        slug = re.sub(r"[^a-z0-9]+", "-", first_name.lower()).strip("-") or "corpus"
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        return normalize_corpus_name(f"{slug}-{timestamp}")

    @staticmethod
    def _page_number(metadata: dict[str, object]) -> int | None:
        page = metadata.get("page")
        return int(page) + 1 if isinstance(page, int) else None

    def _document_preview(self, index: int, document: Document) -> DocumentPreview:
        return DocumentPreview(
            doc_id=f"doc-{index:04d}",
            source_name=str(document.metadata.get("source_name", "unknown")),
            source_type=str(document.metadata.get("source_type", "unknown")),
            page=self._page_number(document.metadata),
            sample_content=document.page_content[:240],
            metadata=document.metadata,
        )

    def _chunk_preview(self, document: Document) -> ChunkPreview:
        return ChunkPreview(
            chunk_id=str(document.metadata.get("chunk_id", "unknown")),
            source_name=str(document.metadata.get("source_name", "unknown")),
            source_type=str(document.metadata.get("source_type", "unknown")),
            page=self._page_number(document.metadata),
            preview=document.page_content[:360],
            metadata=document.metadata,
        )

    def _demo_chat(self, corpus_name: str, question: str, existing_messages, top_k: int) -> tuple[list[Document], str]:
        embeddings = build_embeddings(self.settings)
        vector_store = get_vector_store(self.settings, corpus_name, embeddings)
        retrieval_query = self._rewrite_for_demo(question, existing_messages)
        supporting_docs = vector_store.similarity_search(retrieval_query, k=top_k)
        answer = self._grounded_demo_answer(question, supporting_docs)
        return supporting_docs, answer

    def _rewrite_for_demo(self, question: str, existing_messages) -> str:
        lowered = question.lower()
        follow_up_cues = ["explain more", "previous point", "that section", "that point", "summarize that"]
        if not existing_messages or not any(cue in lowered for cue in follow_up_cues):
            return question

        prior_user_messages = [str(message.content) for message in existing_messages if message.type == "human"]
        if not prior_user_messages:
            return question
        return f"{prior_user_messages[-1]} {question}"

    def _grounded_demo_answer(self, question: str, supporting_docs: list[Document]) -> str:
        if not supporting_docs:
            return "I don't know."

        question_terms = {term for term in re.findall(r"[a-z0-9]+", question.lower()) if len(term) > 2}
        picked_sentences: list[tuple[str, str]] = []
        for doc in supporting_docs:
            source_name = str(doc.metadata.get("source_name", "unknown"))
            for sentence in re.split(r"(?<=[.!?])\s+", doc.page_content.strip()):
                terms = set(re.findall(r"[a-z0-9]+", sentence.lower()))
                overlap = len(question_terms & terms)
                if overlap > 0 or not question_terms:
                    picked_sentences.append((sentence.strip(), source_name))
                if len(picked_sentences) >= 3:
                    break
            if len(picked_sentences) >= 3:
                break

        if not picked_sentences:
            return "I don't know."

        rendered = " ".join(sentence for sentence, _source in picked_sentences)
        sources = ", ".join(sorted({source for _sentence, source in picked_sentences}))
        return f"{rendered} [{sources}]"
