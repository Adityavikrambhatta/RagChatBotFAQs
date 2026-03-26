from __future__ import annotations
from textwrap import shorten

import httpx

from app.config import Settings
from app.retrieval import RankedHit


def build_prompt(question: str, hits: list[RankedHit], *, prompt_mode: str) -> str:
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
    if prompt_mode == "strict":
        instructions = (
            "You are a support FAQ assistant. Answer only from the provided context. "
            "If the context is not sufficient, say the corpus does not contain enough evidence."
        )
    else:
        instructions = (
            "You are a support FAQ assistant. Use the retrieved context as your primary evidence. "
            "You may synthesize across sources and make small, clearly labeled inferences when the evidence strongly implies them, "
            "but do not invent unsupported facts. If evidence is mixed or incomplete, say what is certain and what is uncertain."
        )

    user_prompt = (
        f"Question:\n{question}\n\n"
        f"Context:\n{joined_context}\n\n"
        "Return markdown with these sections when applicable:\n"
        "- Answer\n"
        "- Likely cause\n"
        "- Recommended resolution\n"
        "- Evidence used"
    )
    return instructions, user_prompt


class AnswerGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def answer(self, question: str, hits: list[RankedHit]) -> str:
        provider = self.settings.llm_provider.strip().lower()
        if provider == "openai" and self.settings.llm_model and self.settings.llm_api_key:
            return self._answer_with_openai(question, hits)
        if provider == "ollama" and self.settings.ollama_chat_model:
            return self._answer_with_ollama(question, hits)
        return self._fallback_answer(question, hits)

    def _answer_with_ollama(self, question: str, hits: list[RankedHit]) -> str:
        instructions, user_prompt = build_prompt(question, hits, prompt_mode=self.settings.prompt_mode)
        response = httpx.post(
            f"{self.settings.ollama_base_url.rstrip('/')}/api/generate",
            json={
                "model": self.settings.ollama_chat_model,
                "system": instructions,
                "prompt": user_prompt,
                "stream": False,
                "options": {"temperature": self.settings.llm_temperature},
            },
            timeout=180,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("response", "").strip()

    def _answer_with_openai(self, question: str, hits: list[RankedHit]) -> str:
        instructions, user_prompt = build_prompt(question, hits, prompt_mode=self.settings.prompt_mode)
        response = httpx.post(
            f"{self.settings.llm_base_url.rstrip('/')}/responses",
            headers={
                "Authorization": f"Bearer {self.settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.settings.llm_model,
                "instructions": instructions,
                "input": user_prompt,
                "temperature": self.settings.llm_temperature,
                "truncation": "auto",
            },
            timeout=180,
        )
        response.raise_for_status()
        payload = response.json()
        output_text = payload.get("output_text")
        if output_text:
            return str(output_text).strip()
        return self._extract_openai_output(payload)

    def _extract_openai_output(self, payload: dict) -> str:
        chunks: list[str] = []
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    chunks.append(content["text"])
        return "\n".join(chunks).strip()

    def _fallback_answer(self, question: str, hits: list[RankedHit]) -> str:
        if not hits:
            return "I could not find enough evidence in the indexed FAQ corpus to answer that."

        best_score = max(hits[0].score, 0.0001)
        top_hits = [hit for hit in hits[:5] if hit.score >= best_score * 0.65][:3]
        if not top_hits:
            top_hits = hits[:1]
        best = top_hits[0]
        answer_lines = ["## Answer", shorten(best.text, width=420, placeholder="...")]

        likely_causes = [str(hit.metadata.get("error_message", "") or "").strip() for hit in top_hits if hit.metadata.get("error_message")]
        if likely_causes:
            answer_lines.extend(["", "## Likely cause", likely_causes[0]])

        resolutions = []
        for hit in top_hits:
            resolution = str(hit.metadata.get("resolution", "") or "").strip()
            if resolution and resolution not in resolutions:
                resolutions.append(resolution)
        if resolutions:
            answer_lines.extend(["", "## Recommended resolution"])
            for resolution in resolutions[:3]:
                answer_lines.append(f"- {resolution}")

        answer_lines.extend(["", "## Evidence used"])
        for hit in top_hits:
            source_bits = [str(hit.metadata.get("source_file", "unknown source"))]
            if hit.metadata.get("page_number"):
                source_bits.append(f"page {hit.metadata['page_number']}")
            if hit.metadata.get("sheet_name"):
                source_bits.append(f"sheet {hit.metadata['sheet_name']}")
            if hit.metadata.get("row_number"):
                source_bits.append(f"row {hit.metadata['row_number']}")
            answer_lines.append(f"- {', '.join(source_bits)}")
        return "\n".join(answer_lines)
