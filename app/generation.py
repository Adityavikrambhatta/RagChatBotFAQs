from __future__ import annotations

from textwrap import shorten

import httpx

from app.config import Settings
from app.retrieval import RankedHit


def build_prompt(question: str, hits: list[RankedHit]) -> str:
    context_blocks: list[str] = []
    for index, hit in enumerate(hits, start=1):
        source = hit.metadata.get("source_file", "unknown")
        source_type = hit.metadata.get("source_type", "unknown")
        details: list[str] = [f"Source {index}: {source} ({source_type})"]
        if hit.metadata.get("page_number"):
            details.append(f"Page: {hit.metadata['page_number']}")
        if hit.metadata.get("sheet_name"):
            details.append(f"Sheet: {hit.metadata['sheet_name']}")
        if hit.metadata.get("row_number"):
            details.append(f"Row: {hit.metadata['row_number']}")
        details.append(hit.text)
        context_blocks.append("\n".join(str(item) for item in details))

    joined_context = "\n\n".join(context_blocks)
    return (
        "You are a support FAQ assistant. Answer only from the provided context. "
        "If the context is not sufficient, say that the available FAQ corpus does not contain enough evidence.\n\n"
        f"Question:\n{question}\n\n"
        f"Context:\n{joined_context}\n\n"
        "Return a concise answer with likely cause, recommended resolution, and mention the supporting sources."
    )


class AnswerGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def answer(self, question: str, hits: list[RankedHit]) -> str:
        if self.settings.ollama_chat_model:
            return self._answer_with_ollama(question, hits)
        return self._fallback_answer(question, hits)

    def _answer_with_ollama(self, question: str, hits: list[RankedHit]) -> str:
        prompt = build_prompt(question, hits)
        response = httpx.post(
            f"{self.settings.ollama_base_url.rstrip('/')}/api/generate",
            json={"model": self.settings.ollama_chat_model, "prompt": prompt, "stream": False},
            timeout=180,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("response", "").strip()

    def _fallback_answer(self, question: str, hits: list[RankedHit]) -> str:
        if not hits:
            return "I could not find enough evidence in the indexed FAQ corpus to answer that."

        best = hits[0]
        answer_lines = [
            f"Best match for your question: {shorten(best.text, width=320, placeholder='...')}",
        ]
        resolution = best.metadata.get("resolution")
        if resolution:
            answer_lines.append(f"Recommended resolution: {resolution}")
        source_bits = [best.metadata.get("source_file", "unknown source")]
        if best.metadata.get("page_number"):
            source_bits.append(f"page {best.metadata['page_number']}")
        if best.metadata.get("sheet_name"):
            source_bits.append(f"sheet {best.metadata['sheet_name']}")
        if best.metadata.get("row_number"):
            source_bits.append(f"row {best.metadata['row_number']}")
        answer_lines.append(f"Primary source: {', '.join(str(bit) for bit in source_bits)}.")
        if len(hits) > 1:
            answer_lines.append("Additional related evidence was also retrieved from the corpus.")
        return "\n".join(answer_lines)
