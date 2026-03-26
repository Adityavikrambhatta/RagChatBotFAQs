from __future__ import annotations

import re
from dataclasses import dataclass

from rapidfuzz import fuzz

from app.config import Settings
from app.embeddings import EmbeddingModel
from app.vector_store import ChromaVectorStore


@dataclass(slots=True)
class RankedHit:
    chunk_id: str
    text: str
    metadata: dict
    score: float


class HybridRetriever:
    def __init__(self, vector_store: ChromaVectorStore, embeddings: EmbeddingModel, settings: Settings) -> None:
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.settings = settings

    def search(self, question: str, *, top_k: int) -> list[RankedHit]:
        vector_hits = self.vector_store.query(
            embedding=self.embeddings.embed_query(question),
            top_k=max(top_k * self.settings.retrieval_query_multiplier, 12),
        )
        keyword_hits = self._keyword_hits(question)

        merged: dict[str, RankedHit] = {}
        for hit in vector_hits:
            merged[hit.chunk_id] = RankedHit(
                chunk_id=hit.chunk_id,
                text=hit.text,
                metadata=hit.metadata,
                score=max(hit.score, 0.0) * self.settings.retrieval_vector_weight,
            )

        for hit in keyword_hits:
            current = merged.get(hit.chunk_id)
            if current:
                current.score += hit.score * self.settings.retrieval_keyword_weight
            else:
                merged[hit.chunk_id] = hit

        ranked = sorted(merged.values(), key=lambda item: item.score, reverse=True)
        return ranked[:top_k]

    def _keyword_hits(self, question: str) -> list[RankedHit]:
        question_clean = question.strip().lower()
        maybe_code = self._extract_error_code(question_clean)
        ranked: list[RankedHit] = []
        for entry in self.vector_store.get_all():
            error_message = str(entry.metadata.get("error_message", "") or "")
            error_code = str(entry.metadata.get("error_code", "") or "")
            resolution = str(entry.metadata.get("resolution", "") or "")
            joined = " ".join([error_message, error_code, resolution, entry.text]).lower()

            score = fuzz.token_set_ratio(question_clean, joined) / 100.0
            if error_message:
                score = max(score, fuzz.partial_ratio(question_clean, error_message.lower()) / 100.0)
            if maybe_code and error_code and maybe_code in error_code.lower():
                score = max(score, 0.98)
            if score >= self.settings.retrieval_keyword_min_score:
                ranked.append(
                    RankedHit(
                        chunk_id=entry.chunk_id,
                        text=entry.text,
                        metadata=entry.metadata,
                        score=score * self.settings.retrieval_keyword_weight,
                    )
                )
        return sorted(ranked, key=lambda item: item.score, reverse=True)[:20]

    @staticmethod
    def _extract_error_code(question: str) -> str | None:
        match = re.search(r"\b[a-z]{1,6}[-_ ]?\d{2,6}\b", question, flags=re.IGNORECASE)
        return match.group(0).replace(" ", "").lower() if match else None
