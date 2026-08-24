# 📋 BÁO CÁO TỔNG KẾT CÔNG VIỆC — 22/08/2026

**Người thực hiện:** Tiến Hưng
**Dự án:** VinFast Dealership Onboarding & Operational AI Assistant (P223)
**Nhánh:** `develop` | **Commit cuối:** `ebd662d`

---

## I. TỔNG QUAN

Hôm nay hoàn thành **7 hạng mục** trải đều sáng và chiều:

| # | Hạng mục | Trạng thái |
|:---:|:---|:---:|
| 1 | Video Player + Chapter Markers + Auto-seek | ✅ Done |
| 2 | Cải thiện Prompt tổng hợp LLM cho video & đa nguồn | ✅ Done |
| 3 | Feedback Widget + SQLite Feedback Loop | ✅ Done |
| 4 | Framework Retrieval Debugger (`retrieval_debugger/`) | ✅ Done |
| 5 | **Rebuild ChromaDB + BM25** (fix lỗi index gap nghiêm trọng) | ✅ Done |
| 6 | **Mở rộng Ground Truth**: 7 → 52 câu hỏi, fix GT004 | ✅ Done |
| 7 | **Setup RAGAS Evaluation Framework** (`eval/ragas_baseline.py`) | ✅ Done |

---
                                HỆ THỐNG ĐÁNH GIÁ & GIÁM SÁT (EVAL & OBSERVABILITY)
 ┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │ 1. RETRIEVAL DEBUGGER (Đo tầng Tìm kiếm Chunk)  │  2. RAGAS (Đo chất lượng RAG Triad 3 tiêu chí)        │
 │    - Tool: python retrieval_debugger/run_debug.py│     - Tool: python eval/ragas_baseline.py            │
 │    - Dashboard: retrieval_debugger/reports/*.md  │     - Report: eval/results/ragas_*.json              │
 ├──────────────────────────────────────────────────┼─────────────────────────────────────────────────────┤
 │ 3. LANGFUSE (Giám sát Realtime & Tracing UI)     │  4. BRAINTRUST (Benchmark & Chấm điểm Cloud)         │
 │    - UI: http://localhost:3000                   │     - Web Cloud: https://www.braintrust.dev         │
 │    - Xem: Latency, Token tốn, Logs từng lượt chat│     - Tool: python eval/braintrust_eval.py           │
 └────────────────────────────────────────────────────────────────────────────────────────────────────────┘


## II. CHI TIẾT CÁC HẠNG MỤC

### 1. Video Player với Chapter Markers & Rerank Scores

**Lý do:** Hệ thống trước đây chỉ trả lời văn bản thô, không cho xem video trực tiếp hay tự động nhảy đến đúng phân đoạn chứa câu trả lời.

**Đã làm:**
- **Frontend** — `VideoSourcePlayer.tsx`: nạp video qua JWT Blob URL, timeline chapter marker đổi màu theo `rerank_score`, auto-seek đến mốc liên quan nhất, click để nhảy, Fullscreen 90vh.
- **Backend** — `rag_node.py`: thêm `_parse_timestamp_to_seconds()`, trích xuất `content_type`, `source_path`, `timestamp_seconds`.
- **Fix** — `src/api/routes.py`: endpoint `/chat` thiếu truyền metadata video khi khởi tạo `RetrievedDocInfo`.

---

### 2. Cải thiện Prompt Tổng hợp LLM

**Lý do:** LLM hay liệt kê timestamp rời rạc (`[01:47]... | [01:00]...`) thay vì hướng dẫn mạch lạc từng bước.

**Đã làm:** Cập nhật System Prompt trong `rag_node.py` — bắt buộc LLM tổng hợp transcript video thành các bước tuần tự và tổng hợp theo chủ đề khi có nhiều nguồn.

---

### 3. Feedback Widget & Feedback Loop (Human-in-the-Loop)

**Lý do:** Cần tín hiệu đánh giá người dùng thực (↑/−/↓) để cải thiện RAG threshold, prompt và phát hiện tài liệu còn thiếu.

**Đã làm:**
- **DB** — `models.py`: thêm bảng `chat_feedback` + enum `FeedbackRating`.
- **API** — `feedback_routes.py`: `POST /api/v1/feedback` (lưu đánh giá) + `GET /api/v1/feedback/stats` (thống kê cho Manager).
- **Frontend** — `FeedbackWidget.tsx`: 3 nút đánh giá, hiệu ứng chọn, thông báo cảm ơn, tích hợp vào `ChatWidget.tsx`.

---

### 4. Framework Retrieval Debugger (`retrieval_debugger/`)

**Lý do:** Cần công cụ tự động chẩn đoán lỗi tìm kiếm (Embedding, BM25, RBAC, Reranker, LLM context) mà không cần kiểm tra thủ công.

**Đã làm:** Xây dựng trọn bộ `retrieval_debugger/`:
- `ground_truth.json` — tập câu hỏi chuẩn theo vai trò
- `canary_tester.py` — Unique Canary Test, tự dọn sạch sau khi chạy
- `diagnostics.py` — tự suy luận nguyên nhân (HIT_TOP_1 / MISSED / RERANKER_DROPPED / LLM_IGNORED_CONTEXT...)
- `reporter.py` — xuất console + lưu Markdown/JSON vào `reports/`
- `run_debug.py` + `run_debug.bat` — CLI đa chế độ, 1-click Windows

---

### 5. Rebuild ChromaDB + BM25 (Fix Index Gap nghiêm trọng)

**Lý do (phát hiện chiều):** Audit script phát hiện 62 file JSON (1259 chunks) đã processed nhưng **chưa bao giờ được index vào ChromaDB** — chatbot thiếu ~70% kiến thức mới. Báo cáo 100% Top-1 buổi sáng là con số giả vì dataset test quá nhỏ và Ground Truth sai.

**Đã làm:**
- Chạy `python scripts/rebuild_vector_db.py` — xóa sạch data cũ, embed lại toàn bộ 1259 chunks với BAAI/bge-m3 (1024 dims) trên CUDA.
- Hoàn thành trong **1.8 phút**.
- Kết quả: ChromaDB ✅ 1259 chunks | BM25 ✅ 1259 chunks

---

### 6. Mở rộng Ground Truth: 7 → 52 câu hỏi

**Lý do:** 7 câu không đủ đại diện thống kê. GT004 khai báo sai `expected_document_id`. Thiếu negative test cases để phát hiện false positive.

**Đã làm:**
- Viết 52 câu hỏi thực tế (`retrieval_debugger/ground_truth.json`):
  - 50 câu domain: accounting (22), sales (9), technician (7), general (7)
  - 2 câu OOD: NEG001 (VF9 ô tô — ngoài scope), NEG002 (xe đạp điện hãng khác)
- Fix GT004: `expected_document_id` → `KETO001_vf_hdsd_luong_claim_bu_ton_cho_xmd_v1_0`
- Thêm `scripts/generate_ground_truth.py` để sinh candidate GT bán tự động.

---

### 7. Setup RAGAS Evaluation Framework

**Lý do:** `retrieval_debugger/` chỉ đo Retrieval layer. Cần đo Generation quality để biết LLM có hallucinate không, câu trả lời có đúng câu hỏi không.

**Đã làm:**
- Cài `ragas==0.1.21`, thêm vào `requirements.txt`.
- Tạo `eval/ragas_baseline.py` — đo 3 metrics với target cụ thể:

  | Metric | Ý nghĩa | Target |
  |:---|:---|:---:|
  | Context Precision | Tỷ lệ chunk retrieved thực sự có ích | > 0.70 |
  | Faithfulness | LLM có bịa thêm ngoài context không | > 0.85 |
  | Answer Relevancy | Câu trả lời có đúng câu hỏi không | > 0.80 |

- Lưu kết quả JSON timestamp vào `eval/results/`.

---

## III. KẾT QUẢ KIỂM THỬ

### Retrieval Baseline (sau khi rebuild — số liệu thật):

```
Dataset     : 52 GT cases + CANARY (54 tests tổng)
Top-1 Hit   : 36/54 = 66.7%
Top-K Hit   : 48/54 = 88.9%
Missed      :  6/54 = 11.1%
```

**Phân tích lỗi:**

| Loại lỗi | Số case | Cases cụ thể |
|:---|:---:|:---|
| RERANKER_DROPPED_DOCUMENT | 3 | GT007, GT033, GT037 |
| RETRIEVAL_OR_INDEXING_FAILURE | 3 | CANARY_01×2, GT031, GT034 |
| SUBOPTIMAL_RANKING (Top-K không phải Top-1) | 12 | GT010-016, GT019, GT021, GT023, GT027, GT036, GT047, GT049 |

### Unit Tests & Linter:

```
pytest          : 139/139 PASSED
ruff format     : 90 files formatted ✅  (fix CI)
ruff check      : All checks passed ✅
npm run build   : TypeScript + Vite OK ✅
```

---

## IV. LỖI & TỒN ĐỌNG

### Lỗi đang mắc phải:

| # | Lỗi | Mức độ | Hướng xử lý |
|:---:|:---|:---:|:---|
| 1 | **Reranker quá aggressive** — GT007, GT033, GT037 bị lọc mất chunk đúng | 🔴 High | Giảm `min_score` threshold trong `hybrid_search.py` |
| 2 | **CANARY_01 chạy 2 lần** — 1 lần HIT, 1 lần MISS — bug trong `run_debug.py` | 🟡 Med | Debug runner loop trong `run_debug.py` |
| 3 | **RAGAS chưa chạy được** — conflict `langchain-core 0.2.43` vs `>=0.3` cần bởi ragas | 🟡 Med | Upgrade `langchain-core` hoặc tạo venv riêng |
| 4 | **Feedback Analytics chưa có UI** — data đang thu thập nhưng không có trang xem | 🟢 Low | Build dashboard (Sprint tiếp theo) |

### Sprint tiếp theo:

- [ ] Fix reranker threshold → mục tiêu Top-1 > 80%
- [ ] Resolve langchain-core conflict → chạy RAGAS baseline lần đầu
- [ ] CANARY_01 duplicate bug fix trong `run_debug.py`
- [ ] Build Feedback Analytics dashboard
- [ ] HybridSearch alpha tuning (BM25/Vector weight)
