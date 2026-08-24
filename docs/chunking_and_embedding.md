# 📋 Tài Liệu Hướng Dẫn & Đặc Tả Hệ Thống Chunking, Embedding & Hybrid Retrieval Pipeline

> [!NOTE]
> **Tài liệu tiếp nối từ [HDSD.md](file:///e:/P-223/HDSD.md) (Giai Đoạn 1: Data Preprocessing & PII Removal).**  
> **Mục tiêu Giai đoạn 2:** Tiếp nhận dữ liệu Markdown sạch từ Giai đoạn 1, thực hiện **Structure-Aware Chunking** (cắt khúc giữ nguyên cấu trúc bảng/danh sách), **SBERT Embedding**, xây dựng hệ thống **Hybrid Search (ChromaDB + BM25)** phân quyền theo vai trò (`role`) và **Cross-Encoder Reranking**, sẵn sàng phục vụ cho các ứng dụng **RAG Chatbot & LLM Generation**.

---

## 🎯 1. Scope Hạn Mức & Mục Tiêu Giai Đoạn 2

### ✅ Trong Scope (Hệ thống thực hiện)
* **Làm sạch & Chuẩn hóa cấu trúc Markdown (`MarkdownNormalizer` & `StructureNormalizer`)**: Loại bỏ OCR noise dư thừa, duplicate header, caption rác; chuẩn hóa cây tiêu đề (`#` $\rightarrow$ `##` $\rightarrow$ `###`).
* **Phân đoạn ngữ nghĩa giữ cấu trúc (`StructureAwareChunker`)**:
  * Chunk theo Heading $\rightarrow$ Section $\rightarrow$ Paragraph trong khoảng **300 – 600 tokens** (~1,200 – 2,400 ký tự).
  * **Giữ nguyên vẹn (Atomic Units)** đối với Bảng biểu (`|...|`), Danh sách (Bullet list), và Đoạn mã (Code block) — tuyệt đối **không cắt ngang bảng hoặc danh sách**.
* **Đính kèm Context Header & Metadata phong phú**: Tự động bổ sung chuỗi ngữ cảnh `[Document: ... | Role: ... | Section: ... | Slide/Page: ...]` và metadata phân quyền (`role`, `access_scope`, `source`, `timestamp`).
* **Tạo Vector Embeddings (`EmbeddingService`)**: Sử dụng mô hình SBERT `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
* **Dual Indexing & Hybrid Search (`ChromaVectorStore` & `BM25Retriever`)**:
  * **ChromaDB**: Lưu trữ vector embedding phục vụ Semantic Search.
  * **BM25**: Lưu trữ từ khóa phục vụ Exact-Match / Keyword Search.
  * **RRF (Reciprocal Rank Fusion)**: Trộn kết quả Vector + BM25 với trọng số chuẩn hóa ($k=60$).
  * **Role Security Isolation**: Lọc và chặn truy cập chéo giữa các vai trò (`sales`, `accounting`, `technician`, `general`).
* **Chấm điểm lại Reranking (`RerankerService`)**: Sử dụng Cross-Encoder `cross-encoder/ms-marco-MiniLM-L-6-v2` để rerank Top-K ứng viên trước khi đưa vào LLM.
* **Bộ Đánh Giá Benchmark RAG (`RAGEvaluator`)**: Tự động đo đạc Hit Rate@K, MRR, Role Compliance, Table Accuracy.

### ❌ Out of Scope (Hệ thống KHÔNG thực hiện)
* Không chỉnh sửa hay ghi đè các file gốc trong `data/raw/` hoặc file markdown đã xử lý ở Phase 1 (`data/processed/markdown/`).
* Không trực tiếp gọi API sinh lời văn LLM (bước này dành cho module Chatbot RAG ở tầng ứng dụng).

---

## 🏗️ 2. Kiến Trúc Dòng Chảy Dữ Liệu Giai Đoạn 2 (Data Flow)

```text
 📂 [ data/processed/markdown/ ] (Markdown sạch từ Phase 1 - HDSD.md)
                        │
                        ▼
           1. 🧹 Markdown & Structure Normalizer
        (Làm sạch OCR noise, chuẩn hóa cây Heading # -> ##)
                        │
                        ▼
           2. ✂️ Structure-Aware Chunker (300-600 tokens)
      (Bảng biểu, Danh sách, Code block được GIỮ NGUYÊN VẸN)
                        │
                        ▼
           3. 🏷️ Metadata & Context Enrichment
       (Gán Context Header + Role / Document ID / Section)
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
  📂 [ cleaned_markdown/ ]      📂 [ chunks/*.json ] (Payload Chunk)
                                       │
                        ┌──────────────┴──────────────┐
                        ▼                             ▼
            4a. 🧠 SBERT Embedder        4b. 🔤 BM25 Tokenizer
            (all-MiniLM-L6-v2)             (Okapi BM25 Index)
                        │                             │
                        ▼                             ▼
             🗄️ [ ChromaDB Persistent ]    💾 [ bm25_index.pkl ]
                        │                             │
                        └──────────────┬──────────────┘
                                       │
                                       ▼ (Khi người dùng đặt câu hỏi)
                        5. 🔀 Hybrid Search (RRF Fusion)
                          + Role Access Enforcement
                                       │
                                       ▼
                        6. 🎯 Cross-Encoder Reranker
                         (ms-marco-MiniLM-L-6-v2)
                                       │
                                       ▼
                        7. 🤖 Top-K Context -> LLM Chatbot
```

---

## 📂 3. Cấu Trúc Thư Mục & Phân Phối Module Code

```text
data/
└── processed/
    ├── markdown/           <-- Dữ liệu Markdown thô từ Phase 1 (GIỮ NGUYÊN 100%)
    ├── cleaned_markdown/   <-- Markdown đã làm sạch & chuẩn hóa Heading
    └── chunks/             # File JSON lưu trữ payload chunks & metadata
data/
├── chroma/                 <-- Thư mục lưu trữ ChromaDB Vector Database Persistence
└── bm25_index.pkl          <-- File lưu trữ Serialized BM25 Index

src/
├── preprocess/
│   ├── markdown_normalizer.py     <-- Xóa OCR noise, Unicode NFC, xóa duplicate headers
│   ├── structure_normalizer.py    <-- Chuẩn hóa cây Heading, phát hiện Bảng/List/Code block
│   ├── structure_aware_chunker.py <-- Phân đoạn 300-600 tokens & đính kèm Metadata
│   └── markdown_pipeline.py       <-- Điều phối Pipeline Chunking từ Markdown
├── embedding/
│   └── embedder.py                <-- Service tạo SBERT Embeddings (all-MiniLM-L6-v2)
└── vectordb/
    ├── chroma_store.py            <-- Quản lý ChromaDB Vector DB & Role Filter
    ├── bm25_store.py              <-- Quản lý BM25 Index & Exact Match
    ├── hybrid_search.py           <-- Reciprocal Rank Fusion (RRF) Hybrid Search
    └── reranker.py                <-- Service Reranking bằng Cross-Encoder (MS-MARCO)

eval/
├── dataset.json                   <-- Bộ câu hỏi ground-truth đánh giá thực tế
├── evaluator.py                   <-- Engine đo đạc Hit Rate, MRR, Role Compliance
└── results/
    └── eval_report.json           <-- Báo cáo kết quả đánh giá RAG Benchmark

scripts/
├── run_markdown_pipeline.py       <-- Script CLI 1: Chạy Preprocessing & Chunking
├── index_chunks.py                <-- Script CLI 2: Embed & Index vào ChromaDB + BM25
└── run_evaluation.py              <-- Script CLI 3: Chạy Đánh giá Benchmark RAG

tests/
└── test_retrieval_and_eval.py     <-- Pytest suite kiểm thử tự động toàn bộ RAG Pipeline
```

---

## 🔬 4. Giải Thích Chi Tiết 5 Bước Trong Pipeline Giai Đoạn 2

> [!IMPORTANT]
> **Nguyên tắc cốt lõi:** **Bảo toàn tính toàn vẹn ngữ nghĩa của Bảng biểu & Danh sách — Phân quyền chặt chẽ theo Role người dùng — Rerank chính xác trước khi gửi vào LLM**.

### 🛠️ Bước 1: Làm sạch & Chuẩn hóa Cấu trúc (`MarkdownNormalizer` & `StructureNormalizer`)
- **Xóa OCR Noise**: Xóa các dòng ký tự rác do EasyOCR/Tesseract sinh ra (ví dụ: `, a £ ~. “ -`, `_ + = z <<.“ .`).
- **Unicode & Headers**: Chuẩn hóa Unicode NFC, xóa các tiêu đề lặp lại liên tiếp (như `## 00:00\n## 00:00` trong video transcript).
- **Chuẩn hóa cây Heading**: Ép các Heading nhảy cấp sai định dạng về phân cấp chuẩn (`#` $\rightarrow$ `##` $\rightarrow$ `###`).

### ✂️ Bước 2: Structure-Aware Chunking (`StructureAwareChunker`)
- **Kích thước chunk**: Giữ trong khoảng **300 – 600 tokens** (tương đương 1,200 – 2,400 ký tự).
- **Khối nguyên tử (Atomic Blocks)**: Bảng Markdown (`| Col 1 | Col 2 |`), Bullet Lists, và Code Blocks được coi là 1 khối không thể chia nhỏ. Nếu Section chứa bảng, toàn bộ bảng sẽ được giữ trọn vẹn trong 1 chunk.
- **Thêm Context Prefix**: Đầu mỗi chunk được đính kèm thông tin vị trí:
  `[Document: SALE003 | Role: sales | Section: Quy trình tư vấn | Slide: 2]`

### 🗄️ Bước 3: Dual Indexing (ChromaDB + BM25)
- **Embedding Service**: Dùng `sentence-transformers/all-MiniLM-L6-v2` tạo vector 384 chiều, tự động chuẩn hóa vector về độ dài đơn vị (`normalize_embeddings=True`).
- **ChromaDB Store**: Lưu trữ vectors kèm metadata (`role`, `document_id`, `section`, `heading_path`, `source`).
- **BM25 Store**: Tách từ Tiếng Việt & Tiếng Anh, xây dựng chỉ mục tần suất từ `BM25Okapi` và lưu thành file `.pkl`.

### 🔀 Bước 4: Hybrid Search & Role Access Enforcement (`HybridRetriever`)
- **Phân quyền người dùng (Role Isolation)**:
  | Vai trò Người Dùng (`user_role`) | Được quyền truy cập các Chunks có `role` |
  | :--- | :--- |
  | `sales` | `["sales", "general"]` |
  | `accounting` | `["accounting", "general"]` |
  | `technician` | `["technician", "general"]` |
  | `general` | `["general"]` |
- **Thuật toán Reciprocal Rank Fusion (RRF)**:
  $$RRF\_Score(d) = w_{vector} \cdot \frac{1}{k + rank_{vector}(d)} + w_{bm25} \cdot \frac{1}{k + rank_{bm25}(d)}$$
  (với hằng số chuẩn $k = 60$).

### 🎯 Bước 5: Cross-Encoder Reranking (`RerankerService`)
- Ứng viên thu được từ Hybrid Search (ví dụ Top-15) được đưa qua mô hình Cross-Encoder `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- Mô hình đánh giá mối tương quan trực tiếp giữa cặp `(Query, Chunk Content)` để chọn ra **Top-K (ví dụ Top-5)** có chất lượng cao nhất đưa vào Prompt của LLM Chatbot.

---

## 🚀 5. Hướng Dẫn Chạy Pipeline (Lệnh CLI Cho Teammate)

### 5.1 Khởi tạo Môi Trường Virtualenv
```powershell
# Mở Terminal tại E:\P-223 và kích hoạt venv
.venv\Scripts\Activate.ps1

# Cài đặt thư viện (nếu chưa cài)
pip install -r requirements.txt
```

### 5.2 Bước 1: Chạy Làm Sạch & Cắt Chunking
```powershell
python scripts/run_markdown_pipeline.py
```
> **Đầu ra:** Các file `.md` sạch tại `data/processed/cleaned_markdown/` và các file `.json` chunks tại `data/processed/chunks/`.

### 5.3 Bước 2: Chạy Tạo Embedding & Indexing
```powershell
python scripts/index_chunks.py
```
> **Đầu ra:** Khởi tạo Vector DB tại `data/chroma/` và file BM25 tại `data/bm25_index.pkl` (Index thành công 1,133 chunks).

### 5.4 Bước 3: Chạy Benchmark Đánh Giá Hệ Thống
```powershell
python scripts/run_evaluation.py
```
> **Đầu ra:** Xuất bảng kết quả và lưu file báo cáo JSON chi tiết tại `eval/results/eval_report.json`.

### 5.5 Bước 4: Chạy Kiểm Thử Tự Động (Unit Tests)
```powershell
pytest tests/test_retrieval_and_eval.py -v
```

---

## 💻 6. Hướng Dẫn Tích Hợp Vào Code Python (Sử Dụng Cho RAG & Chatbot)

### 6.1 Sử dụng Module Retrieval & Rerank Đơn Giản
Các teammate khác có thể gọi trực tiếp module này trong code ứng dụng:

```python
from src.vectordb.hybrid_search import HybridRetriever
from src.vectordb.reranker import RerankerService

# 1. Khởi tạo các Service
retriever = HybridRetriever()
reranker = RerankerService()

# 2. Đầu vào truy vấn
query_text = "Thời gian bảo hành pin LFP và ắc quy 12V xe máy điện VinFast là bao nhiêu năm?"
user_role = "technician"  # Chọn vai trò: "sales", "accounting", "technician", hoặc "general"

# 3. Hybrid Search (Lấy Top 15 ứng viên)
candidates = retriever.search(query_text=query_text, top_k=15, role=user_role)

# 4. Rerank bằng Cross-Encoder (Chọn Top 5 context tốt nhất)
top_k_chunks = reranker.rerank(query_text=query_text, candidates=candidates, top_k=5)

# 5. In kết quả thu được
for rank, chunk in enumerate(top_k_chunks, start=1):
    print(f"[{rank}] Rerank Score: {chunk['rerank_score']:.4f}")
    print(f"Document ID : {chunk['metadata'].get('document_id')}")
    print(f"Section     : {chunk['metadata'].get('section')}")
    print(f"Content     :\n{chunk['content']}\n" + "=" * 40)
```

---

### 6.2 Lớp Tích Hợp Hoàn Chỉnh Với LLM Chatbot (`RAGChatbotEngine`)

Teammate có thể tham khảo lớp bên dưới để dựng dịch vụ Chatbot trả lời câu hỏi:

```python
import os
from typing import List, Dict, Any
from src.vectordb.hybrid_search import HybridRetriever
from src.vectordb.reranker import RerankerService


class RAGChatbotEngine:
    """
    Engine Chatbot RAG hoàn chỉnh kết hợp Hybrid Search,
    Cross-Encoder Reranking và LLM Generation.
    """

    def __init__(self):
        self.retriever = HybridRetriever()
        self.reranker = RerankerService()

    def get_formatted_context(self, query: str, user_role: str, top_k: int = 5) -> str:
        """Truy xuất và định dạng các khối ngữ cảnh cho Prompt LLM."""
        # 1. Hybrid Search
        candidates = self.retriever.search(query_text=query, top_k=15, role=user_role)

        # 2. Rerank
        top_chunks = self.reranker.rerank(query_text=query, candidates=candidates, top_k=top_k)

        # 3. Định dạng chuỗi Context
        context_parts = []
        for i, chunk in enumerate(top_chunks, start=1):
            meta = chunk.get("metadata", {})
            header = f"[TÀI LIỆU {i}: {meta.get('document_id', 'N/A')} | Vai trò: {meta.get('role', 'N/A')} | Mục: {meta.get('section', 'N/A')}]"
            context_parts.append(f"{header}\n{chunk['content']}")

        return "\n\n=========================================\n\n".join(context_parts)

    def generate_answer(self, user_query: str, user_role: str) -> Dict[str, Any]:
        # Bước 1: Lấy ngữ cảnh truy xuất
        context_str = self.get_formatted_context(query=user_query, user_role=user_role, top_k=5)

        # Bước 2: Dựng System Prompt cho LLM
        system_prompt = f"""Bạn là Trợ lý AI tư vấn tài liệu nội bộ VinFast.
Hãy trả lời câu hỏi dựa CHÍNH XÁC và CHỈ DỰA VÀO các đoạn văn bản ngữ cảnh dưới đây.
Nếu thông tin không có trong ngữ cảnh, hãy phản hồi: "Không tìm thấy thông tin phù hợp trong tài liệu được cấp quyền."

================ CONTEXT BẮT ĐẦU ================
{context_str}
================ CONTEXT KẾT THÚC ================

YÊU CẦU:
- Trả lời rõ ràng, đầy đủ ý, trích dẫn bảng biểu hoặc con số chính xác nếu có.
- Không tự suy đoán hoặc đưa thông tin bên ngoài ngữ cảnh.
"""

        # Bước 3: Gửi đến LLM (Ví dụ gọi OpenAI / Gemini API)
        # response = client.chat.completions.create(
        #     model="gpt-4o-mini",
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": user_query}
        #     ],
        #     temperature=0.1
        # )
        # answer_text = response.choices[0].message.content

        return {
            "query": user_query,
            "user_role": user_role,
            "context_used": context_str,
            "system_prompt": system_prompt,
        }


# --- Demo chạy Chatbot ---
if __name__ == "__main__":
    bot = RAGChatbotEngine()
    result = bot.generate_answer(
        user_query="Thời gian bảo hành xe máy điện pin LFP là bao nhiêu năm?", user_role="technician"
    )
    print("Dự thảo System Prompt gửi tới LLM:")
    print(result["system_prompt"][:500] + "\n...")
```

---

## 📊 7. Kết Quả Benchmark Đánh Giá (Evaluation Benchmark)

Báo cáo kết quả đánh giá thực tế trên bộ dataset testcase (`eval/dataset.json`):

```text
=================================================================
           RAG RETRIEVAL & RERANKING EVALUATION BENCHMARK
=================================================================
 Total Evaluation Queries : 6
 Top-K Context Window    : 5
 Hit Rate @ K (Recall)   : 83.33% (100% đối với câu hỏi hợp lệ)
 Mean Reciprocal Rank    : 0.7500
 Role Access Compliance  : 100.00% (An toàn bảo mật tuyệt đối)
 Table Retrieval Accuracy: 100.00% (Bảng biểu truy xuất chính xác)
 Section Match Accuracy  : 50.00%
=================================================================
```

---

## ✅ 8. Tiêu Chí Nghiệm Thu Giai Đoạn 2

1. **Chuẩn hóa & Cắt Chunk**: Cắt chunk 300–600 tokens, 100% bảng biểu và danh sách không bị băm nhỏ ngang chừng.
2. **Indexing chính xác**: Index thành công 1,133 chunks vào ChromaDB và BM25 mà không bị lỗi trùng lặp ID (`DuplicateIDError`).
3. **Phân quyền tuyệt đối**: Người dùng role `sales` không thể truy vấn được tài liệu riêng của `technician` hay `accounting`.
4. **Hiệu năng Rerank**: Cross-Encoder chấm điểm và đưa đúng thông tin cốt lõi lên Top 1 - Top 2.
5. **Dễ dàng tích hợp**: Cung cấp giao diện Python đơn giản cho các teammate tiếp tục phát triển giao diện Web/Chatbot RAG.
