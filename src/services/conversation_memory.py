"""Bounded, expiring short-term conversation memory."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock


@dataclass
class _StoredMessage:
    role: str
    content: str
    created_at: datetime


class ConversationMemory:
    """Process-local memory for the disposable first deployment.

    Keys include both user identity and conversation ID to prevent cross-user
    access. PostgreSQL persistence can replace this implementation later without
    changing the API contract.
    """

    def __init__(
        self,
        *,
        max_messages: int = 8,
        max_characters: int = 8000,
        ttl_seconds: int = 3600,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.max_messages = max_messages
        self.max_characters = max_characters
        self.ttl_seconds = ttl_seconds
        self.clock = clock
        self._messages: dict[tuple[str, str], list[_StoredMessage]] = {}
        self._lock = Lock()

    def _key(self, conversation_id: str, user_id: str) -> tuple[str, str]:
        return user_id, conversation_id

    def _prune(self, key: tuple[str, str]) -> None:
        now = self.clock()
        messages = [
            message
            for message in self._messages.get(key, [])
            if (now - message.created_at).total_seconds() <= self.ttl_seconds
        ][-self.max_messages :]
        while messages and sum(len(message.content) for message in messages) > self.max_characters:
            messages.pop(0)
        if messages:
            self._messages[key] = messages
        else:
            self._messages.pop(key, None)

    def append(self, conversation_id: str, user_id: str, role: str, content: str) -> None:
        clean_content = content.strip()
        if not clean_content:
            return
        if role not in {"user", "assistant"}:
            raise ValueError("conversation role must be user or assistant")
        key = self._key(conversation_id, user_id)
        with self._lock:
            self._messages.setdefault(key, []).append(
                _StoredMessage(role=role, content=clean_content, created_at=self.clock())
            )
            self._prune(key)

    def get(self, conversation_id: str, user_id: str) -> list[dict[str, str]]:
        key = self._key(conversation_id, user_id)
        with self._lock:
            self._prune(key)
            return [{"role": message.role, "content": message.content} for message in self._messages.get(key, [])]

    def delete(self, conversation_id: str, user_id: str) -> None:
        with self._lock:
            self._messages.pop(self._key(conversation_id, user_id), None)


conversation_memory = ConversationMemory()
