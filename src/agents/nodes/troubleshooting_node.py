from src.agents.state import AgentState

ERROR_DATABASE = {
    "P01": {
        "title": "Lỗi P01: Quá nhiệt hệ thống Pin LFP (BMS Overheat Warning)",
        "symptoms": "Màn hình xe chớp biểu tượng nhiệt độ màu đỏ, xe bị giới hạn tốc độ dưới 15km/h.",
        "steps": [
            "1. Tắt khóa điện xe và đưa xe vào khu vực thoáng mát, tránh ánh nắng trực tiếp.",
            "2. Chờ 15-20 phút cho khối Pin hạ nhiệt dưới 45°C.",
            "3. Sử dụng phần mềm chẩn đoán kết nối cổng OBD2 đọc thông số nhiệt độ Cell Pin.",
            "4. Nếu lỗi vẫn xuất hiện sau khi nguội, tiến hành tháo giắc cắm BMS và kiểm tra cảm biến nhiệt độ.",
        ],
        "safety_warning": "⚠️ CAUTION: KHÔNG tiến hành sạc pin ngay khi vừa báo lỗi P01. Rủi ro ngắt aptomat hoặc hỏng cell pin.",
        "ref": "Tài liệu Kỹ thuật Chẩn đoán Lỗi Hệ thống Điện - Trang 42",
    },
    "E03": {
        "title": "Lỗi E03: Mất kết nối tay ga hoặc bộ điều khiển ECU (Throttle Communication Error)",
        "symptoms": "Vặn tay ga xe không nhích, màn hình báo lỗi E03 kèm tiếng bíp ngắt quãng.",
        "steps": [
            "1. Kiểm tra công tắc ngắt điện tay phanh (Brake Switch) xem có bị kẹt không.",
            "2. Kiểm tra dây tín hiệu tay ga nối về ECU dưới yên xe.",
            "3. Đo điện áp nguồn cấp 5V cho cảm biến tay ga.",
            "4. Thay thế thử cụm tay ga mẫu nếu nguồn 5V vẫn bình thường.",
        ],
        "safety_warning": "⚠️ CAUTION: Đảm bảo dựng chân chống giữa an toàn trước khi thử lại tay ga.",
        "ref": "Hướng dẫn Xử lý Sự cố Điện & ECU Xe máy Điện - Trang 18",
    },
}


async def troubleshooting_node(state: AgentState) -> dict:
    """Tra cứu Bảng mã lỗi Xưởng dịch vụ & Quy trình chẩn đoán sự cố."""
    raw_query = (state.get("raw_query") or state.get("query") or "").upper()
    code = "E03" if "E03" in raw_query else "P01"
    error_info = ERROR_DATABASE.get(code, ERROR_DATABASE["P01"])

    steps_formatted = "\n".join(error_info["steps"])
    diagnostic_text = (
        f"### {error_info['title']}\n\n"
        f"**Dấu hiệu nhận biết:** {error_info['symptoms']}\n\n"
        f"**Các bước xử lý nhanh tại Xưởng ĐLPP:**\n{steps_formatted}\n\n"
        f"{error_info['safety_warning']}"
    )

    return {
        "context": diagnostic_text,
        "citations": [error_info["ref"]],
        "rag_confidence": 0.98,
        "needs_escalation": False,
    }
