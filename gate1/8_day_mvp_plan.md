# Kế hoạch Thực thi MVP 8 Ngày - Team T223
**Dự án:** Nền tảng Hỗ trợ Self-Onboarding & Trợ lý AI Tra cứu Nghiệp vụ ĐLPP Xe Máy Điện
**Version:** 2.1.0 — Refocused: ĐLPP-First Strategy

> **Chiến lược cốt lõi:** Tập trung toàn bộ 8 ngày vào **một người dùng duy nhất — Kỹ thuật viên/Nhân viên mới tại ĐLPP**. Không làm rộng, làm thật. Sales và Manager là Phase 2.

---

## 👥 Phân công Vai trò (Roles)
* **Lương Quỳnh Chi (PO):** Chuẩn bị dữ liệu thực (tài liệu PDI, mã lỗi kỹ thuật), viết test cases từ góc nhìn ĐLPP, QA/QC nghiệm thu.
* **Phạm Tiến Hưng (PM):** Quản lý tiến độ Kanban, viết & tinh chỉnh System Prompts, thiết kế luồng kịch bản ĐLPP, chuẩn bị Demo.
* **Nguyễn Duy Thái (Tech Lead):** Kiến trúc hệ thống, phát triển Lightweight Router (Trie + Embedding), RAG Engine, FastAPI Core.
* **Sẻ Thế Hưng (Dev Lead):** UI/UX Chatbot, FastAPI endpoints, Static Form Ticketing, tích hợp toàn hệ thống.

---

## 🎯 Scope MVP — ĐLPP-First (8 Ngày)

| Làm ngay (MVP) | Để sau (Phase 2) |
| :--- | :--- |
| ✅ Onboarding flow cho **Kỹ thuật viên** (PDI, bảo dưỡng pin LFP) | ⏳ Onboarding cho Sales, Kế toán |
| ✅ Tra cứu mã lỗi xe điện (`P01`, `E03`, `BMS_OVERHEAT`) | ⏳ Chiết khấu, hoa hồng Manager |
| ✅ RAG Policy Copilot (tài liệu kỹ thuật ĐLPP) | ⏳ Module quản lý kho, hóa đơn VAT |
| ✅ Static Form báo lỗi gửi IT/Admin | ⏳ Dashboard KPI Manager |
| ✅ RBAC cơ bản (Level 1 — ĐLPP tech) | ⏳ RBAC Level 3 Manager |

---

## 📅 Bảng Kế hoạch Chi tiết (8 Days)

### 📌 Ngày 1: Kickoff & ĐLPP Data Collection
**Mục tiêu:** Đồng thuận scope ĐLPP-First, setup môi trường, thu đủ dữ liệu thực.

* **Lương Quỳnh Chi (PO):**
  - Thu thập tài liệu: Hướng dẫn PDI, Bảng mã lỗi xe điện (P01→P99, E01→E20, BMS codes), Quy trình bảo dưỡng pin LFP.
  - Xác nhận danh sách **5–10 câu hỏi thực tế** Kỹ thuật viên thường hỏi nhất (golden test set).

* **Phạm Tiến Hưng (PM):**
  - Setup Kanban board (GitHub Projects) với 3 cột: `To Do / In Progress / Done`.
  - Chốt danh sách tài liệu ĐLPP cho Knowledge Base ngày 2.
  - Đặt lịch daily standup 15 phút mỗi sáng.

* **Nguyễn Duy Thái (Tech Lead):**
  - Init Git repo, setup Python venv, cài: `fastapi`, `langgraph`, `langchain`, `chromadb`, `sentence-transformers`.
  - Thiết kế cấu trúc thư mục: `src/router/`, `src/skills/rag/`, `src/skills/error_lookup/`, `src/api/`, `data/raw/`, `data/processed/`.
  - Draft kiến trúc Lightweight Router 3-layer (Trie → Embedding → LLM fallback).

* **Sẻ Thế Hưng (Dev Lead):**
  - Init Next.js project (hoặc React + Vite), dựng layout Chatbot cơ bản (khung hội thoại + Role Selector).
  - Thiết kế wireframe giao diện Static Form Báo lỗi.

---

### 📌 Ngày 2: Data Processing & Vector DB
**Mục tiêu:** Toàn bộ tài liệu ĐLPP vào được Vector DB, backend kết nối được frontend.

* **Lương Quỳnh Chi (PO):**
  - Dùng Whisper/Gemini transcribe video hướng dẫn DMS → `.txt`.
  - Gán nhãn metadata: `{ "role": "technician", "topic": "PDI|error_code|battery", "source": "filename.pdf", "page": N }`.

