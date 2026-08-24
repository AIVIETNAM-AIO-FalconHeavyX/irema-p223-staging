import uuid

from src.agents.state import AgentState


async def static_form_node(state: AgentState) -> dict:
    """Trigger Form tĩnh (Static Form) khi AI không giải quyết được hoặc người dùng yêu cầu hỗ trợ trực tiếp."""
    user_role = state.get("user_role", "sales")
    vehicle_model = state.get("vehicle_model", "unknown")
    error_code = state.get("error_code", "N/A")
    raw_query = state.get("raw_query") or state.get("query", "")

    form_id = f"FORM-{uuid.uuid4().hex[:6].upper()}"
    form_payload = {
        "form_id": form_id,
        "is_static_form_open": True,
        "target_department": "Bộ phận IT / Admin ĐLPP",
        "prefilled_data": {
            "user_role": user_role,
            "vehicle_model": vehicle_model.upper(),
            "error_code": error_code,
            "query_context": raw_query,
        },
        "status": "READY_TO_SUBMIT",
    }

    form_message = (
        f"📋 **Bật Form tĩnh Báo lỗi & Yêu cầu Hỗ trợ (Static Form Active)**\n\n"
        f"Hệ thống đã tự động mở Form tĩnh chuẩn hóa để gửi yêu cầu hỗ trợ nhanh tới IT/Admin:\n"
        f"- **Mã Form:** `{form_id}`\n"
        f"- **Vai trò:** {user_role.upper()}\n"
        f"- **Dòng xe / Mã lỗi:** {vehicle_model.upper()} / {error_code}\n"
        f'- **Ngữ cảnh yêu cầu:** *"{raw_query}"*\n\n'
        f'💡 *Thao tác:* Vui lòng kiểm tra thông tin pre-filled trên màn hình Form tĩnh và bấm **"Gửi Ticket"** (< 30 giây).'
    )

    return {
        "needs_escalation": True,
        "ticket_payload": form_payload,
        "context": form_message,
        "citations": [],
    }
