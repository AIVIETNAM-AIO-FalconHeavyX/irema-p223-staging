# 📐 VF-Onboarding Copilot — Architecture Diagrams

| Trường | Nội dung |
| :--- | :--- |
| **Tài liệu** | ARCHITECTURE_DIAGRAMS — Gate 2 |
| **Phiên bản** | 1.0.0 |
| **Ngày** | 12/08/2026 |
| **Nguồn gốc** | ARCHITECTURE_DIAGRAM.md |

---

## 1. Sơ đồ Kiến trúc Tổng thể — System Context (C4 Model)

> Toàn bộ luồng từ User → Client → Gateway → Guardrails → Core Runtime → Skills → Data → Output → Frontend

```mermaid
flowchart TB
    classDef person   fill:#1e3a5f,stroke:#4a90d9,color:#e8f4fd,stroke-width:2px
    classDef client   fill:#1e3a5f,stroke:#4a90d9,color:#e8f4fd,stroke-width:2px
    classDef gateway  fill:#1e3d20,stroke:#4caf50,color:#e8f8e8,stroke-width:2px
    classDef guard    fill:#4a0e0e,stroke:#ef5350,color:#fde8e8,stroke-width:2px
    classDef core     fill:#3d2800,stroke:#ffa726,color:#fff9e6,stroke-width:2px
    classDef skill    fill:#0e3320,stroke:#26a65b,color:#e8fdf3,stroke-width:2px
    classDef data     fill:#1e0e3d,stroke:#7c4dff,color:#f3e8fd,stroke-width:2px
    classDef output   fill:#0e2240,stroke:#29b6f6,color:#e8f3fd,stroke-width:2px
    classDef ai       fill:#1a0e3d,stroke:#9b59b6,color:#e8e8fd,stroke-width:2px
    classDef danger   fill:#4a0e0e,stroke:#ff1744,color:#fde8e8,stroke-width:3px,font-weight:bold

    %% USERS
    KTV["👤 Kỹ Thuật Viên\n(technician)"]:::person
    LT["👤 Tổ Trưởng KT\n(lead_tech)"]:::person
    SM["👤 Quản Lý Xưởng\n(service_manager)"]:::person
    IT["👤 IT Admin\n(it_admin)"]:::person

    %% CLIENT LAYER
    subgraph L1["🖥️ LAYER 1 — CLIENT (Vercel)"]
        direction LR
        RS["Role Selector\n4 vai trò"]:::client
        CW["Chat Window\nMarkdown Renderer"]:::client
        CB["CAUTION Banner\n🔴 High Voltage Alert"]:::danger
        CA["Citation Accordion\nXem nguồn tài liệu"]:::client
        SF["Static Form Modal\nAuto-fill context"]:::client
        TC2["Ticket Confirmation\nTCK-YYYYMMDD-XXXXXX"]:::client
    end

    %% API GATEWAY
    subgraph L2["🔀 LAYER 2 — API GATEWAY (Render.com)"]
        direction LR
        RL["Rate Limiter\n20 req/min"]:::gateway
        MW["CORS & Session\nMiddleware"]:::gateway
        R1["POST /api/v1/chat"]:::gateway
        R2["POST /api/v1/tickets"]:::gateway
        R3["GET /api/v1/tickets"]:::gateway
        R4["PATCH /api/v1/tickets/{id}"]:::gateway
        R5["GET /api/v1/health"]:::gateway
    end

    %% INPUT GUARDRAILS
    subgraph L3A["🛡️ LAYER 3A — INPUT GUARDRAILS (10 Checkers, less than 80ms)"]
        IG["GRD-01 Length · GRD-02 Encoding · GRD-03 Toxic\nGRD-04 Prompt Injection · GRD-05 Jailbreak\nGRD-06 Domain · GRD-07 PII Masker\nGRD-08 SQL/XSS · GRD-09 Spam\nGRD-10 Prompt Firewall (Semantic less than 50ms)"]:::guard
    end

    %% CORE RUNTIME
    subgraph L3B["⚙️ LAYER 3B — CORE RUNTIME"]
        direction TB
        QN["🔤 Query Normalizer\nEV Dictionary + Role Context\nless than 5ms · No LLM"]:::core
        subgraph RTR["🧭 Lightweight Router (4-Layer)"]
            direction LR
            L1C["L1 Cache\nless than 1ms ~10%"]:::core
            L2T["L2 Trie\nless than 10ms ~75%"]:::core
            L3E["L3 Embedding\nless than 80ms ~12%"]:::core
            L4L["L4 LLM\nless than 500ms max 3%"]:::core
            L1C --> L2T --> L3E --> L4L
        end
        OE["🎛️ LangGraph Orchestration\nStateGraph Controller\nAgentState Management"]:::core
        QN --> RTR --> OE
    end

    %% SKILL MODULES
    subgraph L4["🔧 LAYER 4 — SKILL MODULES"]
        direction LR
        WF["📋 Workflow Guidance\nYAML Template Load\nNo LLM · less than 50ms"]:::skill
        PC["🤖 Policy Copilot\nRAG Engine + Citations\nLLM · less than 1.5s"]:::skill
        EL["🔍 Error Code Lookup\nRegex + Semantic\nNo LLM · less than 200ms"]:::skill
        TK["🎫 Ticket Skill\nCreate TCK-YYYYMMDD-XXXXXX\nPriority: urgent/high/normal"]:::skill
    end

    %% DATA & RETRIEVAL
    subgraph L5["🗄️ LAYER 5 — DATA & RETRIEVAL"]
        direction LR
        subgraph KB["ChromaDB — Knowledge Base"]
            TD["technician_docs\nPDF · DOCX · XLSX\nChunk max 500 tokens"]:::data
            EC["error_codes\n30 P-codes · 10 BMS · 10 E-codes"]:::data
        end
        subgraph HYB["Hybrid Retrieval Engine"]
            BM["BM25 Lexical\nSearch"]:::data
            VS["Vector Semantic\nSearch"]:::data
            RF["RRF Fusion\n+ Reranker"]:::data
            BM --> RF
            VS --> RF
        end
        IP["Offline Ingestion Pipeline\nCLI · Chunker · RBAC Tagger\nCaution Tagger · Embedding"]:::data
        DB["Ticket & Audit DB\nPostgreSQL\nLogs · Security Events"]:::data
    end

    %% OUTPUT DEFENSE
    subgraph L6["✅ LAYER 6 — OUTPUT DEFENSE & FORMATTER"]
        direction LR
        OG["OUT-01 Citation · OUT-02 Hallucination\nOUT-03 RBAC Leak · OUT-04 Safety\nOUT-05 Language · OUT-06 Length\nOUT-07 PII Output"]:::output
        FMT["Response Formatter\nMarkdown Checklist\nError Table · Caution Banner\nCitation Accordion"]:::output
        OG --> FMT
    end

    %% EXTERNAL AI
    subgraph L7["🤖 LAYER 7 — EXTERNAL AI SERVICES"]
        direction LR
        PM["Primary LLM\nGemini / Claude API\nContext max 2000 tokens"]:::ai
        FB["Fallback LLM\nAuto-switch on failure\nTransparent to user"]:::ai
        PM -.->|"FAIL/TIMEOUT"| FB
    end

    %% CONNECTIONS
    KTV --> RS
    LT  --> RS
    SM  --> RS
    IT  --> RS
    RS  --> CW
    CW  -->|"HTTP POST"| RL
    RL  --> MW --> R1
    R1  --> IG
    IG  -->|"PASS less than 80ms"| QN
    IG  -->|"FAIL HTTP 400/429"| DB

    OE  -->|"WORKFLOW"| WF
    OE  -->|"RAG_POLICY"| PC
    OE  -->|"ERROR_LOOKUP"| EL
    OE  -->|"STATIC_FORM"| TK

    WF  <-->|"YAML Load"| KB
    EL  <-->|"Regex + Query"| EC
    PC  --> HYB
    HYB <--> TD
    HYB <--> EC

    PC  -->|"conf >= 0.70"| PM
    PC  -->|"conf >= 0.70"| FB

    WF  --> OG
    EL  --> OG
    PC  --> OG
    TK  --> DB

    FMT -->|"HTTP 200"| CW
    CW  --> CB
    CW  --> CA
    CW  --> SF
    SF  -->|"POST /api/v1/tickets"| R2
    R2  --> TK
    R3  --> DB
    R4  --> DB
    IT  -->|"Manage tickets"| R3

    IP  -->|"Offline ingest"| TD
    IP  -->|"Offline ingest"| EC
```

