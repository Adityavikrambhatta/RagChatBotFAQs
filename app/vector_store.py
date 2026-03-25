from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings


@dataclass(slots=True)
class SearchResult:
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    score: float


class ChromaVectorStore:
    def __init__(self, *, persist_directory: str, collection_name: str) -> None:
        self.client = chromadb.PersistentClient(path=persist_directory, settings=ChromaSettings(anonymized_telemetry=False))
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})

    def reset(self) -> None:
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(name=self.collection_name, metadata={"hnsw:space": "cosine"})

    def add_chunks(self, chunks: list[dict[str, Any]], embeddings: list[list[float]]) -> None:
        ids = [chunk["id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)

    def count(self) -> int:
        return int(self.collection.count())

    def query(self, *, embedding: list[float], top_k: int) -> list[SearchResult]:
        n_results = min(top_k, self.count())
        if n_results == 0:
            return []
        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]

        hits: list[SearchResult] = []
        for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
            score = 1.0 - float(distance)
            hits.append(SearchResult(chunk_id=chunk_id, text=text, metadata=metadata or {}, score=score))
        return hits

    def get_all(self) -> list[SearchResult]:
        result = self.collection.get(include=["documents", "metadatas"])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])
        ids = result.get("ids", [])
        hits: list[SearchResult] = []
        for chunk_id, text, metadata in zip(ids, documents, metadatas):
            hits.append(SearchResult(chunk_id=chunk_id, text=text, metadata=metadata or {}, score=0.0))
        return hits
