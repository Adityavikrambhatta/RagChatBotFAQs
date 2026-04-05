from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CorpusBuildRequest(BaseModel):
    corpus_name: str = Field(min_length=1)
    input_dir: str = Field(min_length=1)
    force_rebuild: bool = False


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    corpus_name: str | None = None
    session_id: str | None = None
    top_k: int | None = Field(default=None, ge=1, le=12)


class RetrievalPreviewRequest(BaseModel):
    question: str = Field(min_length=1)
    corpus_name: str
    top_k: int = Field(default=4, ge=1, le=12)


class HealthResponse(BaseModel):
    status: str
    default_corpus: str
    embedding_provider: str
    embedding_model: str
    llm_provider: str
    llm_model: str
    frontend_origin: str


class CorpusSummary(BaseModel):
    corpus_name: str
    collection_name: str
    input_dir: str
    input_file_count: int
    loaded_document_count: int
    chunk_count: int
    chunk_size: int
    chunk_overlap: int
    last_ingested_at: str


class DocumentPreview(BaseModel):
    doc_id: str
    source_name: str
    source_type: str
    page: int | None = None
    sample_content: str
    metadata: dict[str, Any]


class ChunkPreview(BaseModel):
    chunk_id: str
    source_name: str
    source_type: str
    page: int | None = None
    preview: str
    metadata: dict[str, Any]
    score: float | None = None


class ChatTurn(BaseModel):
    role: str
    content: str


class SessionSummary(BaseModel):
    session_id: str
    corpus_name: str
    message_count: int
    updated_at: str
    preview: str


class IngestResponse(BaseModel):
    corpus_name: str
    collection_name: str
    input_dir: str
    uploaded_files: list[str] = Field(default_factory=list)
    input_file_count: int
    loaded_document_count: int
    chunk_count: int
    chunk_size: int
    chunk_overlap: int
    sample_documents: list[DocumentPreview]
    manifest_path: str


class ChatResponse(BaseModel):
    answer: str
    corpus_name: str
    session_id: str
    retrieval_count: int
    sources: list[ChunkPreview]
    chat_history: list[ChatTurn]


class AdminOverview(BaseModel):
    corpora: list[CorpusSummary]
    sessions: list[SessionSummary]
