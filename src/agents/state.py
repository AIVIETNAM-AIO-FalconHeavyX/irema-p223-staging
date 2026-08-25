from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    """State schema cho LangGraph agent.

    Mỗi node đọc và ghi vào state này.
    total=False cho phép tất cả fields là optional.
    """

    query: str
    raw_query: str
    user_role: str
    intent: str
    intent_confidence: float
    rewritten_query: str
    retrieval_queries: list[str]
    conversation_history: list[dict[str, str]]
    conversation_meta_type: str
    context: str
    retrieved_docs: list
    # Rich metadata cho từng chunk đã rerank — dùng để render source badges ở frontend.
    # Mỗi phần tử là dict: {doc_name, section, rerank_score, rrf_score, content_preview}
    retrieved_docs_detail: list[dict]
    citations: list
    rag_confidence: float
    needs_escalation: bool
    ticket_payload: dict
    analysis: str
    response: str
    metadata: dict
