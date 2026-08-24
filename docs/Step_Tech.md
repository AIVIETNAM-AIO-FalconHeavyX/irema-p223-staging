# Step_Tech.md — Nhật ký Kỹ thuật Triển khai

> **Mục đích:** ghi lại **từng bước** thay đổi code, **kỹ thuật** đã dùng, **dùng như thế nào** và **kỹ thuật đó để làm gì**.
> Mỗi lần thêm/sửa code hoặc thêm file mới → bổ sung một mục vào đây trước khi commit.

| | |
|:---|:---|
| **Dự án** | VF-Onboarding Copilot — Đại lý 3S VinFast Xe máy điện |
| **Nhánh** | `feature/step1-auth-appshell` |
| **Tính năng** | Lộ trình hội nhập cá nhân hóa theo vai trò, dùng tài liệu thật |
| **Quy mô** | 5 vai trò · 23 bước · 84 tài liệu · 3 câu hỏi/bước |
| **Giao diện** | 1 sidebar + vùng nội dung (2 cột) |
| **Bản đặc tả** | `implementation_plan.md` (gốc repo) |
| **Bản thi hành** | `src/content/onboarding_catalog.py` |

---

## 0. Kiến trúc đã chốt — Hybrid "Seed-first"

Câu hỏi ban đầu: làm UI với mockdata trước, hay lấy thẳng dữ liệu thật ngay từ đầu?

Kết luận: **không dùng mockdata**, vì sẽ phải viết lại toàn bộ phần render khi thay bằng API thật.

```
implementation_plan.md      onboarding_catalog.py       SQLite            FastAPI                React
   (đặc tả nghiệp vụ)   →      (bản thi hành)       →  onboarding_steps → /api/v1/auth/...  →  OnboardingPage
                                      │                                  → /api/v1/files/... →  ResourceViewerModal
                                      │
                              Data/Data_separate/  (84 tham chiếu tài liệu PDF · MP4 · DOCX · XLSX · PPTX)
```

**Nguyên tắc xuyên suốt:** nội dung nghiệp vụ chỉ tồn tại ở **một** nơi. Frontend không hardcode câu hỏi, tên bước hay đường dẫn tài liệu — tất cả đọc từ API.

---

## Bảng tra nhanh — Kỹ thuật đã dùng

| # | Kỹ thuật | Dùng ở đâu | Để làm gì |
|:--|:---|:---|:---|
| 1 | Single Source of Truth | `onboarding_catalog.py` | Nội dung bài học chỉ định nghĩa một nơi |
| 2 | Content versioning | `CATALOG_VERSION` | Tự nạp lại DB khi nội dung đổi, không cần xoá tay |
| 3 | Cột JSON trong SQLAlchemy | `OnboardingStep.guides/resources/quiz` | Lưu cấu trúc lồng nhau không cần thêm 3 bảng |
| 4 | Lightweight migration | `src/db/__init__.py` | SQLite không ALTER thêm cột qua `create_all` |
| 5 | Authenticated file serving | `src/api/media_routes.py` | Tài liệu đại lý không được để public |
| 6 | JWT qua query string | `get_current_user_allow_query_token` | `<video>`/`<iframe>` không gửi được header |
| 7 | RBAC whitelist đường dẫn | `resource_paths_for_role()` | Chặn rò rỉ tài liệu chéo vai trò |
| 8 | Path traversal guard | `resolve_media_path()` | Chặn `../../.env` từ URL người dùng |
| 9 | HTTP Range / 206 | `FileResponse` (Starlette) | Tua video không tải lại cả file |
| 10 | Unicode NFC normalization | `normalize_path()` | Khớp tên file tiếng Việt macOS ↔ trình duyệt |
| 11 | RFC 5987 `filename*` | `Content-Disposition` | Giữ dấu tiếng Việt khi tải file về |
| 12 | Bảng join tiến độ | `UserStepProgress` | Idempotent + không mất tiến độ khi F5 |
| 13 | `@functools.cache` | `resource_paths_for_role()` | Mỗi Range request đều check quyền → phải rẻ |
| 14 | Optimistic UI update | `handleStepComplete` | Nút phản hồi ngay, không chờ round-trip |
| 15 | `Promise.all` + cancel flag | `OnboardingPage.useEffect` | Tải song song, tránh setState sau unmount |
| 16 | `preload="metadata"` | `ResourceViewerModal` | Không kéo cả video vài chục MB khi mở modal |
| 17 | Executable specification | `test_catalog_matches_implementation_plan` | Plan và code lệch nhau là test đỏ |
| 18 | Codemod | Bước 9 | Sửa 25 chỗ giống nhau không sót, không lệch |
| 19 | Invariant hằng số | `QUIZ_QUESTIONS_PER_STEP` | Biến quy ước nội dung thành thứ CI kiểm tra được |
| 20 | Data migration khi thu hẹp enum | `_remove_retired_roles()` | Dòng DB cũ mang giá trị enum đã xoá sẽ làm ORM crash |
| 21 | Tombstone constant | `RETIRED_ROLES` | Ghi lại thứ đã xoá để migration & test bám vào |
| 22 | Tách nhãn hiển thị khỏi tên định danh | `short_title` vs `title` | UI gọn mà spec vẫn giữ tên đầy đủ |
| 23 | Dọn CSS chết bằng parser | Bước 12 | Gỡ component thì phải gỡ cả style, không để rác |

---

## Bước 1 — Gom nội dung lộ trình về một catalog

**Việc đã làm:** gỡ khối `ROLE_ONBOARDING_DATA` (767 dòng hardcode trong React) và khối `seed_onboarding_steps()` cũ (URL giả `/docs/xxx.pdf`), gộp thành một catalog Python trỏ tới tài liệu thật.

**File:** ➕ `src/content/__init__.py` · ➕ `src/content/onboarding_catalog.py` · ✏️ `frontend/src/pages/OnboardingPage.tsx`

### Kỹ thuật: Single Source of Truth

- **Là gì:** một dữ liệu chỉ định nghĩa ở đúng một nơi; mọi nơi khác đọc lại từ đó.
- **Vì sao cần:** trước đây nội dung bài học tồn tại **hai bản** — bản đầy đủ hardcode ở React và bản rút gọn ở `crud.py`. Sửa một bên là hai bên lệch ngay.
- **Dùng thế nào:** catalog → seed vào SQLite → API → React render.

### Kỹ thuật: Hằng số tiền tố đường dẫn

- **Là gì:** gom các đoạn đường dẫn lặp lại thành hằng số (`KETOAN_DMS`, `KYTHUAT_BAO_HANH`…).
- **Vì sao:** tên thư mục thật rất dài và có ký tự khó — `"Đào tạo Hội nhập XMĐ _ VinFast "` **có dấu cách ở cuối**. Gõ lại mỗi lần là sai chính tả.

---

## Bước 2 — Script kiểm tra tài liệu có thật

**File:** ➕ `scripts/verify_onboarding_resources.py`

```bash
python -m scripts.verify_onboarding_resources
# Đã kiểm tra : 84 tài liệu trong 5 vai trò
# ✅ Tất cả tài liệu đều tồn tại.
```

### Kỹ thuật: Fail-fast validation

