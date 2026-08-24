"""CRUD operations for User, Invitation, OnboardingStep, SupportTicket."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.auth.security import hash_password
from src.cloud.s3_service import s3_service
from src.content.onboarding_catalog import CATALOG_VERSION, ROLE_ONBOARDING_CATALOG
from src.db.models import (
    Invitation,
    OnboardingStep,
    PendingUpdate,
    SupportTicket,
    TicketStatus,
    User,
    UserModuleQuiz,
    UserRole,
    UserSectionProgress,
    UserStatus,
    UserStepProgress,
)
from src.media import describe_file, resolve_media_path

# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower().strip()).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    role: UserRole | str = UserRole.sale,
    agency_id: str | None = None,
    status: UserStatus = UserStatus.active,
) -> User:
    user_role = UserRole(role) if isinstance(role, str) else role
    user = User(
        email=email.lower().strip(),
        hashed_password=hash_password(password),
        full_name=full_name,
        role=user_role,
        agency_id=agency_id,
        status=status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_progress(db: Session, user_id: str, progress: int) -> User | None:
    user = get_user_by_id(db, user_id)
    if user:
        user.onboarding_progress = max(0, min(100, progress))
        db.commit()
        db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Invitation
# ---------------------------------------------------------------------------


def create_invitation(db: Session, *, inviter_id: str, email: str, role: UserRole) -> Invitation:
    from src.config import get_settings

    inv = Invitation(
        inviter_id=inviter_id,
        email=email.lower().strip(),
        role=role,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now(UTC) + timedelta(hours=get_settings().invite_ttl_hours),
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def get_invitation_by_token(db: Session, token: str) -> Invitation | None:
    return db.query(Invitation).filter(Invitation.token == token).first()


# ---------------------------------------------------------------------------
# OnboardingStep
# ---------------------------------------------------------------------------


def get_steps_by_role(db: Session, role: str) -> list[OnboardingStep]:
    return (
        db.query(OnboardingStep)
        .filter((OnboardingStep.role_target == role) | (OnboardingStep.role_target == "all"))
        .order_by(OnboardingStep.order, OnboardingStep.id)
        .all()
    )


def _build_resources(raw_resources: list[dict]) -> list[dict]:
    """Gắn thêm `meta` (loại file + dung lượng) đọc trực tiếp từ file trên đĩa.

    Đọc lúc seed thay vì hardcode để con số hiển thị luôn khớp tài liệu thật.
    """
    enriched = []
    for res in raw_resources:
        raw_path = res.get("path", "")
        if raw_path.startswith("s3://"):
            object_key = raw_path[5:]
            try:
                latest_object_key = s3_service.get_latest_version(object_key)
                if s3_service.object_exists(latest_object_key):
                    raw_path = f"s3://{latest_object_key}"
            except Exception:
                pass

        try:
            path = resolve_media_path(raw_path)
            meta = describe_file(path)
        except ValueError:
            # File đã bị xóa trên MinIO, không đưa vào danh sách
            continue
        section_id = "section-" + hashlib.sha1(f"{res.get('name', '')}::{raw_path}".encode()).hexdigest()[:16]

        # Cập nhật path trong res để UI dùng phiên bản mới nhất
        res_copy = {**res, "meta": meta, "section_id": section_id, "path": raw_path}
        # Nếu phiên bản mới nhất khác với file gốc, cập nhật lại tên hiển thị (tùy chọn, ở đây giữ nguyên tên)
        enriched.append(res_copy)
    return enriched


def seed_onboarding_steps(db: Session) -> None:
    """Nạp lộ trình onboarding của 6 vai trò từ catalog vào DB.

    Chỉ nạp lại khi `content_version` trong DB khác CATALOG_VERSION, nên hàm này
    gọi được ở mọi request mà chỉ tốn đúng một câu SELECT.
    """
    # Deduplicate: nếu có nhiều row (role_target, order) trùng nhau (không phải AI), giữ ID cao nhất.
    all_non_ai = [s for s in db.query(OnboardingStep).all() if s.content_version != "AI_GENERATED"]
    seen: dict[tuple[str, int], OnboardingStep] = {}
    dups: list[int] = []
    for step in sorted(all_non_ai, key=lambda s: s.id):
        key = (step.role_target, step.order)
        if key in seen:
            dups.append(seen[key].id)
        seen[key] = step
    if dups:
        db.query(UserStepProgress).filter(UserStepProgress.step_id.in_(dups)).delete(synchronize_session=False)
        db.query(OnboardingStep).filter(OnboardingStep.id.in_(dups)).delete(synchronize_session=False)
        db.commit()

    existing = {
        (step.role_target, step.order): step
        for step in db.query(OnboardingStep).all()
        if step.content_version != "AI_GENERATED"
    }
    catalog_keys: set[tuple[str, int]] = set()
    for role, role_steps in ROLE_ONBOARDING_CATALOG.items():
        for index, step in enumerate(role_steps, start=1):
            resources = _build_resources(step.get("resources", []))

            # Nếu step này vốn dĩ có tài liệu, nhưng file đã bị xoá hết trên MinIO -> Ẩn luôn step
            if step.get("resources") and not resources:
                continue

            catalog_keys.add((role, index))
            values = dict(
                title=step["title"],
                short_title=step["short_title"],
                description=step.get("description", ""),
                step_type=step["step_type"],
                duration_minutes=step["duration_minutes"],
                is_required=True,
                resource_url=resources[0]["path"] if resources else None,
                goal=step["goal"],
                guides=step["guides"],
                resources=resources,
                quiz=step["quiz"],
                content_version=CATALOG_VERSION,
            )
            row = existing.get((role, index))
            if row is None:
                db.add(OnboardingStep(role_target=role, order=index, **values))
            else:
                for key, value in values.items():
                    setattr(row, key, value)

    # Remove only steps that no longer exist; IDs for unchanged steps remain stable.
    # CHÚ Ý: Không xóa các step do AI sinh ra (content_version == 'AI_GENERATED').
    obsolete = [row for key, row in existing.items() if key not in catalog_keys]
    obsolete_ids = [row.id for row in obsolete]
    if obsolete_ids:
        db.query(UserStepProgress).filter(UserStepProgress.step_id.in_(obsolete_ids)).delete(synchronize_session=False)
        db.query(OnboardingStep).filter(OnboardingStep.id.in_(obsolete_ids)).delete(synchronize_session=False)

    # Dọn dẹp các AI_GENERATED steps mồ côi (file bị xoá khỏi MinIO bằng tay hoặc do lỗi cũ)
    ai_steps = db.query(OnboardingStep).filter(OnboardingStep.content_version == "AI_GENERATED").all()
    for step in ai_steps:
        valid_resources = []
        for res in step.resources:
            raw_path = res.get("path", "")
            if raw_path.startswith("s3://"):
                object_key = raw_path[5:]
                if s3_service.object_exists(object_key):
                    valid_resources.append(res)

        if len(valid_resources) != len(step.resources):
            if not valid_resources:
                db.query(UserStepProgress).filter_by(step_id=step.id).delete()
                db.query(PendingUpdate).filter_by(step_id=step.id).delete()
                db.delete(step)
            else:
                step.resources = valid_resources
                step.resource_url = valid_resources[0].get("path")

    db.commit()


# ---------------------------------------------------------------------------
# Tiến độ onboarding
# ---------------------------------------------------------------------------


def get_completed_step_ids(db: Session, user_id: str) -> list[int]:
    rows = db.query(UserStepProgress.step_id).filter(UserStepProgress.user_id == user_id).all()
    return [row[0] for row in rows]


def get_completed_section_ids(db: Session, user_id: str) -> list[str]:
    rows = db.query(UserSectionProgress.section_id).filter(UserSectionProgress.user_id == user_id).all()
    return [row[0] for row in rows]


def complete_section_for_user(db: Session, user_id: str, section_id: str) -> int:
    user = get_user_by_id(db, user_id)
    if not user:
        return 0
    steps = get_steps_by_role(db, user.role.value)
    target_step = next(
        (step for step in steps if any(resource.get("section_id") == section_id for resource in step.resources)), None
    )
    if target_step is None:
        return user.onboarding_progress
    module_status = next((item for item in get_module_statuses(db, user) if target_step.id in item["step_ids"]), None)
    if not module_status or not module_status["unlocked"]:
        return user.onboarding_progress

    exists = (
        db.query(UserSectionProgress)
        .filter(
            UserSectionProgress.user_id == user_id,
            UserSectionProgress.section_id == section_id,
        )
        .first()
    )
    if not exists:
        db.add(UserSectionProgress(user_id=user_id, section_id=section_id))
        db.flush()

    completed = set(get_completed_section_ids(db, user_id)) | {section_id}
    required = {resource.get("section_id") for resource in target_step.resources}
    if required and required.issubset(completed):
        step_done = (
            db.query(UserStepProgress)
            .filter(
                UserStepProgress.user_id == user_id,
                UserStepProgress.step_id == target_step.id,
            )
            .first()
        )
        if not step_done:
            db.add(UserStepProgress(user_id=user_id, step_id=target_step.id))
    db.commit()
    user.onboarding_progress = _recalculate_progress(db, user)
    db.commit()
    return user.onboarding_progress


def module_id_for_step(step: OnboardingStep, max_order: int) -> int:
    if step.order <= 1:
        return 1
    if max_order > 1 and step.order >= max_order:
        return 3
    return 2


def get_module_statuses(db: Session, user: User) -> list[dict]:
    steps = get_steps_by_role(db, user.role.value)
    max_order = max([s.order for s in steps] + [0])
    quizzes = {row.module_id: row for row in db.query(UserModuleQuiz).filter(UserModuleQuiz.user_id == user.id).all()}
    statuses = []
    previous_passed = True
    for module_id in (1, 2, 3):
        module_steps = [s for s in steps if module_id_for_step(s, max_order) == module_id]
        quiz = quizzes.get(module_id)
        passed = bool(quiz and quiz.passed)
        statuses.append(
            {
                "module_id": module_id,
                "unlocked": previous_passed and bool(module_steps),
                "completed": passed,
                "quiz_score": quiz.score if quiz else None,
                "step_ids": [s.id for s in module_steps],
            }
        )
        previous_passed = passed
    return statuses


def submit_module_quiz(
    db: Session, user_id: str, module_id: int, score: int, passing_score: int = 80
) -> UserModuleQuiz | None:
    user = get_user_by_id(db, user_id)
    if not user or module_id not in (1, 2, 3):
        return None
    status = next((item for item in get_module_statuses(db, user) if item["module_id"] == module_id), None)
    if not status or not status["unlocked"]:
        return None
    row = (
        db.query(UserModuleQuiz)
        .filter(
            UserModuleQuiz.user_id == user_id,
            UserModuleQuiz.module_id == module_id,
        )
        .first()
    )
    if row is None:
        row = UserModuleQuiz(user_id=user_id, module_id=module_id)
        db.add(row)
    row.score = max(0, min(100, score))
    row.passed = row.score >= passing_score
    row.attempts = (row.attempts or 0) + 1
    db.commit()
    db.refresh(row)
    return row


def _recalculate_progress(db: Session, user: User) -> int:
    """% tiến độ = số bước đã hoàn thành / tổng số bước của vai trò."""
    total_steps = (
        db.query(OnboardingStep)
        .filter((OnboardingStep.role_target == user.role.value) | (OnboardingStep.role_target == "all"))
        .count()
    )
    if total_steps == 0:
        return 0

    step_ids = {
        row[0]
        for row in db.query(OnboardingStep.id)
        .filter((OnboardingStep.role_target == user.role.value) | (OnboardingStep.role_target == "all"))
        .all()
    }
    done = sum(1 for sid in get_completed_step_ids(db, user.id) if sid in step_ids)
    return min(100, round(done * 100 / total_steps))


def complete_step_for_user(db: Session, user_id: str, step_id: int) -> int:
    """Đánh dấu hoàn thành 1 bước (idempotent) và trả về % tiến độ mới."""
    user = get_user_by_id(db, user_id)
    if not user:
        return 0

    step = db.query(OnboardingStep).filter(OnboardingStep.id == step_id).first()
    if not step or step.role_target not in (user.role.value, "all"):
        return user.onboarding_progress

    module_status = next(
        (item for item in get_module_statuses(db, user) if step.id in item["step_ids"]),
        None,
    )
    if module_status and not module_status["unlocked"]:
        return user.onboarding_progress

    already_done = (
        db.query(UserStepProgress)
        .filter(UserStepProgress.user_id == user_id, UserStepProgress.step_id == step_id)
        .first()
    )
    if not already_done:
        db.add(UserStepProgress(user_id=user_id, step_id=step_id))
        db.commit()

    user.onboarding_progress = _recalculate_progress(db, user)
    db.commit()
    db.refresh(user)
    return user.onboarding_progress


def seed_default_users(db: Session) -> None:
    """Seed initial demo accounts for all roles if they don't exist."""
    users = [
        # Owners
        {
            "email": "thehung@vinfast.vn",
            "password": "12345678",
            "full_name": "Thế Hưng",
            "role": UserRole.owner,
            "agency_id": "VF-HN-001",
        },
        {
            "email": "thai@vinfast.vn",
            "password": "23456789",
            "full_name": "Quang Thái",
            "role": UserRole.owner,
            "agency_id": "VF-DN-002",
        },
        {
            "email": "chi@vinfast.vn",
            "password": "34567898",
            "full_name": "Kim Chi",
            "role": UserRole.owner,
            "agency_id": "VF-HCM-003",
        },
        {
            "email": "tienhung@vinfast.vn",
            "password": "45678987",
            "full_name": "Tiến Hùng",
            "role": UserRole.owner,
            "agency_id": "VF-HP-004",
        },
        {
            "email": "thehung@gmail.com",
            "password": "12345678",
            "full_name": "Thế Hưng",
            "role": UserRole.owner,
            "agency_id": "VF-HN-001",
        },
        # VinFast Admin
        {
            "email": "vinfast@vinfast.vn",
            "password": "12345678",
            "full_name": "VinFast Admin",
            "role": UserRole.vinfast,
            "agency_id": "VF-HQ-000",
        },
        # Demo accounts for other roles
        {
            "email": "ketoan@vinfast.vn",
            "password": "12345678",
            "full_name": "Kế Toán",
            "role": UserRole.accountant,
            "agency_id": "VF-HN-001",
        },
        {
            "email": "kythuat@vinfast.vn",
            "password": "12345678",
            "full_name": "Kỹ Thuật",
            "role": UserRole.technician,
            "agency_id": "VF-HN-001",
        },
        {
            "email": "sales@vinfast.vn",
            "password": "12345678",
            "full_name": "Sales",
            "role": UserRole.sale,
            "agency_id": "VF-HN-001",
        },
        {
            "email": "quanly@vinfast.vn",
            "password": "12345678",
            "full_name": "Quản Lý",
            "role": UserRole.manager,
            "agency_id": "VF-HN-001",
        },
    ]
    for u in users:
        if not get_user_by_email(db, u["email"]):
            create_user(
                db,
                email=u["email"],
                password=u["password"],
                full_name=u["full_name"],
                role=u["role"],
                agency_id=u["agency_id"],
            )


