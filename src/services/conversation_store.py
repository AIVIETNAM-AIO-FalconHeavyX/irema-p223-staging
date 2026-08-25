"""PostgreSQL-backed conversation storage with bounded prompt history."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.db.models import ChatConversation, ChatMessage, ChatMessageRole


class ConversationStore:
    """Persist user-owned chat turns while keeping prompts small and predictable."""

    max_messages = 8
    max_characters = 8000
    retention_days = 90

    @classmethod
    def get_or_create(cls, db: Session, conversation_id: str, user_id: str) -> ChatConversation | None:
        now = datetime.now(UTC)
        assistant_created_at = now + timedelta(microseconds=1)
        conversation = db.get(ChatConversation, conversation_id)
        if conversation is not None and conversation.user_id != user_id:
            # Do not reveal that an ID belongs to another user.
            return None

        expires_at = conversation.expires_at if conversation is not None else None
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if conversation is not None and expires_at <= now:
            db.delete(conversation)
            db.flush()
            conversation = None

        if conversation is None:
            conversation = ChatConversation(
                id=conversation_id,
                user_id=user_id,
                created_at=now,
                updated_at=now,
                expires_at=now + timedelta(days=cls.retention_days),
            )
            db.add(conversation)
            db.flush()
        return conversation

    @classmethod
    def load_history(cls, db: Session, conversation_id: str, user_id: str) -> list[dict[str, str]]:
        conversation = db.get(ChatConversation, conversation_id)
        if conversation is None or conversation.user_id != user_id:
            return []

        rows = list(
            db.scalars(
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conversation_id)
                .order_by(ChatMessage.created_at.desc())
                .limit(cls.max_messages)
            )
        )
        history_reversed: list[dict[str, str]] = []
        total_characters = 0
        for row in reversed(rows):
            if total_characters + len(row.content) > cls.max_characters:
                break
            history_reversed.append({"role": row.role.value, "content": row.content})
            total_characters += len(row.content)
        history_reversed.reverse()
        return history_reversed

    @classmethod
    def load_display_history(cls, db: Session, conversation_id: str, user_id: str) -> dict | None:
        conversation = db.get(ChatConversation, conversation_id)
        if conversation is None or conversation.user_id != user_id:
            return None

        rows = list(
            db.scalars(
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conversation_id)
                .order_by(ChatMessage.created_at.desc())
                .limit(cls.max_messages)
            )
        )
        selected_rows: list[ChatMessage] = []
        total_characters = 0
        for row in rows:
            if len(selected_rows) >= cls.max_messages or total_characters + len(row.content) > cls.max_characters:
                break
            selected_rows.append(row)
            total_characters += len(row.content)
        selected_rows.reverse()
        return {
            "conversation_id": conversation.id,
            "messages": [
                {
                    "id": row.id,
                    "role": row.role.value,
                    "content": row.content,
                    "metadata": row.message_metadata or {},
                    "timestamp": row.created_at.isoformat(),
                }
                for row in selected_rows
            ],
        }

    @classmethod
    def append_turn(
        cls,
        db: Session,
        conversation: ChatConversation,
        user_message: str,
        assistant_message: str,
        assistant_metadata: dict | None = None,
    ) -> None:
        now = datetime.now(UTC)
        db.add(
            ChatMessage(
                conversation_id=conversation.id,
                role=ChatMessageRole.user,
                content=user_message.strip(),
                created_at=now,
            )
        )
        db.add(
            ChatMessage(
                conversation_id=conversation.id,
                role=ChatMessageRole.assistant,
                content=assistant_message.strip(),
                message_metadata=assistant_metadata or {},
                created_at=assistant_created_at,
            )
        )
        conversation.updated_at = now
        conversation.expires_at = now + timedelta(days=cls.retention_days)
        db.add(conversation)
        db.commit()

    @staticmethod
    def cleanup_expired(db: Session) -> int:
        result = db.execute(delete(ChatConversation).where(ChatConversation.expires_at < datetime.now(UTC)))
        db.commit()
        return int(result.rowcount or 0)
