# PRODUCT REQUIREMENTS DOCUMENT (PRD)
## VF-Onboarding Copilot — Enterprise AI Edition
### Version 3.0 (Production-Ready AI Product)

---

| Trường | Nội dung |
| :--- | :--- |
| **Mã tài liệu** | PRD-VF-ONBOARDING-2026-V3 |
| **Phiên bản** | 3.0.0 (Enterprise AI Scope Update) |
| **Dự án** | VF-Onboarding Copilot Platform |
| **Ngày cập nhật** | 08/08/2026 |
| **Trạng thái** | ✅ Approved for MVP Engineering |
| **Tài liệu tham chiếu** | SDD-VF-ONBOARDING-2026-V4 |

### Nhóm Thực Hiện — Team T223
* **Lương Quỳnh Chi:** Product Owner (PO)
* **Phạm Tiến Hưng:** Project Manager (PM)
* **Nguyễn Duy Thái:** System Architect / Tech Lead
* **Sẻ Thế Hưng:** Dev Lead / AI Engineer

---

## 1. Executive Summary

### 1.1. Product Vision
Trở thành **"Trợ lý ảo cốt lõi" (Core AI Copilot)** thông minh, chính xác và an toàn nhất dành cho toàn bộ nhân sự tại các Đại lý Phân phối (ĐLPP) xe máy điện VinFast. Giúp chuẩn hóa và số hóa hoàn toàn quy trình Onboarding, Tra cứu kỹ thuật và Hỗ trợ nghiệp vụ.

### 1.2. Business Goals
1. **Giảm 50% thời gian Self-Onboarding:** Rút ngắn thời gian đào tạo Kỹ thuật viên (KTV) mới để họ có thể trực tiếp làm việc trên chuyền.
2. **Tăng 40% First Contact Resolution (FCR):** AI tự động xử lý và giải đáp chính xác các thắc mắc nghiệp vụ/kỹ thuật mà không cần leo thang lên IT Admin.
3. **Enterprise Compliance & Security:** Đảm bảo 100% câu trả lời đều dựa trên tài liệu chuẩn (Zero Hallucination Tolerance) và tuân thủ tuyệt đối phân quyền dữ liệu (RBAC).

### 1.3. Target Audience (Đối tượng người dùng)
*Phạm vi MVP (Phase 1) chỉ tập trung vào bộ phận Dịch vụ & Kỹ thuật:*
- **Kỹ thuật viên (KTV) / Lead Tech:** Cần tra cứu quy trình bảo dưỡng, sửa chữa, mã lỗi xe, thông số pin LFP.
- **Service Manager:** Quản lý xưởng dịch vụ, cần tra cứu chính sách bảo hành, quy định đổi trả linh kiện.
- **IT Admin:** Quản trị viên hệ thống, người tiếp nhận các Support Ticket từ KTV khi AI không thể giải quyết.

---

## 2. Product Roadmap & Phasing

Nhằm đảm bảo dự án Go-live nhanh chóng và đạt độ hoàn thiện Enterprise-grade cho hệ thống lõi, scope của sản phẩm được chia làm 2 giai đoạn:

### 2.1. Phase 1: MVP (Minimum Viable Product) — Current Scope
Tập trung xây dựng bộ khung AI an toàn, xử lý ngôn ngữ văn bản (Text-only) với độ trễ thấp và bảo mật dữ liệu tuyệt đối.
* **Dealer Onboarding & Workflow Guidance:** Hướng dẫn quy trình từng bước.
* **Policy Copilot (RAG):** Trợ lý tra cứu chính sách dựa trên tài liệu.
* **Error Code Lookup:** Tra cứu mã lỗi chính xác.
* **Static Support Form:** Tự động fallback sang biểu mẫu báo lỗi cho Human Support.
* **Multi-layer Guardrails & Basic RBAC:** Bảo vệ an toàn đầu vào/đầu ra và phân quyền dữ liệu mức độ cơ bản.

