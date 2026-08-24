"""Kiểm thử lộ trình onboarding và endpoint phục vụ tài liệu thật.

Các test chạy trên DB seed sẵn (`data/app.db`) với tài khoản demo do
`seed_default_users()` tạo, giống môi trường dev.
"""

import re
import unicodedata
from urllib.parse import quote

import pytest

from src.content.onboarding_catalog import (
    QUIZ_QUESTIONS_PER_STEP,
    ROLE_ONBOARDING_CATALOG,
    resource_paths_for_role,
)
from src.db import SessionLocal
from src.db.crud import get_user_by_email
from src.db.models import RETIRED_ROLES, UserModuleQuiz, UserRole, UserSectionProgress
from src.media import PROJECT_ROOT, resolve_media_path

ALL_STEPS = [(role, step) for role, steps in ROLE_ONBOARDING_CATALOG.items() for step in steps]

# Cột sidebar rộng 300px — quá ngưỡng này nhãn sẽ tràn sang dòng thứ hai.
MAX_SHORT_TITLE_LEN = 26

PLAN_PATH = PROJECT_ROOT / "docs" / "implementation_plan.md"
# Thứ tự khối "# ... ROLE n:" trong plan tương ứng với các vai trò sau.
PLAN_ROLE_ORDER = ("accountant", "sale", "technician", "manager")


def _plan_step_titles() -> dict[str, list[str]]:
    """Đọc tiêu đề các bước từ implementation_plan.md theo từng ROLE."""
    text = PLAN_PATH.read_text(encoding="utf-8")
    sections = re.split(r"^# .*ROLE \d+:", text, flags=re.M)[1:]
    return {
        role: re.findall(r"^### 📍 BƯỚC \d+ — (.+)$", section, flags=re.M)
        for role, section in zip(PLAN_ROLE_ORDER, sections)
    }


DEMO_ACCOUNTS = {
    "accountant": "ketoan@vinfast.vn",
    "technician": "kythuat@vinfast.vn",
    "sale": "sales@vinfast.vn",
    "manager": "quanly@vinfast.vn",
    "owner": "thehung@vinfast.vn",
}

# Các test tiến độ có ghi vào DB nên dùng tài khoản phụ, tránh làm bẩn dữ liệu
# của tài khoản chính hay dùng để demo.
PROGRESS_TEST_ACCOUNT = "thehung@gmail.com"


async def _login(client, email: str, password: str = "12345678") -> str:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _file_url(path: str) -> str:
    return "/api/v1/files/" + quote(path)


def _module1_path(role: str = "accountant") -> str:
    """Trả về đường dẫn tài liệu thuộc Module 1 (luôn mở khóa cho user mới)."""
    from src.content.onboarding_catalog import ROLE_ONBOARDING_CATALOG

    step1 = ROLE_ONBOARDING_CATALOG[role][0]
    return step1["resources"][0]["path"]


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("role", PLAN_ROLE_ORDER)
def test_catalog_matches_implementation_plan(role):
    """Catalog phải khớp 1-1 với các bước đặc tả trong implementation_plan.md."""
    plan_titles = _plan_step_titles()[role]
    catalog_titles = [step["title"] for step in ROLE_ONBOARDING_CATALOG[role]]
    assert catalog_titles == plan_titles


def test_plan_declares_three_questions_per_step():
    """Mọi khối 'THAO TÁC THỬ' trong plan phải liệt kê đúng 3 câu hỏi."""
    text = PLAN_PATH.read_text(encoding="utf-8")
    blocks = re.findall(r"🎮 THAO TÁC THỬ.*?(?=├─)", text, flags=re.S)
    assert blocks, "Không tìm thấy khối THAO TÁC THỬ nào trong plan"
    wrong = [i for i, b in enumerate(blocks, 1) if len(re.findall(r"Q\d:", b)) != QUIZ_QUESTIONS_PER_STEP]
    assert wrong == [], f"Các khối không đủ {QUIZ_QUESTIONS_PER_STEP} câu: {wrong}"