---

## 2. C4 Model — Container Diagram (Chi tiết)

> Luồng: Frontend SPA → FastAPI Backend → LangGraph Agent → ChromaDB / PostgreSQL / LLM APIs / YAML

```mermaid
flowchart LR
    classDef client  fill:#1e3a5f,stroke:#4a90d9,color:#e8f4fd,stroke-width:2px
    classDef backend fill:#1e3d20,stroke:#4caf50,color:#e8f8e8,stroke-width:2px
    classDef agent   fill:#3d2800,stroke:#ffa726,color:#fff9e6,stroke-width:2px
    classDef store   fill:#1e0e3d,stroke:#7c4dff,color:#f3e8fd,stroke-width:2px
    classDef ext     fill:#1a0e3d,stroke:#9b59b6,color:#e8e8fd,stroke-width:2px

    FE["Frontend SPA\nNext.js / Vercel\nPort: 443 HTTPS\n\nComponents:\n- Role Selector\n- Chat Window\n- CAUTION Banner\n- Citation Accordion\n- Static Form Modal"]:::client

    API["FastAPI Backend\nRender.com\nPort: 8000\n\nEndpoints:\nPOST /api/v1/chat\nPOST /api/v1/tickets\nGET /api/v1/tickets\nPATCH /api/v1/tickets/{id}\nGET /api/v1/health\n\nMiddleware:\n- Rate Limit 20/min\n- CORS\n- Session"]:::backend

    AG["LangGraph Agent\nStateGraph Engine\n\nNodes:\n- input_guardrails\n- normalizer\n- router\n- workflow_skill\n- policy_skill\n- error_skill\n- ticket_skill\n- output_guardrails\n- formatter"]:::agent

    VDB["ChromaDB\nVector Store\n\nCollections:\n- technician_docs\n- error_codes\n\nChunk max 500 tokens\nRBAC metadata\nCaution tags"]:::store

    SQL["PostgreSQL\nRelational DB\n\nTables:\n- tickets\n- audit_logs\n- guardrail_events\n- sessions"]:::store

    LLM["LLM APIs\nExternal Services\n\nPrimary: Gemini/Claude\nFallback: Auto-switch\nContext: max 2000 tokens"]:::ext

    YAML["YAML Templates\nFile System\n\n- PDI Klara S\n- Bao duong LFP\n- Tiep nhan xe hong"]:::store

    FE  -->|"HTTPS JSON"| API
    API -->|"Python call"| AG
    AG  -->|"Query"| VDB
    AG  -->|"Read/Write"| SQL
    AG  -->|"gRPC/HTTPS"| LLM
    AG  -->|"File I/O"| YAML
```