# ---------------------------------------------------------------------------
# SupportTicket
# ---------------------------------------------------------------------------


def create_support_ticket(
    db: Session,
    *,
    sender_id: str,
    sender_role: str,
    sender_name: str,
    agency_id: str,
    description: str,
    attachment_path: str | None = None,
    attachment_mime: str | None = None,
) -> SupportTicket:
    ticket = SupportTicket(
        sender_id=sender_id,
        sender_role=sender_role,
        sender_name=sender_name,
        agency_id=agency_id,
        description=description,
        attachment_path=attachment_path,
        attachment_mime=attachment_mime,
        status=TicketStatus.open,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def get_support_tickets(db: Session, limit: int = 100) -> list[SupportTicket]:
    """Lấy tất cả tickets, mới nhất lên đầu."""
    return db.query(SupportTicket).order_by(SupportTicket.created_at.desc()).limit(limit).all()


def count_unread_tickets(db: Session) -> int:
    """Đếm số tickets chưa đọc (status = open)."""
    return db.query(func.count(SupportTicket.id)).filter(SupportTicket.status == TicketStatus.open).scalar() or 0


def mark_ticket_read(db: Session, ticket_id: str) -> SupportTicket | None:
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if ticket and ticket.status == TicketStatus.open:
        ticket.status = TicketStatus.read
        db.commit()
        db.refresh(ticket)
    return ticket


# ---------------------------------------------------------------------------
# Manager: Team Progress
# ---------------------------------------------------------------------------


def get_all_users_with_progress(db: Session) -> list[dict]:
    """Lấy danh sách tất cả users (trừ owner) kèm thông tin tiến độ."""
    users = (
        db.query(User)
        .filter(User.role != UserRole.owner, User.role != UserRole.vinfast, User.is_active == True)  # noqa: E712
        .order_by(User.created_at.asc())
        .all()
    )

    result = []
    for user in users:
        # Đếm số bước đã hoàn thành
        completed_count = (
            db.query(func.count(UserStepProgress.id)).filter(UserStepProgress.user_id == user.id).scalar() or 0
        )
        # Đếm tổng số bước cho role
        total_steps = (
            db.query(func.count(OnboardingStep.id))
            .filter((OnboardingStep.role_target == user.role.value) | (OnboardingStep.role_target == "all"))
            .scalar()
            or 0
        )

        progress = user.onboarding_progress
        if progress == 0 and completed_count == 0:
            status_label = "not_started"
        elif progress >= 100:
            status_label = "completed"
        else:
            status_label = "in_progress"

        result.append(
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role.value,
                "agency_id": user.agency_id or "",
                "onboarding_progress": progress,
                "completed_steps": completed_count,
                "total_steps": total_steps,
                "status": status_label,
            }
        )

    return result