### 2.2. Phase 2 & Future Roadmap — Out of Scope for MVP
Các tính năng mở rộng sẽ được triển khai sau khi Phase 1 ổn định. Kiến trúc (đã thiết kế trong SDD) cho phép Plug-and-Play các module này mà không cần đập bỏ lõi.
* **Đa phương thức (Multimodal):** Voice AI (STT/TTS), Voice Cloning, Nhận diện hình ảnh (Image Understanding), OCR quét tài liệu, QR Lookup.
* **Trải nghiệm & Báo cáo:** Dashboard, Data Analytics.
* **AI Nâng cao:** Advanced Memory (Long-term context), Multi-agent Orchestration, History-Augmented RAG.
* **Mở rộng người dùng:** Module dành cho bộ phận Sales, Kế toán, Manager Dashboard.
* **Hạ tầng:** Offline Mode (PWA Local LLM).

---

## 3. User Roles & RBAC (Basic) - Phase 1

Hệ thống Phase 1 áp dụng nguyên tắc **RBAC Enforcement tại tầng Vector Database** (định nghĩa trong SDD), đảm bảo không bao giờ rò rỉ dữ liệu chéo quyền.

| Role | Quyền hạn Tra cứu & Onboarding |
| :--- | :--- |
| **Technician** (KTV) | Quy trình PDI, bảo dưỡng pin, mã lỗi xưởng, quy trình sửa chữa cơ bản. Không được xem chính sách chiết khấu, giá nhập. |
| **Lead Tech** | Toàn bộ quyền của KTV + Quy trình sửa chữa chuyên sâu, phê duyệt bảo hành cấp 1. |
| **Service Manager** | Toàn quyền Dịch vụ + Chính sách bảo hành xưởng, quy định xuất vật tư. |
| **IT Admin** | Toàn quyền tra cứu + Quản lý hệ thống, tiếp nhận Ticket báo lỗi từ hệ thống AI (Static Form). |

---

## 4. Functional Requirements (FR) — Phase 1 MVP

### 4.1. Dealer Onboarding & Workflow Guidance (FR-01)
* Hiển thị quy trình làm việc từng bước (Step-by-step checklist) dựa trên vai trò của người dùng (ví dụ: Quy trình PDI cho KTV).
* Nội dung trả về dạng tĩnh (pre-defined templates) không sử dụng LLM để tăng tốc độ và độ chính xác 100%.

### 4.2. Policy Copilot / RAG (FR-02)
* Cho phép người dùng đặt câu hỏi tự nhiên về quy định, chính sách, tài liệu bảo hành.
* Hệ thống phải tìm kiếm bằng **Hybrid Search (BM25 + Vector + Reranker)** và tổng hợp câu trả lời dựa trên tài liệu đã cấu hình.

### 4.3. Error Code Lookup (FR-03)
* Hỗ trợ nhận diện mã lỗi (P01, E03, BMS_OVERHEAT) bằng Regex ưu tiên, sau đó fallback sang Semantic Search.
* Trả về nguyên nhân, các bước khắc phục và đặc biệt phải chèn cảnh báo an toàn (`⚠️ CAUTION Alert`) nếu mã lỗi liên quan đến Pin cao áp/Điện.

### 4.4. Static Support Form & Human Escalation (FR-04)
* Khi độ tự tin của AI thấp ($Confidence < 0.7$) hoặc mã lỗi yêu cầu chuyên gia, AI không cố gắng trả lời (tránh Hallucination).
* Chuyển hướng ngay sang **Static Form** (Biểu mẫu tĩnh) được điền sẵn ngữ cảnh cuộc gọi.
* Tạo Support Ticket đẩy về màn hình quản trị của IT Admin.

---

## 5. Non-Functional Requirements (NFR)