- **Là gì:** kiểm tra giả định của hệ thống ngay từ đầu thay vì để lỗi lộ ra lúc chạy.
- **Vì sao:** một đường dẫn sai chính tả chỉ hiện thành nút "Xem" bấm ra 404 — rất khó thấy khi demo. Script trả **exit code 1** nên cắm được vào CI.

---

## Bước 3 — Mở rộng schema DB

**File:** ✏️ `src/db/models.py`

Thêm vào `OnboardingStep`: `goal`, `guides` (JSON), `resources` (JSON), `quiz` (JSON), `content_version`. Thêm bảng `UserStepProgress`.

### Kỹ thuật: Cột JSON trong SQLAlchemy

- **Là gì:** kiểu `JSON` tự serialize list/dict Python thành TEXT khi lưu SQLite và parse ngược lại khi đọc.
- **Vì sao dùng ở đây:** `guides`, `resources`, `quiz` là list object lồng nhau, **chỉ đọc**, luôn lấy trọn gói theo bước. Tách ra 3 bảng con sẽ phải JOIN 3 lần chỉ để render một màn hình mà không được lợi gì.
- **Giới hạn cần biết:** không query/filter được theo nội dung bên trong JSON. Chấp nhận được vì không có nhu cầu đó.

### Kỹ thuật: Bảng join ghi tiến độ

- **Là gì:** bảng nối `user_id` ↔ `step_id` kèm `UniqueConstraint("user_id", "step_id")`.
- **Vấn đề nó giải quyết:** code cũ cộng dồn `progress += 100/total_steps` mỗi lần bấm nút →
  - bấm 2 lần cùng một bước là **tiến độ nhảy sai**;
  - server chỉ giữ con số %, **không biết bước nào đã xong** → F5 là UI về 0%.
- **Dùng thế nào:** ghi một dòng cho mỗi bước hoàn thành, `% = số dòng / tổng số bước`. Ràng buộc UNIQUE khiến thao tác thành **idempotent**.

---

## Bước 4 — Migration nhẹ cho SQLite

**File:** ✏️ `src/db/__init__.py` → `_drop_outdated_onboarding_table()`

### Kỹ thuật: Drop-and-reseed có điều kiện

- **Vấn đề:** `Base.metadata.create_all()` chỉ **tạo bảng chưa có**, không ALTER thêm cột vào bảng đã tồn tại. DB `data/app.db` đang chạy sẽ thiếu 5 cột mới → app crash.
- **Cách làm:** dùng `sqlalchemy.inspect()` đọc danh sách cột hiện có; nếu thiếu cột bắt buộc thì `DROP TABLE` rồi để `create_all` + `seed` dựng lại.
- **Vì sao an toàn:** `onboarding_steps` là **dữ liệu seed thuần**, không chứa dữ liệu người dùng nhập.
- **Lưu ý:** drop luôn `user_step_progress` vì khoá ngoại của nó trỏ tới `id` các bước sắp bị đánh số lại.
- **Khi nào phải thay:** khi có dữ liệu người dùng thật thì chuyển sang **Alembic**, không dùng cách này nữa.

### Kỹ thuật: Content versioning

- **Là gì:** lưu `CATALOG_VERSION` vào từng dòng; `seed_onboarding_steps()` so sánh version trong DB với version trong code.
- **Vì sao:** thay cho điều kiện cũ `if count >= 20: return` — điều kiện đó khiến **sửa nội dung xong DB không bao giờ cập nhật** trừ khi xoá file `.db` bằng tay.
- **Chi phí:** đúng 1 câu `SELECT ... LIMIT 1` mỗi request, nên gọi thoải mái ở đầu endpoint.

---

## Bước 5 — Endpoint phục vụ tài liệu có kiểm soát quyền

**File:** ➕ `src/api/media_routes.py` · ➕ `src/media.py` · ✏️ `src/config.py` · ✏️ `src/main.py`

`GET /api/v1/files/{path}` — thay vì `app.mount(StaticFiles(...))`.

### Kỹ thuật: Authenticated file serving

**Vì sao không mount StaticFiles:** nó phục vụ file **công khai**, không cắm được 3 thứ bắt buộc:

1. bắt buộc JWT — tài liệu chính sách giá, bảng claim, hợp đồng của đại lý không được public;
2. RBAC — mỗi vai trò chỉ tải được tài liệu trong lộ trình của mình;
3. chặn path traversal.

### Kỹ thuật: RBAC bằng whitelist đường dẫn

- **Là gì:** so đường dẫn client gửi lên với **tập hợp đường dẫn hợp lệ** của vai trò đó, sai là 403.
- **Vì sao chọn whitelist thay vì so tiền tố thư mục:** nhiều bước dùng chung tài liệu chéo thư mục — Kỹ thuật viên và Manager đều học bộ "Chăm sóc xe miễn phí" nằm trong `Chương trình khuyến mãi/`, Manager xem video tồn kho nằm trong `KeToan/`. Lọc theo tiền tố sẽ chặn nhầm; whitelist bám đúng **lộ trình nghiệp vụ**.
- **Liên hệ MVP_SPEC:** đáp ứng rủi ro **R-02 (RBAC Leak)** và Release Gate *"Technician KHÔNG xem được tài liệu Manager"*.

### Kỹ thuật: Path traversal guard

- **Tấn công:** `GET /api/v1/files/../../.env` → đọc trộm secret key.
- **Cách chặn:** `(root / path).resolve()` rồi kiểm tra `root` có nằm trong `.parents` của kết quả không. `.resolve()` triệt tiêu hết `..` và symlink **trước** khi so sánh — so sánh chuỗi thô sẽ bị `..%2f` qua mặt.

### Kỹ thuật: JWT qua query string

- **Vấn đề:** `<video src="...">` và `<iframe src="...">` do trình duyệt tự phát request, **không cách nào gắn header `Authorization`**.
- **Giải pháp:** `get_current_user_allow_query_token` nhận token từ header **hoặc** `?token=`. Ưu tiên header khi có cả hai.
- **Đánh đổi phải biết:** token nằm trong URL nên có thể lọt vào access log / lịch sử trình duyệt. Chấp nhận ở phạm vi MVP nội bộ. **Hướng nâng cấp:** token ký riêng cho từng file, hạn dùng ~5 phút.

### Kỹ thuật: HTTP Range / 206 Partial Content

- **Là gì:** client gửi `Range: bytes=1000-1999`, server trả `206` kèm `Content-Range` thay vì cả file.
- **Để làm gì:** đây chính là cơ chế cho phép **tua video**. Không có nó, kéo thanh thời gian phải tải lại từ đầu.
- **Cách dùng:** `FileResponse` của Starlette 1.3.1 xử lý sẵn header `Range` — chỉ cần **không** tự đọc file rồi trả `Response(bytes)`, vì làm vậy là mất tính năng này.
  Đã kiểm chứng: `HTTP/1.1 206 Partial Content · content-range: bytes 1000-1999/10825408`.

### Kỹ thuật: Unicode NFC normalization

- **Vấn đề:** macOS lưu tên file dạng **NFD** (`ề` = `e` + dấu rời), trình duyệt gửi lên dạng **NFC** (`ề` là 1 ký tự). Hai chuỗi *hiện lên giống hệt nhau* nhưng `==` trả `False` → whitelist RBAC trượt oan.
- **Cách xử lý:** `unicodedata.normalize("NFC", path)` trước mọi phép so sánh.

