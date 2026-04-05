from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.schemas import ChatTurn, SessionSummary


def serialize_message(message: BaseMessage) -> dict[str, str]:
    role = "assistant" if isinstance(message, AIMessage) else "user"
    return {"role": role, "content": str(message.content)}


def deserialize_message(payload: dict[str, str]) -> BaseMessage:
    role = payload.get("role", "user")
    content = payload.get("content", "")
    if role == "assistant":
        return AIMessage(content=content)
    return HumanMessage(content=content)


class FileBackedChatHistory:
    def __init__(self, root_dir: Path, max_history_messages: int) -> None:
        self.root_dir = root_dir
        self.max_history_messages = max_history_messages
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def load_messages(self, session_id: str) -> list[BaseMessage]:
        path = self._path_for(session_id)
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [deserialize_message(item) for item in payload.get("messages", [])]

    def append_turn(self, *, session_id: str, corpus_name: str, user_message: str, assistant_message: str) -> list[BaseMessage]:
        messages = self.load_messages(session_id)
        messages.extend([HumanMessage(content=user_message), AIMessage(content=assistant_message)])
        trimmed = messages[-self.max_history_messages :]
        self._write_payload(session_id, corpus_name, trimmed)
        return trimmed

    def list_sessions(self) -> list[SessionSummary]:
        sessions: list[SessionSummary] = []
        for path in sorted(self.root_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            messages = payload.get("messages", [])
            preview = ""
            for item in reversed(messages):
                if item.get("role") == "assistant" and item.get("content"):
                    preview = item["content"]
                    break
            sessions.append(
                SessionSummary(
                    session_id=payload.get("session_id", path.stem),
                    corpus_name=payload.get("corpus_name", "unknown"),
                    message_count=len(messages),
                    updated_at=payload.get("updated_at", datetime.now(UTC).isoformat()),
                    preview=preview[:180],
                )
            )
        sessions.sort(key=lambda item: item.updated_at, reverse=True)
        return sessions

    def turns_for(self, session_id: str) -> list[ChatTurn]:
        return [ChatTurn(**serialize_message(message)) for message in self.load_messages(session_id)]

    def _write_payload(self, session_id: str, corpus_name: str, messages: list[BaseMessage]) -> None:
        payload = {
            "session_id": session_id,
            "corpus_name": corpus_name,
            "updated_at": datetime.now(UTC).isoformat(),
            "messages": [serialize_message(message) for message in messages],
        }
        self._path_for(session_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _path_for(self, session_id: str) -> Path:
        safe_session_id = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in session_id)
        return self.root_dir / f"{safe_session_id}.json"
