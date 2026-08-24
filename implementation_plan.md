# Kế Hoạch Cải Thiện Input Pipeline — P223

> **Cho ai đọc**: PM non-tech. Không cần hiểu code để đọc tài liệu này.  
> **Mục tiêu cuối**: Tăng điểm rerank từ 5-6 lên 7-8/10 bằng cách làm sạch đầu vào.

---

## 🎯 Tóm Tắt Vấn Đề Gốc Rễ

Hệ thống RAG hoạt động theo 3 bước nối tiếp:

```
File PDF/PPTX  →  [INPUT PIPELINE]  →  Chunks  →  [VECTOR DB]  →  [RAG / Rerank]
```

Nếu bước INPUT PIPELINE tạo ra chunks rác, thì dù Vector DB và RAG có tốt đến đâu, kết quả vẫn kém. **Đây là lý do điểm rerank chỉ đạt 5-6.**

---

## 🔴 Lỗi 1 — Bảng bị nhân 3 lần (Ưu tiên cao nhất)

### Hiện tại đang xảy ra gì?
File PDF (export từ PowerPoint) chứa bảng có **ô ghép (merged cells)**. Ví dụ ô "XMĐ" ghép qua 3 cột thành 1 ô to. Tool đang dùng (PyMuPDF) không hiểu ô ghép, nên nó in nội dung của ô đó 3 lần.

**Kết quả trong file Markdown:**
```
|XMĐ|XMĐ|XMĐ|Xe máy điện|Xe máy điện|Xe máy điện|
```
Thay vì phải là:
```
|XMĐ|Xe máy điện|
```

### Tại sao điều này phá hỏng RAG?
RAG nhìn vào chunk đó và "nghĩ" rằng từ "XMĐ" quan trọng gấp 3 lần thực tế, làm lệch trọng số vector embedding. Reranker sau đó chấm điểm thấp vì nội dung chunk không "thuần" và không khớp tốt với câu hỏi.

### Fix

