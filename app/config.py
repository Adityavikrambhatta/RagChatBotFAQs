from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    data_dir: Path = Field(default=Path("./data"), alias="RAG_APP_DATA_DIR")
    default_corpus: str = Field(default="document-qa", alias="RAG_APP_DEFAULT_CORPUS")
    collection_prefix: str = Field(default="rag_", alias="RAG_APP_COLLECTION_PREFIX")
    chunk_size: int = Field(default=1000, alias="RAG_APP_CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="RAG_APP_CHUNK_OVERLAP")
    default_top_k: int = Field(default=4, alias="RAG_APP_DEFAULT_TOP_K")
    embedding_provider: str = Field(default="ollama", alias="RAG_APP_EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="nomic-embed-text", alias="RAG_APP_EMBEDDING_MODEL")
    llm_provider: str = Field(default="ollama", alias="RAG_APP_LLM_PROVIDER")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="RAG_APP_OPENAI_MODEL")
    openai_base_url: str | None = Field(default=None, alias="RAG_APP_OPENAI_BASE_URL")
    ollama_base_url: str = Field(default="http://127.0.0.1:11434", alias="RAG_APP_OLLAMA_BASE_URL")
    ollama_chat_model: str = Field(default="llama3.1", alias="RAG_APP_OLLAMA_CHAT_MODEL")
    ollama_embedding_model: str = Field(default="nomic-embed-text", alias="RAG_APP_OLLAMA_EMBED_MODEL")
    llm_temperature: float = Field(default=0.0, alias="RAG_APP_LLM_TEMPERATURE")
    max_history_messages: int = Field(default=12, alias="RAG_APP_MAX_HISTORY_MESSAGES")
    frontend_origin: str = Field(default="http://127.0.0.1:5173", alias="RAG_APP_FRONTEND_ORIGIN")

    @field_validator("openai_api_key", "openai_base_url", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        if not normalized:
            return None
        normalized = normalized.strip("\"'")
        if not normalized:
            return None
        return normalized

    @property
    def incoming_dir(self) -> Path:
        return self.data_dir / "incoming"

    @property
    def corpora_dir(self) -> Path:
        return self.data_dir / "corpora"

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "chroma"

    @property
    def sessions_dir(self) -> Path:
        return self.data_dir / "sessions"

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.incoming_dir.mkdir(parents=True, exist_ok=True)
        self.corpora_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def collection_name_for(self, corpus_name: str) -> str:
        safe = "-".join(corpus_name.strip().lower().split())
        return f"{self.collection_prefix}{safe}"

    def active_embedding_model(self) -> str:
        if self.embedding_provider.lower() == "ollama":
            return self.ollama_embedding_model
        return self.embedding_model

    def active_llm_model(self) -> str:
        if self.llm_provider.lower() == "ollama":
            return self.ollama_chat_model
        return self.openai_model


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
