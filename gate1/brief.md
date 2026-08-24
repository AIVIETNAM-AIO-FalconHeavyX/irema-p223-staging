# Project Brief - VF-Onboarding Copilot (Enterprise AI Edition)

## Thông tin Phiên bản
* **Version:** 3.0.0
* **Trạng thái:** Approved Scope Update (Enterprise AI Architecture & Phase 1 MVP)
* **Dự án thuộc:** VF-Onboarding Copilot Platform

## Tên Dự án
**VF-Onboarding Copilot - Trợ lý AI Tra cứu Kỹ thuật & Nghiệp vụ dành cho Đại lý Phân phối Xe máy Điện**

## Nhóm thực hiện: Team T223
1. **Lương Quỳnh Chi:** Product Owner (PO)
2. **Phạm Tiến Hưng:** Project Manager (PM)
3. **Nguyễn Duy Thái:** System Architect / Tech Lead
4. **Sẻ Thế Hưng:** Dev Lead / AI Engineer

---

# 1. Bối cảnh & Vấn đề
Đại lý phân phối (ĐLPP) xe máy điện thường gặp khó khăn trong việc đào tạo Kỹ thuật viên (KTV) mới. Việc tra cứu tài liệu sửa chữa, quy trình bảo dưỡng và xử lý mã lỗi hiện phụ thuộc vào trao đổi thủ công qua nhắn tin/điện thoại tới Quản lý xưởng hoặc IT. Điều này gây gián đoạn công việc sửa chữa, tốn thời gian hỗ trợ và tiềm ẩn rủi ro thao tác sai gây mất an toàn (đặc biệt với xe máy điện và hệ thống pin cao áp).

---

# 2. Định hướng Giải pháp (Enterprise AI MVP - Phase 1)
Xây dựng nền tảng Web/Mobile tích hợp **AI Copilot** dành riêng cho bộ phận Kỹ thuật & Dịch vụ. Giải pháp áp dụng kiến trúc **Enterprise AI Production-Ready**, tuân thủ khắt khe các tiêu chuẩn về bảo mật, tính chính xác và độ trễ:

1. **Kiến trúc Interface-First & Clean Architecture:** Tách biệt hoàn toàn luồng xử lý tài liệu (Ingestion Pipeline) và luồng xử lý truy vấn (Runtime Pipeline) với LangGraph đóng vai trò Orchestrator thuần túy.
2. **Bảo vệ bằng Multi-layer Guardrails:** 10 lớp kiểm duyệt đầu vào (chống Prompt Injection, Jailbreak, lọc PII) và 7 lớp kiểm duyệt đầu ra (bắt buộc trích dẫn Citation, chặn Hallucination, chống rò rỉ dữ liệu RBAC).
3. **Hybrid Search RAG:** Kết hợp BM25 (Lexical) và Vector Search (Semantic) cùng Cross-Encoder Reranker để tra cứu chính xác 100% các thuật ngữ kỹ thuật tiếng Việt.
4. **Lightweight Router & Static Form Ticketing:** Sử dụng Router thuật toán siêu nhẹ (Trie/Embedding) định tuyến Intent trong $< 100\text{ms}$. Tự động chuyển hướng sang biểu mẫu tĩnh (Static Form) gửi ticket cho IT Admin khi AI không đủ tự tin giải quyết.

---

# 3. Phân hệ Tính năng Cốt lõi (Phase 1)
*Lưu ý: Các tính năng dành cho Sales, Kế toán, Manager Dashboard và Đa phương thức (Voice/OCR/Vision) được quy hoạch sang Phase 2 (Future Roadmap).*

### 3.1. Dealer Onboarding & Workflow Guidance
- Hướng dẫn lộ trình tự học và checklist công việc tĩnh (pre-defined templates) dành riêng cho Kỹ thuật viên (KTV), Lead Tech và Service Manager.

### 3.2. AI Policy Copilot & Error Lookup
- **Tra cứu Chính sách & Kỹ thuật (RAG):** Tra cứu quy trình PDI, bảo dưỡng, chính sách bảo hành. Tích hợp bộ lọc RBAC tại tầng Vector DB đảm bảo KTV không thể xem tài liệu nội bộ của Manager. 100% câu trả lời kỹ thuật đều phải có trích dẫn nguồn (Tên File - Trang).
- **Tra cứu Mã lỗi Xưởng:** Khớp chính xác danh mục mã lỗi (`P01`, `BMS_OVERHEAT`), trả về nguyên nhân, checklist khắc phục và tự động chèn cảnh báo an toàn điện (`⚠️ CAUTION Alert`).

### 3.3. Trung tâm Xử lý Sự cố (Human Escalation)
- Tự động fallback sang biểu mẫu tĩnh báo lỗi, gửi Ticket thẳng về IT Admin khi AI không tìm được tài liệu ($RAG\_confidence < 0.70$) hoặc khi phát hiện rủi ro ảo giác (Hallucination).

---

# 4. Chỉ số Thành công (KPIs)
- **AI Deflection Rate:** $\ge 60\%$ (AI tự xử lý thành công thắc mắc, không cần tạo Support Ticket).
- **Zero Hallucination Tolerance:** $\le 1\%$ tỷ lệ sinh thông tin sai lệch so với tài liệu.
- **Latency E2E:** $< 1.5$ giây, Router Latency $< 100\text{ms}$.
- **Tiết kiệm Token:** Giảm 60-70% chi phí so với kiến trúc dùng LLM lớn làm Router.
- **Thời gian Onboarding KTV mới:** Giảm $50\%$ (từ 5 ngày xuống $< 2$ ngày).
