# Retrieval Testing & Debugging Framework cho Chatbot AI VinFast

Bộ công cụ chuyên dụng giúp kiểm thử, chẩn đoán và khoanh vùng chính xác các lỗi trong khâu truy xuất tài liệu (Retrieval & Reranking) và tổng hợp câu trả lời (LLM Generation) của hệ thống Chatbot VinFast AI Onboarding.

---

## 1. Mục tiêu
1. **Xác định chính xác chất lượng truy xuất**: Đánh giá xem câu hỏi người dùng có tìm ra đúng tài liệu chứa câu trả lời trong cơ sở dữ liệu (ChromaDB + BM25) hay không.
2. **Khoanh vùng nguyên nhân gốc (Root Cause Analysis)**:
   - Lỗi do Vector Embedding không khớp ngữ nghĩa?
   - Lỗi do BM25 Keyword Search thiếu từ khóa?
   - Lỗi do Phân quyền RBAC (Role Filtering) vô tình chặn tài liệu?
   - Lỗi do Cross-Encoder Reranker loại bỏ tài liệu đúng?
   - Lỗi do Prompt hoặc LLM không tận dụng thông tin trong Context?
3. **Unique Test (Canary Document)**: Kiểm tra nhanh tính toàn vẹn của toàn bộ pipeline bằng một tài liệu chứa mã bí mật (`XKCD-98765-VINFAST-CANARY`) được nạp và tự động dọn sạch.

---

## 2. Cấu trúc Thư mục

```
retrieval_debugger/
├── ground_truth.json       # Tập câu hỏi chuẩn & danh sách tài liệu mong đợi
├── canary_tester.py        # Logic nạp, kiểm thử và dọn dẹp Canary Document
├── logger.py               # Thu thập log có cấu trúc theo correlation_id
├── diagnostics.py          # Engine chẩn đoán nguyên nhân lỗi và đưa ra giải pháp
├── reporter.py             # Xuất bảng Console, file Markdown (.md) và JSON (.json)
├── run_debug.py            # CLI Runner chính hỗ trợ nhiều tham số
├── run_debug.bat           # File batch 1-click chạy trên Windows
├── README.md               # Tài liệu hướng dẫn sử dụng
└── reports/                # Thư mục lưu trữ các báo cáo sau mỗi lần chạy
```

---

## 3. Hướng dẫn Sử dụng

### Cách 1: Click đúp file Batch (Windows)
Chạy file `retrieval_debugger/run_debug.bat` và chọn menu tương tác:
- `1`: Chạy toàn bộ (Canary Test + Ground Truth End-to-End với LLM)
- `2`: Chạy nhanh (Retrieval-Only, không gọi LLM, 0 token cost)
- `3`: Chỉ chạy Unique Canary Test
- `4`: Nhập câu hỏi tùy chỉnh để debug ngay tại chỗ

### Cách 2: Chạy qua Terminal CLI

```bash
# 1. Chạy nhanh chỉ kiểm tra bước truy xuất (Retrieval-Only)
python retrieval_debugger/run_debug.py --retrieval-only

# 2. Chạy toàn bộ End-to-End với LLM
python retrieval_debugger/run_debug.py

# 3. Chỉ chạy Unique Canary Test
python retrieval_debugger/run_debug.py --canary-only

# 4. Debug cho một câu hỏi cụ thể theo vai trò
python retrieval_debugger/run_debug.py --query "Làm thế nào để đăng nhập hệ thống DMS?" --role accounting

# 5. Tùy chỉnh Top K
python retrieval_debugger/run_debug.py --top-k 3
```

---

## 4. Bảng Phân tích & Hướng dẫn Khắc phục Lỗi

| Hiện tượng | Nguyên nhân có thể | Hướng khắc phục |
| :--- | :--- | :--- |
| **MISSED** (Không xuất hiện trong kết quả) | - Tài liệu chưa được index vào ChromaDB / BM25.<br>- Vector embedding không bắt được ngữ nghĩa câu hỏi.<br>- Phân quyền RBAC (Role) lọc mất tài liệu. | - Kiểm tra pipeline ingest và index lại tài liệu.<br>- Bổ sung từ khóa / từ đồng nghĩa vào câu query.<br>- Kiểm tra metadata `role` của chunk so với `access_scope`. |
| **RERANKER_DROPPED** (Có trong ứng viên ban đầu nhưng trượt Top K) | - Điểm Cross-Encoder logit score quá thấp.<br>- `min_score_threshold` đặt quá cao. | - Điều chỉnh `min_score_threshold` trong `config.yaml`.<br>- Tăng số lượng candidate lấy từ Hybrid Retriever (`top_k * 3`). |
| **SUBOPTIMAL_RANKING** (Nằm trong Top K nhưng chưa đạt Top 1) | - Trọng số RRF giữa Vector và BM25 chưa tối ưu.<br>- Reranker bị nhiễu bởi các đoạn văn bản tương tự. | - Tinh chỉnh `vector_weight` và `bm25_weight` trong `HybridRetriever`. |
| **LLM_IGNORED_CONTEXT** (Top 1 đúng nhưng LLM trả lời sai) | - LLM bị ảo giác (hallucination) hoặc bỏ qua context.<br>- Prompt chưa đủ chặt chẽ. | - Cập nhật System Prompt với quy tắc trích dẫn bắt buộc.<br>- Giảm `temperature` của LLM xuống 0.0 - 0.2. |

---

## 5. Định dạng Log chuẩn (JSON Correlation Log)

Mỗi lần chạy sẽ tạo ra file `reports/debug_logs_<timestamp>.json` chứa nhật ký chi tiết:

```json
{
  "correlation_id": "8f673510-09a2-4a0b-967b-123456789abc",
  "timestamp": "2026-08-22T01:50:00Z",
  "step": "retrieval_and_generation",
  "input_query": "Làm thế nào để đăng nhập vào hệ thống DMS?",
  "processed_query": "Làm thế nào để đăng nhập vào hệ thống DMS?",
  "retrieval_results": [
    {
      "document_id": "01_huong_dan_dang_nhap_dms_chunk_1",
      "score": 8.42,
      "rank": 1,
      "title": "01 Huong Dan Dang Nhap Dms",
      "section": "01:47"
    }
  ],
  "selected_context": [
    "[01_huong_dan_dang_nhap_dms] Khi có thông báo tiếp tục, ấn nút đăng nhập..."
  ],
  "final_answer": "Để đăng nhập DMS: 1) Mở trình duyệt...",
  "diagnosis": {
    "status": "HIT_TOP_1",
    "hit_rank": 1,
    "root_cause": null,
    "recommendation": "Truy xuất chính xác tuyệt đối ở vị trí Top 1."
  }
}
```
