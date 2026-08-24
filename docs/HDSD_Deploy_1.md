# 📖 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG — Deploy v1.0
> **Dự án:** VinFast Dealership Onboarding & Operational AI Assistant (P-223)  
> **Nhánh:** `deploy` | **Ngày cập nhật:** 23/08/2026

---

## I. TÓM TẮT ĐỀ TÀI

### Mô Tả Chung
Hệ thống hỗ trợ quy trình **onboarding nhân viên đại lý VinFast** thông qua 2 track chính:

| Track | Tên | Mô tả |
|-------|-----|-------|
| **Track 1** | Lộ Trình Đào Tạo | Giao diện học tập theo module, theo dõi tiến độ, quiz trắc nghiệm, quản lý tài liệu MinIO |
| **Track 2** | AI Chatbot RAG | Chatbot AI trả lời câu hỏi nghiệp vụ từ tài liệu nội bộ (ChromaDB + BM25 + LLM) |

### Hệ Thống Phân Quyền (5 Role)

| Role | Quyền | Giao diện mặc định |
|------|-------|-------------------|
| `vinfast` | Upload/xoá tài liệu, xem support ticket, kích hoạt cập nhật chatbot | `/files` |
| `owner` | Xem tiến độ toàn đại lý, mời nhân viên | `/progress` |
| `manager` | Xem tiến độ team | `/progress` |
| `sale` / `accountant` / `technician` | Học tập, sử dụng chatbot, gửi support ticket | `/onboarding` |

### Kiến Trúc Hệ Thống

```
Frontend (React/Vite) ←→ Backend (FastAPI) ←→ PostgreSQL (users, progress, tickets)
                                          ←→ MinIO (file storage)
                                          ←→ ChromaDB (vector search)
                                          ←→ BM25 Index (keyword search)
                                          ←→ LLM (OpenRouter/Gemini)
```

---

## II. CÁCH KHỞI ĐỘNG

### Yêu Cầu

| Thành phần | Phiên bản | Ghi chú |
|-----------|----------|---------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| PostgreSQL | 14+ | Chạy local hoặc cloud |
| MinIO | Latest | `docker run minio/minio` |
| CUDA (tuỳ chọn) | 11.8+ | Tăng tốc embedding |

### Bước 1 — Cài đặt môi trường

```bash
# Clone và tạo virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux

# Cài dependencies
pip install -e ".[dev]"
```

### Bước 2 — Cấu hình biến môi trường

```bash
# Copy file mẫu
cp .env.example .env
```

Cần điền các giá trị trong `.env`:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/vinfast_onboarding

# MinIO
AWS_S3_ENDPOINT_URL=http://localhost:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET_NAME=vinfast-onboarding

# LLM
OPENROUTER_API_KEY=sk-or-...          # Primary
GEMINI_API_KEY=AIza...                # Fallback