# ---------------------------------------------------------------------------
# PendingUpdate
# ---------------------------------------------------------------------------


def create_pending_updates_for_step(db: Session, step_id: int) -> int:
    """Tạo PendingUpdate cho tất cả user đã hoàn thành bước này (để bắt họ làm lại Quiz mới)."""
    from src.db.models import PendingUpdate

    # Tìm các user_id đã hoàn thành bước này
    completed_user_ids = [
        row[0]
        for row in db.query(UserStepProgress.user_id)
        .join(User, User.id == UserStepProgress.user_id)
        .filter(UserStepProgress.step_id == step_id, User.is_active)
        .all()
    ]

    count = 0
    for uid in completed_user_ids:
        # Check if already exists
        exists = db.query(PendingUpdate).filter_by(user_id=uid, step_id=step_id, is_completed=False).first()
        if not exists:
            db.add(PendingUpdate(user_id=uid, step_id=step_id))
            count += 1

    db.commit()
    return count


def get_pending_updates(db: Session, user_id: str) -> list[PendingUpdate]:
    from src.db.models import PendingUpdate

    return db.query(PendingUpdate).filter_by(user_id=user_id, is_completed=False).all()


def complete_pending_update(db: Session, update_id: int, user_id: str) -> bool:
    from datetime import UTC, datetime

    from src.db.models import PendingUpdate

    update = db.query(PendingUpdate).filter_by(id=update_id, user_id=user_id, is_completed=False).first()
    if update:
        update.is_completed = True
        update.completed_at = datetime.now(UTC)
        db.commit()
        return True
    return False
