---
document_id: GATE001
title: gate1 SDD VF Onboarding Copilot
source_file: gate1_SDD_VF_Onboarding_Copilot.pdf
source_path: gate1_SDD_VF_Onboarding_Copilot.pdf/gate1_SDD_VF_Onboarding_Copilot.pdf
document_type: pdf
role: general
category: gate1_SDD_VF_Onboarding_Copilot.pdf
access_scope:
- accounting
- sales
- technician
language: vi
version: '1.0'
pages: 5
pii_processed: true
pii_removed: true
processed_at: '2026-08-19'
---

# gate1 SDD VF Onboarding Copilot

## Page 1

SOFTWARE DESIGN DOCUMENT (SDD)
Hệ Thống VF-Onboarding Copilot Engine
Mã Tài Liệu: SDD-VF-ONBOARDING-2026
Phiên Bản: 2.0 (Engineering Spec)
Tác Giả: Lead System Architect / AI Engineer
Ngày Phát Hành: 07/08/2026
Dự Án: VF-Onboarding Platform (Trợ lý AI Hỗ trợ Đại lý Phân phối & KTV )
1. Tổng Quan Hệ Thống (System Overview)
2. Module M0: Input Processing Engine (Module Xử Lý Đầu Vào Đa Định Dạng)
Module M0 đảm nhận vai trò tiếp nhận, bóc tách, làm sạch và chuẩn hóa mọi loại dữ liệu đầu vào trong hệ thống (cả chu
trình Ingestion hàng loạt và câu hỏi động của người dùng).
Trang 1 / 5

## Page 2

1. Audio Stream ➔ Whisper STT.
2. Frame Stream ➔ Keyframe (Scene
Change) ➔ OCR đọc máy chẩn đoán /
HUD.
Temporal Alignment JSON
(Speech + Visual Tokens)
1.
Trang 2 / 5

## Page 3

