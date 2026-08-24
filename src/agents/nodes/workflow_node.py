from src.agents.state import AgentState

WORKFLOW_DATA = {
    "sales": {
        "title": "Lộ trình & Quy trình Onboarding dành cho Nhân viên Bán hàng (Sales)",
        "steps": [
            "Bước 1: Tìm hiểu thông số kỹ thuật & bảng giá các dòng xe (Klara S, Feliz S, Vento S, Evo200).",
            "Bước 2: Hướng dẫn tư vấn gói Thuê pin vs Mua đứt pin LFP cho khách hàng.",
            "Bước 3: Lập đơn hàng bán lẻ trên phần mềm DMS Đại lý.",
            "Bước 4: Bàn giao xe, hướng dẫn khách kích hoạt App kết nối xe thông minh và ký biên bản giao nhận.",
        ],
        "document_ref": "Quy trình Bán hàng & Onboarding Sales v1.4.pdf",
    },
    "accounting": {
        "title": "Lộ trình & Quy trình Onboarding dành cho Kế toán Đại lý",
        "steps": [
            "Bước 1: Tra cứu đơn hàng đã chốt từ bộ phận Sales trên hệ thống DMS.",
            "Bước 2: Đối soát thanh toán tiền mặt/chuyển khoản hoặc chứng từ duyệt vay trả góp ngân hàng.",
            "Bước 3: Kiểm tra số khung VIN và số Seri Pin trùng khớp với phiếu xuất kho.",
            "Bước 4: Xuất hóa đơn VAT điện tử và lưu trữ chứng từ đại lý.",
        ],
        "document_ref": "Quy chuẩn Nghiệp vụ Kế toán ĐLPP v2.0.pdf",
    },
    "technician": {
        "title": "Lộ trình & Quy trình Onboarding dành cho Kỹ thuật viên Dịch vụ",
        "steps": [
            "Bước 1: Quy trình PDI (Pre-Delivery Inspection) kiểm tra tổng thể xe trước khi bàn giao.",
            "Bước 2: Sử dụng máy chẩn đoán đọc mã lỗi ECU và BMS của xe.",
            "Bước 3: Quy trình kích hoạt, sạc xả và bảo dưỡng định kỳ hệ thống Pin LFP.",
            "Bước 4: Tiếp nhận bảo hành, lập phiếu sửa chữa và yêu cầu vật tư phụ tùng thay thế.",
        ],
        "document_ref": "Sổ tay Kỹ thuật & Bảo hành Xưởng Dịch vụ v3.0.pdf",
    },
    "manager": {
        "title": "Lộ trình Onboarding & Quản lý Vận hành Đại lý",
        "steps": [
            "Bước 1: Phê duyệt hạn mức tín dụng kho xe và theo dõi chỉ số KPI đại lý.",
            "Bước 2: Quản lý phân quyền tài khoản DMS cho nhân viên mới.",
            "Bước 3: Theo dõi báo cáo bán hàng, tồn kho pin và tỷ lệ giải quyết ticket kỹ thuật.",
        ],
        "document_ref": "Cẩm nang Quản lý Đại lý Phân phối v1.0.pdf",
    },
}


async def workflow_node(state: AgentState) -> dict:
    """Tra cứu Sơ đồ Workflow và Lộ trình Onboarding theo từng Vai trò."""
    user_role = (state.get("user_role") or "sales").lower()
    workflow_info = WORKFLOW_DATA.get(user_role, WORKFLOW_DATA["sales"])

    steps_text = "\n".join(workflow_info["steps"])
    context_text = f"### {workflow_info['title']}\n\n{steps_text}"

    return {
        "context": context_text,
        "citations": [workflow_info["document_ref"]],
        "rag_confidence": 0.95,
        "onboarding_step": "Onboarding Roadmap Active",
    }
