# 📋 Tài Liệu Hướng Dẫn & Đặc Tả Hệ Thống Hạ Tầng & Giao Diện (Track 1)

> [!NOTE]
> **Mục tiêu hệ thống:** Xây dựng nền tảng hạ tầng lưu trữ vững chắc trên Đám mây ảo (MinIO S3, PostgreSQL), tích hợp các công cụ bảo mật, cùng với Giao diện Web (React/Vite) hiện đại, siêu mượt để quản lý quy trình và hiển thị tài liệu Onboarding cho các Đại lý VinFast.

---

## 🎯 1. Scope Hạn Mức & Mục Tiêu

### ✅ Trong Scope (Hệ thống thực hiện)
* **Hạ tầng Cloud Storage:** Triển khai S3 Object Storage nội bộ (MinIO) để lưu trữ an toàn, độc lập hàng trăm tệp dữ liệu thô (PDF, MP4, PPTX, DOCX, XLSX).
* **Cơ sở dữ liệu (RDBMS):** Sử dụng PostgreSQL để lưu trữ metadata tài liệu, quản lý phân quyền theo Role (Sale, Kế toán, KTV, Owner) và trạng thái Onboarding.
* **Giao diện Web (SPA):** Xây dựng hệ thống Web bằng React, TypeScript, Tailwind CSS chuẩn UI/UX hiện đại.
* **Trình xem tài liệu (Document Viewer):** Tích hợp Modal xem PDF trực tiếp với cơ chế chống Cache (Cache-Buster) và Trình phát Video MP4 không cần tải về.
* **Đồng bộ Dữ liệu (Migration):** Cung cấp các Script tự động (`migrate_to_s3.py`) để chuyển đổi dữ liệu từ ổ cứng cục bộ lên Đám mây.
* **Tích hợp AI Pipeline (Ingestion):** Cung cấp Script cầu nối (`rag_ingestion_pipeline.py`) tự động tải dữ liệu từ Cloud về cấp phát cho hệ thống AI của Track 2.

### ❌ Out of Scope (Hệ thống KHÔNG thực hiện)
* Không xử lý bóc tách văn bản, OCR, hay gỡ bỏ thông tin PII (Thuộc phạm vi của Track 2).
* Không chia đoạn văn bản (Chunking) hay Vector DB (Thuộc phạm vi của Track 2).
* Không thực hiện truy vấn RAG hay tương tác Chatbot LLM (Thuộc phạm vi của Track 3).

---

## 🏗️ 2. Kiến Trúc Hạ Tầng & Dòng Chảy Dữ Liệu (Architecture)

```text
               👨‍💻 [ Người dùng / Đại lý ]
                        │
                        ▼
          1. 🌐 Giao diện Web (React / Vite)
             (Hiển thị Onboarding, PDF/Video Viewer)
                        │
          ┌─────────────┴──────────────┐
          ▼                            ▼
  2. ⚙️ Backend API (FastAPI)       4. ☁️ MinIO (S3 Storage)
     (Xử lý Logic, Auth)            (Lưu trữ PDF, DOCX, MP4)
          │                            ▲
          ▼                            │
  3. 🗄️ PostgreSQL (Database)           │
     (Lưu Role, Metadata, MinIO URL)   │
          │                            │
          └─────────────┬──────────────┘
                        │
                        ▼
          5. 🔗 RAG Ingestion Pipeline Script
             (rag_ingestion_pipeline.py)
                        │
                        ▼
               🧠 [ AI PIPELINE - TRACK 2 ]
```

---

## 📂 3. Cấu Trúc Thư Mục & Vai Trò

Hệ thống được thiết kế theo mô hình **Client-Server** kết hợp **Microservices**, tách biệt hoàn toàn giữa Giao diện, Backend và Database/Storage:

```text
Project_Root/
├── docker-compose.yml         <-- File cấu hình triển khai Hạ tầng (PostgreSQL, MinIO, ClamAV)
├── .env                       <-- Chứa các biến môi trường cấu hình kết nối an toàn
│
├── frontend/                  <-- 🌐 1. Giao diện Web (React + TypeScript)
│   ├── package.json
│   └── src/
│       ├── components/        <-- Các UI Components tái sử dụng (ResourceViewerModal...)
│       ├── pages/             <-- Các trang chính của ứng dụng
│       ├── services/          <-- Nơi gọi API giao tiếp với Backend
│       └── index.css          <-- File cấu hình CSS & Tailwind chuẩn
│
├── src/                       <-- ⚙️ 2. Backend API (Python FastAPI)
│   ├── main.py                <-- Entrypoint của Server
│   ├── cloud/                 <-- Tương tác với MinIO S3 (s3_service.py)
│   └── db/                    <-- Kết nối PostgreSQL & CRUD Models
│
└── scripts/                   <-- 🔗 3. Các Script Tiện Ích & Tích Hợp
    ├── migrate_to_s3.py       <-- Script bơm dữ liệu từ ổ cứng cục bộ lên Cloud MinIO
    └── rag_ingestion_pipeline.py <-- Script tích hợp lấy file từ Cloud cho Track 2
```

---

## 🚀 4. Hướng Dẫn Sử Dụng & Khởi Chạy Hệ Thống

> [!IMPORTANT]
> Bạn bắt buộc phải chạy Docker trước tiên để hệ thống CSDL và Đám mây ảo có thể hoạt động!

### 4.1 Khởi chạy Hạ tầng Docker (Database & Storage)
Mở Terminal ở thư mục gốc dự án và chạy:

```bash
docker-compose up -d
```
*Các dịch vụ sẽ chạy:*
- **PostgreSQL:** Port `5432`
- **MinIO S3 (Data):** Port `9000`
- **MinIO Console (UI):** Port `9001` (Truy cập Web: http://localhost:9001 - user/pass: `minioadmin`)

### 4.2 Khởi chạy Backend Server (FastAPI)
Mở một Terminal mới, kích hoạt môi trường ảo (nếu có) và chạy:

```bash
# Đảm bảo bạn đang ở thư mục gốc
python -m uvicorn src.main:app --port 8001 --reload
```
*Backend sẽ chạy tại:* http://localhost:8001

### 4.3 Khởi chạy Giao diện Frontend (React)
Mở thêm một Terminal mới, di chuyển vào thư mục `frontend/` và chạy:

```bash
cd frontend
npm install
npm run dev
```
*Giao diện sẽ chạy tại:* http://localhost:5173

---

## 🔗 5. Hướng Dẫn Sử Dụng Các Script Tiện Ích

### 5.1 Script Bơm Dữ Liệu (Migration)
Dùng khi bạn muốn đẩy toàn bộ file tài liệu gốc từ máy tính cá nhân lên MinIO S3 và đồng bộ link S3 vào Database PostgreSQL.

```bash
python scripts/migrate_to_s3.py
```

### 5.2 Script Cầu Nối RAG Ingestion (Cho Track 2)
Dùng để tự động quét Database, tải file từ Cloud về máy và xử lý AI. Đây là cầu nối hoàn hảo giữa Track 1 và Track 2.

```bash
python scripts/rag_ingestion_pipeline.py
```
* **Luồng hoạt động:** 
  1. Quét PostgreSQL để tìm các bài học có file đính kèm.
  2. Dùng thư viện `boto3` tải file (S3 Object) từ MinIO về thư mục tạm `temp_rag_data/`.
  3. Kích hoạt bộ xử lý của Track 2 (Khoảng trống để nhúng Code Docling/Whisper).
  4. Tự động xoá file tạm để giải phóng Ổ cứng/RAM.

---

## ✅ 6. Tiêu Chí Nghiệm Thu (Acceptance Criteria)

1. **Lưu trữ độc lập (S3):** Tuyệt đối không lưu file tài liệu (PDF, MP4) trong thư mục source code (Github) hay ổ cứng máy chủ Backend. Mọi file phải ở trên MinIO S3.
2. **PostgreSQL mạnh mẽ:** Thông tin về các bước Onboarding, quyền truy cập của Role và URL tài liệu được lưu trữ chuẩn Relational Database.
3. **UI Trực quan & Mượt mà:** Chức năng xem tài liệu bằng Modal không bị lỗi trắng trang (Cache-Buster tích hợp), Video phát trực tiếp sắc nét.
4. **Tích hợp liền mạch (Seamless Integration):** Script Ingestion Pipeline chạy trơn tru, làm đầu vào hoàn hảo không cần độ trễ cho Track 2.