**File thay đổi**: [`src/extract/pdf_extractor.py`](file:///d:/Classroom/Code/Codelabs/P223/src/extract/pdf_extractor.py)

**Chiến lược**: Cài thêm thư viện `pdfplumber` (miễn phí, không cần GPU), dùng nó thay PyMuPDF khi phát hiện trang có bảng. PyMuPDF vẫn làm việc bình thường với text thuần.

**Hậu xử lý thêm** (trong [`src/preprocess/markdown_normalizer.py`](file:///d:/Classroom/Code/Codelabs/P223/src/preprocess/markdown_normalizer.py)):
- Phát hiện và xóa cột trùng lặp trong bảng
- Sửa header rác (`Col1`, `Col2`, `Col3`) thành tên cột có nghĩa khi có thể
- Loại bỏ các ký tự HTML bị escape vô nghĩa (`&lt;br&gt;`) trong cell bảng

> [!IMPORTANT]
> Bước này ảnh hưởng tới mọi PDF trong hệ thống. Sau khi fix xong, cần chạy lại `rebuild_vector_db.py` để cập nhật toàn bộ chỉ mục.

---

## 🟡 Lỗi 2 — Ảnh chụp màn hình DMS đọc thiếu nội dung (Ưu tiên trung bình)

### Hiện tại đang xảy ra gì?
Ảnh chụp màn hình DMS (bảng dữ liệu phần mềm — nền xám, chữ nhỏ) bị bộ lọc OCR loại bỏ vì tương phản thấp. Hệ thống render ảnh ở 300 DPI — đủ cho OCR văn bản thông thường, nhưng chưa đủ cho ảnh màn hình DMS nhỏ.

### Fix

**File thay đổi**: [`src/extract/pdf_extractor.py`](file:///d:/Classroom/Code/Codelabs/P223/src/extract/pdf_extractor.py) — hàm `_ocr_page()`

**Chiến lược**: Tăng DPI render từ **300 lên 400** khi trang được phát hiện là ảnh màn hình. Ngưỡng lọc tương phản Tier-3 giảm từ 30.0 xuống 20.0 để giữ lại thêm vùng chữ trong ảnh DMS.

> [!NOTE]
> Theo yêu cầu của bạn, chúng ta **chấp nhận mất 60-70% nội dung ảnh DMS** vì caption text bên cạnh đã đủ để RAG hiểu bước thao tác. Fix này chỉ cải thiện thêm, không phải giải quyết hoàn toàn.

---

## 🟢 Cải Tiến 3 — Context Header trong Chunk giàu thông tin hơn (Ưu tiên trung bình)

### Hiện tại đang xảy ra gì?
Mỗi chunk được đóng gói với header như sau:
```
[Document: ... | Role: accounting | Source: ... | Page: 2 | Section: Page 2]
```
Header này thiếu 2 thông tin quan trọng:
1. **Loại nội dung** — đây là chunk bảng biểu hay đoạn văn? Reranker không phân biệt được.
2. **Section title thực sự** — "Page 2" không có ý nghĩa gì; đáng lẽ phải là "Quản lý phiên bản tài liệu" (tiêu đề thực của phần đó).

### Fix

**File thay đổi**: [`src/preprocess/structure_aware_chunker.py`](file:///d:/Classroom/Code/Codelabs/P223/src/preprocess/structure_aware_chunker.py) — hàm `_build_chunk()`

**Chiến lược**: Thêm trường `Content-Type` vào context header, và tách tiêu đề section thực sự từ bảng Markdown để ghi vào header thay vì "Page N".

**Kết quả kỳ vọng:**
```
[Document: VF HDSD Bán hàng XMĐ thuê Pin trả trước | Role: accounting | 
 Source: KeToan/... | Page: 2 | Section: Quản lý phiên bản tài liệu | 
 Content-Type: table | Language: vi]
```

---

## 🟢 Cải Tiến 4 — BM25 Table Boost (Ưu tiên thấp hơn)

### Hiện tại đang xảy ra gì?
BM25 (tìm kiếm từ khóa chính xác) không phân biệt chunk chứa bảng biểu chuẩn vs chunk văn bản thường. Bảng biểu thường chứa dữ liệu số và từ khóa nghiệp vụ mà người dùng hỏi thẳng, nên cần được ưu tiên hơn.

### Fix

**File thay đổi**: [`src/vectordb/hybrid_search.py`](file:///d:/Classroom/Code/Codelabs/P223/src/vectordb/hybrid_search.py)

**Chiến lược**: Khi chunk có chứa `|---|` (dấu hiệu bảng Markdown), cộng thêm boost `+0.15` vào RRF score.

---

## 📋 Thứ Tự Thực Hiện

| Bước | Việc cần làm | File | Ước lượng |
|------|-------------|------|-----------|
| 1 | Cài `pdfplumber` vào `.venv` | `requirements.txt` | 2 phút |
| 2 | Fix đọc bảng merged cells | `pdf_extractor.py` | 45 phút |
| 3 | Hậu xử lý bảng (xóa cột trùng, fix header rác, xóa HTML escape) | `markdown_normalizer.py` | 30 phút |
| 4 | Tăng DPI render OCR, giảm ngưỡng contrast | `pdf_extractor.py` | 15 phút |
| 5 | Cải thiện Context Header chunk | `structure_aware_chunker.py` | 20 phút |
| 6 | BM25 Table Boost | `hybrid_search.py` | 10 phút |
| 7 | Chạy lại Preprocessing trên file test | Script | 10 phút |
| 8 | Rebuild Vector DB | Script | 2 phút |
| 9 | Chạy full test suite để xác minh | pytest | 3 phút |

---

## 🔍 Câu Hỏi Mở Cần Xác Nhận

> [!IMPORTANT]
> **Scope fix**: Bước 1-4 sẽ ảnh hưởng đến **tất cả PDF/PPTX** trong hệ thống. Sau khi fix, cần preprocessing lại TẤT CẢ file và rebuild Vector DB. Bạn có muốn làm toàn bộ (batch) hay chỉ làm 1 file thử trước?

> [!NOTE]
> `pdfplumber` hoạt động tốt với PDF vector (export từ Word/PPT). Với ảnh DMS screenshot embed trong PDF, nó vẫn sẽ trả về text rỗng — phần này vẫn do OCR xử lý.

## ✅ Quyết Định Đã Thống Nhất

- ✅ Dùng `pdfplumber` + PyMuPDF fallback cho bảng
- ✅ Chạy `docling` local CPU (sẽ xem xét ở giai đoạn sau nếu cần)
- ✅ Tăng DPI render khi OCR ảnh PPTX
- ✅ Chấp nhận mất 60-70% nội dung ảnh DMS — không bắt buộc phải đọc hoàn toàn
- ✅ Cải thiện Context Header và BM25 Table Boost