### Kỹ thuật: RFC 5987 `filename*`

- **Là gì:** cú pháp `Content-Disposition: attachment; filename*=UTF-8''<percent-encoded>`.
- **Để làm gì:** header HTTP chỉ mang được ASCII. Tên `Giấy đề nghị thanh toán NPP.docx` sẽ thành ký tự rác nếu dùng `filename=` thường.

---

## Bước 6 — API tiến độ

**File:** ✏️ `src/api/auth_routes.py` · ✏️ `src/db/crud.py` · ✏️ `src/models/schemas.py`

- ➕ `GET /api/v1/auth/onboarding/progress`
- ✏️ `POST .../steps/{id}/complete` → trả `OnboardingProgressResponse` thay vì dict tự do

### Kỹ thuật: Idempotency

- **Là gì:** gọi API nhiều lần cho cùng kết quả như gọi một lần.
- **Vì sao cần:** người dùng bấm đúp, mạng chập chờn retry — không được cộng tiến độ hai lần.
- **Cách làm:** kiểm tra dòng đã tồn tại chưa trước khi INSERT, rồi **tính lại** % từ số bước thay vì cộng dồn.

### Kỹ thuật: Response model có kiểu (Pydantic)

- **Là gì:** khai báo `response_model=` để FastAPI validate output và sinh OpenAPI schema.
- **Vì sao:** endpoint cũ trả dict tự do — frontend không có gì đảm bảo về hình dạng dữ liệu, và `/docs` không mô tả được.

### Kỹ thuật: Lọc theo quyền ở tầng dữ liệu

`complete_step_for_user` kiểm tra `step.role_target` có thuộc vai trò user không rồi mới ghi. Không có bước này, ai cũng POST được `step_id` bất kỳ để tự đẩy tiến độ.

---

## Bước 7 — Frontend đọc dữ liệu thật

**File:** ✏️ `frontend/src/types/index.ts` · ✏️ `frontend/src/services/api.ts` · ✏️ `frontend/src/pages/OnboardingPage.tsx` · ➕ `frontend/src/components/onboarding/ResourceViewerModal.tsx` · ✏️ `frontend/src/index.css`

### Kỹ thuật: Helper `mediaUrl()`

- **Là gì:** hàm dựng URL tài liệu — encode từng segment đường dẫn rồi gắn `?token=`.
- **Chi tiết quan trọng:** dùng `path.split("/").map(encodeURIComponent).join("/")` chứ **không** `encodeURIComponent(path)`. Cách thứ hai encode luôn dấu `/` thành `%2F` và phá vỡ route `{file_path:path}`.

### Kỹ thuật: Render theo khả năng của trình duyệt

| Định dạng | Cách hiển thị | Lý do |
|:---|:---|:---|
| `.mp4`, `.webm` | `<video controls>` | Trình duyệt phát native, tua bằng Range |
| `.pdf` | `<iframe>` | Trình duyệt có sẵn PDF viewer |
| `.docx`, `.xlsx`, `.pptx` | Nút tải xuống | Trình duyệt **không** đọc được Office → hiện nút tải trung thực còn hơn iframe trắng |

### Kỹ thuật: `preload="metadata"`

Bảo trình duyệt chỉ tải phần header của video (thời lượng, kích thước) khi mở modal. Video DMS nặng 10–50 MB; mặc định `preload="auto"` sẽ nuốt băng thông ngay cả khi người dùng không bấm play.

### Kỹ thuật: Optimistic UI update

Cập nhật giao diện **trước**, gọi API sau, rồi đồng bộ lại bằng kết quả server trả về. Nút "Hoàn thành" tick xanh ngay thay vì đợi round-trip mạng.

### Kỹ thuật: `Promise.all` + cancel flag

```ts
Promise.all([getSteps(), getProgress()])   // tải song song thay vì nối tiếp
return () => { cancelled = true; };        // cleanup: không setState sau unmount
```

- **`Promise.all`:** hai request độc lập → thời gian chờ bằng request chậm nhất, không phải tổng.
- **Cancel flag:** nếu người dùng rời trang trước khi API trả về, `setState` trên component đã unmount sẽ gây memory leak warning.

### Kỹ thuật: Khôi phục vị trí học dở

Sau khi tải tiến độ, `findIndex` bước chưa hoàn thành đầu tiên và mở đúng bước đó, thay vì luôn quay về bước 1.

---

## Bước 8 — Bộ kiểm thử

**File:** ➕ `tests/test_api/test_onboarding.py`

### Kỹ thuật: `ASGITransport` (httpx)

Gọi thẳng vào ASGI app trong tiến trình, **không** cần chạy server thật. Test nhanh (~3s) và không phụ thuộc cổng mạng.

### Kỹ thuật: `pytest.mark.parametrize` với `ids`

- **Là gì:** chạy cùng một test với nhiều bộ dữ liệu đầu vào.
- **Vì sao đặt `ids=[...]`:** đặt tên từng case theo `role:tiêu đề bước`. Khi hỏng, pytest chỉ thẳng bước nào sai thay vì báo `test[step17]` vô nghĩa.

---

## Bước 9 — Nâng mỗi bước lên 3 câu hỏi nhanh

**Yêu cầu:** mỗi bước onboarding phải có **3 câu hỏi nhanh**.

**Không phải sửa:** `OnboardingPage.tsx` và `QuizModal.tsx` — cả hai đã render theo `quiz.length` ngay từ đầu chứ không hardcode số 2. Đây chính là lợi ích của việc **không** nhúng số lượng cố định vào giao diện.

### Kỹ thuật: Codemod — sửa hàng loạt bằng script thay vì sửa tay

- **Là gì:** viết một script tự động biến đổi mã nguồn, thay cho việc mở file sửa từng chỗ.
- **Vì sao cần ở đây:** phải chèn 25 khối code giống hệt nhau về cấu trúc vào một file ~950 dòng. Sửa tay 25 lần thì gần như chắc chắn lệch thụt lề, thiếu dấu phẩy, hoặc bỏ sót một bước — mà lỗi bỏ sót thì **không có gì báo cho biết**.
- **Dùng thế nào:** neo vào chuỗi đóng của mảng `quiz`, tách file thành 26 mảnh rồi ghép lại kèm khối mới. Script **tự kiểm tra trước khi ghi**:

  ```python
  if len(parts) - 1 != len(Q3):
      sys.exit(f"Số vị trí ({len(parts) - 1}) khác số câu hỏi ({len(Q3)})")
  ```

- **Nguyên tắc rút ra:** một thay đổi lặp lại N lần với N lớn thì viết script rẻ hơn và an toàn hơn sửa tay — miễn là script tự thất bại to khi giả định sai, thay vì âm thầm sửa nhầm.

### Kỹ thuật: Invariant hằng số

```python
QUIZ_QUESTIONS_PER_STEP = 3  # trong catalog
```

Biến quy ước dạng chữ thành hằng số để test tham chiếu, thay vì rải số `3` khắp nơi.

---

## Bước 10 — Đồng bộ code với `implementation_plan.md`

**Bối cảnh:** `implementation_plan.md` xuất hiện ở gốc repo **sau** khi các bước 1–9 đã hoàn thành. Đây mới là bản đặc tả nghiệp vụ chính thức, và nó **lệch đáng kể** so với catalog đã dựng (catalog trước đó xây từ mockdata cũ trong React).

