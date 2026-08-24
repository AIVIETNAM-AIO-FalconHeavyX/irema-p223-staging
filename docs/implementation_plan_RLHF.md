# Plan: Video Player + Feedback Loop

## Tóm tắt

3 tính năng mới được thiết kế cho nhau:

```
[AI trả lời] 
  → [Video player với highlighted markers]   (Feature 1)
  → [LLM tổng hợp mạch lạc hơn]             (Feature 2)  
  → [Widget ↑ − ↓ để user đánh giá]          (Feature 3)
  → [Log SQLite → cải thiện RAG sau này]     (Feature 3)
```

---

## Feature 1 — Full Video Player với Chapter Markers

### Thiết kế UI

```
┌─────────────────────────────────────────────────────┐
│ 🎬 Hướng dẫn đăng nhập DMS           [⛶ Fullscreen] │
│ ┌─────────────────────────────────────────────────┐ │
│ │                                                 │ │
│ │              [VIDEO CONTENT]                    │ │ ← max-height 260px
│ │                                                 │ │
│ └─────────────────────────────────────────────────┘ │
│ ▶ ──●────▲──────────▲──────▲──── 02:30            │ │
│         ↑01:00    ↑01:28  ↑01:47                   │
│         (hover → tooltip)                           │
└─────────────────────────────────────────────────────┘
```

**Tooltip khi hover vào marker:**
```
┌──────────────────────────────┐
│ ⏱ 01:47                      │
│ 📄 Hướng dẫn đăng nhập DMS   │
│ "Khi có thông báo tiếp tục…" │
│ Score: 8.4                   │
└──────────────────────────────┘
```

### Behavior
- **Auto-seek**: Video load → tự seek đến chunk có `rerank_score` cao nhất
- **Markers**: Mỗi chunk từ video → 1 marker màu vàng/xanh trên thanh progress bar
- **Click marker**: Jump đến timestamp đó
- **Fullscreen**: Click `⛶` → modal overlay `90vh`
- **Auth**: `fetch('/api/v1/files/{source_path}', {headers: {Authorization: 'Bearer ...'}})` → `createObjectURL(blob)` → `<video src={blobUrl}>`

### Infrastructure đã có sẵn
- `/api/v1/files/{path}` serve video với JWT auth ✅
- Chunk metadata có `source_path` + `section = "MM:SS"` ✅
- Chỉ cần thêm `content_type`, `source_path`, `timestamp_seconds` vào `retrieved_docs_detail`

---

## Feature 2 — LLM Synthesis Improvement

### Vấn đề
System prompt hiện tại chưa phân biệt video transcript chunks với document chunks. LLM đôi khi liệt kê từng tài liệu thay vì tổng hợp.

### Giải pháp: Cập nhật system prompt trong `rag_node.py`

Thêm instruction rõ ràng:

```
QUAN TRỌNG — Quy tắc tổng hợp:
- Nếu các tài liệu nguồn là VIDEO (transcript từ MM:SS), hãy tổng hợp
  thành hướng dẫn bước-by-bước theo thứ tự thời gian. KHÔNG liệt kê timestamp.
  Ví dụ đúng: "Để đăng nhập DMS: 1) Sau khi vào màn hình này... 2) Đổi sang múi giờ... 3) Khi có thông báo, ấn nút đăng nhập..."
  Ví dụ sai: "Tài liệu 1 [01:47]: Ấn nút đăng nhập | Tài liệu 2 [01:00]:..."
- Nếu có nhiều tài liệu từ các nguồn KHÁC NHAU: tổng hợp theo chủ đề,
  không liệt kê từng tài liệu riêng lẻ.
```

---

## Feature 3 — Feedback Widget (Human-in-the-Loop)

### Thiết kế UI

```
AI response text here...

[Video Player nếu có]

🔍 Nguồn tra cứu: [badges]

                              ┌──────────────────────┐
                              │ Câu trả lời có đúng? │
                              │  [↑] [−] [↓]         │
                              └──────────────────────┘
```

- **↑ (Thumbs up)**: Câu trả lời chính xác
- **−  (Neutral)**: Phần đúng phần sai / chưa rõ
- **↓ (Thumbs down)**: Sai hoặc không tìm thấy

Sau khi click → button đổi màu + "Cảm ơn phản hồi!" toast nhỏ

### Database — SQLite (mới)

Thêm bảng `chat_feedback` vào database hiện tại:

```sql
CREATE TABLE chat_feedback (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id     TEXT NOT NULL,          -- FK → users.id
    user_role   TEXT NOT NULL,          -- "accounting", "sales"...
    query       TEXT NOT NULL,          -- Câu hỏi
    response    TEXT NOT NULL,          -- Câu trả lời AI
    intent      TEXT,                   -- "RAG_SEARCH", "WORKFLOW"...
    citations   TEXT,                   -- JSON array ["doc1", "doc2"]
    rating      TEXT NOT NULL,          -- "up" | "neutral" | "down"
    rag_confidence REAL,                -- float từ agent state
    rerank_scores  TEXT                 -- JSON array [8.4, 7.1, ...] 
);
```

