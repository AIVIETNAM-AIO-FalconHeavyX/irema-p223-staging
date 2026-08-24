"""Auth & Onboarding API routes."""

from __future__ import annotations

import io
import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user, require_manager_or_owner, require_owner, require_vinfast
from src.auth.security import create_access_token, verify_password
from src.db import get_db
from src.db.crud import (
    complete_pending_update,
    complete_section_for_user,
    complete_step_for_user,
    count_unread_tickets,
    create_invitation,
    create_support_ticket,
    create_user,
    get_all_users_with_progress,
    get_completed_section_ids,
    get_completed_step_ids,
    get_invitation_by_token,
    get_module_statuses,
    get_pending_updates,
    get_steps_by_role,
    get_support_tickets,
    get_user_by_email,
    mark_ticket_read,
    seed_onboarding_steps,
    submit_module_quiz,
)
from src.db.models import User, UserRole
from src.models.schemas import (
    InviteAcceptRequest,
    InviteRequest,
    InviteResponse,
    LoginRequest,
    OnboardingProgressResponse,
    OnboardingStepResponse,
    PendingUpdateResponse,
    QuizResultResponse,
    QuizSubmitRequest,
    SupportTicketResponse,
    TeamMemberProgress,
    TeamProgressResponse,
    Token,
    UnreadCountResponse,
    UserCreate,
    UserResponse,
)
from src.services.email import send_invitation_email

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(body: UserCreate, db: Session = Depends(get_db)):
    """Đăng ký tài khoản Owner mới (khởi tạo đại lý)."""
    if get_user_by_email(db, body.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email đã được sử dụng.",
        )

    # Public registration cannot create privileged or staff accounts. Employee
    # roles are assigned only through the owner invitation workflow.
    if body.role != UserRole.sale.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Public registration is limited to the sale role; use an owner invitation for staff accounts.",
        )
    role = UserRole.sale

    user = create_user(
        db,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        role=role,
        agency_id=body.agency_id,
    )
    token = create_access_token({"sub": user.id, "role": user.role.value})
    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Đăng nhập và nhận JWT access token."""
    user = get_user_by_email(db, body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa.",
        )
    token = create_access_token({"sub": user.id, "role": user.role.value})
    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """Trả về thông tin tài khoản đang đăng nhập."""
    return UserResponse.model_validate(current_user)


@router.post("/invite", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
def invite(
    body: InviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Owner gửi lời mời tham gia đại lý với role được chỉ định."""
    try:
        role = UserRole(body.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Role không hợp lệ: {body.role}",
        )

    if get_user_by_email(db, body.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email đã được sử dụng.")
    inv = create_invitation(db, inviter_id=current_user.id, email=body.email, role=role)
    try:
        send_invitation_email(recipient=inv.email, token=inv.token, role=inv.role.value)
    except RuntimeError as exc:
        logger.warning("Invitation email delivery failed for %s: %s", inv.email, exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Không thể gửi email mời.") from exc
    return InviteResponse(
        id=inv.id,
        email=inv.email,
        role=inv.role.value,
        accepted=inv.accepted,
        created_at=inv.created_at,
    )


@router.post("/invite/accept", response_model=Token)
def accept_invite(body: InviteAcceptRequest, db: Session = Depends(get_db)):
    inv = get_invitation_by_token(db, body.token)
    if not inv:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lời mời không hợp lệ hoặc đã hết hạn.")
    expires_at = inv.expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if inv.accepted or expires_at is None or expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lời mời không hợp lệ hoặc đã hết hạn.")
    if get_user_by_email(db, inv.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email đã được sử dụng.")

    inviter = db.query(User).filter(User.id == inv.inviter_id).first()
    user = create_user(
        db,
        email=inv.email,
        password=body.password,
        full_name=body.full_name,
        role=inv.role,
        agency_id=inviter.agency_id if inviter else None,
    )
    inv.accepted = True
    inv.accepted_at = datetime.now(UTC)
    db.commit()
    token = create_access_token({"sub": user.id, "role": user.role.value})
    return Token(access_token=token, user=UserResponse.model_validate(user))


# ---------------------------------------------------------------------------
# Onboarding endpoints
# ---------------------------------------------------------------------------


@router.get("/onboarding/steps", response_model=list[OnboardingStepResponse])
def get_onboarding_steps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trả về các bước onboarding theo role của user hiện tại."""
    # VinFast Admin là người quản lý hệ thống, không cần lộ trình onboarding
    if current_user.role.value == "vinfast":
        return []
    seed_onboarding_steps(db)
    steps = get_steps_by_role(db, current_user.role.value)
    return [OnboardingStepResponse.model_validate(s) for s in steps]


@router.get("/onboarding/progress", response_model=OnboardingProgressResponse)
def get_onboarding_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tiến độ đã lưu của user — để UI khôi phục đúng trạng thái sau khi tải lại trang."""
    # VinFast Admin không tham gia onboarding — trả về trạng thái "hoàn thành" để UI không hiện progress bar
    if current_user.role.value == "vinfast":
        return OnboardingProgressResponse(
            progress=100,
            completed_step_ids=[],
            completed_section_ids=[],
            total_steps=0,
            modules=[],
        )
    seed_onboarding_steps(db)
    steps = get_steps_by_role(db, current_user.role.value)
    step_ids = {s.id for s in steps}
    completed = [sid for sid in get_completed_step_ids(db, current_user.id) if sid in step_ids]
    return OnboardingProgressResponse(
        progress=current_user.onboarding_progress,
        completed_step_ids=completed,
        completed_section_ids=get_completed_section_ids(db, current_user.id),
        total_steps=len(steps),
        modules=get_module_statuses(db, current_user),
    )


@router.post("/onboarding/steps/{step_id}/complete", response_model=OnboardingProgressResponse)
def complete_step(
    step_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Đánh dấu hoàn thành bước onboarding và trả về tiến độ mới."""
    new_progress = complete_step_for_user(db, current_user.id, step_id)
    steps = get_steps_by_role(db, current_user.role.value)
    step_ids = {s.id for s in steps}
    completed = [sid for sid in get_completed_step_ids(db, current_user.id) if sid in step_ids]
    return OnboardingProgressResponse(
        progress=new_progress,
        completed_step_ids=completed,
        completed_section_ids=get_completed_section_ids(db, current_user.id),
        total_steps=len(steps),
        modules=get_module_statuses(db, current_user),
    )


@router.post("/onboarding/quizzes/submit", response_model=QuizResultResponse)
def submit_quiz(
    body: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lưu kết quả quiz module và làm căn cứ mở module kế tiếp."""
    seed_onboarding_steps(db)
    result = submit_module_quiz(db, current_user.id, body.module_id, body.score)
    if result is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Module chưa được mở.")
    return QuizResultResponse(
        module_id=result.module_id,
        score=result.score,
        passed=result.passed,
        attempts=result.attempts,
        modules=get_module_statuses(db, current_user),
    )


@router.post("/onboarding/sections/{section_id}/complete", response_model=OnboardingProgressResponse)
def complete_section(
    section_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Đánh dấu một section/resource đã học."""
    seed_onboarding_steps(db)
    complete_section_for_user(db, current_user.id, section_id)
    steps = get_steps_by_role(db, current_user.role.value)
    step_ids = {s.id for s in steps}
    return OnboardingProgressResponse(
        progress=current_user.onboarding_progress,
        completed_step_ids=[sid for sid in get_completed_step_ids(db, current_user.id) if sid in step_ids],
        completed_section_ids=get_completed_section_ids(db, current_user.id),
        total_steps=len(steps),
        modules=get_module_statuses(db, current_user),
    )


# ---------------------------------------------------------------------------
# Support Ticket endpoints
# ---------------------------------------------------------------------------


@router.post("/support/tickets", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    agency_id: str = Form(...),
    description: str = Form(...),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Nhân viên gửi yêu cầu hỗ trợ tới Manager."""
    attachment_path: str | None = None
    attachment_mime: str | None = None

    # Upload file lên MinIO nếu có
    if file and file.filename:
        try:
            import boto3

            from src.config import get_settings

            settings = get_settings()
            s3 = boto3.client(
                "s3",
                endpoint_url=settings.aws_s3_endpoint_url,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
            )
            file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
            object_key = f"support-tickets/{uuid.uuid4().hex}.{file_ext}"
            content = await file.read()
            s3.upload_fileobj(
                io.BytesIO(content),
                settings.s3_bucket_name,
                object_key,
                ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
            )
            attachment_path = object_key
            attachment_mime = file.content_type
        except Exception as e:
            logger.warning(f"File upload to MinIO failed (non-fatal): {e}")
            # Tiếp tục tạo ticket không có file

    ticket = create_support_ticket(
        db,
        sender_id=current_user.id,
        sender_role=current_user.role.value,
        sender_name=current_user.full_name,
        agency_id=agency_id,
        description=description,
        attachment_path=attachment_path,
        attachment_mime=attachment_mime,
    )
    return SupportTicketResponse.model_validate(ticket)


@router.get("/support/tickets", response_model=list[SupportTicketResponse])
def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vinfast),
):
    """VinFast xem tất cả yêu cầu hỗ trợ."""
    tickets = get_support_tickets(db)
    return [SupportTicketResponse.model_validate(t) for t in tickets]


@router.get("/support/tickets/unread-count", response_model=UnreadCountResponse)
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vinfast),
):
    """Đếm số ticket chưa đọc (dùng cho badge)."""
    count = count_unread_tickets(db)
    return UnreadCountResponse(unread_count=count)


@router.get("/support/tickets/files/{object_key:path}")
def get_support_ticket_file(
    object_key: str,
    current_user: User = Depends(require_vinfast),
):
    """Tải file đính kèm ticket từ MinIO."""
    try:
        import boto3
        from botocore.config import Config

        from src.config import get_settings

        settings = get_settings()
        s3 = boto3.client(
            "s3",
            endpoint_url=settings.aws_s3_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
            config=Config(connect_timeout=3, read_timeout=5, retries={"max_attempts": 1}),
        )
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket_name, "Key": object_key},
            ExpiresIn=3600,
        )
        return {"url": url}
    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không thể lấy file đính kèm.")