@pytest.mark.parametrize("role,step", ALL_STEPS, ids=[f"{r}:{s['title'][:28]}" for r, s in ALL_STEPS])
def test_every_step_has_exactly_three_quick_questions(role, step):
    """Quy ước: mỗi bước phải có đúng 3 câu hỏi nhanh, đánh số 1..3."""
    quiz = step["quiz"]
    assert len(quiz) == QUIZ_QUESTIONS_PER_STEP
    assert [q["id"] for q in quiz] == list(range(1, QUIZ_QUESTIONS_PER_STEP + 1))


@pytest.mark.parametrize("role,step", ALL_STEPS, ids=[f"{r}:{s['title'][:28]}" for r, s in ALL_STEPS])
def test_quiz_questions_are_well_formed(role, step):
    """Mỗi câu 4 lựa chọn, đáp án đúng nằm trong dải, và có giải thích."""
    for question in step["quiz"]:
        assert question["question"].strip()
        assert len(question["options"]) == 4
        assert 0 <= question["correctIndex"] < len(question["options"])
        assert question["explanation"].strip()


@pytest.mark.parametrize("retired", RETIRED_ROLES)
def test_retired_roles_are_fully_removed(retired):
    """Vai trò đã loại bỏ không được còn sót ở enum hay catalog."""
    assert retired not in {r.value for r in UserRole}
    assert retired not in ROLE_ONBOARDING_CATALOG