### API Endpoint mới

```
POST /api/v1/feedback
{
  "query": "Hướng dẫn đăng nhập DMS",
  "response": "Để đăng nhập DMS: 1)...",
  "intent": "RAG_SEARCH",
  "citations": ["01. Hướng dẫn đăng nhập DMS"],
  "rating": "up",
  "rag_confidence": 0.92,
  "rerank_scores": [8.4, 7.1, 6.2]
}
```

### Frontend API Call

```typescript
// services/api.ts
async submitFeedback(payload: FeedbackPayload): Promise<void> {
  await this.client.post('/feedback', payload);
}
```

### Ứng dụng sau này
Dữ liệu `chat_feedback` có thể dùng để:
- **Tìm câu hỏi hay bị ↓**: Biết chủ đề nào RAG kém → re-index hoặc cải thiện chunking
- **Tìm chunk kém**: `rerank_scores` thấp + rating ↓ → điều chỉnh threshold
- **Cải thiện prompt**: Câu hỏi nào LLM trả lời sai để fine-tune

---

## Proposed Changes

### Backend

#### [NEW] DB Migration — `chat_feedback` table
- File: `src/db/migrations/` hoặc thêm vào `src/db/models.py`

#### [MODIFY] [`rag_node.py`](file:///d:/Classroom/Code/Codelabs/P223/src/agents/nodes/rag_node.py)
- Hàm `_build_doc_detail()`: thêm `content_type`, `source_path`, `timestamp_seconds`
- Hàm `_parse_timestamp_to_seconds("01:47") → 107`
- System prompt: thêm video synthesis rules

#### [MODIFY] [`schemas.py`](file:///d:/Classroom/Code/Codelabs/P223/src/models/schemas.py)
- `RetrievedDocInfo`: thêm `content_type`, `source_path`, `timestamp_seconds`
- Thêm `FeedbackRequest` schema mới

#### [NEW] Feedback API — [`src/api/feedback_routes.py`](file:///d:/Classroom/Code/Codelabs/P223/src/api/feedback_routes.py)
- `POST /feedback` → insert vào `chat_feedback`
- `GET /feedback/stats` → thống kê ↑/↓ theo intent và ngày

#### [MODIFY] [`src/main.py`](file:///d:/Classroom/Code/Codelabs/P223/src/main.py)
- Register `feedback_routes` router

### Frontend

#### [NEW] [`VideoSourcePlayer.tsx`](file:///d:/Classroom/Code/Codelabs/P223/frontend/src/components/chat/VideoSourcePlayer.tsx)
- Fetch video qua `Authorization` header → Blob URL
- Custom progress bar overlay với colored chapter markers
- Tooltip on hover: timestamp + section + score
- Modal fullscreen

#### [NEW] [`FeedbackWidget.tsx`](file:///d:/Classroom/Code/Codelabs/P223/frontend/src/components/chat/FeedbackWidget.tsx)
- 3 nút: ↑ (xanh lá) | − (xám) | ↓ (đỏ)
- State: idle → selected (một nút sáng lên) → "Cảm ơn!"
- Call `chatApi.submitFeedback()` khi click

#### [MODIFY] [`ChatWidget.tsx`](file:///d:/Classroom/Code/Codelabs/P223/frontend/src/components/chat/ChatWidget.tsx)
- Detect chunk có `content_type === "video"` → render `<VideoSourcePlayer>`
- Thêm `<FeedbackWidget>` ở cuối mỗi AI message

#### [MODIFY] [`types/index.ts`](file:///d:/Classroom/Code/Codelabs/P223/frontend/src/types/index.ts)
- `RetrievedDocInfo`: thêm `content_type`, `source_path`, `timestamp_seconds`
- Thêm `FeedbackPayload` interface

#### [MODIFY] [`index.css`](file:///d:/Classroom/Code/Codelabs/P223/frontend/src/index.css)
- Video player styles
- Chapter marker overlay styles
- Tooltip styles
- Feedback widget button styles

---

## Verification Plan

### Automated Tests
```bash
ruff check src/ tests/
pytest tests/ -m "not integration" -q
```

### Manual Verification
1. Hỏi "Hướng dẫn đăng nhập DMS" với role `accountant`
2. ✅ Response tổng hợp bước-by-bước (không liệt kê file)
3. ✅ Video player xuất hiện với chapter markers tại `01:00`, `01:28`, `01:47`
4. ✅ Video auto-seek đến chunk rerank score cao nhất
5. ✅ Hover marker → tooltip hiển thị đúng thông tin
6. ✅ Click `⛶` → modal fullscreen
7. ✅ Click ↑ → button highlight + "Cảm ơn!" + row trong SQLite `chat_feedback`
8. ✅ `GET /api/v1/feedback/stats` trả về thống kê
