# Nhật ký Phát triển & Tổng hợp Kỹ thuật - Ngày 21/08/2026

Tài liệu này đóng vai trò như một cuốn logbook để ghi nhận lại toàn bộ tiến trình công việc, các lỗi đã xử lý, cũng như các thảo luận thiết kế và giải pháp kỹ thuật đã triển khai trong ngày hôm nay.

---

## 1. Hợp nhất nhánh làm việc (Git Merge & Backup) - 14:45

### Mô tả công việc:
- **Tình trạng:** Nhánh `develop` đã được thành viên khác cập nhật với các tính năng mới (Pipeline Ingestion RAG cho Chatbot, cài đặt ChromaDB, Format code với Ruff). Trong khi đó, tính năng quản lý MinIO và Lộ trình (Catalog Sync) đang nằm ở nhánh `develop_3`.
- **Thực thi:**
  1. Đẩy mã nguồn nhánh `develop_3` lên một nhánh backup mang tên `TheHung-backup-work` để bảo vệ thành quả.
  2. Kéo (fetch & pull) nhánh `develop` mới nhất về máy local.
  3. Tạo nhánh `develop_4` và tiến hành merge (hòa trộn) nhánh `develop_3` vào `develop_4`.
- **Khắc phục xung đột (Merge Conflicts):**
  - Xảy ra xung đột lớn tại khoảng 15 file do sự khác biệt giữa code đã format (bởi Ruff) và code logic S3 chưa format.
  - Sử dụng chiến lược merge thủ công: Giữ lại toàn bộ logic phức tạp của cơ chế S3 (regex tìm version, auto-resolve URL, secondary sort) và hòa trộn an toàn với tính năng RAG Node mới.
- **Kết quả:** Đã đẩy nhánh hội tụ `develop_4` lên GitHub. Đây là bản code hoàn chỉnh tích hợp cả Chatbot (Track 2) và S3 Quản lý File (Track 1).

---

## 2. Phân tích & Thảo luận: Kiến trúc RAG Ingestion Pipeline (Track 2) - 15:20

### Bối cảnh:
Thảo luận và tìm hiểu về phần việc của đồng đội ở Track 2 liên quan đến việc xử lý dữ liệu thô cho Chatbot AI.

### Phân tích luồng xử lý dữ liệu (Data Pipeline):
1. **Nguồn Input (Dữ liệu đầu vào):**
   - Các tài liệu gốc (PDF, PPTX, DOCX...) được nạp từ `data/raw/` (hoặc MinIO).
   - Hỗ trợ xử lý các file văn bản và slide phức tạp.

2. **Dây chuyền xử lý 5 bước nghiêm ngặt:**
   - **Validation & Security Scan:** Kiểm tra định dạng và quét mã độc (Auto-Reject nếu có rủi ro).
   - **PII Scan (Bảo vệ dữ liệu cá nhân):** Quét thông tin nhạy cảm (Tên, SĐT, Căn cước...). Tự động che giấu (Masking) hoặc báo cờ yêu cầu con người duyệt (HITL).
   - **Extraction & OCR:** Sử dụng **Google Gemini Vision API** (`--gemini-ocr`) để nhận diện hình ảnh/slide phức tạp.
   - **Chunking:** Cắt nhỏ văn bản thành các đoạn (chunks) để Chatbot dễ hiểu.
   - **Embedding:** Mã hóa các chunk thành dạng Vector (bằng SentenceTransformer).

3. **Output (Kho chứa dữ liệu):**
   - **File tĩnh (`data/processed/`):** File Markdown làm sạch, Metadata, và báo cáo PII.
   - **Kho Vector (ChromaDB - `data/chroma/`):** Lưu trữ vector, phục vụ **Semantic Search (Tìm kiếm ngữ nghĩa)**.
   - **Kho Từ khóa (BM25 Index - `data/raw/bm25_index.pkl`):** Lưu trữ từ điển, phục vụ **Keyword Search (Tìm kiếm chính xác)**.