EV Term Dictionary Mapping: Chuyển đổi từ viết tắt/từ lóng xưởng dịch vụ sang chuẩn kỹ thuật (VD: "vf8" ➔ VF8, "pin
cao áp" ➔ High_Voltage_Battery, "bộ sạc" ➔ OBC_Charger).
Anonymization & PII Masking: Ẩn số điện thoại, biển số xe và mã VIN 17 ký tự (VD: [MASKED_VIN]).
3. Module M2: 4-Layer Lightweight Router (<100ms)
Router đóng vai trò bộ lọc tốc độ cao giúp phân loại Intent mà không cần tốn chi phí gọi LLM cho các câu hỏi tra cứu định
hình sẵn.
4. Module M3: LangGraph StateGraph Architecture
LangGraph điều phối toàn bộ các bước suy luận và truy xuất thông qua StateGraph tập trung.
# Định nghĩa State trong LangGraph (Python Engine)
from typing import TypedDict, List, Optional, Dict, Any
class AgentState(TypedDict):
    raw_query: str
    normalized_query: str
    user_role: str # "technician", "sales_agent", "service_manager"
    intent: str # "POLICY_SEARCH", "ERROR_LOOKUP", "TICKET_TRIGGER"
    confidence_score: float
    retrieved_docs: List[Dict[str, Any]]
    dtc_details: Optional[Dict[str, Any]]
    final_response: str
    citations: List[Dict[str, Any]]
    need_caution_alert: bool
2.
3.
Lớp
Router
Thuật Toán / Mô Hình
Độ Trễ
(Latency)
Nhiệm Vụ Chính
Layer 1
Query Rewriter (Regex +
Dict)
~2 ms
Sửa lỗi chính tả tiếng Việt, chuẩn hóa ký tự và từ viết tắt.
Layer 2
Prefix Trie Classifier
~1 ms
Khớp chính xác mã lỗi DTC (P0A80, C1234) hoặc từ khóa Form
cố định ($O(1)$).
Layer 3
Embedding (MiniLM / BGE-
ONNX)
~25 ms
Phân loại Intent dựa trên Cosine Similarity với Centroids câu hỏi
mẫu.
Layer 4
Gemini Flash (LLM Fallback)
~80 ms
Xử lý các câu hỏi phức tạp hoặc không khớp 3 lớp trên (Zero-shot
JSON).
Trang 3 / 5

## Page 4

5. Module M4: API Specifications (Định Dạng Chuẩn)
5.1. Chat Endpoint: POST /api/v1/chat
// Request Body JSON:
  "query": "Xe VF8 báo lỗi P0A80 trên màn hình thì xử lý thế nào?",
  "user_role": "technician",
  "session_id": "sess_20260807_9981"
// Response Body JSON:
  "code": 200,
  "message": "Success",
  "data": {
    "intent": "ERROR_LOOKUP",
    "response_text": "Mã lỗi **P0A80** chỉ ra sự cố suy giảm chất lượng Bộ Pin Cao Áp (High Voltage
Battery Pack)...
⚠️ **CẢNH BÁO AN TOÀN:** Yêu cầu đeo găng tay cách điện 1000V khi thao tác.",
    "citations": [
        "id": "doc_bm_vf8_p012",
        "title": "Cẩm nang Kỹ thuật VF8 - Hệ thống Pin",
        "source": "HDSD_VF8.pdf",
        "page": 142,
        "score": 0.94
    ],
    "ticket_trigger": { "required": false },
    "caution_alert": true,
    "execution_time_ms": 420
6. Module M5 & M6: Data Models, Vector DB & AI Skills
6.1. Metadata Phân Quyền Trong ChromaDB (RBAC)
Mọi Chunk dữ liệu khi đẩy vào Vector DB đều đi kèm Metadata phân quyền:
  "doc_id": "doc_vf8_bms_001",
  "allowed_roles": "technician,service_manager", // Filter qua Chroma $contains
  "car_model": "VF8",
  "chunk_type": "text"
6.2. Safe Guardrail & Safety Caution Alert Engine
Cơ chế Banner Cảnh Báo An Toàn (⚠️ CAUTION):
Nếu câu hỏi/mã lỗi liên quan đến các hệ thống nguy hiểm cao như: Pin Cao Áp (BMS), Phanh Điện Tử (EPB), hoặc Túi Khí
(SRS), hệ thống tự động gán cờ need_caution_alert = true và chèn Banner cảnh báo an toàn lao động bắt buộc ở đầu
câu trả lời.
Trang 4 / 5

## Page 5

7. Module M7 & M8: UI/UX Guidelines & Verification Plan
7.1. Hướng Dẫn UI/UX Frontend
Role Selector Enforcement: Bắt buộc chọn Vai trò (KTV / Sale / Quản lý) trước khi gửi tin nhắn đầu tiên.
Citation Accordion: Render trích dẫn dạng xổ xuống (Accordion) ở cuối câu trả lời kèm link mở trang PDF / timestamp
Video.
Fallback Static Form Pop-up: Khi Confidence Score $< 0.70$, tự động hiển thị gợi ý mở Form gửi Ticket cho chuyên gia
kỹ thuật cấp cao.
7.2. Kế Hoạch Kiểm Thử (Verification Plan)
Loại Test
Mục Tiêu Kiểm Thử
Tiêu Chí Chấp Nhận (Acceptance Criteria)
Unit Test M2
4-Layer Router Engine
100% test cases Router phản hồi $< 50 ext{ ms}$. Độ chính xác phân loại $> 98\%$.
Unit Test M0
Parsing Multi-Format
Files
Trích xuất chính xác $100\%$ các bảng dữ liệu từ PDF và Excel không bị lệch hàng/
cột.
Integration
Test
End-to-End Chat Flow
Thời gian phản hồi toàn luồng $< 1.5 ext{ giây}$. Đã gắn đúng Citation và RBAC.
Trang 5 / 5