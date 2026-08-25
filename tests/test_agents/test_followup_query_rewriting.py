from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_followup_query_uses_recent_user_topic() -> None:
    from src.agents.nodes.query_rewriter import query_rewriter_node

    result = await query_rewriter_node(
        {
            "raw_query": "Còn mẫu đó thì sao?",
            "conversation_history": [
                {"role": "user", "content": "Giá và chính sách pin của Evo200 là gì?"},
                {"role": "assistant", "content": "Evo200 có các chính sách sau..."},
            ],
        }
    )

    assert result["rewritten_query"] == "Giá và chính sách pin của Evo200 là gì? — Còn mẫu đó thì sao?"


@pytest.mark.asyncio
async def test_self_contained_query_is_not_changed_by_history() -> None:
    from src.agents.nodes.query_rewriter import query_rewriter_node

    result = await query_rewriter_node(
        {
            "raw_query": "Thời gian bảo hành pin LFP là bao lâu?",
            "conversation_history": [{"role": "user", "content": "Giá Evo200 là bao nhiêu?"}],
        }
    )

    assert result["rewritten_query"] == "Thời gian bảo hành pin LFP là bao lâu?"


@pytest.mark.asyncio
async def test_followup_rewriter_uses_only_bounded_recent_history() -> None:
    from src.agents.nodes.query_rewriter import query_rewriter_node

    result = await query_rewriter_node(
        {
            "raw_query": "Còn mẫu đó?",
            "conversation_history": [
                {"role": "user", "content": "OLD SECRET TOPIC"},
                {"role": "assistant", "content": "old answer"},
                {"role": "user", "content": "Giá Feliz S là gì?"},
                {"role": "assistant", "content": "recent answer"},
            ],
        }
    )

    assert "Feliz S" in result["rewritten_query"]
    assert "OLD SECRET TOPIC" not in result["rewritten_query"]


@pytest.mark.asyncio
async def test_conversation_meta_question_returns_last_user_question_intent() -> None:
    from src.agents.nodes.controller import controller_node
    from src.agents.nodes.query_rewriter import query_rewriter_node

    rewritten = await query_rewriter_node({"raw_query": "tôi mới hỏi gì?"})
    classified = await controller_node(rewritten)

    assert rewritten["conversation_meta_type"] == "last_user_question"
    assert classified["intent"] == "CONVERSATION_META"


@pytest.mark.asyncio
async def test_conversation_meta_answer_uses_previous_assistant_message() -> None:
    from src.agents.nodes.response_generator import response_generator_node

    result = await response_generator_node(
        {
            "intent": "CONVERSATION_META",
            "conversation_meta_type": "repeat_last_answer",
            "conversation_history": [{"role": "assistant", "content": "Đây là câu trả lời trước đó."}],
        }
    )

    assert result["response"] == "Đây là câu trả lời trước đó."