4. **Cách Chatbot tận dụng dữ liệu (Tại `rag_node.py`):**
   - Khi có câu hỏi, hệ thống dùng **Hybrid Search** (kết hợp cả ChromaDB và BM25) để lấy ra 10 đoạn liên quan nhất.
   - Chạy qua **Reranker (CrossEncoder)** để chấm điểm lại, chọn ra 3 đoạn xuất sắc nhất rồi mới đưa cho LLM tổng hợp thành câu trả lời.

---

*(Các cập nhật tiếp theo trong ngày sẽ được bổ sung liên tục bên dưới...)*

### 21-8-2026: Sửa lỗi luồng Delete/Upload trên nhánh `develop_4`
- **Vấn đề Delete File**:
  - Khi VinFast admin thực hiện xoá file, API `/delete` trong `s3_manager_routes.py` sẽ thực hiện `db.delete(step)`. Tuy nhiên, vì các step này đã được user hoàn thành (`UserStepProgress`, `PendingUpdate`), Postgres Database báo lỗi `IntegrityError` (vi phạm khoá ngoại) và API trả về HTTP 500 lỗi. Do đó giao diện báo "Lỗi khi xoá file".
  - **Khắc phục**: Trước khi xoá `step`, thực hiện rà soát và xoá toàn bộ `UserStepProgress` và `PendingUpdate` có chứa `step_id` tương ứng bằng lệnh query xoá. Đảm bảo toàn vẹn dữ liệu.

- **Vấn đề Upload File Mới Hoàn Toàn (Chưa có trong Catalog)**:
  - Khi VinFast admin upload 1 file mới không có trong danh sách chuẩn, LLM (`generate_quiz_and_match_step`) thường nhầm lẫn và map vào `step_id: 1` của Module 1, thay vì tạo mới (`step_id: 0`). Do đó file bị gộp chung vào "Section 1" thay vì thành một Section mới riêng biệt.
  - **Khắc phục**: Ghi đè logic của LLM bằng cách ép `is_new_step = True` (Luôn luôn tạo Step/Section mới cho file chưa từng tồn tại). Đồng thời phân bổ giá trị `order` sao cho step mới được gán đúng Module:
    - Nếu folder đích là `General_doc`, `order = 1` (Tự động vào cuối Module 1).
    - Các folder chuyên môn (như `KeToan`, `Sale`, v.v.), `order = max_order + 1` (Tự động vào cuối Module 3).

- **Vấn đề Hiển thị file rác (Orphaned AI Steps)**:
  - Do lỗi Delete File ở trên (báo 500 lỗi khoá ngoại), dù file đã bị xoá khỏi MinIO thành công nhưng bài học (step) vẫn chưa được xoá khỏi cơ sở dữ liệu (do rollback). Hậu quả là UI của học viên vẫn hiển thị bài học đó nhưng không có file thật. Lỗi này đặc biệt nghiêm trọng với các bài học do AI sinh ra (`content_version = "AI_GENERATED"`) vì chúng không đi qua bước kiểm tra tồn tại file (`s3_service.object_exists`) của luồng `seed_onboarding_steps` dành cho Catalog chuẩn.
  - **Khắc phục**: Đã bổ sung thêm cơ chế "tự phục hồi" (self-healing) vào `src/db/crud.py` (hàm `seed_onboarding_steps`). Cơ chế này sẽ quét qua toàn bộ các bài học AI-generated, kiểm tra xem file vật lý của chúng trên MinIO còn tồn tại không. Nếu không tồn tại (do bị xoá bằng tay hoặc do lỗi cũ), hệ thống sẽ tự động dọn dẹp và xoá bỏ bài học mồ côi này khỏi Database. Đảm bảo UI luôn sạch sẽ và đồng bộ 100% với MinIO.