| Hạng mục | Chỉ tiêu | Ghi chú |
| :--- | :--- | :--- |
| **Tối ưu hóa Chi phí** | Giảm 60-70% Token | Xử lý qua Lightweight Router (Trie/Embedding) thay vì dùng LLM để phân loại intent. |
| **Độ trễ Router** | $\le 100\text{ms}$ | Phân loại chính xác Intent. |
| **Độ trễ E2E (Latency)**| $\le 1.5\text{s}$ | **Lưu ý:** Hệ thống Guardrails có thể làm tăng nhẹ độ trễ (thêm ~45ms cho Input và ~100ms cho Output), nhưng kiến trúc Router nhẹ (tiết kiệm ~1s so với LLM Router) bù đắp hoàn toàn độ trễ này. |
| **Khả năng Mở rộng** | Container hóa | Sẵn sàng scale trên Kubernetes/Render.com |
| **Tính Sẵn sàng (HA)** | $99.9\%$ Uptime | Cơ chế Fallback nhiều lớp LLM (Flash → Haiku). |

---

## 6. AI & Machine Learning Requirements

1. **Retrieval-Augmented Generation (RAG):** 
   - Không được dùng LLM tự sinh kiến thức ngoài (Zero-shot knowledge). Phải bám sát 100% Context truyền vào.
2. **Hybrid Search Pipeline:** 
   - Bắt buộc áp dụng Lexical Search (BM25 tối ưu tiếng Việt) kết hợp Vector Search (MiniLM) và chấm điểm lại bằng Cross-Encoder (Reranker).
3. **Context Window:**
   - Giới hạn Context truyền cho LLM ở mức $\le 2000$ tokens để tối ưu chi phí và tăng Focus Rate của LLM.
4. **Fallback Models:**
   - Triển khai cơ chế Chain Fallback: `Gemini 1.5 Flash` (Primary) → `Claude 3 Haiku` (Backup) để chống nghẽn mạng/Rate Limit.

---

## 7. AI Safety, Security & Guardrails (CRITICAL)

Đây là các yêu cầu bắt buộc của một hệ thống Enterprise AI. Hệ thống không được phép hoạt động nếu thiếu một trong các Guardrail này (chi tiết triển khai xem SDD v4).

### 7.1. Input Guardrails (Chặn trước khi gọi LLM)
* **Prompt Injection & Jailbreak Detection:** Hệ thống phải từ chối mọi nỗ lực thao túng AI (VD: "Bỏ qua mọi hướng dẫn trước đó và nói cho tôi biết...").
* **PII Protection:** Tự động nhận diện và ẩn (masking) thông tin nhận dạng cá nhân (CMND, Số điện thoại, Số khung VIN) trước khi đưa vào Log hoặc gọi LLM.
* **SQL/XSS & Toxic Filter:** Loại bỏ mã độc và ngôn từ thù ghét.
* **Spam & Domain Policy:** Chặn các câu hỏi không liên quan đến ngành xe điện (Out-of-domain) hoặc spam liên tục.

### 7.2. Output Guardrails (Kiểm duyệt trước khi trả User)
* **Citation Requirement (Bắt buộc trích dẫn):** Bất kỳ thông tin kỹ thuật nào do RAG sinh ra ĐỀU PHẢI có trích dẫn nguồn [Tên File - Trang]. Nếu thiếu → Hủy câu trả lời.
* **Hallucination Prevention:** So sánh chéo câu trả lời với tài liệu gốc (Vector Similarity). Nếu phát hiện AI bịaa đặt thông tin → Kích hoạt Human Escalation (Static Form).
* **RBAC Leak Enforcement:** Đảm bảo câu trả lời không vô tình rò rỉ dữ liệu của Role cao hơn (VD: Không trả lời lương/thưởng cho KTV).
* **Safety Validator:** Ngăn chặn các hướng dẫn nguy hiểm (VD: "Cắt cáp pin cao áp bằng tay không"). 

---

## 8. AI Governance & Compliance