---

## 3. Module Dependency Map

> Luồng phụ thuộc giữa 15 module từ RBAC → Ingestion → Input Guards → Router → Orchestration → Skills → Output → Frontend

```mermaid
graph LR
    classDef mod fill:#1e3a5f,stroke:#4a90d9,color:#e8f4fd,stroke-width:2px

    MOD02["MOD-02\nRBAC Auth"]:::mod
    MOD03["MOD-03\nIngestion Pipeline"]:::mod
    MOD04["MOD-04\nInput Guardrails"]:::mod
    MOD05["MOD-05\nQuery Normalizer"]:::mod
    MOD06["MOD-06\nRouter 4-Layer"]:::mod
    MOD07["MOD-07\nOrchestration"]:::mod
    MOD08["MOD-08\nWorkflow Skill"]:::mod
    MOD09["MOD-09\nPolicy RAG Skill"]:::mod
    MOD10["MOD-10\nError Lookup Skill"]:::mod
    MOD11["MOD-11\nTicket Skill"]:::mod
    MOD12["MOD-12\nHybrid Retrieval"]:::mod
    MOD13["MOD-13\nLLM + Output Guard"]:::mod
    MOD14["MOD-14\nFormatter"]:::mod
    MOD15["MOD-15\nFrontend UI"]:::mod
    MOD16["MOD-16\nAPI Layer"]:::mod

    MOD02 --> MOD04
    MOD02 --> MOD07
    MOD03 --> MOD12
    MOD04 --> MOD05
    MOD05 --> MOD06
    MOD06 --> MOD07
    MOD07 --> MOD08
    MOD07 --> MOD09
    MOD07 --> MOD10
    MOD07 --> MOD11
    MOD08 --> MOD14
    MOD09 --> MOD12
    MOD12 --> MOD13
    MOD13 --> MOD14
    MOD10 --> MOD14
    MOD11 --> MOD14
    MOD14 --> MOD16
    MOD15 --> MOD16
    MOD16 --> MOD04
```

---

## 4. Deployment Architecture

> Luồng triển khai: Vercel (Frontend) → Render.com (Backend + Agent + DB) → External AI APIs

