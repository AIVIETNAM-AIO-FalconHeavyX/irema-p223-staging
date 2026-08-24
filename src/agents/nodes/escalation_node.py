import uuid

from src.agents.state import AgentState


async def escalation_node(state: AgentState) -> dict:
    """Tự động đóng gói Ticket Hỗ trợ gửi thẳng tới IT hoặc Quản lý ĐLPP."""
    user_role = state.get("user_role", "sales")
    raw_query = state.get("raw_query") or state.get("query", "")

    target_department = "Bộ phận IT Support" if "it" in raw_query.lower() else "Quản lý Đại lý (Manager)"

    ticket_id = f"TICK-{uuid.uuid4().hex[:6].upper()}"
    ticket_payload = {
        "ticket_id": ticket_id,
        "target_department": target_department,
        "user_role": user_role,
        "query_summary": raw_query,
        "status": "CREATED",
        "priority": "HIGH" if "gấp" in raw_query.lower() or "it" in raw_query.lower() else "MEDIUM",
    }

    escalation_message = (
        f"⚠️ **Thông báo Chuyển tiếp Hỗ trợ (Escalation Active)**\n\n"
        f"AI không tìm thấy tài liệu phù hợp 100% trong dữ liệu nội bộ hoặc yêu cầu vượt quá thẩm quyền tự động.\n\n"
        f"**Đã khởi tạo Ticket hỗ trợ thành công:**\n"
        f"- **Mã Ticket:** `{ticket_id}`\n"
        f"- **Đơn vị tiếp nhận:** {target_department}\n"
        f"- **Vai trò gửi:** {user_role.upper()}\n"
        f'- **Nội dung yêu cầu:** *"{raw_query}"*\n\n'
        f"IT/Quản lý sẽ phản hồi trực tiếp qua hệ thống DMS trong vòng 15-30 phút."
    )

    return {
        "needs_escalation": True,
        "ticket_payload": ticket_payload,
        "context": escalation_message,
        "citations": [],
    }