# Eval (tuỳ chọn)
LANGFUSE_SECRET_KEY=sk-lf-...
BRAINTRUST_API_KEY=sk-...
```

### Bước 3 — Khởi động MinIO

```bash
docker run -d -p 9000:9000 -p 9001:9001 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"
```

Truy cập MinIO Console: http://localhost:9001 (tạo bucket `vinfast-onboarding`)

### Bước 4 — Khởi động Backend

```bash
uvicorn main:app --reload --port 8000
```

Khi khởi động lần đầu, hệ thống tự động:
- Tạo bảng DB và sync enum PostgreSQL
- Seed 6 tài khoản demo (xem bên dưới)
- Seed onboarding steps theo catalog

### Bước 5 — Khởi động Frontend

```bash
cd frontend
npm install
npm run dev   # Dev server: http://localhost:5173
```

> **Lưu ý production:** `npm run build` → phục vụ `dist/` qua Nginx/FastAPI static

### Tài Khoản Demo Mặc Định

| Email | Mật khẩu | Role | Ghi chú |
|-------|----------|------|---------|
| `vinfast@vinfast.vn` | `12345678` | `vinfast` | Quản lý tài liệu |
| `thehung@vinfast.vn` | `12345678` | `owner` | Chủ đại lý HN |
| `quanly@vinfast.vn` | `12345678` | `manager` | Quản lý |
| `sales@vinfast.vn` | `12345678` | `sale` | Nhân viên Sales |
| `ketoan@vinfast.vn` | `12345678` | `accountant` | Kế toán |
| `kythuat@vinfast.vn` | `12345678` | `technician` | Kỹ thuật viên |

### Bước 6 — Nạp Dữ Liệu Vào Chatbot (ChromaDB)

```bash
# Chạy pipeline ingestion (lần đầu hoặc khi có tài liệu mới)
python scripts/rag_ingestion_pipeline.py
```

> **Sau khi deploy:** VinFast có thể kích hoạt re-index từ giao diện — nút **"Cập nhật Chatbot"** trên trang Kho Tài Liệu.

---

## III. HƯỚNG DẪN VẬN HÀNH CHO VINFAST

### Upload Tài Liệu Mới

1. Đăng nhập bằng tài khoản `vinfast@vinfast.vn`
2. Vào menu **"Tài liệu"** (icon Upload trên sidebar)
3. Điều hướng vào đúng thư mục (vd: `KeToan/`, `Sale/`, `General_doc/`)
4. Chọn **"Vai trò nhận tài liệu"** trong dropdown:
   - 🤖 **Tự động** — hệ thống đoán từ tên thư mục (mặc định)
   - 📢 **Tất cả nhân viên** — tất cả đều học được
   - 💼 **Kế toán** / 🚗 **Sales** / 🔧 **Kỹ thuật viên** / 👔 **Quản lý**
5. Nhấn **"Tải lên"** — chọn 1 hoặc nhiều file cùng lúc (PDF/DOCX/MP4)
6. Chờ kết quả upload. Nếu file trùng tên, hệ thống hỏi xác nhận ghi đè
7. Hệ thống tự động **cập nhật chatbot** sau khi upload thành công

### Xoá Tài Liệu

1. Tìm file trong danh sách → nhấn icon 🗑️ (màu đỏ)
2. Xác nhận trong popup → file bị xoá khỏi MinIO và lộ trình học
3. Chatbot tự động được cập nhật

### Xem Support Ticket

1. Vào menu **"Support"** trên sidebar
2. Xem danh sách ticket từ nhân viên
3. Nhấn để đánh dấu đã đọc

---

## IV. KẾT QUẢ KIỂM THỬ (22/08/2026)

### Retrieval Accuracy (Ground Truth: 54 test cases)

| Chỉ số | Số lượng | Tỷ lệ | Đánh giá |
|--------|---------|-------|---------|
| **Top-1 Chính xác** | 37/54 | **68.5%** | 🟡 Đang cải thiện |
| **Top-K Chính xác** | 48/54 | **88.9%** | 🟢 Tốt |
| **Bị bỏ sót** | 6/54 | **11.1%** | 🔴 Cần fix |

**Phân tích lỗi chi tiết:**

| Loại lỗi | Số case | Nguyên nhân |
|----------|---------|-------------|
| Reranker loại nhầm chunk đúng | 3 | `min_score` threshold quá cao |
| Retrieval/Index thất bại | 3 | CANARY duplicate bug + 2 GT gap |
| Top-K đúng nhưng không đứng Top-1 | 12 | BM25/Vector weight chưa tối ưu |

### Unit Tests

```
pytest tests/          : 29/29 PASSED ✅  (API routes + ingestion)
ruff check src/        : 0 errors ✅
TypeScript build       : OK ✅
```

### ChromaDB Index

```
Tổng chunks : 1259
Embedding   : BAAI/bge-m3 (1024 dims)
Thời gian rebuild : ~1.8 phút (với CUDA)
```

---

## V. CÁC SCRIPTS QUAN TRỌNG

| Script | Mục đích | Cách chạy |
|--------|----------|----------|
| `scripts/rag_ingestion_pipeline.py` | Rebuild ChromaDB + BM25 từ markdown | `python scripts/rag_ingestion_pipeline.py` |
| `scripts/rebuild_vector_db.py` | Reset hoàn toàn ChromaDB | `python scripts/rebuild_vector_db.py` |
| `retrieval_debugger/run_debug.py` | Đo chất lượng retrieval | `python retrieval_debugger/run_debug.py` |
| `eval/braintrust_eval.py` | Benchmark cloud (Braintrust) | `python eval/braintrust_eval.py` |
| `eval/ragas_baseline.py` | Đo chất lượng RAG (RAGAS) | `python eval/ragas_baseline.py` |

---

## VI. LỖI TỒN ĐỌNG & KẾ HOẠCH

### Lỗi Đang Tồn Tại

| # | Lỗi | Mức Độ | Hướng Xử Lý |
|---|-----|--------|-------------|
| 1 | Reranker quá aggressive (GT007, GT033, GT037 bị lọc nhầm) | 🔴 High | Giảm `min_score` trong `hybrid_search.py` |
| 2 | CANARY_01 chạy duplicate | 🟡 Med | Debug runner loop trong `run_debug.py` |
| 3 | RAGAS conflict `langchain-core` version | 🟡 Med | Upgrade hoặc tạo venv riêng |
| 4 | Feedback Analytics chưa có UI dashboard | 🟢 Low | Sprint tiếp theo |

### Sprint Tiếp Theo

- [ ] Fix reranker threshold → Top-1 > 80%
- [ ] Resolve langchain-core conflict → RAGAS baseline
- [ ] CANARY_01 bug fix
- [ ] Feedback Analytics dashboard
- [ ] HybridSearch alpha tuning (BM25/Vector weight)

---

## VII. TÀI LIỆU LIÊN QUAN

| Tài liệu | Mô tả |
|----------|-------|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Kiến trúc toàn hệ thống |
| [`DATAFLOW_AND_ROLE_MAPPING.md`](DATAFLOW_AND_ROLE_MAPPING.md) | Luồng dữ liệu và phân quyền |
| [`HANDOFF.md`](HANDOFF.md) | Tài liệu bàn giao kỹ thuật |
| [`HDSD_connection.md`](HDSD_connection.md) | Hướng dẫn kết nối dịch vụ |
| [`HDSD_input.md`](HDSD_input.md) | Hướng dẫn nhập liệu và pipeline |
| [`TienHung_summary_22_08.md`](TienHung_summary_22_08.md) | Báo cáo công việc 22/08/2026 |
| [`document_21-8.md`](document_21-8.md) | Nhật ký phát triển 21/08/2026 |
| [`guide/troubleshooting.md`](guide/troubleshooting.md) | Xử lý lỗi thường gặp |

---

> **Lưu ý:** Tài liệu này được cập nhật tự động sau mỗi sprint. Phiên bản hiện tại: `deploy v1.0` — nhánh `deploy` (merge `develop` + `develop_4`).