### 10.1. Chuẩn hoá bản kế hoạch

**File:** ✏️ `implementation_plan.md`

| Vấn đề trong plan | Xử lý |
|:---|:---|
| Số câu hỏi mỗi bước không đồng nhất (2, 3 hoặc 4) | Chuẩn hoá về **đúng 3 câu** ở cả 19 bước |
| Kỹ thuật viên: tiêu đề ghi "5 BƯỚC", bảng tổng hợp ghi 4 | Lấy phần chi tiết làm chuẩn → **5 bước**, sửa bảng tổng hợp |
| Manager: tiêu đề ghi "4 BƯỚC", bảng khung liệt kê B1–B5, chi tiết chỉ có B1–B4 | **Bổ sung khối chi tiết B5** theo đúng mô tả đã có sẵn trong bảng khung → 5 bước |

Nguyên tắc xử lý mâu thuẫn: **phần chi tiết là chuẩn**, bảng tóm tắt phải chạy theo — vì phần chi tiết là thứ được dùng để sinh code.

Với 4 bước vốn có 4 câu (Kế toán B1–B4), giữ Q1–Q3 và bỏ Q4. Với 13 bước vốn có 2 câu, viết bổ sung câu thứ 3 bám nội dung tài liệu của chính bước đó.

**Kỹ thuật dùng lại:** codemod (như Bước 9). Script neo vào dòng `🎮 THAO TÁC THỬ`, thay toàn bộ vùng câu hỏi tới dòng `├─` kế tiếp, và tự đệm khoảng trắng cho khung ASCII:

```python
def box(text, indent):
    body = " " * indent + text
    pad = WIDTH - 2 - len(body)
    if pad < 0:
        sys.exit(f"Dòng quá dài ({-pad} ký tự thừa): {text}")
    return "│" + body + " " * pad + "│"
```

Câu dài quá khung được tự động xuống dòng và canh thẳng dưới chữ `Q`.

### 10.2. Viết lại catalog theo plan

**File:** ✏️ `src/content/onboarding_catalog.py` (viết lại toàn bộ)

Mỗi bước trong catalog giờ tương ứng **1-1** với một khối `### 📍 BƯỚC N` trong plan: cùng tiêu đề, cùng mục tiêu (`🎯 MỤC TIÊU`), cùng hướng dẫn nhanh (`📋 HƯỚNG DẪN NHANH`), cùng tài liệu (`📎 TÀI LIỆU & VIDEO`), cùng câu hỏi (`🎮 THAO TÁC THỬ`).

| Vai trò | Trước | Sau | Nguồn |
|:---|:---:|:---:|:---|
| accountant | 5 bước · 22 tài liệu | **5 bước · 48 tài liệu** | Plan Role 1 |
| sale | 4 bước · 14 tài liệu | **4 bước · 5 tài liệu** | Plan Role 2 |
| technician | 4 bước · 12 tài liệu | **5 bước · 12 tài liệu** | Plan Role 3 |
| manager | 4 bước · 10 tài liệu | **5 bước · 10 tài liệu** | Plan Role 4 |
| owner | 4 bước · 9 tài liệu | 4 bước · 9 tài liệu | *Ngoài plan — giữ nguyên* |
| it | 4 bước · 8 tài liệu | *(đã xoá ở Bước 11)* | *Ngoài plan* |

Hai thay đổi đáng chú ý về nghiệp vụ, đều theo đúng plan:

- **Sale giảm từ 14 xuống 5 tài liệu.** Plan ghi rõ: thư mục `Sale/.../Hướng dẫn hệ thống DMS/` **trống hoàn toàn** — TVBH **không** thao tác DMS trực tiếp; toàn bộ nhập đơn, ghép xe, thu tiền do Kế toán làm. Catalog cũ gán nhầm video DMS cho Sale.
- **Kế toán tăng lên 48 tài liệu.** Plan liệt kê toàn trình 22 video DMS cộng bộ hồ sơ HĐTP Pin (chấm dứt / đổi chủ / kích hoạt lại) mà catalog cũ bỏ sót.

**Vì sao giữ `owner` và `it`:** plan chưa đặc tả hai vai trò này, nhưng hệ thống đã có tài khoản demo đang hoạt động (`thehung@vinfast.vn` là `owner`). Xoá đi sẽ khiến chính tài khoản đang dùng để demo đăng nhập vào thấy màn hình trống. Đánh dấu rõ trong docstring là **phần mở rộng ngoài plan**.

### Kỹ thuật: Executable specification — test đối chiếu code với tài liệu

- **Là gì:** biến bản đặc tả từ tài liệu người đọc thành thứ **máy kiểm tra được**.
- **Vấn đề nó giải quyết:** plan và code lệch nhau âm thầm suốt nhiều ngày mà không ai biết — đúng như tình huống vừa xảy ra. Comment kiểu "nhớ cập nhật cả hai nơi" không bao giờ có tác dụng.
- **Dùng thế nào:** test đọc thẳng `implementation_plan.md`, trích tiêu đề các bước bằng regex rồi so với catalog:

  ```python
  def _plan_step_titles() -> dict[str, list[str]]:
      text = PLAN_PATH.read_text(encoding="utf-8")
      sections = re.split(r"^# .*ROLE \d+:", text, flags=re.M)[1:]
      return {role: re.findall(r"^### 📍 BƯỚC \d+ — (.+)$", s, flags=re.M) for role, s in zip(PLAN_ROLE_ORDER, sections)}


  @pytest.mark.parametrize("role", PLAN_ROLES)
  def test_catalog_matches_implementation_plan(role):
      assert [s["title"] for s in ROLE_ONBOARDING_CATALOG[role]] == _plan_step_titles()[role]
  ```

- **Test thứ hai** (`test_plan_declares_three_questions_per_step`) kiểm tra chính bản plan: mọi khối `THAO TÁC THỬ` phải liệt kê đúng 3 câu. Nghĩa là **sửa plan sai quy ước cũng làm test đỏ**, không chỉ sửa code.
- **Đánh đổi:** test phụ thuộc vào định dạng Markdown của plan. Đổi cấu trúc tiêu đề là test hỏng. Đây là cái giá chấp nhận được để hai bên không lệch nhau.

---

## Bước 11 — Loại bỏ vai trò `it`

**Lý do nghiệp vụ:** vai trò IT đại lý không có nghiệp vụ riêng cần onboard — việc cài đặt DMS, chữ ký số và xử lý sự cố CNTT thuộc **IT Helpdesk của VinFast**, không phải quy trình nội bộ đại lý.

**Phạm vi ảnh hưởng — 12 file:**

