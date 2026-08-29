from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException


def test_memory_is_bounded_and_isolated_by_user() -> None:
    from src.services.conversation_memory import ConversationMemory

    memory = ConversationMemory(max_messages=4, max_characters=1000, ttl_seconds=3600)
    for index in range(6):
        memory.append("conversation", "user-a", "user", f"message-{index}")
    memory.append("conversation", "user-b", "user", "private-b")

    assert [message["content"] for message in memory.get("conversation", "user-a")] == [
        "message-2",
        "message-3",
        "message-4",
        "message-5",
    ]
    assert memory.get("conversation", "user-b") == [{"role": "user", "content": "private-b"}]


def test_memory_expires_old_conversations() -> None:
    from src.services.conversation_memory import ConversationMemory

    now = datetime.now(UTC)
    clock_value = [now]
    memory = ConversationMemory(ttl_seconds=60, clock=lambda: clock_value[0])
    memory.append("conversation", "user-a", "user", "hello")

    clock_value[0] = now + timedelta(seconds=61)

    assert memory.get("conversation", "user-a") == []


def test_memory_enforces_character_limit() -> None:
    from src.services.conversation_memory import ConversationMemory

    memory = ConversationMemory(max_messages=10, max_characters=10)
    memory.append("conversation", "user-a", "user", "123456")
    memory.append("conversation", "user-a", "assistant", "abcdef")

    assert memory.get("conversation", "user-a") == [{"role": "assistant", "content": "abcdef"}]


@pytest.mark.asyncio
async def test_chat_uses_authenticated_role_and_isolates_same_conversation_id(monkeypatch) -> None:
    from src.api import routes
    from src.db.models import UserRole
    from src.models.schemas import ChatRequest
    from src.services.conversation_memory import ConversationMemory

    memory = ConversationMemory()
    agent = SimpleNamespace(
        ainvoke=AsyncMock(
            side_effect=[
                {"response": "answer-a", "citations": []},
                {"response": "answer-b", "citations": []},
            ]
        )
    )
    log_interaction = Mock()
    monkeypatch.setattr(routes, "conversation_memory", memory)
    monkeypatch.setattr(routes, "agent", agent)
    monkeypatch.setattr(routes, "get_langfuse_handler", Mock(return_value=None))
    monkeypatch.setattr(routes, "log_chat_interaction", log_interaction)

    request = ChatRequest(message="Question", conversation_id="sharedconversation")
    user_a = SimpleNamespace(id="user-a", role=UserRole.sale)
    user_b = SimpleNamespace(id="user-b", role=UserRole.accountant)

    response_a = await routes.chat(request, current_user=user_a)
    response_b = await routes.chat(request, current_user=user_b)

    assert response_a.response == "answer-a"
    assert response_b.response == "answer-b"
    first_state = agent.ainvoke.call_args_list[0].args[0]
    second_state = agent.ainvoke.call_args_list[1].args[0]
    assert first_state["user_role"] == "sale"
    assert second_state["user_role"] == "accountant"
    assert first_state["conversation_history"] == []
    assert second_state["conversation_history"] == []
    assert log_interaction.call_args_list[0].kwargs["user_role"] == "sale"
    assert log_interaction.call_args_list[1].kwargs["user_role"] == "accountant"


@pytest.mark.asyncio
async def test_postgres_conversation_survives_requests_and_enforces_owner(monkeypatch) -> None:
    from src.api import routes
    from src.db import SessionLocal
    from src.db.models import UserRole
    from src.models.schemas import ChatRequest

    agent = SimpleNamespace(
        ainvoke=AsyncMock(
            side_effect=[
                {"response": "first answer", "citations": []},
                {"response": "second answer", "citations": []},
            ]
        )
    )
    monkeypatch.setattr(routes, "agent", agent)
    monkeypatch.setattr(routes, "get_langfuse_handler", Mock(return_value=None))
    monkeypatch.setattr(routes, "log_chat_interaction", Mock())
    monkeypatch.setattr(routes, "get_settings", lambda: SimpleNamespace(conversation_memory_backend="postgres"))

    db = SessionLocal()
    try:
        request_one = ChatRequest(message="first question", conversation_id="persistent-conversation")
        request_two = ChatRequest(message="what about that?", conversation_id="persistent-conversation")
        user_a = SimpleNamespace(id="persistent-user-a", role=UserRole.sale)
        user_b = SimpleNamespace(id="persistent-user-b", role=UserRole.sale)

        await routes.chat(request_one, current_user=user_a, db=db)
        response_two = await routes.chat(request_two, current_user=user_a, db=db)

        assert response_two.response == "second answer"
        second_state = agent.ainvoke.call_args_list[1].args[0]
        assert second_state["conversation_history"] == [
            {"role": "user", "content": "first question"},
            {"role": "assistant", "content": "first answer"},
        ]

        with pytest.raises(HTTPException) as error:
            await routes.chat(request_two, current_user=user_b, db=db)
        assert error.value.status_code == 404
    finally:
        db.close()


def test_postgres_append_turn_persists_user_before_assistant() -> None:
    from src.db import SessionLocal
    from src.db.models import ChatConversation, ChatMessage
    from src.services.conversation_store import ConversationStore

    db = SessionLocal()
    try:
        conversation = ConversationStore.get_or_create(db, "timestamp-order", "timestamp-user")
        assert conversation is not None
        ConversationStore.append_turn(db, conversation, "question", "answer")
        rows = (
            db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == "timestamp-order")
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        assert [row.content for row in rows] == ["question", "answer"]
    finally:
        db.close()
