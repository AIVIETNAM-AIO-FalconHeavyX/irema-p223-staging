"""Vietnamese-first deterministic user-query preprocessing."""

from __future__ import annotations

import re
import unicodedata

from src.agents.state import AgentState

_ABBREVIATIONS = {
    "dlpp": "đại lý phân phối",
    "vat": "hóa đơn giá trị gia tăng",
    "bms": "hệ thống quản lý pin",
}


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return (
        "".join(character for character in decomposed if unicodedata.category(character) != "Mn")
        .replace("đ", "d")
        .replace("Đ", "D")
    )


def _expand_abbreviations(query: str) -> str:
    rewritten = query
    for abbreviation, expansion in _ABBREVIATIONS.items():
        pattern = re.compile(rf"(?<!\w){re.escape(abbreviation)}(?!\w)", flags=re.IGNORECASE)
        rewritten = pattern.sub(lambda match: f"{match.group(0)} ({expansion})", rewritten)
    return rewritten


def _is_ambiguous_followup(query: str) -> bool:
    normalized = _strip_accents(query).casefold()
    return any(
        phrase in normalized
        for phrase in (
            "mau do",
            "cai do",
            "viec do",
            "thi sao",
            "con no",
            "what about that",
            "what about it",
            "and for",
            "compare it",
        )
    )


def _conversation_meta_type(query: str) -> str | None:
    normalized = _strip_accents(query).casefold().strip(" ?!.,")
    if any(
        phrase in normalized
        for phrase in (
            "toi moi hoi gi",
            "toi vua hoi gi",
            "what did i just ask",
            "what was my last question",
            "cau hoi vua roi",
        )
    ):
        return "last_user_question"
    if any(
        phrase in normalized
        for phrase in (
            "ban vua noi gi",
            "what did you say",
            "what was your previous answer",
            "repeat your last answer",
        )
    ):
        return "last_assistant_answer"
    if any(
        phrase in normalized
        for phrase in (
            "giai thich lai",
            "noi lai",
            "explain that again",
            "explain it again",
            "can you repeat",
        )
    ):
        return "repeat_last_answer"
    if normalized in {"start over", "new chat", "bat dau lai", "lam lai tu dau"}:
        return "start_new"
    return None


def _latest_user_topic(history: object) -> str | None:
    if not isinstance(history, list):
        return None
    # Two recent turns are sufficient to resolve a follow-up while preventing
    # old topics from drifting into current retrieval.
    for message in reversed(history[-2:]):
        if isinstance(message, dict) and message.get("role") == "user":
            content = unicodedata.normalize("NFC", str(message.get("content") or "")).strip()
            if content:
                return content
    return None


async def query_rewriter_node(state: AgentState) -> dict:
    """Normalize and expand a query while keeping authorization out of its text."""
    raw_query = unicodedata.normalize("NFC", str(state.get("raw_query") or state.get("query") or "")).strip()
    if not raw_query:
        raise ValueError("query must not be empty")

    meta_type = _conversation_meta_type(raw_query)
    if meta_type:
        return {
            "raw_query": raw_query,
            "query": raw_query,
            "rewritten_query": raw_query,
            "retrieval_queries": [],
            "conversation_meta_type": meta_type,
        }

    standalone_query = raw_query
    if _is_ambiguous_followup(raw_query):
        topic = _latest_user_topic(state.get("conversation_history"))
        if topic:
            standalone_query = f"{topic} — {raw_query}"

    rewritten = _expand_abbreviations(standalone_query)
    accent_insensitive = _strip_accents(rewritten)
    retrieval_queries = list(dict.fromkeys([rewritten, accent_insensitive]))
    return {
        "raw_query": raw_query,
        "query": raw_query,
        "rewritten_query": rewritten,
        "retrieval_queries": retrieval_queries,
        "conversation_meta_type": None,
    }