| Tầng | File | Thay đổi |
|:---|:---|:---|
| DB | `src/db/models.py` | Bỏ `UserRole.it`; thêm `RETIRED_ROLES = ("it",)` |
| DB | `src/db/__init__.py` | ➕ `_remove_retired_roles()` |
| DB | `src/db/crud.py` | Bỏ tài khoản seed `it@vinfast.vn` |
| Nội dung | `src/content/onboarding_catalog.py` | Xoá khối `"it"` (158 dòng, 4 bước, 8 tài liệu); bump `CATALOG_VERSION` |
| API | `src/models/schemas.py`, `src/api/auth_routes.py` | Bỏ `it` khỏi mô tả & thông báo lỗi role hợp lệ |
| Chatbot | `src/agents/nodes/rag_node.py` | Bỏ `"it": 3` khỏi `ROLE_HIERARCHY` |
| FE | `types/index.ts` | Bỏ khỏi `UserRole`, `ROLE_LABELS`, `ROLE_COLORS` |
| FE | `OnboardingPage.tsx`, `DashboardPage.tsx`, `InvitePage.tsx` | Bỏ khỏi nhãn, gợi ý dashboard, danh sách role mời được |
| Test | `tests/test_api/test_onboarding.py` | Bỏ khỏi `DEMO_ACCOUNTS`; ➕ 2 test chặn hồi quy |

### Kỹ thuật: Data migration khi thu hẹp enum

- **Vấn đề:** xoá một giá trị khỏi `UserRole` **không** đụng gì tới DB. Dòng `users` cũ vẫn mang `role='it'`, và ngay khi ORM nạp dòng đó lên sẽ ném `LookupError: 'it' is not among the defined enum values`. Ứng dụng chết ở chỗ tưởng như vô hại — chẳng hạn khi Owner mở trang danh sách nhân viên.
- **Cách xử lý:** dọn bằng **SQL thô**, chạy **trước** khi ORM chạm vào bảng `users`:

  ```python
  def _remove_retired_roles() -> None:
      ...
      stale_ids = [row[0] for row in conn.execute(text(f"SELECT id FROM users WHERE role IN ({placeholders})"), params)]
      if not stale_ids:
          return
      # Dọn bản ghi phụ thuộc trước để không vướng khoá ngoại.
      for table, column in (("user_step_progress", "user_id"), ("invitations", "inviter_id")):
          conn.execute(text(f"DELETE FROM {table} WHERE {column} = :uid"), rows)
      conn.execute(text(f"DELETE FROM users WHERE role IN ({placeholders})"), params)
  ```

- **Ba chi tiết quan trọng:**
  1. **SQL thô, không dùng ORM** — vì chính ORM là thứ không đọc nổi dữ liệu này.
  2. **Thứ tự xoá** — `user_step_progress` và `invitations` có khoá ngoại trỏ tới `users.id`, phải xoá trước nếu không sẽ vướng ràng buộc.
  3. **Idempotent** — không có dòng nào thì `return` sớm, chạy lại lần nữa cũng không sao.
- **Vì sao không cần đổi CHECK constraint của cột:** SQLite lưu Enum thành `VARCHAR` kèm `CHECK`. Ràng buộc cũ vẫn *cho phép* giá trị `'it'` — rộng hơn mức cần thiết, nhưng vô hại vì tầng Python không bao giờ sinh ra giá trị đó nữa. Siết lại constraint đòi hỏi dựng lại cả bảng `users` — **có** dữ liệu người dùng thật nên không đáng đánh đổi.

### Kỹ thuật: Tombstone constant

- **Là gì:** giữ lại danh sách những thứ **đã xoá** thay vì xoá sạch dấu vết.

  ```python
  RETIRED_ROLES = ("it",)
  ```

- **Để làm gì:** migration và test đều bám vào hằng số này. Lần sau bỏ thêm một vai trò khác, chỉ cần thêm vào tuple — logic dọn dữ liệu và test hồi quy tự áp dụng, không phải viết lại.

### Kỹ thuật: Test hồi quy cho việc xoá

Xoá thứ gì đó dễ sót. Hai test bám `RETIRED_ROLES` để chặn nó quay lại:

```python
@pytest.mark.parametrize("retired", RETIRED_ROLES)
def test_retired_roles_are_fully_removed(retired):
    assert retired not in {r.value for r in UserRole}
    assert retired not in ROLE_ONBOARDING_CATALOG


@pytest.mark.asyncio
@pytest.mark.parametrize("retired", RETIRED_ROLES)
async def test_cannot_register_with_retired_role(client, retired): ...  # API phải trả 422
```

Test thứ hai quan trọng hơn vẻ ngoài: nó chứng minh **không ai đăng ký lại được** vai trò đã bỏ qua đường API, chứ không chỉ là nó vắng mặt trong code.

### Kiểm chứng migration

Dựng lại đúng tình huống dữ liệu cũ rồi chạy hàm dọn:

```
TRƯỚC: users(it)=1  progress=1  invitations(it)=1
Đã xoá 1 tài khoản thuộc vai trò ngừng sử dụng: it
SAU  : users(it)=0  progress=0  invitations(it)=0
```

Cả bản ghi phụ thuộc lẫn lời mời đều được dọn, không để lại dòng mồ côi.

---

## Bước 12 — Gọn lại giao diện theo phản hồi người dùng

**Phản hồi nhận được:** *"giao diện đang quá nhiều thông tin, có cả 2 sidebar là quá nhiều"*, *"không cần chức năng Tài liệu VF"*, *"tên từng bước không cần quá dài và không cần chú thích ở dưới tên"*.

### 12.1. Từ 3 cột xuống 2 cột

Trang onboarding trước đây hiển thị **cùng một danh sách bước ở 3 nơi**:

| Vị trí | Nội dung | Xử lý |
|:---|:---|:---|
| Cột trái `onboarding-sidebar` | Tên bước + mô tả + thời lượng | ✅ Giữ — bổ sung thanh tiến độ |
| Thanh ngang `subtabs-bar` | Lặp lại y hệt danh sách bước | ❌ Xoá |
| Cột phải `onboarding-right-panel` | Vòng tiến độ + mini-checklist (lặp lần 3) + thẻ bài thi + thẻ hỗ trợ | ❌ Xoá, gộp phần cần thiết vào sidebar |

Những thứ **không** mất đi, chỉ chuyển chỗ:

- Vòng tiến độ → **thanh tiến độ mảnh** ngay dưới tiêu đề sidebar (gọn hơn nhiều, cùng thông tin).
- Thẻ "🏆 Bài kiểm tra tốt nghiệp" → một dòng badge ở chân sidebar.
- Thẻ "🆘 Gửi yêu cầu hỗ trợ" → nút ở chân sidebar.

Grid CSS: `290px 1fr 300px` → `300px 1fr`.

### Kỹ thuật: Dọn CSS chết bằng parser, không grep

- **Vấn đề:** gỡ 3 khối JSX để lại ~38 rule CSS không còn ai dùng. Xoá tay dễ sót, mà `grep` theo tên class thì bắt hụt các rule có modifier — `.subtab-btn.active`, `.mini-check-item.done .mini-dot`.
- **Cách làm:** script duyệt file CSS theo cặp `{...}`, với mỗi nhóm selector lấy **class đầu tiên của từng phần** (tách theo dấu phẩy) rồi so với danh sách class đã chết:

  ```python
  def dead_selector(sel: str) -> bool:
      parts = [p.strip() for p in sel.split(",") if p.strip()]
      for part in parts:
          first = re.search(r"\.([\w-]+)", part)
          if not first or first.group(1) not in DEAD:
              return False  # còn 1 phần đang dùng thì giữ cả nhóm
      return True
  ```