@pytest.mark.asyncio
@pytest.mark.parametrize("retired", RETIRED_ROLES)
async def test_cannot_register_with_retired_role(client, retired):
    """API phải từ chối đăng ký bằng vai trò đã loại bỏ."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"thu-{retired}@vinfast.vn",
            "password": "12345678",
            "full_name": "Tài khoản thử",
            "role": retired,
        },
    )
    assert response.status_code == 422


@pytest.mark.parametrize("role,step", ALL_STEPS, ids=[f"{r}:{s['title'][:28]}" for r, s in ALL_STEPS])
def test_short_title_fits_sidebar(role, step):
    """Nhãn sidebar phải ngắn — dài quá sẽ xuống dòng và làm rối cột điều hướng."""
    short = step["short_title"]
    assert short.strip(), "Bước nào cũng phải có short_title"
    assert len(short) <= MAX_SHORT_TITLE_LEN, f"'{short}' dài {len(short)} ký tự"
    assert len(short) < len(step["title"]), "short_title phải ngắn hơn title đầy đủ"


@pytest.mark.integration
def test_catalog_resources_exist_on_disk():
    """Mọi tài liệu tham chiếu local (không phải s3://) trong catalog phải có thật.

    Đánh dấu @integration — chỉ chạy khi thư mục Data/raw có đầy đủ file thật.
    Dùng: pytest -m integration
    """
    missing = [
        res["path"]
        for steps in ROLE_ONBOARDING_CATALOG.values()
        for step in steps
        for res in step["resources"]
        if not res["path"].startswith("s3://") and not resolve_media_path(res["path"]).is_file()
    ]
    assert missing == [], f"Thiếu {len(missing)} file: {missing}"


# ---------------------------------------------------------------------------
# Lộ trình onboarding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_steps_require_authentication(client):
    response = await client.get("/api/v1/auth/onboarding/steps")
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("role,email", DEMO_ACCOUNTS.items())
async def test_steps_returned_with_real_resources(client, role, email):
    token = await _login(client, email)
    response = await client.get("/api/v1/auth/onboarding/steps", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    steps = response.json()
    assert len(steps) == len(ROLE_ONBOARDING_CATALOG[role])

    for step in steps:
        assert step["role_target"] == role
        assert step["goal"], "Bước phải có mục tiêu bài học"
        assert step["guides"], "Bước phải có hướng dẫn nhanh"
        assert step["resources"], "Bước phải có tài liệu đính kèm"
        assert len(step["quiz"]) == QUIZ_QUESTIONS_PER_STEP, "API phải trả đủ 3 câu hỏi nhanh"
        for resource in step["resources"]:
            # meta được tính từ file thật lúc seed nên không được rỗng
            assert resource["meta"]
            assert unicodedata.normalize("NFC", resource["path"]) in resource_paths_for_role(role)


# ---------------------------------------------------------------------------
# Endpoint tài liệu: xác thực, RBAC, Range
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_file_requires_authentication(client):
    path = _module1_path()
    response = await client.get(_file_url(path))
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_file_served_with_bearer_header(client):
    token = await _login(client, DEMO_ACCOUNTS["accountant"])
    path = _module1_path()
    response = await client.get(_file_url(path), headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["content-disposition"] == "inline"


@pytest.mark.asyncio
async def test_file_served_with_query_token(client):
    """Thẻ <video>/<iframe> không gửi được header nên phải nhận token qua query."""
    token = await _login(client, DEMO_ACCOUNTS["accountant"])
    path = _module1_path()
    response = await client.get(_file_url(path), params={"token": token})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_download_flag_forces_attachment(client):
    token = await _login(client, DEMO_ACCOUNTS["accountant"])
    path = _module1_path()
    response = await client.get(_file_url(path), params={"token": token, "download": "true"})
    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith("attachment")
    assert "filename*=UTF-8''" in response.headers["content-disposition"]


@pytest.mark.asyncio
async def test_rbac_blocks_cross_role_file_access(client):
    """Kỹ thuật viên không được tải tài liệu tài chính của Kế toán."""
    token = await _login(client, DEMO_ACCOUNTS["technician"])
    forbidden = sorted(resource_paths_for_role("accountant") - resource_paths_for_role("technician"))
    assert forbidden, "Cần ít nhất một tài liệu chỉ Kế toán mới có"

    for path in forbidden[:5]:
        response = await client.get(_file_url(path), params={"token": token})
        assert response.status_code == 403, f"Rò rỉ RBAC tại {path}"


@pytest.mark.asyncio
async def test_path_traversal_is_rejected(client):
    token = await _login(client, DEMO_ACCOUNTS["accountant"])
    response = await client.get("/api/v1/files/../../.env", params={"token": token})
    assert response.status_code in (400, 403, 404)


@pytest.mark.asyncio
async def test_range_request_returns_partial_content(client):
    """Tài liệu phải hỗ trợ Range request — trình duyệt dựa vào 206 Partial Content để tua video/PDF."""
    token = await _login(client, DEMO_ACCOUNTS["accountant"])
    # Dùng tài liệu module 1 (luôn mở khóa) — tất cả mp4 của kế toán đều ở module 2+
    file_path = _module1_path()
    response = await client.get(_file_url(file_path), params={"token": token}, headers={"Range": "bytes=0-1023"})
    assert response.status_code == 206
    assert response.headers["content-range"].startswith("bytes 0-1023/")


@pytest.mark.asyncio
async def test_etag_and_cache_revalidation(client):
    """Phản hồi media phải có ETag và trả 304 khi If-None-Match khớp."""
    token = await _login(client, DEMO_ACCOUNTS["accountant"])
    file_path = _module1_path()
    response = await client.get(_file_url(file_path), params={"token": token})
    assert response.status_code == 200
    assert "etag" in response.headers
    assert "last-modified" in response.headers
    assert "no-cache" in response.headers.get("cache-control", "")

    etag = response.headers["etag"]
    # Revalidation request
    reval = await client.get(
        _file_url(file_path),
        params={"token": token},
        headers={"If-None-Match": etag},
    )
    assert reval.status_code == 304


# ---------------------------------------------------------------------------
# Tiến độ
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_completing_a_step_twice_does_not_double_count(client):
    token = await _login(client, PROGRESS_TEST_ACCOUNT)
    auth = {"Authorization": f"Bearer {token}"}

    steps = (await client.get("/api/v1/auth/onboarding/steps", headers=auth)).json()
    step_id = steps[0]["id"]

    first = (await client.post(f"/api/v1/auth/onboarding/steps/{step_id}/complete", headers=auth)).json()
    second = (await client.post(f"/api/v1/auth/onboarding/steps/{step_id}/complete", headers=auth)).json()

    assert first["progress"] == second["progress"]
    assert second["completed_step_ids"].count(step_id) == 1


@pytest.mark.asyncio
async def test_progress_survives_reload(client):
    """GET /progress phải trả lại đúng những bước đã hoàn thành."""
    token = await _login(client, PROGRESS_TEST_ACCOUNT)
    auth = {"Authorization": f"Bearer {token}"}

    steps = (await client.get("/api/v1/auth/onboarding/steps", headers=auth)).json()
    step_id = steps[0]["id"]
    await client.post(f"/api/v1/auth/onboarding/steps/{step_id}/complete", headers=auth)

    progress = (await client.get("/api/v1/auth/onboarding/progress", headers=auth)).json()
    assert step_id in progress["completed_step_ids"]
    assert progress["total_steps"] == len(steps)
    assert progress["progress"] > 0


@pytest.mark.asyncio
async def test_completing_step_of_another_role_is_ignored(client):
    token = await _login(client, PROGRESS_TEST_ACCOUNT)
    auth = {"Authorization": f"Bearer {token}"}

    role_step_ids = {s["id"] for s in (await client.get("/api/v1/auth/onboarding/steps", headers=auth)).json()}
    before = (await client.get("/api/v1/auth/onboarding/progress", headers=auth)).json()

    foreign_step_id = max(role_step_ids) + 1000
    after = (await client.post(f"/api/v1/auth/onboarding/steps/{foreign_step_id}/complete", headers=auth)).json()

    assert after["progress"] == before["progress"]
    assert foreign_step_id not in after["completed_step_ids"]


@pytest.mark.asyncio
async def test_quiz_pass_unlocks_next_module(client):
    db = SessionLocal()
    user = get_user_by_email(db, PROGRESS_TEST_ACCOUNT)
    assert user is not None
    db.query(UserModuleQuiz).filter(UserModuleQuiz.user_id == user.id).delete(synchronize_session=False)
    db.commit()
    db.close()

    token = await _login(client, PROGRESS_TEST_ACCOUNT)
    auth = {"Authorization": f"Bearer {token}"}
    try:
        locked = await client.post(
            "/api/v1/auth/onboarding/quizzes/submit",
            headers=auth,
            json={"module_id": 2, "score": 100},
        )
        assert locked.status_code == 403

        result = await client.post(
            "/api/v1/auth/onboarding/quizzes/submit",
            headers=auth,
            json={"module_id": 1, "score": 80},
        )
        assert result.status_code == 200
        modules = {item["module_id"]: item for item in result.json()["modules"]}
        assert modules[1]["completed"] is True
        assert modules[2]["unlocked"] is True
        assert modules[3]["unlocked"] is False
    finally:
        db = SessionLocal()
        user = get_user_by_email(db, PROGRESS_TEST_ACCOUNT)
        assert user is not None
        db.query(UserModuleQuiz).filter(UserModuleQuiz.user_id == user.id).delete(synchronize_session=False)
        db.commit()
        db.close()


@pytest.mark.asyncio
async def test_section_progress_is_saved_separately(client):
    token = await _login(client, PROGRESS_TEST_ACCOUNT)
    auth = {"Authorization": f"Bearer {token}"}
    steps = (await client.get("/api/v1/auth/onboarding/steps", headers=auth)).json()
    section_id = steps[0]["resources"][0]["section_id"]

    try:
        response = await client.post(f"/api/v1/auth/onboarding/sections/{section_id}/complete", headers=auth)
        assert response.status_code == 200
        assert section_id in response.json()["completed_section_ids"]
    finally:
        db = SessionLocal()
        user = get_user_by_email(db, PROGRESS_TEST_ACCOUNT)
        assert user is not None
        db.query(UserSectionProgress).filter(
            UserSectionProgress.user_id == user.id,
            UserSectionProgress.section_id == section_id,
        ).delete(synchronize_session=False)
        db.commit()
        db.close()
