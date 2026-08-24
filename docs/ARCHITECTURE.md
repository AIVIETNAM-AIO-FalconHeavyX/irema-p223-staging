# Architecture Document - AI Agent Hỗ trợ Onboarding ĐLPP Xe Máy Điện (Team T223)

## System Overview

Hệ thống AI Agent hỗ trợ onboarding và vận hành cho **Đại lý Phân phối (ĐLPP) Xe máy Điện** được thiết kế theo kiến trúc **Dynamic Agent Controller & Intent Router**. Kiến trúc cho phép hệ thống phân loại linh hoạt ý định người dùng (Intent Classification), trích xuất ngữ cảnh dòng xe/mã lỗi, phân quyền tra cứu tài liệu theo vai trò (RBAC Security), và tự động chuyển tiếp yêu cầu tới IT/Quản lý khi dữ liệu không đủ.

## Overall System Architecture Diagram

```mermaid
graph TB
    %% ==========================================
    %% 1. TẦNG TIẾP NHẬN & XỬ LÝ FILE (OWNER INGESTION)
    %% ==========================================
    subgraph INPUT_SEC [1. Ingestion, Security & Fuzzy Match Pipeline]
        OWNER([Dealer Owner / Admin]) -->|Upload File + Gắn Role| API_UP[FastAPI Ingestion Endpoint]
        
        API_UP --> VAL[MIME & Size Validation]
        VAL --> SCAN[ClamAV Virus & Macro Scan]
        SCAN --> FUZZY{Fuzzy Match Tên File<br/>trong Database?}
        
        %% Nhánh file trùng (Update version)
        FUZZY -->|Trùng: Update| DEL_OLD[Xóa File Cũ trên MinIO / S3]
        DEL_OLD --> UP_NEW[Upload Bản Mới & Cập nhật Version]
        
        %% Nhánh file mới
        FUZZY -->|Mới: New Document| GEN_UUID[Tạo Safe UUID Filename]
        GEN_UUID --> UP_MINIO[Upload Asset lên MinIO / AWS S3]
    end

    %% ==========================================
    %% 2. TẦNG AI CLASSIFIER & QUIZ GENERATION
    %% ==========================================
    subgraph AGENT_LAYER [2. Classifier & Knowledge Agent]
        UP_MINIO --> AGENT[Classifier Agent: LLM / GPT Engine]
        UP_NEW -->|Update Quiz cho file v2| AGENT
        
        AGENT --> CLASSIFY[Xác định Bước Onboarding: step_id]
        AGENT --> GEN_QUIZ[Tự động sinh bộ Quiz: 3 câu hỏi đánh giá]
    end

    %% ==========================================
    %% 3. TẦNG LƯU TRỮ & ĐỒNG BỘ TIẾN ĐỘ (DB & NOTIFICATION)
    %% ==========================================
    subgraph STORAGE_NOTIF [3. Storage & State Management]
        CLASSIFY & GEN_QUIZ --> DB_INSERT[Thêm/Sửa Bảng Onboarding_Steps]
        DB_INSERT --> PG[(PostgreSQL Database)]
        
        %% Tạo thông báo cho nhân viên đã hoàn thành trước đó
        DB_INSERT --> PENDING[Tạo PendingUpdate cho Nhân viên đã tốt nghiệp]
        PENDING --> PG
    end

    %% ==========================================
    %% 4. TẦNG GIAO DIỆN & POP-UP MODAL (FRONTEND)
    %% ==========================================
    subgraph FRONTEND_LAYER [4. User Experience & Dynamic Workflow]
        USER((Nhân viên: Sale / KTV / KT)) -->|1. Đăng nhập / Auth Token| AUTH[Auth Context: role, user_id]
        
        PG -->|2. Check PendingUpdate| POPUP[Frontend Pop-up / Modal: Tài liệu mới]
        POPUP --> SHOW_QUIZ[Làm Quiz 3 câu hỏi để hoàn tất cập nhật]
        
        UP_MINIO -->|Stream Binary Content| UI_VIEW[React UI: PDF / Video Viewer]
        UP_NEW --> UI_VIEW
        AUTH --> UI_VIEW
    end

    %% ==========================================
    %% 5. TẦNG RAG CHATBOT INGESTION (TRACK 2 - CHI'S PIPELINE)
    %% ==========================================
    subgraph CHI_RAG_FLOW [5. Track 2: RAG Pipeline - Chi's Ingestion]
        UP_MINIO -.->|S3/MinIO Event / Webhook Trigger| FETCH[Kéo Stream File từ Storage]
        UP_NEW -.-> FETCH
        
        FETCH --> EXTRACT[Parser Engine: Docling / Faster-Whisper / OCR]
        EXTRACT --> CLEAN[Làm sạch Markdown & Loại bỏ PII]
        CLEAN --> CHUNK[Structure-Aware Chunking: 300-600 tokens]
        CHUNK --> EMBED[SBERT all-MiniLM-L6-v2 Embedding]
        
        EMBED --> VECTOR[(ChromaDB + BM25 Hybrid Index)]
    end

    %% ==========================================
    %% 6. RUNTIME COPILOT CHATBOT (MERGE POINT)
    %% ==========================================
    subgraph MERGE_COPILOT [6. Runtime Copilot Merge Layer]
        UI_VIEW -->|Hỏi đáp tại Bước X kèm Context| COPILOT[FastAPI RAG Copilot]
        AUTH -.->|Truyền Role & Step ID| COPILOT
        
        COPILOT -->|Role-Filtered Search| VECTOR
        VECTOR -->|Rerank Context| RERANK[Cross-Encoder Reranker]
        RERANK --> LLM_GEN[LLM Generator: Trả lời kèm Citation]
        LLM_GEN --> UI_VIEW
    end

    %% ==========================================
    %% ĐỊNH NGHĨA MÀU SẮC (STYLING)
    %% ==========================================
    classDef secStyle fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef agentStyle fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef dbStyle fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;
    classDef feStyle fill:#fce4ec,stroke:#c2185b,stroke-width:2px;
    classDef ragStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    
    class INPUT_SEC secStyle;
    class AGENT_LAYER agentStyle;
    class STORAGE_NOTIF dbStyle;
    class FRONTEND_LAYER feStyle;
    class CHI_RAG_FLOW,MERGE_COPILOT ragStyle;
```