- **Vì sao lấy class đầu tiên:** trong `.subtab-btn.active .subtab-num`, class đầu quyết định rule này thuộc về component nào; các phần sau chỉ là trạng thái hoặc phần tử con.
- **Vì sao xét cả nhóm selector:** một rule dùng chung cho nhiều component (`.a, .b { ... }`) chỉ được xoá khi **mọi** phần đều đã chết — nếu không sẽ vô tình xoá style của component còn sống.
- **Kết quả:** 38 rule, `index.css` từ 2061 → 1791 dòng.

### 12.2. Nhãn bước ngắn gọn

**Vấn đề:** tên bước lấy nguyên từ plan nên rất dài — `"Đăng nhập DMS, Tra cứu Thông tin Xe & Mở Lệnh Sửa chữa (RO)"` (59 ký tự) tràn 3 dòng trong cột 300px. Code cũ chữa cháy bằng `title.split(" & ")[0]` — cắt bừa theo dấu `&`, ra kết quả cụt lủn và sai ngữ nghĩa.

### Kỹ thuật: Tách nhãn hiển thị khỏi tên định danh

- **Là gì:** thêm trường `short_title` bên cạnh `title`, thay vì rút gọn `title` hoặc cắt chuỗi lúc render.
- **Vì sao không rút gọn thẳng `title`:** `title` là **tên định danh của bước trong bản đặc tả** — `test_catalog_matches_implementation_plan` đối chiếu đúng chuỗi này với `implementation_plan.md`. Rút gọn nó là phá vỡ liên kết giữa spec và code.
- **Vì sao không cắt chuỗi lúc render:** cắt tự động không bao giờ ra nhãn tốt. `"Cam kết Thời gian SLA, Tồn kho Phụ tùng & QC Xuất xưởng"` cắt máy móc ra `"Cam kết Thời gian SLA, Tồn kho Phụ tùng"` — vẫn dài. Viết tay được `"Cam kết SLA & QC"`.
- **Dùng ở đâu:** `short_title` cho sidebar; `title` đầy đủ cho tiêu đề trang, breadcrumb và tooltip khi hover.
- **Lan qua các tầng:** catalog → cột DB `short_title` → `OnboardingStepResponse` → `types/index.ts` → sidebar. Thêm `short_title` vào tập cột bắt buộc trong `_drop_outdated_onboarding_table()` để DB cũ tự dựng lại.

**Bỏ dòng mô tả dưới tên bước:** `step.description` từng hiển thị ngay dưới tiêu đề trong sidebar — nội dung gần trùng `goal` đã hiện ở khu nội dung chính. Nay sidebar chỉ còn *số thứ tự · nhãn ngắn · thời lượng*.

### Kỹ thuật: Test ràng buộc độ dài nhãn

Nhãn dài lại là chuyện sẽ tái diễn khi thêm bước mới, nên ràng buộc bằng test thay vì bằng lời nhắc:

```python
MAX_SHORT_TITLE_LEN = 26  # cột sidebar rộng 300px


def test_short_title_fits_sidebar(role, step):
    short = step["short_title"]
    assert len(short) <= MAX_SHORT_TITLE_LEN, f"'{short}' dài {len(short)} ký tự"
    assert len(short) < len(step["title"])
```

Nhãn hiện tại dài 11–24 ký tự, đều dưới ngưỡng.

### 12.3. Gỡ chức năng "Tài liệu VF"

Xoá `DocumentsPage.tsx`, route `/documents`, mục nav trong `AppShell` và quick-link ở Dashboard. Người dùng đã có mọi tài liệu ngay trong từng bước onboarding kèm kiểm soát RBAC — một trang kho tài liệu riêng vừa thừa vừa là đường vòng qua phân quyền.

File xoá bằng `git rm` nên khôi phục được bằng `git checkout HEAD -- frontend/src/pages/DocumentsPage.tsx`.

**Sửa kèm:** `useGuidedTour` đang trỏ tới `#onboarding-subtabs` — phần tử vừa bị xoá. Driver.js sẽ hỏng bước tour đó. Đã gộp nội dung vào bước giới thiệu sidebar.

---

## Kiểm chứng đã chạy

```
python -m scripts.verify_onboarding_resources   → 84/84 tài liệu tồn tại
pytest tests/test_api                            → 96 passed
ruff check <các file mới>                        → All checks passed
npx tsc --noEmit                                 → exit 0
npm run build                                    → built in 126ms
```

**E2E thực tế trên server port 8001:**

| Vai trò | Bước | Tài liệu | Tải được | Câu hỏi | RBAC chéo |
|:---|:---:|:---:|:---:|:---:|:---|
| accountant | 5 | 48 | 48/48 ✅ | 15 (3×5) ✅ | 403 ✅ |
| sale | 4 | 5 | 5/5 ✅ | 12 (3×4) ✅ | 403 ✅ |
| technician | 5 | 12 | 12/12 ✅ | 15 (3×5) ✅ | 403 ✅ |
| manager | 5 | 10 | 10/10 ✅ | 15 (3×5) ✅ | 403 ✅ |
| owner | 4 | 9 | 9/9 ✅ | 12 (3×4) ✅ | 403 ✅ |

Tổng: **5 vai trò · 23 bước · 84 tham chiếu tài liệu · 69 câu hỏi nhanh**.

Riêng vai trò đã bỏ: đăng nhập `it@vinfast.vn` → **401**, đăng ký `role="it"` → **422**.

Đã kiểm riêng: tua video trả `206 Partial Content`; `../../.env` bị chặn; bấm "Hoàn thành" hai lần không nhân đôi tiến độ; F5 không mất tiến độ.

*Lưu ý:* 4 test module khác (`test_preprocessing`, `test_retrieval_and_eval`, `test_markdown_pipeline`, `scripts/test_pipeline_e2e`) lỗi collection do **thiếu package** `rank_bm25` trong môi trường — lỗi có sẵn từ trước, không liên quan thay đổi này.

---

## Cách chạy

```bash
# Terminal 1 — Backend  (.venv thiếu sqlalchemy, phải dùng python của Anaconda)
/opt/anaconda3/bin/python -m uvicorn src.main:app --port 8001 --reload

# Terminal 2 — Frontend
cd frontend && npm run dev          # http://localhost:5173
```

Tài khoản demo (mật khẩu `12345678`): `ketoan@` · `sales@` · `kythuat@` · `quanly@` · `thehung@vinfast.vn`.

**Sửa nội dung lộ trình:** sửa `implementation_plan.md` → sửa `onboarding_catalog.py` cho khớp → đổi `CATALOG_VERSION` → chạy `pytest tests/test_api` để chắc hai bên không lệch.

---

## Việc còn để lại (nợ kỹ thuật)

