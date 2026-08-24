import time

from src.agents.state import AgentState


async def controller_node(state: AgentState) -> dict:
    """Smart Router (Lightweight Controller): Kết hợp Query Rewriting & Fast Intent Classifier (<100ms).

    Phân loại intent:
    - GENERAL_QA: câu hỏi chung (chào hỏi, hỏi khả năng) → bypass RAG, trả lời persona trực tiếp.
    - TROUBLESHOOTING: báo lỗi, sự cố thiết bị.
    - WORKFLOW: hỏi về quy trình, onboarding flow.
    - CREATE_TICKET: chuyển tiếp IT/Manager.
    - RAG_SEARCH: tra cứu tài liệu cụ thể (default).
    """
    start_time = time.time()
    raw_query_text = state.get("raw_query") or state.get("query") or ""
    raw_query = raw_query_text.lower()

    # Query preprocessing is owned by query_rewriter_node. The controller only
    # classifies intent and must never mix role/authorization into query text.
    rewritten_query = state.get("rewritten_query") or raw_query_text

    # 2. Fast Intent & Skill Classifier (Heuristic + Lightweight Rules)
    intent = "RAG_SEARCH"
    confidence = 0.90

    rag_keywords = [
        "chính sách",
        "chiết khấu",
        "hoa hồng",
        "bảo hành",
        "xuất hóa đơn",
        "hóa đơn",
        "khuyến mãi",
        "tài liệu",
        "giá",
        "target",
    ]
    has_rag_keyword = any(k in raw_query for k in rag_keywords)

    # --- GENERAL_QA: Câu hỏi chung — KHÔNG cần gọi RAG ---
    general_qa_keywords = [
        "chào",
        "hello",
        "hi ",
        "xin chào",
        "giúp gì",
        "bạn là ai",
        "bạn có thể",
        "bạn hỗ trợ",
        "hỗ trợ gì",
        "làm được gì",
        "khả năng",
        "tính năng",
        "bạn làm gì",
        "ai đây",
        "trợ lý",
        "assistant",
        "bot là",
        "mày là",
        "mình hỏi",
        "cảm ơn",
        "cám ơn",
        "thank",
        "thanks",
        "tốt lắm",
        "tuyệt",
        "hay quá",
        "giỏi",
    ]
    is_general_qa = any(k in raw_query for k in general_qa_keywords)

    if any(
        k in raw_query
        for k in [
            "ticket",
            "it support",
            "gặp quản lý",
            "chuyển tiếp",
            "khiếu nại",
            "gặp người",
            "báo lỗi tĩnh",
            "static form",
        ]
    ):
        intent = "CREATE_TICKET"
        confidence = 0.98
    elif (
        any(k in raw_query for k in ["lỗi", "báo lỗi", "hỏng", "sự cố", "không chạy", "mặt đồng hồ", "cháy", "tắt máy"])
        and not has_rag_keyword
    ):
        intent = "TROUBLESHOOTING"
        confidence = 0.95
    elif any(
        k in raw_query
        for k in [
            "onboarding",
            "lộ trình",
            "sơ đồ",
            "hướng dẫn thao tác",
            "quy trình bán hàng",
            "quy trình kế toán",
            "quy trình kỹ thuật",
            "quy trình onboarding",
        ]
    ) or ("quy trình" in raw_query and not has_rag_keyword):
        intent = "WORKFLOW"
        confidence = 0.92
    elif is_general_qa and not has_rag_keyword:
        # GENERAL_QA: bypass RAG — trả lời persona trực tiếp
        intent = "GENERAL_QA"
        confidence = 0.99
    else:
        intent = "RAG_SEARCH"
        confidence = 0.88

    elapsed_ms = (time.time() - start_time) * 1000

    return {
        "intent": intent,
        "intent_confidence": confidence,
        "rewritten_query": rewritten_query,
        "analysis": f"Smart Router (Fast Classifier {elapsed_ms:.1f}ms): Intent = {intent} (Confidence: {confidence * 100:.0f}%)",
    }