---

## Agent Pipeline Flow (LangGraph StateGraph)

```mermaid
graph LR
    START([User Input]) --> EntityExt[Entity Extractor]
    EntityExt --> Rewriter[Query Rewriter]
    Rewriter --> Controller{Controller Router}

    Controller -->|RAG_SEARCH| RAGNode[RAG Node]
    Controller -->|WORKFLOW| WorkflowNode[Workflow Node]
    Controller -->|TROUBLESHOOTING| DiagnosticNode[Troubleshooting Node]
    Controller -->|CREATE_TICKET| EscalationNode[Escalation Ticket Node]
    Controller -->|GENERAL_QA| ResponseNode[Response Generator]

    RAGNode --> Eval{Confidence < 0.7?}
    WorkflowNode --> ResponseNode
    DiagnosticNode --> ResponseNode

    Eval -->|Yes| EscalationNode
    Eval -->|No| ResponseNode
    EscalationNode --> ResponseNode

    ResponseNode --> END([Output Response])
```

---

## Components Detail

### 1. Entity Extractor Node (`entity_extractor.py`)
- Trích xuất tự động **Dòng xe máy điện** (`Klara S`, `Feliz S`, `Vento S`, `Evo200`) và **Mã lỗi kỹ thuật** (`P01`, `E03`, `BMS_OVERHEAT`).

### 2. Query Rewriter & Role Context Enhancer (`query_rewriter.py`)
- Chuẩn hóa thuật ngữ viết tắt của ngành xe điện và bổ sung thông tin vai trò người dùng (`sales`, `accounting`, `technician`, `manager`, `it`).

### 3. Dynamic Controller Router (`controller.py`)
- Node phân loại Intent câu hỏi và điều hướng luồng xử lý tới các Node chuyên biệt.

### 4. Role-Filtered RAG Node (`rag_node.py`)
- Tìm kiếm tài liệu nghiệp vụ/chính sách với bộ lọc **RBAC Security** (ngăn nhân viên Sales xem chiết khấu/giá nhập kho dành riêng cho Manager).
- Đánh giá chỉ số `rag_confidence`. Nếu dưới 0.7, tự động chuyển luồng sang `Escalation Node`.

### 5. Role Workflow Navigator Node (`workflow_node.py`)
- Cung cấp sơ đồ quy trình bán hàng, kế toán, bảo hành và lộ trình tự học onboarding theo vai trò.

### 6. Troubleshooting & Diagnostic Node (`troubleshooting_node.py`)
- Trả về bảng hướng dẫn xử lý sự cố nhanh tại xưởng dịch vụ kèm các **Cảnh báo an toàn điện (CAUTION Alert)**.

### 7. Escalation Ticket Creator (`escalation_node.py`)
- Khởi tạo Ticket hỗ trợ có cấu trúc (`ticket_id`, `vehicle_model`, `error_code`, `department`) gửi IT hoặc Quản lý ĐLPP theo yêu cầu tại FR-15 & US-05.

### 8. Grounded Response Generator (`response_generator.py`)
- Tổng hợp phản hồi Markdown chuẩn hóa kèm trích dẫn nguồn tài liệu ([Trang X - File Y]) và đề xuất hành động tiếp theo.

---

## Design Decisions (ADR)

| Quyết định | Giải pháp lựa chọn | Lý do thiết kế |
|------------|-------------------|----------------|
| Kiến trúc Agent | LangGraph Dynamic Controller | Cho phép chuyển hướng linh hoạt theo Intent & Confidence thay vì luồng tuyến tính cố định. |
| Security | RBAC Filter at RAG Retrieval Level | Đảm bảo nhân viên mới không tra cứu được các thông tin tài chính/chiết khấu nhạy cảm. |
| Xử lý câu hỏi khó/lỗi | Auto IT/Manager Escalation Ticket Payload | Đáp ứng yêu cầu PRD (FR-15 & US-05): Không bịa câu trả lời khi thiếu dữ liệu. |
| Format câu trả lời | Markdown + Alerts + Citations | Giúp Kỹ thuật viên & Sales đọc nhanh checklist từng bước thay vì các đoạn văn dài. |