| Hạng mục | Mức độ | Ghi chú |
|:---|:---|:---|
| `SECRET_KEY` hardcode trong `src/auth/security.py` | 🔴 Cao | Phải đưa ra biến môi trường trước khi deploy |
| Plan chưa đặc tả vai trò `owner` | 🟡 Vừa | Nội dung 4 bước này do team tự soạn, chưa được PO duyệt |
| CHECK constraint cột `users.role` vẫn cho phép `'it'` | 🟢 Thấp | Vô hại vì tầng Python không sinh ra giá trị đó; siết lại phải dựng lại cả bảng |
| Token trong URL của tài liệu | 🟡 Vừa | Nên đổi sang signed URL hạn 5 phút |
| Drop-and-reseed thay migration | 🟡 Vừa | Chuyển sang Alembic khi có dữ liệu người dùng thật |
| Đổi `CATALOG_VERSION` là reset tiến độ mọi user | 🟡 Vừa | Đúng về mặt dữ liệu nhưng cần thông báo khi vận hành thật |
| Kế toán B3 có 19 tài liệu trong một bước | 🟡 Vừa | Đúng theo plan nhưng UI dày đặc — cân nhắc nhóm "tài liệu chính / tham khảo" |
| `DmsSandboxModal` còn theo `stepIndex` cứng | 🟢 Thấp | Nội dung sandbox chưa lấy từ DB như các phần khác |
| Bundle JS 525 KB | 🟢 Thấp | Cân nhắc code-splitting bằng `React.lazy` |

---

## [12/08/2026] Khắc phục lỗi UI: Khóa bước (Locking) trên Thanh Điều Hướng Ngang

### 1. Vấn đề (Issue)
- **Lỗi:** Sidebar bên trái hiển thị trạng thái "Khóa" (Locked) đúng đối với các bước chưa hoàn thành. Tuy nhiên, ở thanh subtabs ngang, người dùng vẫn có thể click vào bất kỳ bước nào dù chưa hoàn thành bước trước đó.

### 2. Kỹ thuật áp dụng (Technique used)
- **Tính toán trạng thái logic trong React Component (State Derived Logic):**
  - **Sử dụng:** `const isLocked = idx > activeStepIdx && !completedSet.has(steps[idx - 1]?.id);`
  - **Ý nghĩa:** Biến `isLocked` được tính toán trực tiếp trong `.map()` dựa trên `idx`, `activeStepIdx` và `completedSet`. Bổ sung class css và guard condition `onClick={() => !isLocked && setActiveStepIdx(idx)}` để chặn sự kiện nhảy bước nhảy cóc.

### 3. File đã thay đổi (Modified files)
- `frontend/src/pages/OnboardingPage.tsx`: Cập nhật `<div className="subtabs-bar">`.

---

## [12/08/2026] Triển khai Hybrid Architecture: SQLite -> FastAPI -> React (Đang thực hiện)

### 1. Định hướng kiến trúc
- Cần triển khai luồng Onboarding mới (theo `implementation_plan.md`). Không dùng Mockdata UI thuần túy để tránh viết lại 2 lần.

### 2. Kỹ thuật áp dụng (Architecture used)
- **Hybrid "Seed-First + Static File Serve":**
  - **SQLite seed:** Cập nhật `seed_onboarding_steps()` (trong `src/db/crud.py`) với dữ liệu thật (4 roles, bước, resource_url trỏ về `Data_separate`).
  - **FastAPI:** Phục vụ các file trong `Data/Data_separate/` thông qua API có bảo mật.
  - **Frontend:** Fetch dữ liệu từ API thật và render tài liệu thật ngay từ đầu.

---

## [12/08/2026] Đảo ngẫu nhiên câu trả lời Trắc nghiệm (Quiz Shuffling)

### 1. Vấn đề (Issue)
- Các câu hỏi nhanh (Quiz) trả về từ catalog đang có đáp án đúng luôn nằm ở vị trí đầu tiên (A). Người dùng có thể đoán mò mà không cần đọc bài.

### 2. Kỹ thuật áp dụng (Technique used)
- **Đảo mảng ngẫu nhiên (Fisher-Yates Shuffle) kết hợp `useEffect`:**
  - **Sử dụng:** Trong component `QuizModal.tsx`, sử dụng thuật toán Fisher-Yates để đảo vị trí các option trong mảng.
  - **Ý nghĩa:** Việc xáo trộn (shuffle) được thực hiện ở Frontend ngay khi Modal vừa mở (`isOpen === true`). Bằng cách này, dữ liệu API (Backend) vẫn giữ nguyên tính ổn định (không cần randomize mỗi lần gọi API gây khó khăn cho Caching). React sẽ tạo ra mảng `shuffledQuestions` lưu vào state nội bộ, đồng thời cập nhật lại `correctIndex` tương ứng với vị trí mới của đáp án đúng. Mảng này được reset mỗi khi tắt/bật lại Quiz Modal.

### 3. File đã thay đổi (Modified files)
- `frontend/src/components/onboarding/QuizModal.tsx`: Thêm biến state `shuffledQuestions` và `useEffect` xử lý mảng.

---

## [12/08/2026] Làm đều độ dài các câu hỏi Trắc nghiệm (Quiz Options Balancing)

### 1. Vấn đề (Issue)
- Nhược điểm của dữ liệu tĩnh ban đầu là câu trả lời ĐÚNG luôn rất dài và chi tiết, còn 3 câu trả lời SAI lại rất ngắn. Việc này khiến người học dễ dàng vượt qua bài kiểm tra bằng cách luôn chọn câu dài nhất mà không cần hiểu bản chất.

### 2. Kỹ thuật áp dụng (Technique used)
- **Tự động hóa xử lý ngôn ngữ bằng AI (AST + LLM API):**
  - **Sử dụng:** Viết script Python (`scripts/rewrite_options.py`) sử dụng thư viện `langchain_openai` và `langchain_core` gọi mô hình `gpt-4o-mini`. 
  - **Ý nghĩa:**
    - Parse file Python `onboarding_catalog.py` an toàn bằng biểu thức chính quy (`re.sub` + `re.finditer`) và `ast.literal_eval`.
    - Duyệt qua toàn bộ **69 câu hỏi** trong cơ sở dữ liệu.
    - Với mỗi bộ 4 options, gửi lên LLM với prompt yêu cầu: Cân bằng độ dài giữa câu đúng và sai, bịa thêm các chi tiết/quy trình nghe có vẻ hợp lý nhưng sai bản chất cho các câu nhiễu, giữ nguyên đáp án đúng ở vị trí index 0.
    - Ghi đè tự động lại vào source code mà không làm mất định dạng (format).
  - Bằng cách này, chúng ta tiết kiệm được hàng giờ đồng hồ viết lại đáp án bằng tay cho 69 câu.

### 3. File đã thay đổi (Modified files)
- `scripts/rewrite_options.py`: Script tự động sinh đáp án.
- `src/content/onboarding_catalog.py`: Dữ liệu 69 câu hỏi đã được làm đều độ dài, cộng thêm việc bump `CATALOG_VERSION` để Uvicorn tự động re-seed lại Database.

---

## [12/08/2026] Rút ngắn tối đa các câu hỏi Trắc nghiệm (Quiz Options Shortening)

### 1. Vấn đề (Issue)
- Sau khi được làm đều, các câu hỏi trở nên quá dài và khó đọc. Người học dễ bị choáng ngợp bởi một lượng lớn chữ và quy trình. Cần rút ngắn tối đa mọi câu trả lời để có thể đọc lướt nhanh nhưng không được "hallucination" (bịa thông tin).

### 2. Kỹ thuật áp dụng (Technique used)
- **Cập nhật Prompt cho LLM (gpt-4o-mini):**
  - Đặt giới hạn cứng: Tối đa 1 dòng, dưới 15 từ mỗi câu.
  - Ép buộc AI đóng vai trò người tóm tắt: Thay vì để nguyên độ dài gốc, AI phải chủ động tóm gọn bản chất của hành động hoặc danh từ cốt lõi thành 1 cụm từ duy nhất.
  - Chống Hallucination: Yêu cầu AI tuyệt đối không bịa đặt những thứ phi lý, mà chỉ được đưa ra các phương án sai khác liên quan đến ngữ cảnh nhưng sai về mặt quy trình/định nghĩa để làm câu nhiễu.
