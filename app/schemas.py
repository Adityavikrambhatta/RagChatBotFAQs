from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CorpusBuildRequest(BaseModel):
    corpus_name: str = Field(min_length=1)
    input_dir: str = Field(min_length=1)
    force_rebuild: bool = False


class ChatRequest(BaseModel):
    corpus_name: str | None = None
    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)


class HealthResponse(BaseModel):
    status: str
    default_corpus: str
    embedding_backend: str
    ollama_chat_enabled: bool


class CorpusRecord(BaseModel):
    corpus_name: str
    input_dir: str
    collection_name: str
    indexed_files: int
    chunk_count: int
    last_built_at: str


class RetrievalHit(BaseModel):
    chunk_id: str
    source_file: str
    source_type: str
    score: float
    snippet: str
    metadata: dict[str, Any]


class ChatResponse(BaseModel):
    answer: str
    corpus_name: str
    retrieval_count: int
    citations: list[RetrievalHit]


class BuildResponse(BaseModel):
    corpus_name: str
    collection_name: str
    input_dir: str
    indexed_files: int
    chunk_count: int
    skipped: bool
    manifest_path: str
