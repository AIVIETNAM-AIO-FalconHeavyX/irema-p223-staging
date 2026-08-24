# 📘 HDSD — Kết Nối Thống Nhất Track 1 + 2 + 3

> **Tài liệu này hướng dẫn cách vận hành toàn bộ hệ thống từ Upload tài liệu đến Chatbot trả lời câu hỏi.**
> Đọc trước [`HDSD.md`](./HDSD.md) để nắm hạ tầng cơ bản (MinIO, PostgreSQL) và [`HDSD_Track1.md`](./HDSD_Track1.md) để nắm kiến trúc Track 1.

---

## 1. Tổng Quan Kiến Trúc

```
┌────────────────────────────────────────────────────────────────────────────┐
│                      LUỒNG DỮ LIỆU THỐNG NHẤT                              │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  [Admin Upload PDF]                                                        │
│        │                                                                   │
│        ▼                                                                   │
│  MinIO (raw/<role>/<file.pdf>)  ──────────►  [Giao diện Onboarding]       │
│        │                                      (Người dùng đọc file thô)   │
│        │  Track 2: run_preprocessing.py                                    │
│        ▼                                                                   │
│  PII Remove + OCR + Markdown                                               │
│        │                                                                   │
│        ▼                                                                   │
│  MinIO (processed/<role>/<file.md>)                                        │
│        │                                                                   │
│        ├──► PostgreSQL: OnboardingStep.processed_md_url ← cập nhật URL     │
│        │                                                                   │
│        │  Track 3: rag_ingestion_pipeline.py                               │
│        ▼                                                                   │
│  Chunking + Embedding                                                      │
│        │                                                                   │
│        ▼                                                                   │
│  ChromaDB (Vector) + BM25 (Keyword)                                        │
│        │                                                                   │
│        ▼                                                                   │
│  [Chatbot trả lời câu hỏi theo RBAC]                                      │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Điều Kiện Tiên Quyết

Đảm bảo các service sau đang chạy trước khi thực hiện bất kỳ bước nào:

```bash
# Kiểm tra Docker containers
docker-compose ps

# Phải thấy 3 container đang "Up":
#   minio
#   postgres (hoặc db)
#   (optional) minio-createbuckets
```

Kiểm tra file `.env` có đủ các biến:

```bash
# MinIO
AWS_S3_ENDPOINT_URL=http://localhost:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET_NAME=ai20k-docs
AWS_REGION=us-east-1

# PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/onboarding_db

# AI (cho Track 3)
GOOGLE_API_KEY=your-gemini-api-key   # hoặc OPENAI_API_KEY
```

---

## 3. Hướng Dẫn Sử Dụng

### 3.1 Bước 1: Đưa tài liệu thô lên MinIO (Track 1)

Có 2 cách:

**Cách A — Dùng giao diện Web (Khuyến nghị):**
1. Mở trình duyệt → `http://localhost:5173`
2. Đăng nhập với tài khoản Admin/Owner
3. Vào trang quản lý tài liệu → Upload file PDF/DOCX lên đúng role

**Cách B — Dùng script migrate (nếu đã có file local):**
```bash
python scripts/migrate_to_s3.py
```

---

### 3.2 Bước 2: Chạy Track 2 (Tiền Xử Lý + Upload MinIO)

```bash
# Xử lý một file cụ thể VÀ upload lên MinIO luôn:
python scripts/run_preprocessing.py \
  --file "data/raw/Sale/sample.pdf" \
  --with-minio

# Xử lý toàn bộ thư mục + upload MinIO + embed ChromaDB (Full Pipeline):
python scripts/run_preprocessing.py \
  --with-minio \
  --with-embed
```

**Giải thích các flag:**
| Flag | Ý nghĩa |
|---|---|
| `--file <path>` | Chỉ xử lý một file cụ thể |
| `--with-minio` | Sau xử lý, upload `.md` lên MinIO và cập nhật PostgreSQL |
| `--with-embed` | Sau xử lý, Chunk + Embed vào ChromaDB để Chatbot dùng được |
| *(không flag)* | Chỉ xử lý local, không upload, không embed |

**Kết quả mong đợi:**
```
Successfully processed single file:
  Markdown:   data/processed/markdown/Sale/sample.md
  Metadata:   data/processed/metadata/Sale/sample.json
  PII Report: data/processed/pii_reports/Sale/sample.json

Uploaded to MinIO: processed/sales/sample.md
Cập nhật processed_md_url cho step [3]: http://localhost:9000/ai20k-docs/processed/sales/sample.md
```

