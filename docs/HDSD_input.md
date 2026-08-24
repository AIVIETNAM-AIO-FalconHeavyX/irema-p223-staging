# 📋 Tài Liệu Hướng Dẫn & Đặc Tả Hệ Thống RAG Data Input & Preprocessing Pipeline

> [!NOTE]
> **Mục tiêu hệ thống:** Chuyển đổi các tài liệu thô đa định dạng (PDF, DOCX, PPTX, XLSX, Video MP4) thành văn bản **Markdown sạch chuẩn hóa** (đã loại bỏ 100% PII nhạy cảm & khử nhiễu OCR 4 tầng) kèm **JSON Metadata**, thực hiện **Structure-Aware Chunking (400–800 tokens + 80 tokens overlap)**, **BM25 Tokenizer tiếng Việt (`underthesea`)** và nhúng vào **Vector Store (`BAAI/bge-m3` 1024 dims)**.

---

## 📑 Mục Lục
1. [Scope & Mục Tiêu Hệ Thống](#-1-scope--mục-tiêu-hệ-thống)
2. [Kiến Trúc Dòng Chảy Dữ Liệu (Data Pipeline Architecture)](#-2-kiến-trúc-dòng-chảy-dữ-liệu-data-pipeline-architecture)
3. [Cấu Trúc Thư Mục & Phân Quyền Tự Động (Role-Based Access)](#-3-cấu-trúc-thư-mục--phân-quyền-tự-động-role-based-access)
4. [Đặc Tả Kỹ Thuật Chi Tiết Từng Bước](#-4-đặc-tả-kỹ-thuật-chi-tiết-từng-bước)
   - 4.1. Trích xuất đa định dạng (Offline 3-Tier Extraction)
   - 4.2. Thuật toán sắp xếp thứ tự đọc OCR (Top-to-Bottom, Left-to-Right)
   - 4.3. Bộ lọc 4 tầng khử nhiễu OCR & Chuẩn hóa tên thương hiệu (4-Tier OCR Filter)
   - 4.4. Làm sạch & Chuẩn hóa cấu trúc Markdown (Text Cleaning & Normalization)
   - 4.5. Bảo mật PII 100% & Quét bảo mật tài liệu (Presidio + Regex VN + Security Scanner)
   - 4.6. Structure-Aware Chunking (400–800 tokens + Sliding Window Overlap)
   - 4.7. Embedding (`BAAI/bge-m3`) & BM25 Tokenizer (`underthesea`)
5. [Cấu Trúc Mã Nguồn (`src/`, `scripts/`, `data/`)](#-5-cấu-trúc-mã-nguồn-src-scripts-data)
6. [Cấu Hình Hệ Thống & Biến Môi Trường (`config.py` / `.env`)](#-6-cấu-hình-hệ-thống--biến-môi-trường-configpy--env)
7. [Hướng Dẫn Cài Đặt Môi Trường & Chạy Pipeline (CLI Commands)](#-7-hướng-dẫn-cài-đặt-môi-trường--chạy-pipeline-cli-commands)
8. [Kiểm Thử & Đánh Giá Chất Lượng (Benchmark & Tests)](#-8-kiểm-thử--đánh-giá-chất-lượng-benchmark--tests)
9. [Giao Diện Web UI Studio Đối Chiếu 3 Cột (Side-by-Side)](#-9-giao-diện-web-ui-studio-đối-chiếu-3-cột-side-by-side)
10. [Xử Lý Lỗi Thường Gặp (Troubleshooting)](#-10-xử-lý-lỗi-thường-gặp-troubleshooting)

---

## 🎯 1. Scope & Mục Tiêu Hệ Thống

### ✅ Trong Scope (Hệ thống thực hiện)
* **Tự động quét & phân quyền:** Quét đệ quy `data/raw/`, tự động gán `role` và `access_scope` theo thư mục phân cấp.
* **Trích xuất Offline 100%:** Trích xuất văn bản từ PDF, DOCX, PPTX, XLSX và Video (MP4) mà không phụ thuộc vào bất kỳ API thương mại trực tuyến nào (như OpenAI hay Google Gemini API).
* **Bảo toàn thứ tự đọc tự nhiên:** Tự động sắp xếp các khối văn bản/ảnh/chữ trong slide/PDF từ **Trên xuống Dưới, Trái qua Phải**.
* **Bộ lọc 4 tầng khử nhiễu OCR & Chuẩn hóa Brand:** Khử triệt để watermark, text mờ trong ảnh nền sự kiện/banner và tự động sửa các lỗi OCR tên thương hiệu (`VINFA$T` $\rightarrow$ `VINFAST`, `VinGr0up` $\rightarrow$ `VinGroup`, `DN1S` $\rightarrow$ `DMS`).
* **Xử lý âm thanh Video:** Transcribe video tiếng Việt kèm timestamp bằng `faster-whisper`.
* **Loại bỏ PII 100%:** Phát hiện và **xóa bỏ hoàn toàn** các thông tin nhạy cảm (SĐT, Email, CCCD, Tên cá nhân, Số tài khoản, Biển số xe, ID nhân viên/khách hàng,...).
* **Chunking bảo toàn cấu trúc:** Chia đoạn thông minh (400–800 tokens) giữ nguyên vẹn bảng biểu/danh sách, bổ sung 80 tokens overlap.
* **Hybrid Indexing:** Lập chỉ mục đồng thời cho **ChromaDB Vector Store** (`BAAI/bge-m3` 1024 dims) và **BM25 Keyword Index** (`underthesea`).

### ❌ Out of Scope
* Không gọi LLM sinh câu trả lời chat trực tiếp tại tầng tiền xử lý đầu vào (đây là nhiệm vụ của RAG Agent ở tầng sau).
* Không chỉnh sửa hoặc can thiệp trực tiếp vào các tệp gốc nằm trong `data/raw/`.

---

## 🏗️ 2. Kiến Trúc Dòng Chảy Dữ Liệu (Data Pipeline Architecture)

```text
               📂 [ data/raw/ ] (Tài liệu thô: PDF, DOCX, PPTX, XLSX, MP4)
                         │
                         ▼
            1. 🔍 Tự Động Quét & Phân Loại File (Role & Access Scope)
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
   📄 Văn Bản / Slide / Bảng     🎬 Video (MP4)
   (PDF, DOCX, PPTX, XLSX)              │
          │                             ▼
          ▼                      faster-whisper
   2. ⚙️ Trích Xuất Dữ Liệu              │
    * PDF 3-Tier Offline:               ▼
      - Tier 1: MinerU (Magic-PDF)  Transcript kèm Timestamps
      - Tier 2: Chandra OCR 2           │
      - Tier 3: PyMuPDF + EasyOCR       │
                (BBox Sorted) + Tesseract
    * PPTX: BBox Coordinate Sorting     │
    * DOCX & XLSX: Native Markdown      │
          │                             │
          └──────────────┬──────────────┘
                         │
                         ▼
            3. 🖼️ Nhận diện Hình Ảnh & OCR (EasyOCR BBox-Sorted)
                         │
                         ▼
            4. 🛡️ Bộ lọc khử nhiễu OCR & Chuẩn hóa Brand 4 tầng:
               - Tier 1: BBox Confidence Filter (≥ 0.35)
               - Tier 2: Text Height Ratio Filter (≥ 1.5% img height)
               - Tier 3: Background-image Noise Filter (Heuristic)
               - Tier 4: Brand-Name Normalizer (VINFA$T -> VINFAST)
                         │
                         ▼
            5. 🧹 Text Cleaning & Normalization (Unicode NFC, Strip Garbage)
                         │
                         ▼
            6. 🔒 PII Detection & Complete Removal (Presidio + VN Regex)
                         │
                         ▼
            7. 🧩 Structure-Aware Chunker (400-800 tokens + 80 tokens overlap)
                         │
          ┌──────────────┼──────────────┬──────────────┐
          ▼              ▼              ▼              ▼
    📄 Markdown    📊 Metadata    🛡️ PII Report  🧩 Chunks JSON
     (.md)          (.json)        (.json)        (data/processed/chunks/)
                                                       │
                                        ┌──────────────┴──────────────┐
                                        ▼                             ▼
                               🧠 BAAI/bge-m3 (1024d)       🔤 BM25 (underthesea)
                                        │                             │
                                        ▼                             ▼
                               🗄️ ChromaDB Store           🗄️ BM25 Index Pickle
```

---

## 📂 3. Cấu Trúc Thư Mục & Phân Quyền Tự Động (Role-Based Access)

### 3.1. Cấu trúc đầu vào (`data/raw/`)
```text
data/
└── raw/
    ├── KeToan/         <-- Tài liệu Phòng Kế Toán
    ├── Sale/           <-- Tài liệu Phòng Kinh Doanh
    ├── KTV/            <-- Tài liệu Khối Kỹ Thuật
    ├── General_doc/    <-- Tài liệu Chung / Quy định toàn công ty
    └── Huong_dan_DMS/  <-- Tài liệu Hướng dẫn phần mềm DMS
```

### 3.2. Quy tắc phân quyền tự động (Role Mapping)
| Thư mục gốc | `role` (Vai trò) | `access_scope` (Phạm vi truy cập) |
| :--- | :--- | :--- |
| `KeToan` | `accounting` | `["accounting"]` |
| `Sale` | `sales` | `["sales"]` |
| `KTV` | `technician` | `["technician"]` |
| `General_doc` | `general` | `["accounting", "sales", "technician", "general"]` |
| `Huong_dan_DMS` | `general` | `["accounting", "sales", "technician"]` |

### 3.3. Cấu trúc đầu ra (`data/processed/`)
```text
data/
└── processed/
    ├── markdown/       <-- File .md sạch đã gỡ PII, kèm YAML Frontmatter
    ├── metadata/       <-- File .json chứa metadata kỹ thuật & SHA-256 hash
    ├── pii_reports/    <-- File .json thống kê số lượng PII đã gỡ bỏ
    └── chunks/         <-- File .json chứa danh sách chunks (400-800 tokens)
```

---

## 🔬 4. Đặc Tả Kỹ Thuật Chi Tiết Từng Bước

### 4.1. Trích xuất đa định dạng (Offline 3-Tier Extraction)
Để đảm bảo **độ chính xác > 95%** và **hoạt động hoàn toàn offline (No API Dependency)**, hệ thống áp dụng chiến lược phân tầng cho PDF:

1. **Tier 1 — MinerU (Magic-PDF):**
   - Phân tích layout chuyên sâu bằng Deep Learning, tái cấu trúc bảng biểu phức tạp và văn bản đa cột sang Markdown chuẩn.
2. **Tier 2 — Chandra OCR 2 (`datalab-to/chandra-ocr-2`):**
   - Model Vision-Language chuyên dụng cho OCR tài liệu scan và slide bài giảng nhiều hình.
3. **Tier 3 — PyMuPDF + EasyOCR + Tesseract Fallback:**
   - Trích xuất native text cực nhanh với `PyMuPDF`. Với trang scan/ảnh không có text layer, chạy `EasyOCR` (đã kích hoạt thuật toán Bounding Box Sorting) kết hợp fallback `Tesseract OCR` (`vie+eng`).

---

### 4.2. Thuật toán sắp xếp thứ tự đọc OCR (Top-to-Bottom, Left-to-Right)

> [!IMPORTANT]
> **Khắc phục lỗi đọc ngược:** Khi một slide hoặc trang có nhiều ảnh/hộp chữ, việc đọc thô theo thứ tự render của file sẽ khiến chữ bị lộn xộn từ dưới lên. Hệ thống giải quyết triệt để bằng tọa độ hình học không gian.

#### A. Trong `image_processor.py` (EasyOCR):
* Gọi EasyOCR với tham số `detail=1` để lấy tọa độ 4 góc của từng hộp chữ: `bbox = [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]`.
* Tính toán trọng tâm tọa độ:
  - $Y_{\text{mid}} = \frac{y_1 + y_2}{2}$
  - $X_{\text{mid}} = \frac{x_1 + x_2}{2}$
* Gom cụm các dòng bằng kỹ thuật **Row Bucketing (20px)**: $\text{RowBucket} = \text{round}(Y_{\text{mid}} / 20)$.
* Sắp xếp theo tuple `(RowBucket, X_mid)` $\rightarrow$ Chữ từ trên xuống dưới, cùng dòng thì từ trái qua phải.

#### B. Trong `pptx_extractor.py` (Slide PowerPoint):
* Mọi shape trên slide (Text Box, Table, Embedded Image) được sắp xếp theo tọa độ EMU (English Metric Units):
  - $\text{RowBucket} = \text{shape.top} // 200\,000$ (tương đương ~5.5mm trên slide)
  - Sort Key: `(_reading_order_sort_key)` $\rightarrow$ duyệt shape theo `(RowBucket, shape.left)`.

---

### 4.3. Bộ lọc 4 tầng khử nhiễu OCR & Chuẩn hóa tên thương hiệu (4-Tier OCR Filter)

Khi chạy OCR trên ảnh slide bài giảng có ảnh nền (background banner, đám đông, logo cách điệu), EasyOCR thường bắt phải các chuỗi ký tự rác hoặc đọc sai font chữ đặc thù. Hệ thống thiết lập bộ lọc 4 tầng:

```text
  [Ảnh trích xuất / Slide Image]
                │
                ▼
  [Tier 1: BBox Confidence Filter] (image_processor.py)
  * Loại bỏ các bounding box có confidence < OCR_CONFIDENCE_THRESHOLD (0.35)
                │
                ▼
  [Tier 2: Text Height Ratio Filter] (image_processor.py)
  * Loại bỏ các bounding box có (BBox Height / Image Height) < OCR_MIN_TEXT_HEIGHT_RATIO (0.015)
  * Khử triệt để watermark & chữ li ti ở góc ảnh
                │
                ▼
  [Tier 3: Line-Level Background Noise Heuristic] (markdown_normalizer.py)
  * Phát hiện dòng văn bản đọc từ ảnh sự kiện/banner:
    - Tỷ lệ số rời rạc + ký tự ASCII đơn lẻ ≥ 45%
    - Tỷ lệ từ tiếng Việt có dấu ≤ 15%
    - Chuỗi số dày đặc (≥ 60% tokens là số)
                │
                ▼
  [Tier 4: Brand-Name Post-Processor] (markdown_normalizer.py)
  * Tự động sửa các lỗi nhận diện thương hiệu phổ biến:
    - VINFA$T, VI N F A $ T, V I N F A S T, V1NFAST  ──►  VINFAST
    - VinFa$t                                         ──►  VinFast
    - V1NGROUP, VinGr0up                              ──►  VinGroup
    - DN1S, D M S                                     ──►  DMS
    - XMĐ.                                            ──►  XMĐ
```

---

### 4.4. Làm sạch & Chuẩn hóa văn bản (Text Cleaning & Normalization)
* **Chuẩn hóa Unicode:** Toàn bộ văn bản được đưa về chuẩn **NFC**.
* **Khử nhiễu ký tự rác:** Tự động phát hiện và loại bỏ các chuỗi rác OCR (ví dụ: `V Bo Whee eh) \u01afr >>...`).
* **Bảo toàn bảng & danh sách:** Giữ nguyên vẹn định dạng bảng Markdown `| Cột 1 | Cột 2 |`, bullet points, số thứ tự quy trình.
* **Chuẩn hóa Heading:** Cấu trúc phân cấp `# Title` $\rightarrow$ `## Section` $\rightarrow$ `### Subsection` rõ ràng, loại bỏ placeholder vô nghĩa.

---

### 4.5. Bảo mật PII 100% & Quét bảo mật tài liệu

> [!CAUTION]
> **Chính sách bảo mật:** Toàn bộ dữ liệu nhạy cảm được **XÓA BỎ TRIỆT ĐỂ** (Complete Removal), không để lộ số thẻ, CCCD hay số điện thoại khách hàng trong Vector DB.

* **Các thực thể PII được bảo vệ (`pii_entities`):**
  - `PERSON` (Họ tên cá nhân)
  - `PHONE_NUMBER` (Số điện thoại VN)
  - `EMAIL_ADDRESS` (Email)
  - `ID_NUMBER` (CCCD/CMND)
  - `BANK_ACCOUNT` (Số tài khoản ngân hàng)
  - `CREDIT_CARD` (Số thẻ tín dụng)
  - `ADDRESS` (Địa chỉ cư trú)
  - `CUSTOMER_ID` (Mã định danh khách hàng)
  - `EMPLOYEE_ID` (Mã nhân viên)
  - `VEHICLE_PLATE` (Biển số xe ô tô/xe máy)
  - `USERNAME` & `PASSWORD` (Tài khoản, mật khẩu)
* **Ví dụ:**
  - *Gốc:* `"Khách hàng Nguyễn Văn A, SĐT: 0912345678, mang xe biển số 29A-123.45 đến bảo dưỡng."`
  - *Sau khi lọc:* `"Khách hàng , SĐT: , mang xe biển số  đến bảo dưỡng."`
* **Security Scanner (`src/ingestion/`):** Tự động quét phát hiện Prompt Injection, mã độc nhúng, tập tin quá kích thước hoặc sai MIME type trước khi xử lý.

---

### 4.6. Structure-Aware Chunking (400–800 tokens + Sliding Window Overlap)

* **Kích thước tối ưu:** 
  - $\text{MIN\_TOKENS} = 400$
  - $\text{MAX\_TOKENS} = 800$
  - $\text{OVERLAP\_TOKENS} = 80$ (~10% sliding window)
* **Nguyên tắc phân đoạn:**
  1. Các khối nguyên tử (Bảng biểu, Danh sách quy trình, Code block) được giữ nguyên không bao giờ bị cắt đôi.
  2. Khi đoạn văn bản vượt quá 800 tokens, hệ thống cắt tại ranh giới câu (`.`, `!`, `?`).
  3. Khi sinh chunk tiếp theo, **80 tokens cuối cùng** của đoạn văn trước sẽ được đưa vào làm tiền tố để giữ trọn vẹn ngữ cảnh.
* **Context Header:** Mỗi chunk đều được gắn tiền tố định danh:
  ```text
  [Document: Quy trình bán hàng | Role: sales | Section: Tư vấn > Báo giá | Slide: 5]
  ```

---

### 4.7. Embedding (`BAAI/bge-m3`) & BM25 Tokenizer (`underthesea`)

| Thành phần | Công nghệ cũ | Công nghệ mới nâng cấp | Lợi ích |
| :--- | :--- | :--- | :--- |
| **Embedding Model** | `all-MiniLM-L6-v2` (384 dims) | **`BAAI/bge-m3` (1024 dims)** | Đa ngôn ngữ chuyên sâu tiếng Việt, ngữ cảnh 8192 tokens, độ chính xác ngữ nghĩa vượt trội. |
| **Vector Database** | ChromaDB (384d) | **ChromaDB (1024d)** | Tự động phát hiện và xử lý Dimension Mismatch (`_ensure_collection_compatible`). |
| **BM25 Tokenizer** | Whitespace split | **`underthesea.word_tokenize`** | Tách từ ghép tiếng Việt chính xác (ví dụ: `hệ_thống`, `quản_lý_pin`). |

---

## 💻 5. Cấu Trúc Mã Nguồn (`src/`, `scripts/`, `data/`)

```text
P-223/
├── data/
│   ├── raw/                           <-- Dữ liệu tài liệu gốc (KeToan, Sale, KTV, General_doc, Huong_dan_DMS)
│   ├── processed/
│   │   ├── markdown/                  <-- Markdown sạch đã gỡ PII, kèm Frontmatter
│   │   ├── metadata/                  <-- JSON Metadata & SHA-256 hash
│   │   ├── pii_reports/               <-- JSON thống kê PII đã gỡ bỏ
│   │   └── chunks/                    <-- JSON chunks (400-800 tokens + context header)
│   ├── chroma/                        <-- ChromaDB Vector Database (1024 dims)
│   └── bm25_index.pkl                 <-- BM25 Index lưu trữ từ điển tiếng Việt
├── src/
│   ├── config.py                      <-- Cấu hình hệ thống & Pydantic Settings
│   ├── extract/
│   │   ├── base.py                    <-- BaseExtractor, ExtractedDocument model
│   │   ├── pdf_extractor.py           <-- Hybrid 3-Tier Offline PDF Extractor
│   │   ├── docx_extractor.py          <-- Trích xuất DOCX
│   │   ├── pptx_extractor.py          <-- Trích xuất PPTX (BBox sorted)
│   │   ├── xlsx_extractor.py          <-- Trích xuất XLSX sang Markdown Table
│   │   └── video_extractor.py         <-- faster-whisper video transcription
│   ├── preprocess/
│   │   ├── pipeline.py                <-- Orchestrator xử lý raw -> markdown
│   │   ├── markdown_pipeline.py       <-- Orchestrator xử lý markdown -> chunks
│   │   ├── cleaner.py                 <-- Làm sạch rác & Unicode NFC
│   │   ├── image_processor.py         <-- EasyOCR BBox-Sorted & Tier 1+2 OCR Filter
│   │   ├── markdown_normalizer.py     <-- Tier 3 Background Noise & Tier 4 Brand Normalizer
│   │   ├── structure_normalizer.py    <-- Chuẩn hóa phân cấp Heading Markdown
│   │   ├── pii_remover.py             <-- Presidio + Regex VN PII Removal
│   │   ├── structure_aware_chunker.py <-- Chunker (400-800 tokens, 80 overlap)
│   │   └── generators/                <-- Xuất Markdown, Metadata, PII Report
│   ├── ingestion/
│   │   ├── file_validator.py          <-- Kiểm tra MIME type, kích thước, magic bytes
│   │   ├── security_scanner.py        <-- Quét Prompt Injection, script độc hại
│   │   ├── pii_scanner.py             <-- Quét và phân loại PII (Auto/HITL)
│   │   └── job_manager.py             <-- Quản lý tiến trình ingestion bất đồng bộ
│   ├── embedding/
│   │   └── embedder.py                <-- Embedding Service (BAAI/bge-m3, 1024d)
│   └── vectordb/
│       ├── chroma_store.py            <-- ChromaDB Vector Store
│       ├── bm25_store.py              <-- BM25 Retriever (underthesea tokenizer)
│       └── hybrid_search.py           <-- Hybrid Search (Dense + Sparse RRF)
├── eval/
│   ├── evaluator.py                   <-- Đánh giá Hit Rate@K, MRR, Role Compliance
│   └── dataset.json                   <-- Bộ câu hỏi ground-truth đánh giá
├── scripts/
│   ├── run_preprocessing.py           <-- CLI chạy trích xuất thô & lọc PII
│   ├── run_markdown_pipeline.py       <-- CLI chạy chuẩn hóa & sinh chunks
│   ├── rebuild_vector_db.py           <-- CLI rebuild ChromaDB + BM25 với bge-m3
│   └── run_benchmark.py               <-- CLI chạy đo lường chất lượng RAG
└── test_input.html                    <-- Giao diện Studio Web UI đối chiếu 3 cột
```

---

## ⚙️ 6. Cấu Hình Hệ Thống & Biến Môi Trường (`config.py` / `.env`)

Các tham số có thể tùy biến qua tệp `.env`:

```ini
# --- Cấu hình chung ---
APP_NAME=AI20K Agent
APP_ENV=development
APP_PORT=8000
LOG_LEVEL=INFO

# --- Đường dẫn dữ liệu ---
RAW_DATA_DIR=Data/raw
PROCESSED_DATA_DIR=Data/processed
CHROMA_PERSIST_DIR=./data/chroma

# --- Bộ lọc OCR 4 tầng ---
# Ngưỡng tin cậy của EasyOCR (Tier 1): bỏ bounding box có score < 0.35
OCR_CONFIDENCE_THRESHOLD=0.35

# Tỷ lệ chiều cao chữ tối thiểu so với ảnh (Tier 2): bỏ text li ti < 1.5% chiều cao ảnh
OCR_MIN_TEXT_HEIGHT_RATIO=0.015

# --- Cấu hình Whisper & PII ---
VIDEO_MODEL=large-v3
VIDEO_LANGUAGE=vi
WHISPER_DOWNLOAD_ROOT=./models/whisper
PII_ENABLED=true
PII_REMOVE=true
PII_CONFIDENCE_THRESHOLD=0.7
```

---

## 🚀 7. Hướng Dẫn Cài Đặt Môi Trường & Chạy Pipeline (CLI Commands)

### 7.1. Kích hoạt môi trường `.venv` (Python 3.13.15)
```powershell
# Kích hoạt môi trường trong PowerShell:
.venv\Scripts\activate
```
*(Sau khi kích hoạt, đầu dòng lệnh sẽ hiển thị `(.venv)`).*

---

### 7.2. Các bước chạy Pipeline hoàn chỉnh

#### 📍 Bước 1: Trích xuất thô từ `data/raw/` sang `data/processed/markdown/`
```powershell
python scripts/run_preprocessing.py
```
*Tùy chọn nâng cao:*
* **Chỉ quét kiểm tra an ninh & PII (không ghi đè index):**
  ```powershell
  python scripts/run_preprocessing.py --scan-only
  ```
* **Xử lý 1 file duy nhất:**
  ```powershell
  python scripts/run_preprocessing.py --file "data/raw/Sale/4. Tài liệu Quy trình và Kỹ năng bán hàng XMĐ.pdf"
  ```
* **Bỏ qua HITL Review (dành cho CI/CD):**
  ```powershell
  python scripts/run_preprocessing.py --auto-approve
  ```

#### 📍 Bước 2: Chuẩn hóa & Sinh Chunks (400–800 tokens + 80 tokens overlap)
```powershell
python -m scripts.run_markdown_pipeline
```
*Kết quả:* Tạo ra toàn bộ các file JSON chunks trong `data/processed/chunks/` (đã qua lọc rác, làm sạch bảng biểu, chuẩn hóa heading và thêm context header).

#### 📍 Bước 3: Rebuild Vector DB với `BAAI/bge-m3` & BM25
```powershell
python scripts/rebuild_vector_db.py
```
*Script sẽ tự động:*
1. Xóa index cũ không tương thích dimension.
2. Tải model `BAAI/bge-m3` (~2.3GB ở lần đầu chạy).
3. Embed toàn bộ chunks và lưu vào `data/chroma/`.
4. Xây dựng chỉ mục BM25 tiếng Việt lưu vào `data/bm25_index.pkl`.

*Tùy chọn kiểm tra thử (dry-run):*
```powershell
python scripts/rebuild_vector_db.py --dry-run
```

---

## 📊 8. Kiểm Thử & Đánh Giá Chất Lượng (Benchmark & Tests)

### 8.1. Chạy Unit Tests
```powershell
pytest tests/ -v
```

### 8.2. Chạy Benchmark đo lường chất lượng RAG
```powershell
python scripts/run_benchmark.py --save-report
```

**Báo cáo mẫu đầu ra:**
```text
=================================================================
  KET QUA BENCHMARK RAG
=================================================================
  Embedding model : BAAI/bge-m3
  Vector dims     : 1024
  Chunk config    : 400-800 tokens, overlap=80
-----------------------------------------------------------------
  Total queries   : 50
  Top-K           : 5
-----------------------------------------------------------------
  Hit Rate@K      : 0.9600  (96.0%)
  MRR             : 0.8733  (87.3%)
  Role Compliance : 1.0000  (100.0%)
  Table Accuracy  : 0.9400  (94.0%)
  Section Match   : 0.9200  (92.0%)
=================================================================
```

### 8.3. Chạy Framework Debug & Unique Test (`retrieval_debugger/`)

Bộ công cụ chuyên dụng giúp kiểm tra, chẩn đoán nguyên nhân gốc (Vector, BM25, RBAC, Reranker hay LLM) và xác thực toàn vẹn bằng **Unique Canary Test**:

```powershell
# Cách 1: Click đúp file batch trên Windows
retrieval_debugger\run_debug.bat

# Cách 2: Chạy qua Terminal (chế độ nhanh không tốn token LLM)
python retrieval_debugger/run_debug.py --retrieval-only

# Chế độ kiểm tra toàn diện kèm LLM
python retrieval_debugger/run_debug.py

# Debug cho 1 câu hỏi cụ thể theo vai trò
python retrieval_debugger/run_debug.py --query "Làm thế nào để đăng nhập DMS?" --role accounting
```

**Đặc điểm nổi bật:**
* **Unique Canary Test:** Tự động nạp chunk chứa mã bí mật (`XKCD-98765-VINFAST-CANARY`), kiểm tra truy xuất và tự động dọn sạch.
* **Tự động phân loại lỗi:** `HIT_TOP_1`, `HIT_TOP_K`, `MISSED`, `RERANKER_DROPPED`, `LLM_IGNORED_CONTEXT`.
* **Tự động xuất báo cáo:** Lưu file Markdown và log JSON chi tiết vào `retrieval_debugger/reports/`.

---

## 🖥️ 9. Giao Diện Web UI Studio Đối Chiếu 3 Cột (Side-by-Side)

Hệ thống tích hợp sẵn giao diện Studio trực quan giúp người dùng kiểm thử từng tệp tài liệu:

### 9.1. Khởi chạy FastAPI Server
```powershell
.venv\Scripts\python.exe -m uvicorn src.main:app --reload
```
* **Web UI Studio:** [http://127.0.0.1:8000/api/v1/test_input](http://127.0.0.1:8000/api/v1/test_input)
* **Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 9.2. Bố cục 3 cột trong Studio
| Cột | Chức năng | Chi tiết |
| :--- | :--- | :--- |
| **Cột 1: Bên trái (Input)** | **Document & Slide Viewer** | Xem trực tiếp tài liệu gốc (PDF, hình ảnh, slide bài giảng) kèm thông tin metadata. |
| **Cột 2: Ở giữa (Process)** | **Pipeline Stepper & Live Logs** | Hiển thị tiến trình 5 bước theo thời gian thực (Extract $\rightarrow$ Scan $\rightarrow$ HITL Review $\rightarrow$ Chunking $\rightarrow$ Indexing) và cửa sổ console log. |
| **Cột 3: Bên phải (Output)** | **Ground Truth Inspection** | Tab chuyển đổi xem: <br>1. **Markdown**: Xem định dạng rendered và raw.<br>2. **Chunks**: Danh sách chunks (400-800 tokens) kèm Context Header.<br>3. **Security & PII**: Báo cáo chi tiết các thực thể đã lọc. |

---

## 🛠️ 10. Xử Lý Lỗi Thường Gặp (Troubleshooting)

### ❌ Lỗi 1: `ModuleNotFoundError: No module named 'pydantic'` hoặc `docx`
* **Nguyên nhân:** Đang chạy lệnh bằng Python của Anaconda base thay vì môi trường `.venv` của dự án.
* **Giải pháp:** Luôn kích hoạt môi trường trước khi chạy:
  ```powershell
  .venv\Scripts\activate
  ```
  Hoặc gọi trực tiếp: `.venv\Scripts\python.exe <tên_script>.py`.

### ❌ Lỗi 2: `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` (Python 3.9)
* **Nguyên nhân:** Cú pháp Union `A | B` chỉ được Python hỗ trợ từ bản 3.10+.
* **Giải pháp:** Dự án đã chuyển sang chạy trên **Python 3.13.15** trong `.venv`, hoàn toàn hỗ trợ cú pháp `A | B` mà không phát sinh lỗi.

### ❌ Lỗi 3: `UnicodeEncodeError: 'charmap' codec can't encode character...`
* **Nguyên nhân:** Console Windows PowerShell sử dụng encoding mặc định `cp1252` không in được tiếng Việt có dấu.
* **Giải pháp:** Toàn bộ scripts (`rebuild_vector_db.py`, `run_benchmark.py`) đã được tích hợp cấu hình tự động:
  ```python
  sys.stdout.reconfigure(encoding="utf-8", errors="replace")
  ```

---

> [!TIP]
> **Khuyến nghị vận hành chuẩn (Standard Workflow):** Khi có tài liệu mới được thêm vào `data/raw/`, chỉ cần chạy tuần tự 3 lệnh:
> 1. `python scripts/run_preprocessing.py` (Trích xuất thô & lọc PII sang `.md`)
> 2. `python -m scripts.run_markdown_pipeline` (Chuẩn hóa & tạo chunks 400–800 tokens)
> 3. `python scripts/rebuild_vector_db.py` (Rebuild Vector DB & BM25)
