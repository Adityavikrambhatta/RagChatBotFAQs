from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    data_dir: Path = Field(default=Path("./data"), alias="RAG_APP_DATA_DIR")
    default_corpus: str = Field(default="product-support", alias="RAG_APP_DEFAULT_CORPUS")
    collection_prefix: str = Field(default="faq_", alias="RAG_APP_COLLECTION_PREFIX")
    chunk_size: int = Field(default=1000, alias="RAG_APP_CHUNK_SIZE")
    chunk_overlap: int = Field(default=150, alias="RAG_APP_CHUNK_OVERLAP")
    default_top_k: int = Field(default=5, alias="RAG_APP_DEFAULT_TOP_K")
    embedding_backend: str = Field(default="sentence_transformers", alias="RAG_APP_EMBEDDING_BACKEND")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", alias="RAG_APP_EMBEDDING_MODEL")
    ollama_base_url: str = Field(default="http://127.0.0.1:11434", alias="RAG_APP_OLLAMA_BASE_URL")
    ollama_chat_model: str | None = Field(default=None, alias="RAG_APP_OLLAMA_CHAT_MODEL")
    ollama_embed_model: str | None = Field(default=None, alias="RAG_APP_OLLAMA_EMBED_MODEL")

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
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.incoming_dir.mkdir(parents=True, exist_ok=True)
        self.corpora_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def collection_name_for(self, corpus_name: str) -> str:
        safe = corpus_name.strip().lower().replace(" ", "-")
        return f"{self.collection_prefix}{safe}"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