* **Phạm Tiến Hưng (PM):**
  - Viết **System Prompt v1** cho Intent Classifier: 4 intent (WORKFLOW, RAG_POLICY, ERROR_LOOKUP, STATIC_FORM).
  - Soạn **từ điển chuẩn hóa** thuật ngữ ĐLPP (BMS, LFP, VIN, PDI, DMS...) cho Query Rewriter.

* **Nguyễn Duy Thái (Tech Lead):**
  - Pipeline: PDF/TXT → chunking (500 token, overlap 50) → embed bằng `paraphrase-multilingual-MiniLM-L12-v2` → lưu ChromaDB.
  - Tách 2 collections riêng: `technician_docs` và `error_codes`.

* **Sẻ Thế Hưng (Dev Lead):**
  - Xây dựng `POST /chat` endpoint: nhận `{ message, role, session_id }`, trả `{ reply, citations, confidence }`.
  - Đảm bảo Frontend ↔ Backend kết nối được (test mock response).

---

### 📌 Ngày 3: Lightweight Router — Thuật toán Trie + Embedding
**Mục tiêu:** Router phân loại intent < 100ms, tiết kiệm 60–70% token LLM.

> **🧠 Thuật toán Router 4-Layer (tối ưu hoá thay vì gọi LLM lớn):**
>
> **Layer 1 — Query Rewriter (< 5ms):**
> Dict Python thay thế từ tắt: `"bms" → "Battery Management System"`, `"vin" → "Vehicle Identification Number"`.
> Regex loại bỏ nhiễu, lowercase, strip dấu câu thừa.
>
> **Layer 2 — Trie Fast-Path Classifier (< 10ms):**
> Build Trie từ keyword patterns:
> - `["lỗi", "mã lỗi", "P0", "E0", "BMS_", "không khởi động", "pin hỏng"]` → `ERROR_LOOKUP`
> - `["quy trình", "PDI", "bảo dưỡng", "onboarding", "làm sao", "hướng dẫn"]` → `WORKFLOW`
> - `["chính sách", "chiết khấu", "giá", "phụ lục", "tài liệu"]` → `RAG_POLICY`
> - `["báo lỗi", "gửi ticket", "cần hỗ trợ", "không tìm thấy"]` → `STATIC_FORM`
>
> Nếu match confidence ≥ 0.85 → **return ngay, skip Layer 3**.
>
> **Layer 3 — Embedding Fallback (< 80ms, chỉ khi Trie fail):**
> Embed query bằng MiniLM-L12-v2, cosine similarity với 4 intent prototype vectors (pre-computed lúc startup).
> Chọn intent similarity cao nhất, ngưỡng tối thiểu 0.6.
>
> **Layer 4 — LLM Fallback (chỉ ~3% queries khi Embedding < 0.6):**
> Gọi Gemini Flash với prompt cực ngắn: `"Classify: [WORKFLOW|RAG|ERROR|FORM]. Query: {q}"`.
>
> **Phân phối dự kiến:** 85% Trie (< 10ms) | 12% Embedding (< 80ms) | 3% LLM → **tiết kiệm 60–70% token**.

* **Lương Quỳnh Chi (PO):** Cung cấp 30 câu hỏi test thực tế từ Kỹ thuật viên ĐLPP (không phải Sales).
* **Phạm Tiến Hưng (PM):** Bổ sung từ điển chuẩn hóa; đo accuracy Router trên 30 test cases (target ≥ 90%).
* **Nguyễn Duy Thái (Tech Lead):**
  - Code `src/router/query_rewriter.py`: regex + dict lookup chuẩn hóa thuật ngữ.
  - Code `src/router/trie_classifier.py`: Trie với dict lồng nhau + confidence scoring.
  - Code `src/router/embedding_classifier.py`: cosine sim với 4 prototype vectors.
  - Viết unit tests cho cả 3 module Router.
* **Sẻ Thế Hưng (Dev Lead):** Hoàn thiện Role Selector UI; gắn `role` metadata vào mỗi API request.

---

### 📌 Ngày 4: RAG Policy Copilot & RBAC
**Mục tiêu:** AI tra cứu tài liệu kỹ thuật ĐLPP chính xác, có trích dẫn, có phân quyền.

> **🔒 RBAC Filter Strategy:**
> Metadata-level filter tại ChromaDB: `where={"role": {"$in": [user_role, "public"]}}`.
> Kỹ thuật viên chỉ thấy `technician_docs` + `error_codes`. Không check quyền ở LLM level → không tốn token bảo mật.