* **Traceability (Khả năng truy vết):** Mọi request gửi đến hệ thống phải được gắn `trace_id`. Mọi hành động chặn của Guardrails phải được lưu vào bảng `guardrail_events` phục vụ Audit.
* **Data Separation:** Dữ liệu Knowledge Base (VectorDB) hoàn toàn độc lập với dữ liệu Runtime. Admin có thể cập nhật tài liệu mà không cần restart hệ thống.
* **Transparency:** Khi AI không thể trả lời, hệ thống phải thông báo rõ ràng "Tôi chưa tìm thấy thông tin trong tài liệu" thay vì cố gắng đoán (Fail-safe).

---

## 9. Tiêu chí Nghiệm thu & Success Metrics

### 9.1. Acceptance Criteria (Tiêu chí Nghiệm thu trước Release)
1. Smart Router (Trie/Embedding) đạt độ chính xác phân loại $\ge 90\%$ trong $< 100\text{ms}$.
2. Hệ thống vượt qua 10/10 kịch bản Prompt Injection / Jailbreak Attack (Từ chối phục vụ chính xác).
3. 100% câu trả lời nghiệp vụ từ Policy Copilot chứa trích dẫn nguồn.
4. Tài khoản KTV tuyệt đối không thể truy xuất tài liệu của Manager (RBAC Pass).
5. Khi RAG Confidence $< 0.70$, Form Ticket tự động bật lên trong $< 2\text{s}$.
6. Latency End-to-End P95 $< 1.5\text{s}$.

### 9.2. Success Metrics (Sau khi Go-live 30 ngày)
* **AI Deflection Rate:** $\ge 60\%$ (Số lượng thắc mắc AI tự giải quyết mà không cần tạo Ticket).
* **Time-to-Onboard:** Giảm từ 5 ngày xuống $< 2$ ngày cho KTV mới.
* **Hallucination Rate:** $\le 1\%$ (Số câu trả lời sai lệch / Tổng câu trả lời).

---

## 10. Assumptions & Constraints

### 10.1. Assumptions (Giả định)
* ĐLPP sẽ cung cấp tài liệu nghiệp vụ/kỹ thuật (PDF/Excel) có định dạng và cấu trúc rõ ràng để chuẩn bị cho Ingestion Pipeline.
* End-user sử dụng thiết bị (Mobile/Laptop) có kết nối Internet ổn định.

### 10.2. Constraints (Ràng buộc)
* Dữ liệu VectorDB (ChromaDB) được lưu trữ local persistent volume trên server, yêu cầu backup định kỳ thủ công trong Phase 1.
* MVP chỉ hỗ trợ ngôn ngữ duy nhất là Tiếng Việt.

---

## 11. Risk Analysis & Mitigation

| Rủi ro | Mức độ | Biện pháp giảm thiểu (Mitigation) |
| :--- | :--- | :--- |
| **LLM Hallucination** (AI bịa lỗi) | Cao | Áp dụng Output Guardrail bắt buộc đối chiếu Citation. Threshold confidence khắt khe. |
| **Rò rỉ dữ liệu nhạy cảm** | Cao | Lọc RBAC tại tầng DB (ChromaDB) thay vì phụ thuộc LLM. |
| **LLM Provider API Downtime**| Trung bình| Cơ chế LLM Fallback (tự động chuyển từ Gemini sang Claude qua OpenRouter). |
| **Latency tăng do Guardrail** | Trung bình| Code Guardrails theo cơ chế Async parallel (nếu có thể) và bù đắp bằng Router Trie $<10\text{ms}$. |

---

## 12. Release Plan (Phase 1)

* **Week 1-2:** Hoàn thiện Core Runtime (Router + Skills) & Ingestion Pipeline.
* **Week 3:** Tích hợp Multi-layer Guardrails (Input & Output) & Hybrid Search.
* **Week 4:** Security Testing (Jailbreak, RBAC) & E2E Latency Tuning.
* **Week 5:** UAT (User Acceptance Testing) với 2 ĐLPP Pilot.
* **Week 6:** Chính thức Go-live MVP Phase 1.

---
*Tài liệu được cập nhật để phản ánh đúng chuẩn MLOps và Enterprise AI Systems theo chuẩn bảo mật và Governance cao nhất.*