@router.patch("/support/tickets/{ticket_id}/read", response_model=SupportTicketResponse)
def read_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vinfast),
):
    """Đánh dấu ticket đã đọc."""
    ticket = mark_ticket_read(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket không tồn tại.")
    return SupportTicketResponse.model_validate(ticket)


# ---------------------------------------------------------------------------
# Manager: Team Progress
# ---------------------------------------------------------------------------


@router.get("/manager/team-progress", response_model=TeamProgressResponse)
def team_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_or_owner),
):
    """Manager/Owner xem tiến độ onboarding của tất cả nhân viên."""
    users_data = get_all_users_with_progress(db)
    total = len(users_data)
    in_progress_count = sum(1 for u in users_data if u["status"] == "in_progress")
    completed_count = sum(1 for u in users_data if u["status"] == "completed")
    not_started_count = sum(1 for u in users_data if u["status"] == "not_started")

    return TeamProgressResponse(
        total=total,
        in_progress=in_progress_count,
        completed=completed_count,
        not_started=not_started_count,
        users=[TeamMemberProgress(**u) for u in users_data],
    )


# ---------------------------------------------------------------------------
# Pending Update endpoints (For forces quizzes)
# ---------------------------------------------------------------------------


@router.get("/pending-updates", response_model=list[PendingUpdateResponse])
def fetch_pending_updates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy danh sách các bài kiểm tra bổ sung mà nhân viên cần phải hoàn thành."""
    updates = get_pending_updates(db, current_user.id)
    return [PendingUpdateResponse.model_validate(u) for u in updates]


@router.post("/pending-updates/{update_id}/complete")
def finish_pending_update(
    update_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Đánh dấu hoàn thành một bài kiểm tra bổ sung."""
    success = complete_pending_update(db, update_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài kiểm tra này hoặc đã hoàn thành.")
    return {"success": True}