- Chạy lại tiến trình xử lý trên toàn bộ 69 câu hỏi thông qua `scripts/rewrite_options.py`.
- Bump `CATALOG_VERSION` lên `2026.08.12-shortened-quiz-options` để kích hoạt nạp lại DB.

### 3. File đã thay đổi (Modified files)
- `scripts/rewrite_options.py`: Sửa lại Prompt khắt khe hơn.
- `src/content/onboarding_catalog.py`: Cập nhật nội dung câu hỏi mới, cấu trúc siêu ngắn gọn.

---

## [12/08/2026] Cập nhật câu báo lỗi trang Đăng nhập

### 1. Vấn đề (Issue)
- Thay đổi thông báo lỗi ở trang đăng nhập (khi nhập sai mật khẩu/tài khoản) cho thân thiện và rõ ràng hơn theo yêu cầu.

### 2. Kỹ thuật áp dụng (Technique used)
- Thay vì lấy `detail` từ HTTP Response (backend trả về) hiển thị trực tiếp cho người dùng, ta thiết lập thông báo lỗi cố định (hardcode tĩnh) trên khối `catch` khi bắt exception đăng nhập thất bại.
- Lý do: Với Authentication, đăng nhập sai (dù sai email hay password) đều nên trả về 1 lỗi chung chung để tránh hacker dò tìm tài khoản. Câu báo lỗi tĩnh đảm bảo tính bảo mật và thân thiện.

### 3. File đã thay đổi (Modified files)
- `frontend/src/pages/LoginPage.tsx`: Sửa `setError(...)` thành câu báo lỗi chỉ định.

---

## [12/08/2026] Sửa lỗi tự động tải lại trang khi Đăng nhập sai

### 1. Vấn đề (Issue)
- Khi người dùng nhập sai thông tin ở trang đăng nhập, trang bị tự động tải lại (reload) thay vì hiển thị câu thông báo lỗi bằng chữ màu đỏ. 

### 2. Kỹ thuật áp dụng (Technique used)
- **Fix Axios Interceptors:** 
  - Trong dự án hiện tại, file `api.ts` có cấu hình một interceptor để bắt tất cả các lỗi `401 Unauthorized`. Mỗi khi nhận được 401, nó sẽ tự động xóa token và chuyển hướng `window.location.href = "/login"`.
  - **Lỗi xảy ra vì:** Khi gọi API đăng nhập (`/api/v1/auth/login`) mà bị sai mật khẩu, server trả về lỗi `401`. Interceptor vớt được lỗi này và tưởng là token hết hạn, nên nó lập tức force tải lại (refresh) lại trang `/login` ngay lập tức! Do đó, state `error` chứa thông báo lỗi bên file `LoginPage.tsx` chưa kịp render ra màn hình thì trang đã bị reload sạch sẽ.
  - **Cách xử lý:** Thêm câu lệnh điều kiện `if (err.config?.url !== "/api/v1/auth/login")` vào interceptor để bỏ qua lệnh redirect nếu request đó chính là request đăng nhập. Khi đó, lỗi 401 sẽ được ném thẳng về component `LoginPage.tsx` để xử lý và hiển thị thông báo lỗi bình thường.

### 3. File đã thay đổi (Modified files)
- `frontend/src/services/api.ts`: Cập nhật logic `interceptors.response`.

---

## [12/08/2026] Bổ sung trang Tài Liệu VF (Documents Page)

### 1. Vấn đề (Issue)
- Nút "Tài liệu VF" ở trang Dashboard đang điều hướng nhầm sang trang Onboarding (`/onboarding`).
- Người dùng muốn có một trang riêng chứa toàn bộ danh sách các tài liệu liên quan đến role (vai trò) của họ để dễ theo dõi và tra cứu.

### 2. Kỹ thuật áp dụng (Technique used)
- **Tạo trang React mới (`DocumentsPage.tsx`):**
  - Gọi API `onboardingApi.getSteps()` để lấy toàn bộ các bước onboarding của role hiện tại.
  - Sử dụng logic `.forEach()` để làm phẳng (flatten) toàn bộ mảng `resources` nằm rải rác bên trong các bước Onboarding thành một mảng tài liệu duy nhất.
  - Loại bỏ trùng lặp bằng cấu trúc `new Map()` dựa trên URL của tài liệu, để đảm bảo không hiển thị 2 file giống nhau.
  - Hiển thị danh sách tài liệu lên màn hình dưới dạng Grid với Framer Motion animations.
- **Cập nhật Routing (`router/index.tsx`):** Đăng ký Route `/documents` vào AppShell để nó nằm trong khối Protected Route (phải đăng nhập mới xem được).
- **Cập nhật UI Điều hướng:** 
  - Đổi link của nút "Tài liệu VF" trong `DashboardPage.tsx` từ `/onboarding` sang `/documents`.
  - Bổ sung menu item "Tài liệu VF" vào thanh Sidebar trong file `AppShell.tsx` để người dùng tiện nhấp vào.

### 3. File đã thay đổi (Modified files)
- `frontend/src/pages/DocumentsPage.tsx` (Mới tạo)
- `frontend/src/router/index.tsx`
- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/pages/DashboardPage.tsx`

---

## [12/08/2026] Sửa lỗi Trang Tài Liệu VF không hiện danh sách và không mở được file

### 1. Vấn đề (Issue)
- Ở trang Tài Liệu VF (`/documents`) hiển thị dòng chữ "Không có tài liệu nào cho vai trò của bạn" dù trong cơ sở dữ liệu đã có tài liệu.
- Kể cả khi có tài liệu hiển thị, click vào cũng không mở được (không tải được file).

### 2. Kỹ thuật áp dụng (Technique used)
- **Fix Data Mapping Bug:**
  - Khởi điểm, tôi sử dụng thuộc tính `url` (`res.url`) làm key để lọc trùng lặp và làm href cho liên kết thẻ. Tuy nhiên, schema thực tế trong cơ sở dữ liệu và type của API trả về cho thuộc tính này là `path` chứ không phải `url`. 
  - Điều này dẫn đến tất cả `res.url` đều là `undefined`, khi đưa qua `new Map()` thì tất cả bị đè lên nhau thành một key `undefined` duy nhất, hoặc mảng bị lỗi, khiến danh sách rỗng.
  - Sửa lại toàn bộ `res.url` thành `res.path`.
- **Áp dụng Component Xem trước Tài liệu (ResourceViewerModal):**
  - Đổi thẻ `<a>` thành thẻ `<button>` với sự kiện `onClick`.
  - Tái sử dụng component `ResourceViewerModal` (như trang Onboarding đang dùng) để khi click vào tài liệu, màn hình popup sẽ hiện ra cho phép tải file hoặc xem trực tiếp video, tạo trải nghiệm đồng nhất với phần học chính.

### 3. File đã thay đổi (Modified files)
- `frontend/src/pages/DocumentsPage.tsx`: Sửa mapping properties và import Modal vào để sử dụng.