```mermaid
flowchart TB
    classDef cloud fill:#1e3a5f,stroke:#4a90d9,color:#e8f4fd,stroke-width:2px
    classDef infra fill:#1e3d20,stroke:#4caf50,color:#e8f8e8,stroke-width:2px
    classDef ext   fill:#1a0e3d,stroke:#9b59b6,color:#e8e8fd,stroke-width:2px
    classDef dev   fill:#3d2800,stroke:#ffa726,color:#fff9e6,stroke-width:2px

    subgraph VERCEL["☁️ Vercel (CDN Global)"]
        FE["Next.js Frontend\nSSR + Static\nHTTPS · CDN"]:::cloud
    end

    subgraph RENDER["☁️ Render.com (Backend)"]
        API["FastAPI\nPython 3.11\nPort 8000"]:::infra
        AGENT["LangGraph Agent\nIn-process"]:::infra
        CHROMA["ChromaDB\nPersistent Volume\n/data/chroma"]:::infra
        PG["PostgreSQL\nRender DB\nSSL enforced"]:::infra
    end

    subgraph EXTERNAL["🌐 External AI APIs"]
        GEM["Google Gemini API\ngemini-1.5-pro"]:::ext
        CLA["Anthropic Claude API\nclaude-3-sonnet"]:::ext
    end

    DEV["💻 Dev Machine\nOffline Ingestion\nCLI Tool"]:::dev

    FE    -->|"HTTPS"| API
    API   --> AGENT
    AGENT --> CHROMA
    AGENT --> PG
    AGENT -->|"HTTPS"| GEM
    AGENT -->|"HTTPS (Fallback)"| CLA
    DEV   -->|"python ingest.py (offline, one-time)"| CHROMA
```

---

## 5. Security & RBAC Model

> Luồng phân quyền: 4 vai trò → các tập tài liệu được phép truy cập

```mermaid
flowchart TD
    classDef role   fill:#1e3a5f,stroke:#4a90d9,color:#e8f4fd,stroke-width:2px
    classDef access fill:#0e3320,stroke:#26a65b,color:#e8fdf3,stroke-width:2px
    classDef deny   fill:#4a0e0e,stroke:#ef5350,color:#fde8e8,stroke-width:2px

    IT["it_admin"]:::role
    SM["service_manager"]:::role
    LT["lead_tech"]:::role
    TC["technician"]:::role

    A1["technician_docs ✅"]:::access
    A2["error_codes ✅"]:::access
    A3["lead_tech_docs ✅"]:::access
    A4["service_mgr_docs ✅"]:::access
    A5["admin_docs ✅"]:::access
    D1["Docs ngoai quyen ❌"]:::deny

    IT --> A1
    IT --> A2
    IT --> A3
    IT --> A4
    IT --> A5

    SM --> A1
    SM --> A2
    SM --> A3
    SM --> A4
    SM -->|"BLOCK"| D1

    LT --> A1
    LT --> A2
    LT --> A3
    LT -->|"BLOCK"| D1

    TC --> A1
    TC --> A2
    TC -->|"BLOCK"| D1
```

---

## Tech Stack Summary

| Layer | Technology | Vai trò |
|:---|:---|:---|
| Frontend | Next.js · Vercel | Chat UI · Role Selector · CAUTION Banner |
| API Gateway | FastAPI · Python 3.11 · Render.com | REST endpoints · Rate limiting · CORS |
| Orchestration | LangGraph (StateGraph) | Agent workflow · State management |
| Input Safety | Custom Guardrails (10 checkers) | Input validation · Security |
| Router | Trie + Sentence Transformers + LLM | Intent classification 4-layer |
| Retrieval | ChromaDB · BM25 · Cross-Encoder | Hybrid search · Reranking |
| LLM | Gemini / Claude (Primary + Fallback) | Answer generation |
| Output Safety | Custom Guardrails (7 checkers) | Hallucination · RBAC · PII |
| Database | PostgreSQL (Render) | Tickets · Audit logs |
| Storage | YAML files · ChromaDB volume | Templates · Vector store |
| CI/CD | GitHub Actions · Docker | Build · Test · Deploy |
| Monitoring | OpenTelemetry · Structured logs | Observability · trace_id |

---

## KPI & Performance Targets

| Metric | Target | Measured at |
|:---|:---:|:---|
| Workflow YAML latency | less than 50ms | P95 end-to-end |
| Error Lookup latency | less than 200ms | P95 end-to-end |
| RAG Policy latency | less than 1.5s | P95 end-to-end |
| Router accuracy | 90% min | 30 golden queries |
| RAG citations | 100% | All policy responses |
| Input Guardrails | less than 80ms | Total 10 checkers |
| RBAC leak rate | 0% | All roles tested |
| Hallucination rate | max 1% | Eval dataset |
| LLM fallback | Auto less than 2s | On primary failure |
| Ticket SLA (urgent) | less than 1h | From submission |
