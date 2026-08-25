from src.agents.state import AgentState

# Persona responses cho GENERAL_QA — không cần gọi RAG
_GENERAL_QA_PERSONAS: dict[str, str] = {
    "sales": (
        "Xin chào! Tôi là **VF AI Assistant** — Trợ lý AI chuyên môn dành riêng cho **Tư vấn Bán hàng VinFast**.\n\n"
        "Tôi có thể hỗ trợ bạn:\n"
        "- 📋 Tra cứu **chính sách bán hàng**, bảng giá xe máy điện\n"
        "- 🏆 Hướng dẫn **quy trình tư vấn 8 bước** chuẩn VinFast\n"
        "- 🎁 Thông tin **ưu đãi lệ phí trước bạ**, gói sạc, thuê pin\n"
        "- 📄 Hỗ trợ **hồ sơ, thủ tục** mua xe cho khách hàng\n\n"
        "Hãy đặt câu hỏi cụ thể để tôi tìm đúng tài liệu cho bạn! 💡"
    ),
    "accounting": (
        "Xin chào! Tôi là **VF AI Assistant** — Trợ lý AI chuyên môn dành riêng cho **Kế toán Đại lý VinFast**.\n\n"
        "Tôi có thể hỗ trợ bạn:\n"
        "- 🖥️ Hướng dẫn sử dụng **hệ thống DMS** (đăng nhập, xuất báo cáo)\n"
        "- 📦 Quy trình **đặt hàng tồn kho PO** và tạo yêu cầu mua sắm PR\n"
        "- 🧾 **Xuất hóa đơn VAT** cho xe máy điện\n"
        "- 📊 Tra cứu **chính sách chiết khấu**, hoa hồng đại lý\n\n"
        "Hãy đặt câu hỏi cụ thể để tôi tìm đúng tài liệu cho bạn! 💡"
    ),
    "technician": (
        "Xin chào! Tôi là **VF AI Assistant** — Trợ lý AI chuyên môn dành riêng cho **Kỹ thuật viên Xưởng Dịch vụ VinFast**.\n\n"
        "Tôi có thể hỗ trợ bạn:\n"
        "- 🔧 Quy trình **sửa chữa pin xe máy điện** (XDV)\n"
        "- 🛡️ **Kiểm tra 5 hạng mục** bảo dưỡng định kỳ\n"
        "- ⚡ Xử lý **lỗi kỹ thuật** — mã lỗi, triệu chứng, cách sửa\n"
        "- 📋 Chính sách **bảo hành và chăm sóc xe** miễn phí\n\n"
        "Hãy đặt câu hỏi cụ thể để tôi tìm đúng tài liệu cho bạn! 💡"
    ),
    "owner": (
        "Xin chào! Tôi là **VF AI Assistant** — Trợ lý AI Cố vấn dành riêng cho **Chủ Đại lý / Quản lý VinFast**.\n\n"
        "Tôi có thể hỗ trợ bạn:\n"
        "- 📊 Tổng quan **quy trình hoạt động** các phòng ban (Kế toán, Sales, KTV)\n"
        "- 🏪 Tiêu chuẩn **vận hành đại lý** VinFast\n"
        "- 📦 Quy trình **đặt hàng PO, quản trị kho** tổng\n"
        "- 📋 Tra cứu toàn bộ **chính sách, tài liệu** xuyên phòng ban\n\n"
        "Hãy đặt câu hỏi cụ thể để tôi tìm đúng tài liệu cho bạn! 💡"
    ),
}

_DEFAULT_PERSONA = (
    "Xin chào! Tôi là **VF AI Assistant** — Trợ lý AI tra cứu tài liệu nội bộ VinFast.\n\n"
    "Tôi có thể hỗ trợ bạn tra cứu **chính sách, quy trình nghiệp vụ** và **hướng dẫn kỹ thuật** "
    "dành riêng cho vai trò của bạn.\n\n"
    "Hãy đặt câu hỏi cụ thể để tôi tìm đúng tài liệu cho bạn! 💡"
)


def _latest_message(history: object, role: str) -> str | None:
    if not isinstance(history, list):
        return None
    for message in reversed(history):
        if isinstance(message, dict) and message.get("role") == role:
            content = str(message.get("content") or "").strip()
            if content:
                return content
    return None


async def response_generator_node(state: AgentState) -> dict:
    """Node tổng hợp phản hồi Markdown chuẩn hóa kèm trích dẫn nguồn.

    Xử lý đặc biệt:
    - GENERAL_QA: trả lời persona trực tiếp không cần context từ RAG.
    """
    intent = state.get("intent", "RAG_SEARCH")
    context = state.get("context", "")
    citations = state.get("citations", [])
    needs_escalation = state.get("needs_escalation", False)
    error = state.get("error")
    user_role = state.get("user_role", "sales").lower()
    conversation_history = state.get("conversation_history", [])

    if error:
        return {"response": f"❌ Đã xảy ra lỗi trong quá trình xử lý: {error}"}

    if intent == "CONVERSATION_META":
        meta_type = state.get("conversation_meta_type")
        if meta_type == "last_user_question":
            previous = _latest_message(conversation_history, "user")
            response = f"Câu hỏi gần nhất của bạn là: **{previous}**" if previous else "Mình chưa có câu hỏi trước đó trong cuộc trò chuyện này."
        elif meta_type in {"last_assistant_answer", "repeat_last_answer"}:
            previous = _latest_message(conversation_history, "assistant")
            response = previous or "Mình chưa có câu trả lời trước đó trong cuộc trò chuyện này."
        elif meta_type == "start_new":
            response = "Đã sẵn sàng bắt đầu một cuộc trò chuyện mới."
        else:
            response = "Mình chưa hiểu yêu cầu liên quan đến cuộc trò chuyện. Bạn có thể nói rõ hơn không?"
        return {
            "response": response,
            "citations": [],
            "needs_escalation": False,
            "retrieved_docs_detail": [],
            "ticket_payload": None,
        }

    # --- GENERAL_QA: bypass RAG, trả lời persona cố định ---
    if intent == "GENERAL_QA":
        # Normalize role alias
        role_norm = {
            "accountant": "accounting",
            "ketoan": "accounting",
            "sale": "sales",
            "ktv": "technician",
            "manager": "owner",
            "admin": "owner",
        }
        normalized_role = role_norm.get(user_role, user_role)
        persona_response = _GENERAL_QA_PERSONAS.get(normalized_role, _DEFAULT_PERSONA)
        return {
            "response": persona_response,
            "citations": [],
            "needs_escalation": False,
            "retrieved_docs_detail": [],
            "ticket_payload": None,
        }

    response_text = context

    no_info_phrases = [
        "không tìm thấy thông tin phù hợp",
        "không tìm thấy tài liệu liên quan",
        "không có thông tin",
    ]
    if any(phrase in response_text.lower() for phrase in no_info_phrases):
        citations = []

    # Đề xuất hành động tiếp theo
    if intent == "WORKFLOW":
        response_text += "\n\n💡 Gợi ý: Bạn có muốn hỏi chi tiết hơn về từng bước trong quy trình trên không?"
    elif intent == "TROUBLESHOOTING":
        response_text += (
            "\n\n💡 Gợi ý: Nếu sau khi xử lý theo các bước trên vẫn báo lỗi, hãy gửi yêu cầu gặp IT Support."
        )

    return {
        "response": response_text,
        "citations": citations,
        "needs_escalation": needs_escalation,
        "retrieved_docs_detail": state.get("retrieved_docs_detail", []),
        "ticket_payload": state.get("ticket_payload"),
    }