---

### 3.3 Bước 3: Nạp toàn bộ tài liệu vào Chatbot (Track 3)

```bash
# Nạp TẤT CẢ tài liệu từ MinIO vào ChromaDB:
python scripts/rag_ingestion_pipeline.py

# Chỉ nạp tài liệu của một role cụ thể:
python scripts/rag_ingestion_pipeline.py --role sales

# Xóa ChromaDB cũ và nạp lại từ đầu (khi thay đổi lớn):
python scripts/rag_ingestion_pipeline.py --reset
```

**Kết quả mong đợi:**
```
Tổng số OnboardingStep cần xử lý: 12
  📄 [sales] Tổng quan Sale
    ✅ Tải từ MinIO: processed/sales/sample.md
    🔪 Tạo được 47 chunks từ 'Tổng quan Sale'
...
🎉 Hoàn tất RAG Ingestion Pipeline!
   - ChromaDB: 312 chunks
   - BM25:     312 chunks
   - Chatbot đã sẵn sàng!
```

---

### 3.4 Kiểm Tra Kết Nối

```bash
# Kiểm tra MinIO có file .md chưa:
python -c "
from src.cloud.s3_service import s3_service
keys = s3_service.list_processed_mds()
print(f'Tìm thấy {len(keys)} file .md trên MinIO:')
for k in keys: print(f'  {k}')
"

# Kiểm tra ChromaDB có dữ liệu chưa:
python -c "
from src.vectordb.chroma_store import ChromaVectorStore
vs = ChromaVectorStore()
results = vs.query('test', top_k=1)
print(f'ChromaDB có dữ liệu: {len(results) > 0}')
"

# Kiểm tra PostgreSQL đã cập nhật processed_md_url:
python -c "
from src.db import SessionLocal
from src.db.models import OnboardingStep
db = SessionLocal()
steps = db.query(OnboardingStep).filter(OnboardingStep.processed_md_url != None).all()
print(f'Số OnboardingStep có processed_md_url: {len(steps)}')
for s in steps: print(f'  [{s.role_target}] {s.title}: {s.processed_md_url}')
db.close()
"
```

---

## 4. Quy Trình Khi Có Tài Liệu Mới (Quick Reference)

Mỗi khi Admin thêm tài liệu mới, chỉ cần chạy 1 lệnh duy nhất:

```bash
python scripts/run_preprocessing.py --file "data/raw/<Role>/<file.pdf>" --with-minio --with-embed
```

Hệ thống sẽ tự động:
1. ✅ Đọc PDF → Trích xuất văn bản (OCR nếu cần)
2. ✅ Xóa thông tin nhạy cảm (PII)
3. ✅ Tạo file `.md` sạch
4. ✅ Upload `.md` lên MinIO (`processed/<role>/`)
5. ✅ Cập nhật PostgreSQL (`OnboardingStep.processed_md_url`)
6. ✅ Chunk + Embed vào ChromaDB + BM25

---

## 5. Troubleshooting

| Lỗi | Nguyên nhân | Giải pháp |
|---|---|---|
| `Connection refused` (MinIO) | Docker chưa chạy | `docker-compose up -d` |
| `NoSuchBucket` | Bucket chưa tạo | Mở `http://localhost:9001` tạo bucket tên `ai20k-docs` |
| `ModuleNotFoundError` | Thiếu thư viện | `pip install -r requirements.txt` |
| ChromaDB trống khi chat | Chưa chạy ingestion | `python scripts/rag_ingestion_pipeline.py` |
| `processed_md_url` vẫn None trong DB | Chưa dùng `--with-minio` | Chạy lại với flag `--with-minio` |

---

## 6. Cấu Trúc Thư Mục MinIO

```
ai20k-docs/                    ← Bucket chính
├── raw/                       ← File gốc chưa xử lý
│   ├── sales/
│   │   └── sample.pdf
│   ├── accounting/
│   │   └── ke_toan_tong_hop.pdf
│   └── technician/
│       └── huong_dan_ky_thuat.docx
│
└── processed/                 ← File .md đã xử lý PII (dùng cho Chatbot)
    ├── sales/
    │   └── sample.md
    ├── accounting/
    │   └── ke_toan_tong_hop.md
    └── technician/
        └── huong_dan_ky_thuat.md
```

---

*Cập nhật lần cuối: 2026-08-14 | Tác giả: Team The Sigmoid*
