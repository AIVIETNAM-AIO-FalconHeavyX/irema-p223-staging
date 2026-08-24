# 🤝 Project Handoff Document
## VF AI Onboarding Agent — Team The Sigmoid (AI20K Cohort 3, P-223)

> **Last Updated:** 2026-08-15  
> **Prepared by:** Antigravity AI (aadcc76f)  
> **Branch:** `MVP-complete`  
> **Status:** MVP complete — ready for feature extension

---

## Table of Contents

1. [Project Mission & Context](#1-project-mission--context)
2. [Tech Stack](#2-tech-stack)
3. [Repository Structure (Annotated)](#3-repository-structure-annotated)
4. [System Architecture](#4-system-architecture)
5. [Backend Deep Dive](#5-backend-deep-dive)
6. [Frontend Deep Dive](#6-frontend-deep-dive)
7. [Data Layer & RAG Pipeline](#7-data-layer--rag-pipeline)
8. [Authentication & RBAC](#8-authentication--rbac)
9. [Database Schema](#9-database-schema)
10. [Environment Variables Reference](#10-environment-variables-reference)
11. [Local Development Setup](#11-local-development-setup)
12. [Running with Docker](#12-running-with-docker)
13. [Key API Endpoints](#13-key-api-endpoints)
14. [Known Issues & Tech Debt](#14-known-issues--tech-debt)
15. [Suggested Next Steps](#15-suggested-next-steps)
16. [Important Files Quick Reference](#16-important-files-quick-reference)

---

## 1. Project Mission & Context

This is an **AI-powered dealer onboarding and operational support system** built for **VinFast electric scooter dealerships (Đại lý Phân phối — ĐLPP)**. The product was developed as part of the **AI20K Build Phase, Cohort 3** academic program at VinUni.

### What it does

| Track | Feature | Status |
|-------|---------|--------|
| Track 1 | Structured onboarding portal with role-based learning paths | ✅ MVP Done |
| Track 2 | AI Chat Assistant (RAG + LangGraph) embedded in onboarding | ✅ MVP Done |
| Track 3 | Document ingestion pipeline (PDF/Video → Markdown → ChromaDB) | ✅ Pipeline ready, data partial |

### Who uses it

| Role | Vietnamese Label | Access |
|------|-----------------|--------|
| `owner` | Chủ doanh nghiệp đại lý | All content, can invite users |
| `accountant` | Kế toán viên | Accounting docs only + general |
| `technician` | Kỹ thuật viên 3S | Technical docs only + general |
| `sale` | Nhân viên Bán hàng | Sales docs only + general |
| `manager` | Quản lý Showroom | Cross-function docs |

---

## 2. Tech Stack

### Backend
| Component | Technology |
|-----------|-----------|
| Web Framework | **FastAPI** 0.115+ |
| Agent Orchestration | **LangGraph** 0.2+ (StateGraph) |
| LLM Interface | **LangChain** (OpenAI / Google Gemini fallback) |
| Vector Store | **ChromaDB** 0.4+ (persisted to `./data/chroma/`) |
| Keyword Search | **BM25Okapi** via `rank-bm25` |
| Reranker | **CrossEncoder** via `sentence-transformers` |
| Embeddings | **SentenceTransformer** (`paraphrase-multilingual-MiniLM-L12-v2`) |
| Database ORM | **SQLAlchemy** 2.0 + **Alembic** |
| Auth | **JWT** (python-jose) + **bcrypt** (passlib) |
| File Store | **MinIO** (S3-compatible, local) |
| Virus Scan | **ClamAV** via `clamd` |
| PII Removal | **Microsoft Presidio** |
| Video Transcription | **faster-whisper** large-v3 |
| OCR | **EasyOCR** |
| Runtime | **Python 3.11+** |

### Frontend
| Component | Technology |
|-----------|-----------|
| Framework | **React 19** + **TypeScript 6** |
| Build Tool | **Vite 8** |
| Routing | **react-router-dom 7** |
| HTTP Client | **Axios** |
| Animations | **Framer Motion 13** |
| Lottie Animations | `@lottiefiles/react-lottie-player` |
| UI Tour | **Driver.js** |
| Styling | **Vanilla CSS** (single `index.css`, ~62KB) |
| Fonts | **Be Vietnam Pro** (headings) + **Inter** (body) |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| Database | **PostgreSQL 15** |
| Object Storage | **MinIO** (S3 API) |
| Virus Scanning | **ClamAV** |
| Containerization | **Docker** + **docker-compose** |
| Tunneling (demo) | **ngrok** v3 |

---

## 3. Repository Structure (Annotated)

```
team-The_sigmoid/
│
├── src/                          # ← Python backend (FastAPI + LangGraph)
│   ├── main.py                   # FastAPI app entry point, lifespan, CORS
│   ├── config.py                 # Settings (pydantic-settings, .env-driven)
│   ├── media.py                  # File path resolution + description helpers
│   │
│   ├── api/                      # HTTP route handlers
│   │   ├── routes.py             # POST /chat, GET /status
│   │   ├── auth_routes.py        # /register /login /me /invite /onboarding/*
│   │   └── media_routes.py       # GET /files/* (serves training media)
│   │
│   ├── agents/                   # LangGraph agent implementation
│   │   ├── graph.py              # ← MAIN: builds and compiles the StateGraph
│   │   ├── state.py              # AgentState TypedDict (shared state schema)
│   │   └── nodes/
│   │       ├── controller.py     # Fast intent classifier & query rewriter
│   │       ├── rag_node.py       # Hybrid retrieval + LLM generation (MAIN NODE)
│   │       ├── response_generator.py  # Final answer formatter
│   │       ├── troubleshooting_node.py
│   │       ├── workflow_node.py
│   │       ├── escalation_node.py
│   │       ├── entity_extractor.py
│   │       └── query_rewriter.py
│   │
│   ├── auth/                     # JWT + bcrypt security
│   │   ├── security.py           # hash_password, verify_password, create_access_token
│   │   └── dependencies.py       # get_current_user, require_owner FastAPI deps
│   │
│   ├── db/                       # Database layer
│   │   ├── __init__.py           # create_db_and_tables(), get_db(), Base
│   │   ├── models.py             # SQLAlchemy ORM: User, Invitation, OnboardingStep, UserStepProgress
│   │   └── crud.py               # All DB operations (create_user, seed_onboarding_steps, complete_step, etc.)
│   │
│   ├── content/
│   │   └── onboarding_catalog.py # ← MASTER CONTENT FILE (~98KB): all steps/quiz/resources per role
│   │
│   ├── vectordb/                 # RAG infrastructure
│   │   ├── chroma_store.py       # ChromaDB wrapper (vector search + RBAC filter)
│   │   ├── bm25_store.py         # BM25Okapi keyword search store
│   │   ├── hybrid_search.py      # HybridRetriever: RRF fusion of vector + BM25
│   │   └── reranker.py           # CrossEncoder reranking (top 15 → top 5)
│   │
│   ├── embedding/                # Embedding pipeline scripts
│   ├── extract/                  # Document extraction (PDF, PPTX, DOCX, video)
│   ├── preprocess/               # Markdown normalizer + PII removal
│   ├── services/
│   │   └── llm.py                # LLM factory (OpenAI → Gemini fallback)
│   └── cloud/                    # MinIO/S3 upload helpers
│
├── frontend/                     # ← React frontend
│   ├── src/
│   │   ├── main.tsx              # React entry point
│   │   ├── App.tsx               # Root component (AppRouter)
│   │   ├── index.css             # ALL styles (~62KB, single-file CSS system)
│   │   ├── router/index.tsx      # Route definitions (public + protected)
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx   # JWT auth state + localStorage persistence
│   │   ├── services/
│   │   │   └── api.ts            # All Axios API calls (authApi, onboardingApi, chatApi)
│   │   ├── types/index.ts        # TypeScript types (UserProfile, OnboardingStep, etc.)
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── OnboardingPage.tsx  # ← MAIN PAGE (~526 lines, most complex)
│   │   │   └── InvitePage.tsx
│   │   └── components/
│   │       ├── layout/AppShell.tsx   # Sidebar nav + layout wrapper
│   │       ├── auth/ProtectedRoute.tsx
│   │       ├── chat/ChatWidget.tsx   # ← AI chat bubble (fixed bottom-right)
│   │       └── onboarding/
│   │           ├── QuizModal.tsx     # In-step quiz modal
│   │           ├── DmsSandboxModal.tsx  # DMS simulator (currently unused in UI)
│   │           └── ResourceViewerModal.tsx  # PDF/video viewer modal
│   │
│   ├── vite.config.ts            # Vite config (proxy: /api → localhost:8001)
│   └── package.json
│
├── data/                         # Runtime data (gitignored)
│   └── chroma/                   # ChromaDB persisted vectors
│
├── docker-compose.yml            # Postgres + MinIO + ClamAV + backend
├── Dockerfile                    # Backend container
├── requirements.txt              # Python deps
├── .env.example                  # Environment template
├── ARCHITECTURE.md               # Mermaid architecture diagrams
├── DEMO_INSTRUCTION.md           # Demo script for mentor presentation
└── HANDOFF.md                    # ← You are here
```

---

## 4. System Architecture

### Agent Pipeline (LangGraph StateGraph)

```
User Message
     │
     ▼
[controller_node]        ← Fast heuristic intent classifier (<100ms)
     │
     ├── intent = RAG_SEARCH      → [rag_node]           → [response_generator] → END
     ├── intent = TROUBLESHOOTING → [troubleshooting_node] → [rag_node] → [response_generator] → END
     ├── intent = WORKFLOW        → [workflow_node]        → [rag_node] → [response_generator] → END
     └── intent = CREATE_TICKET   → [escalation_node]    → [response_generator] → END
```

### Intent Classification Rules (in `controller.py`)

| Intent | Trigger Keywords |
|--------|----------------|
| `CREATE_TICKET` | "ticket", "khiếu nại", "gặp quản lý", "báo lỗi tĩnh" |
| `TROUBLESHOOTING` | "lỗi", "hỏng", "sự cố", "cháy", "tắt máy" (without policy keywords) |
| `WORKFLOW` | "onboarding", "lộ trình", "quy trình bán hàng/kế toán/kỹ thuật" |
| `RAG_SEARCH` | default / policy/price/document keywords |

### RAG Pipeline Flow (in `rag_node.py`)

```
Query
  ↓
HybridRetriever.search(top_k=15)
  ├── ChromaDB vector search (semantic, RBAC-filtered)
  └── BM25Okapi keyword search (RBAC-filtered)
       ↓ Reciprocal Rank Fusion (RRF, k=60)
RerankerService.rerank(top_k=5)    ← CrossEncoder
  ↓
LLM generation with system prompt (role-personalized)
  ↓
Parse [USED_DOCS: 1,2,3] tag → build citations list
  ↓
Return: context, citations, rag_confidence, needs_escalation
```

---

## 5. Backend Deep Dive

### Starting the backend

```bash
# Development (recommended)
python -m uvicorn src.main:app --port 8001 --reload

# Production
uvicorn src.main:app --host 0.0.0.0 --port 8001
```

> **Port is 8001**, not 8000! The `vite.config.ts` proxies `/api` → `localhost:8001`.

### Startup sequence (`lifespan` in `main.py`)

1. `create_db_and_tables()` — Creates all Postgres tables if not exist
2. `init_rag_models()` — Pre-loads ChromaDB, BM25 index, SentenceTransformer, CrossEncoder into memory (singletons)
3. Application starts accepting requests

### Configuration (`src/config.py`)

All config is driven by `.env` via `pydantic-settings`. Key settings:

```python
# LLM — set at least one:
OPENAI_API_KEY=...       # Primary LLM
GOOGLE_API_KEY=...       # Fallback if OpenAI key missing

MODEL_NAME=gpt-4o-mini   # OpenAI model
GEMINI_MODEL_NAME=gemini-2.5-flash  # Gemini model

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/appdb

# Vector store
CHROMA_PERSIST_DIR=./data/chroma

# CORS (must include frontend URL)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### LLM Factory (`src/services/llm.py`)

```python
get_llm()  # Returns ChatOpenAI if OPENAI_API_KEY set, else ChatGoogleGenerativeAI
```

### Onboarding Content (`src/content/onboarding_catalog.py`)

This is the **single source of truth** for all onboarding steps (~98KB file). It defines `ROLE_ONBOARDING_CATALOG` — a dict keyed by role, each containing a list of step dicts:

```python
{
    "step_id": "sale_step_1",
    "title": "...",
    "short_title": "...",
    "description": "...",
    "goal": "...",
    "guides": [{"letter": "A", "title": "...", "desc": "..."}],
    "resources": [{"name": "...", "type": "video|doc", "path": "..."}],
    "quiz": [{"id": 1, "question": "...", "options": [...], "correctIndex": 0, "explanation": "..."}],
    "role_target": "sale",
    "order": 1,
}
```

`CATALOG_VERSION` is a fingerprint string — changing it forces a re-seed of all steps in DB.

### DB Seeding (`src/db/crud.py::seed_onboarding_steps`)

Called on every `/onboarding/steps` request. Uses `content_version` on each step to detect changes. Only upserts changed steps. **Non-destructive by default**.

---

## 6. Frontend Deep Dive

### Starting the frontend

```bash
cd frontend
npm install  # first time
npm run dev  # starts on http://localhost:5173
```

### Vite proxy config

`frontend/vite.config.ts` proxies all `/api` requests to `http://localhost:8001`. This means the frontend never needs to know the backend URL during development.

### Routing (`frontend/src/router/index.tsx`)

| Path | Component | Guard |
|------|-----------|-------|
| `/login` | LoginPage | Public |
| `/register` | RegisterPage | Public |
| `/` | DashboardPage (inside AppShell) | Auth required |
| `/onboarding` | OnboardingPage (inside AppShell) | Auth required |
| `/invite` | InvitePage (inside AppShell) | Auth + `owner` role |
| `*` | Redirect to `/` | — |

### Auth State (`frontend/src/contexts/AuthContext.tsx`)

- JWT token stored in `localStorage` as `vf_access_token`
- User profile stored as `vf_user` (JSON)
- On mount: rehydrates from localStorage, then silently syncs `/api/v1/auth/me` in background
- `switchRole()` exists for dev testing only (does not call backend)

### OnboardingPage (`frontend/src/pages/OnboardingPage.tsx`)

Most complex component (~526 lines). Has two sub-views:

**OnboardingListView** (List UI)
- Shows all steps as cards with progress ring
- Graduation exam unlocked only when `completedSet.size >= totalCount`
- Exam questions: aggregated from all step quizzes, or fallback hardcoded questions

**OnboardingDetailView** (Step Detail UI)
- Shows: goal, step-by-step guides (A/B/C/D), resources (with viewer modal), quiz button
- "Hoàn thành bài học" button → calls `POST /api/v1/auth/onboarding/steps/{step_id}/complete`
- Quiz via `QuizModal` — must score 100% to complete (or complete without quiz if no quiz)

### ChatWidget (`frontend/src/components/chat/ChatWidget.tsx`)

- Fixed bottom-right floating button
- Sends messages to `POST /api/v1/chat` with `{ message, user_role }`
- Renders markdown responses with citations list
- Role is automatically taken from `useAuth()` context

### CSS System (`frontend/src/index.css`)

All styles are in one file (~62KB). Key CSS class namespacing:

| Prefix | Purpose |
|--------|---------|
| `.vf-` | VF brand components (sidebar, nav, brand) |
| `.ob-` | Onboarding-specific UI |
| `.chat-` | Chat widget |
| `.auth-` | Login/Register forms |
| `.page-` | Page-level layout |

**Typography:**
- Headings/step titles/numbers: `"Be Vietnam Pro", sans-serif` (Bold)
- Body text/descriptions: `"Inter", sans-serif` (Regular)
- Both loaded from Google Fonts in `index.html`

---

## 7. Data Layer & RAG Pipeline

### Vector Store — ChromaDB

- Persisted at `./data/chroma/` (relative to project root)
- Collection name: `vinfast_docs`
- Each document chunk has metadata:
  ```python
  {
      "role": "sales",  # RBAC filter field
      "access_scope": ["sales", "general"],
      "document": "filename",
      "section": "section_title",
      "document_id": "unique_id",
      "source": "file_path",
  }
  ```

### BM25 Index

- Stored in memory at startup; reconstructed from ChromaDB docs
- Filtered in-memory by `access_scope`

### Hybrid Search (RRF)

- Fetches `top_k * 3` from both vector and BM25
- Merges via **Reciprocal Rank Fusion**: `score = weight * 1/(k + rank)`, default k=60
- Returns top_k by fused score

### Reranker

- Uses `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Takes top 15 hybrid results → returns top 5

### Ingesting New Documents

To add documents to the RAG system:
1. Place raw files in `data/raw/<role_folder>/` (role folders: `KeToan`, `Sale`, `KTV`, `General_doc`)
2. Run preprocessing: `python -m src.preprocess.markdown_normalizer`
3. Run embedding: `python -m src.embedding.<script>` (check `src/embedding/` for scripts)
4. Restart backend (ChromaDB reloaded from disk)

### Document → Onboarding Step Resources

Media files (PDFs, videos) are served via `GET /api/v1/files/<path>`.
- Base directory: `Data/Data_separate/` (relative to project root) — set by `onboarding_media_dir` config
- Paths in `resources` array in catalog are relative to this base

---

## 8. Authentication & RBAC

### JWT Flow

```
POST /api/v1/auth/login
  Body: { email, password }
  Returns: { access_token, user: { id, email, full_name, role, ... } }

→ Store token in localStorage ("vf_access_token")
→ Send as header: Authorization: Bearer <token>
```

### Token Validation (`src/auth/dependencies.py`)

```python
get_current_user  # Validates JWT, returns User ORM object
require_owner  # Same + raises 403 if role != "owner"
```

### RBAC in RAG

Access scope per role (defined in `config.py`):

| User Role | Can Access |
|-----------|-----------|
| `accountant` | `["accounting", "general"]` |
| `sale` | `["sales", "general"]` |
| `technician` | `["technician", "general"]` |
| `owner` | `["accounting", "sales", "technician", "general", "owner"]` |

---

## 9. Database Schema

### Tables

**`users`**
```
id (UUID PK) | email | hashed_password | full_name | role (enum) |
agency_id | status (enum) | is_active | created_at | onboarding_progress (0-100)
```

**`invitations`**
```
id (UUID PK) | inviter_id (FK→users) | email | role (enum) |
token (unique) | accepted | created_at
```

**`onboarding_steps`**
```
id (INT PK, autoincrement) | role_target | order | title | short_title |
description | step_type (enum) | resource_url | duration_minutes | is_required |
goal | guides (JSON) | resources (JSON) | quiz (JSON) |
content_version | processed_md_url
```

**`user_step_progress`**
```
id (INT PK) | user_id (FK→users) | step_id (FK→onboarding_steps) |
completed_at
UNIQUE(user_id, step_id)
```

### Enum Values

```python
UserRole:   owner, accountant, technician, sale, manager
UserStatus: active, pending, inactive
StepType:   document, video, quiz, task
```

> ⚠️ The role `"it"` was retired — see `RETIRED_ROLES` in `models.py`. DB cleanup runs on startup.

---

## 10. Environment Variables Reference

Copy `.env.example` → `.env` and fill in:

```bash
# ── LLM (at least one required for AI chat) ──────────────
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...         # Gemini fallback

MODEL_NAME=gpt-4o-mini
GEMINI_MODEL_NAME=gemini-2.5-flash

# ── Database ──────────────────────────────────────────────
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/appdb

# ── Vector Store ──────────────────────────────────────────
CHROMA_PERSIST_DIR=./data/chroma

# ── App ───────────────────────────────────────────────────
APP_ENV=development
APP_PORT=8001                  # Must match vite.config.ts proxy target
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# ── MinIO (S3) ────────────────────────────────────────────
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_S3_ENDPOINT_URL=http://localhost:9000
S3_BUCKET_NAME=vinfast-onboarding

# ── ClamAV ────────────────────────────────────────────────
CLAMAV_HOST=localhost
CLAMAV_PORT=3310

# ── AI Logging (course requirement) ───────────────────────
AI_LOG_SERVER=https://ai-logs.note.transformerlabs.ai/api/ingest
AI_LOG_API_KEY=f3p1dEOhD_z8qjjtbeCtb2t9ASMEliz-...
LANGCHAIN_API_KEY=...          # LangSmith (optional, for tracing)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=ai20k-agent
```

---

## 11. Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15 (or via Docker)
- MinIO (or via Docker)

### Step-by-step

```bash
# 1. Clone and enter project
cd team-The_sigmoid

# 2. Create Python venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install Python deps
pip install -r requirements.txt

# 4. Copy and fill env
cp .env.example .env
# → Edit .env with your API keys and DB URL

# 5. Start Postgres + MinIO (if not running natively)
docker-compose up -d db s3

# 6. Start backend (port 8001)
python -m uvicorn src.main:app --port 8001 --reload

# 7. In another terminal, start frontend
cd frontend
npm install
npm run dev
# → Open http://localhost:5173

# 8. Register first account (becomes owner)
# → Go to /register, fill in email/password, select role "owner"
```

### First-time ChromaDB population

If `data/chroma/` is empty, the AI chat will respond "Không tìm thấy thông tin phù hợp" to all queries. You must populate it:

```bash
# Check if there are any documents embedded
python -c "import chromadb; c = chromadb.PersistentClient('./data/chroma'); print(c.get_collection('vinfast_docs').count())"

# If 0, run the embedding pipeline (adjust script path as needed)
python -m src.embedding.embed_documents
```

---

## 12. Running with Docker

```bash
# Start all services
docker-compose up -d

# Services:
#   backend  → http://localhost:8000
#   db       → localhost:5432
#   s3/minio → http://localhost:9000 (API), http://localhost:9001 (Console)
#   clamav   → localhost:3310

# View logs
docker-compose logs -f backend

# Stop everything
docker-compose down
```

> ⚠️ The Docker backend runs on port **8000**, not 8001. For Docker, you'd need to update `vite.config.ts` proxy target to `:8000`, or use `docker-compose` for the frontend too.

---

## 13. Key API Endpoints

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/register` | No | Register new user (returns JWT) |
| POST | `/api/v1/auth/login` | No | Login (returns JWT) |
| GET | `/api/v1/auth/me` | Yes | Get current user profile |
| POST | `/api/v1/auth/invite` | Owner only | Create invitation |

### Onboarding

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/auth/onboarding/steps` | Yes | Get steps for user's role |
| GET | `/api/v1/auth/onboarding/progress` | Yes | Get completion progress |
| POST | `/api/v1/auth/onboarding/steps/{step_id}/complete` | Yes | Mark step complete |

### AI Chat

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/chat` | No (but sends role) | Chat with AI agent |
| GET | `/api/v1/status` | No | Agent health check |

### Files / Media

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/files/{path}` | No | Serve training media files |
| POST | `/api/v1/upload` | Yes | Upload files (with virus scan) |

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | App health + env name |

---

## 14. Known Issues & Tech Debt

### 🔴 High Priority

1. **ChromaDB empty on fresh clone** — The `data/chroma/` folder is gitignored. A new developer has no documents and the AI chat returns no results. Need a seed script or data bundle.

2. **No alembic migrations** — The DB schema uses `create_all()` (non-destructive but can't handle column changes). Need to initialize `alembic` and create migration scripts.

3. **`DmsSandboxModal.tsx` unused in production UI** — The component exists but the button was removed from `OnboardingPage.tsx`. Decide: keep as hidden feature or delete.

### 🟡 Medium Priority

4. **JWT expiration not handled in frontend** — When token expires, Axios 401 triggers logout but doesn't show an error message to the user.

5. **No refresh token** — Users get logged out after JWT TTL (default 30 min in python-jose). Add refresh token flow.

6. **BM25 index rebuilt in-memory on startup** — On large document sets this can be slow. Consider persisting the BM25 index to disk.

7. **`switchRole()` in AuthContext only changes frontend state** — It doesn't issue a new JWT. Only useful for dev testing. Remove or gate behind `APP_ENV=development`.

8. **ClamAV is optional but fails silently** — If ClamAV is down, file uploads may bypass virus scanning depending on error handling in `media_routes.py`. Verify error handling.

### 🟢 Low Priority / Polish

9. **`data/` and `Data/` inconsistency** — The project has both `data/` (ChromaDB, processed docs) and `Data/Data_separate/` (raw media). Naming is confusing.

10. **`frontend/src/index.css` is 62KB** — Single-file CSS works but will be hard to maintain at scale. Consider splitting into component-scoped files.

11. **No loading skeleton for OnboardingPage** — When steps load from API, there's no skeleton UI, causing a flash of empty content.

---

## 15. Suggested Next Steps

### Immediate (before next mentor checkpoint)

- [ ] Write a `scripts/seed_vector_db.py` that embeds all documents from `Data/Data_separate/` into ChromaDB
- [ ] Initialize Alembic: `alembic init alembic`, create initial migration
- [ ] Add `.env` validation on startup (warn if no LLM key is set)

### Feature Extensions

- [ ] **Email-based invitations** — Currently `create_invitation` generates a token but there's no email sending logic. Integrate SendGrid / SMTP.
- [ ] **Dashboard analytics** — `DashboardPage.tsx` is minimal. Add charts for team progress (owner view), personal progress stats.
- [ ] **Multi-agency support** — `agency_id` field exists on `User` but is not enforced anywhere. Add agency scoping to all queries.
- [ ] **Admin panel** — Owner can see all users, reset progress, manage steps.
- [ ] **Conversation history** — `ChatWidget` does not persist conversation to DB. Each page reload starts fresh.
- [ ] **Streaming responses** — LLM calls are non-streaming. Add SSE/streaming to improve perceived latency for long answers.
- [ ] **Improve intent classification** — Replace heuristic keyword matching in `controller.py` with a lightweight LLM classifier or fine-tuned model.

### Infrastructure

- [ ] Set up **LangSmith tracing** (env vars already present in `.env.example`)
- [ ] Add **GitHub Actions CI** — lint with `ruff`, test with `pytest`
- [ ] **Production deployment** — Terraform configs exist in a previous session; review `gate1/` folder for deployment artifacts

---

## 16. Important Files Quick Reference

| File | Why it matters |
|------|---------------|
| [`src/main.py`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/src/main.py) | Backend entry point, startup, CORS |
| [`src/config.py`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/src/config.py) | ALL configuration settings |
| [`src/agents/graph.py`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/src/agents/graph.py) | LangGraph agent graph definition |
| [`src/agents/nodes/rag_node.py`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/src/agents/nodes/rag_node.py) | Core RAG logic (hybrid search → LLM → citations) |
| [`src/agents/nodes/controller.py`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/src/agents/nodes/controller.py) | Intent classifier (edit to add new intents) |
| [`src/content/onboarding_catalog.py`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/src/content/onboarding_catalog.py) | Master content — all learning steps, quizzes, resources |
| [`src/db/models.py`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/src/db/models.py) | SQLAlchemy ORM models |
| [`src/db/crud.py`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/src/db/crud.py) | All DB operations |
| [`src/api/auth_routes.py`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/src/api/auth_routes.py) | Auth + onboarding API routes |
| [`frontend/src/pages/OnboardingPage.tsx`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/frontend/src/pages/OnboardingPage.tsx) | Main onboarding UI (most complex page) |
| [`frontend/src/components/chat/ChatWidget.tsx`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/frontend/src/components/chat/ChatWidget.tsx) | AI chat floating widget |
| [`frontend/src/contexts/AuthContext.tsx`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/frontend/src/contexts/AuthContext.tsx) | Auth state management |
| [`frontend/src/services/api.ts`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/frontend/src/services/api.ts) | All frontend → backend API calls |
| [`frontend/src/index.css`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/frontend/src/index.css) | Complete UI styling system |
| [`.env.example`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/.env.example) | All required environment variables |
| [`docker-compose.yml`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/docker-compose.yml) | Infrastructure services |
| [`ARCHITECTURE.md`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/ARCHITECTURE.md) | Mermaid architecture diagrams |
| [`DEMO_INSTRUCTION.md`](file:///Users/sethehung/Documents/aithucchien_vinuni/Project/team-The_sigmoid/DEMO_INSTRUCTION.md) | Demo script for mentor presentation |

---

## Appendix: Data Flow for a Chat Message

```
User types: "Quy trình tư vấn bán hàng 7 bước là gì?"
User role: sale

1. ChatWidget.tsx → POST /api/v1/chat
   Body: { message: "...", user_role: "sale" }

2. FastAPI routes.py → agent.ainvoke({ query, raw_query, user_role })

3. controller_node:
   - Detects "quy trình" without has_rag_keyword → intent = WORKFLOW
   - Rewrites: "[SALE] quy trình tư vấn bán hàng 7 bước là gì?"

4. workflow_node:
   - Returns static workflow description for "sale" role
   - Passes context to next node

5. rag_node:
   - access_scope = ["sales", "general"] (for "sale" role)
   - HybridRetriever.search(top_k=15, role="sale", access_scope=[...])
     ├── ChromaDB: filters where metadata.role in access_scope
     └── BM25: filters same
   - RRF fusion → top 15 candidates
   - RerankerService.rerank(top_k=5)
   - Builds LLM prompt with system persona + context
   - LLM generates answer with [USED_DOCS: 1,3] tag
   - Parses tag → citations = ["Tài liệu Bán hàng VF (Bước 1-3)", ...]

6. response_generator_node:
   - Wraps into final response string

7. FastAPI returns ChatResponse:
   { response, citations, needs_escalation, intent, analysis }

8. ChatWidget renders Markdown + citation badges
```

---

*This document was generated by Antigravity AI from live codebase inspection on 2026-08-15. For questions, refer to the conversation log at conversation ID `aadcc76f-5c3d-4f28-8f1a-725cd02dcc4a`.*