* **Lương Quỳnh Chi (PO):** Kiểm tra nhãn metadata tài liệu; chuẩn bị dữ liệu giả lập (bảng chiết khấu Manager) để test RBAC chặn.
* **Phạm Tiến Hưng (PM):** Viết RAG Prompt: *"Trả lời NGẮN GỌN, trích dẫn [File - Trang], KHÔNG bịa thêm. Nếu không tìm thấy → nói không biết."* Format: `reply + citations: [{file, page, snippet}]`.
* **Nguyễn Duy Thái (Tech Lead):**
  - Code `src/skills/rag/rag_skill.py`: ChromaDB query (RBAC filter) → rerank top-k (k=3) → LLM generate → extract citations.
  - Confidence = avg cosine similarity của top-k chunks; ngưỡng 0.7 trigger Static Form.
  - Tích hợp RAG Node vào LangGraph StateGraph.
* **Sẻ Thế Hưng (Dev Lead):** Frontend render Citations dạng accordion (click xem trích dẫn gốc); gắn `role` từ Role Selector vào API request.

---

### 📌 Ngày 5: Error Code Lookup & Static Form
**Mục tiêu:** Kỹ thuật viên tra mã lỗi tức thì (< 200ms), báo lỗi < 30 giây.

> **⚡ Tối ưu Error Lookup — 2-step hybrid:**
> 1. **Exact match** regex `P\d+|E\d+|BMS_\w+` → truy cập thẳng ChromaDB `error_codes` bằng ID (< 50ms).
> 2. Chỉ dùng **semantic search** khi không có exact match (mô tả triệu chứng, không có mã cụ thể).

* **Lương Quỳnh Chi (PO):** Đóng gói bảng mã lỗi: `{ code, description, checklist_steps[], safety_warning, escalate_to_admin: bool }`. Kiểm tra đủ safety warning điện cao áp.
* **Phạm Tiến Hưng (PM):** Xác định trường Static Form: `{ technician_name, error_code, vehicle_model, VIN, symptom_description, phone }`. Trigger: `RAG_confidence < 0.7` HOẶC user chọn "Cần hỗ trợ thêm".
* **Nguyễn Duy Thái (Tech Lead):**
  - Code `src/skills/error_lookup/error_skill.py`: regex exact match → ChromaDB fallback → checklist + ⚠️ CAUTION.
  - Code trigger: `if rag_confidence < 0.7: return StaticFormPayload(context=chat_history)`.
* **Sẻ Thế Hưng (Dev Lead):**
  - Code Static Form UI (modal popup): auto-fill từ context (error code, cuộc trò chuyện hiện tại).
  - Code `POST /tickets`: lưu Ticket vào SQLite, trả `ticket_id`.

---

### 📌 Ngày 6: Integration & End-to-End Flow
**Mục tiêu:** Nối toàn bộ hệ thống thành một luồng hoàn chỉnh, test E2E.

* **Lương Quỳnh Chi (PO):** Đóng vai **Kỹ thuật viên mới** dùng thực hệ thống; ghi lại bugs và ít nhất 5 edge cases (câu mơ hồ, tiếng Việt viết tắt, mã lỗi không có trong DB).
* **Phạm Tiến Hưng (PM):** Đo Latency từng bước (Router, RAG, Error Lookup, E2E); tinh chỉnh prompt nếu câu trả lời > 200 từ không cần thiết.
* **Nguyễn Duy Thái (Tech Lead):**
  - Hoàn thiện `LangGraph StateGraph`: Router → [RAG | Error | Workflow | StaticForm] → Response Generator.
  - Thêm `WorkflowNode` cho ĐLPP: checklist onboarding kỹ thuật viên (bước 1→5).
  - Xử lý edge cases từ PO.
* **Sẻ Thế Hưng (Dev Lead):**
  - Hoàn thiện UI: Markdown rendering, Citation accordion, ⚠️ CAUTION highlight (nền đỏ/vàng nổi bật).
  - Loading skeleton animation khi AI đang xử lý.

---

### 📌 Ngày 7: QA & Bug Fixing
**Mục tiêu:** Zero critical bugs, đạt tất cả KPIs trước khi Deploy.

**Checklist QA Gate (phải PASS hết trước khi sang ngày 8):**
- [ ] Router accuracy ≥ 90% trên 30 test cases.
- [ ] RAG luôn có citations (100% responses).
- [ ] RBAC: Kỹ thuật viên KHÔNG xem được tài liệu Manager.
- [ ] Error Lookup exact match < 200ms.
- [ ] Static Form submit thành công, lưu DB, trả `ticket_id`.
- [ ] End-to-end latency < 1.5s trên máy demo.
- [ ] Mobile responsive (tối thiểu iPhone SE width 375px).

* **Lương Quỳnh Chi (PO):** Chạy 30 test cases, chấm Đạt/Không đạt, ghi bug report có priority.
* **Phạm Tiến Hưng (PM):** Điều phối fix bug; cập nhật `ARCHITECTURE.md` và `PRD.md` theo code thực tế.
* **Nguyễn Duy Thái (Tech Lead):** Fix logic Router/RAG; thử ngưỡng confidence 0.65 vs 0.7 để tìm giá trị tối ưu.
* **Sẻ Thế Hưng (Dev Lead):** Fix UI bugs; đảm bảo Static Form submit flow ổn định end-to-end.

---

### 📌 Ngày 8: Deploy & Demo Day
**Mục tiêu:** Live URL hoạt động, Pitch Deck sẵn sàng, video Demo quay xong.

**Demo Script (5 phút — ĐLPP-First focus):**
1. Kỹ thuật viên mới login → chọn role → xem Onboarding checklist bước 1→5 **(1 phút)**.
2. Gõ: *"xe báo lỗi BMS_OVERHEAT làm sao?"* → Router (Trie, < 10ms) → Error Lookup → checklist + ⚠️ CAUTION **(1.5 phút)**.
3. Gõ: *"quy trình PDI xe Klara S"* → Router → RAG → trả lời + citation [PDF trang 3] **(1.5 phút)**.
4. Gõ câu mơ hồ → RAG confidence < 0.7 → Static Form popup auto-fill → điền & submit ticket **(1 phút)**.

* **Lương Quỳnh Chi (PO):** Quay video Demo theo script trên.
* **Phạm Tiến Hưng (PM):** Hoàn thiện Pitch Deck (slide: Pain point ĐLPP → Solution → Architecture → Demo → KPIs đạt được). Tổng hợp Worklog.
* **Nguyễn Duy Thái (Tech Lead):** Deploy Backend FastAPI + ChromaDB lên Render.com. Cấu hình environment variables.
* **Sẻ Thế Hưng (Dev Lead):** Deploy Frontend lên Vercel, cấu hình CORS, kiểm tra Live URL hoạt động.

---

## 🏗️ Kiến trúc Thuật toán — Tóm tắt

```
User Query (Kỹ thuật viên ĐLPP)
    │
    ▼
[Layer 1: Query Rewriter] ── dict + regex (< 5ms)
    │
    ▼
[Layer 2: Trie Classifier] ── keyword tree matching
    │ match >= 0.85? YES ────────────────────────► [Route to Skill]
    │ NO
    ▼
[Layer 3: Embedding Classifier] ── MiniLM cosine sim
    │ similarity >= 0.60? YES ───────────────────► [Route to Skill]
    │ NO
    ▼
[Layer 4: LLM Fallback] ── Gemini Flash mini prompt (~3%)
    │
    ▼
[Route to Skill]
    ├── WORKFLOW     → Onboarding Checklist Node (buoc 1→5)
    ├── RAG_POLICY   → ChromaDB (RBAC filter) → LLM Generate + Citations
    ├── ERROR_LOOKUP → Exact match regex → Semantic fallback → Checklist + ⚠️
    └── STATIC_FORM  → Form Payload (auto-fill context chat)
```

---

## 📊 KPIs Tracking Table

| KPI | Target | Do lan dau | Do lan cuoi |
| :--- | :--- | :--- | :--- |
| Router accuracy | ≥ 90% | Ngày 3 | Ngày 7 |
| Router latency (Trie path) | < 10ms | Ngày 3 | Ngày 7 |
| Router latency (Embedding path) | < 80ms | Ngày 3 | Ngày 7 |
| End-to-end latency | < 1.5s | Ngày 6 | Ngày 7 |
| RAG citation rate | 100% | Ngày 4 | Ngày 7 |
| Token savings vs. LLM router | ≥ 60% | Ngày 6 | Ngày 7 |
| Error Lookup exact match | < 200ms | Ngày 5 | Ngày 7 |
| Static Form submit time | < 30s | Ngày 5 | Ngày 7 |
| Onboarding completion (DLPP tech) | ≥ 85% | Ngày 6 | Ngày 7 |

---

## ⚠️ Risk Register

| Rủi ro | Mức độ | Kế hoạch dự phòng |
| :--- | :--- | :--- |
| Thiếu tài liệu kỹ thuật ĐLPP thực | Cao | Dùng tài liệu synthetic có cấu trúc tương tự thực tế |
| Embedding model tiếng Việt kém accuracy | Trung bình | Mở rộng từ điển Trie; tăng LLM fallback budget nhẹ |
| ChromaDB không ổn định khi deploy | Trung bình | Backup FAISS local hoặc Qdrant Cloud free tier |
| Latency > 1.5s trên server Render free | Thấp | Cache top-50 queries phổ biến; pre-compute prototypes |
