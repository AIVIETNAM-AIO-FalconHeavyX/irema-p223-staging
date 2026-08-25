"""SQLAlchemy ORM models for VinFast Dealer Onboarding System."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class UserRole(StrEnum):
    owner = "owner"
    accountant = "accountant"
    technician = "technician"
    sale = "sale"
    manager = "manager"
    vinfast = "vinfast"


# Vai trò đã bị loại bỏ khỏi hệ thống — dữ liệu cũ mang các giá trị này sẽ được
# dọn khi khởi động (xem `_remove_retired_roles()` trong src/db/__init__.py).
RETIRED_ROLES = ("it",)


class UserStatus(StrEnum):
    active = "active"
    pending = "pending"
    inactive = "inactive"


class ChatMessageRole(StrEnum):
    user = "user"
    assistant = "assistant"


class StepType(StrEnum):
    document = "document"
    video = "video"
    quiz = "quiz"
    task = "task"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.sale)
    agency_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.active)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    # Onboarding progress (0–100)
    onboarding_progress: Mapped[int] = mapped_column(Integer, default=0)

    invitations: Mapped[list[Invitation]] = relationship(
        "Invitation", back_populates="inviter", foreign_keys="Invitation.inviter_id"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role}]>"


class ChatConversation(Base):
    """A user-owned conversation retained for bounded contextual chat."""

    __tablename__ = "chat_conversations"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC) + timedelta(days=90),
        nullable=False,
        index=True,
    )

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
    messages: Mapped[list[ChatMessage]] = relationship(
        "ChatMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    """One visible user or assistant turn belonging to a conversation."""

    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[ChatMessageRole] = mapped_column(Enum(ChatMessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)

    conversation: Mapped[ChatConversation] = relationship("ChatConversation", back_populates="messages")


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inviter_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    inviter: Mapped[User] = relationship("User", back_populates="invitations", foreign_keys=[inviter_id])


class OnboardingStep(Base):
    __tablename__ = "onboarding_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_target: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "all" or specific role
    order: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # Nhãn ngắn hiển thị ở sidebar; `title` đầy đủ dùng cho tiêu đề trang.
    short_title: Mapped[str] = mapped_column(String(60), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    step_type: Mapped[StepType] = mapped_column(Enum(StepType), default=StepType.document)
    resource_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=15)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)

    # Nội dung bài học — nguồn dữ liệu duy nhất cho UI (thay cho mockdata ở frontend)
    goal: Mapped[str] = mapped_column(Text, default="")
    # [{"letter": "A", "title": ..., "desc": ...}]
    guides: Mapped[list] = mapped_column(JSON, default=list)
    # [{"name": ..., "type": "video|doc", "path": <đường dẫn tương đối trong Data/Data_separate>, "meta": ...}]
    resources: Mapped[list] = mapped_column(JSON, default=list)
    # [{"id": 1, "question": ..., "options": [...], "correctIndex": 0, "explanation": ...}]
    quiz: Mapped[list] = mapped_column(JSON, default=list)
    # Dấu vân tay nội dung của catalog — đổi giá trị này là seed sẽ nạp lại
    content_version: Mapped[str] = mapped_column(String(50), default="", index=True)
    # URL của file .md đã xử lý (PII removed) trên MinIO — dùng cho Track 3 (RAG Chatbot)
    processed_md_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class UserStepProgress(Base):
    """Bản ghi 1 bước onboarding đã hoàn thành của 1 user (idempotent)."""

    __tablename__ = "user_step_progress"
    __table_args__ = (UniqueConstraint("user_id", "step_id", name="uq_user_step"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    step_id: Mapped[int] = mapped_column(Integer, ForeignKey("onboarding_steps.id"), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class UserModuleQuiz(Base):
    """Kết quả quiz module được lưu phía server."""

    __tablename__ = "user_module_quizzes"
    __table_args__ = (UniqueConstraint("user_id", "module_id", name="uq_user_module_quiz"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    module_id: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class UserSectionProgress(Base):
    """Tiến độ theo section; mỗi resource trong module là một section ổn định."""

    __tablename__ = "user_section_progress"
    __table_args__ = (UniqueConstraint("user_id", "section_id", name="uq_user_section"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    section_id: Mapped[str] = mapped_column(String(80), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class PendingUpdate(Base):
    """Bản ghi các bài Quiz bổ sung dành cho nhân viên đã tốt nghiệp khi có tài liệu mới."""

    __tablename__ = "pending_updates"
    __table_args__ = (UniqueConstraint("user_id", "step_id", name="uq_pending_update_user_step"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    step_id: Mapped[int] = mapped_column(Integer, ForeignKey("onboarding_steps.id"), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
    step: Mapped[OnboardingStep] = relationship("OnboardingStep", foreign_keys=[step_id])


class TicketStatus(StrEnum):
    open = "open"
    read = "read"
    resolved = "resolved"


class SupportTicket(Base):
    """Yêu cầu hỗ trợ do nhân viên gửi tới Manager/Owner."""

    __tablename__ = "support_tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    sender_role: Mapped[str] = mapped_column(String(50), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    agency_id: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Đường dẫn file trong MinIO bucket (relative path), None nếu không có file
    attachment_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # MIME type của file đính kèm
    attachment_mime: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.open)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    sender: Mapped[User] = relationship("User", foreign_keys=[sender_id])


# ---------------------------------------------------------------------------
# Document Registry (S3/MinIO Document Tracking)
# ---------------------------------------------------------------------------


class DocStatus(StrEnum):
    pending = "pending"
    processing = "processing"
    processed = "processed"
    failed = "failed"


class IngestionRunStatus(StrEnum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    dry_run = "dry_run"


class DocumentRegistry(Base):
    """Theo dõi file tài liệu trên MinIO và trạng thái xử lý pipeline."""

    __tablename__ = "document_registry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    s3_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content_hash: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[DocStatus] = mapped_column(
        Enum(DocStatus),
        nullable=False,
        default=DocStatus.pending,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )


class IngestionRun(Base):
    """Durable reconciliation/indexing run started by a VinFast administrator."""

    __tablename__ = "ingestion_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[IngestionRunStatus] = mapped_column(
        Enum(IngestionRunStatus), nullable=False, default=IngestionRunStatus.queued, index=True
    )
    dry_run: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    total_documents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_documents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_documents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_documents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_document: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IngestionJobRecord(Base):
    """One durable document job belonging to an ingestion run."""

    __tablename__ = "ingestion_jobs"
    __table_args__ = (UniqueConstraint("run_id", "document_id", name="uq_ingestion_job_run_document"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("document_registry.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[DocStatus] = mapped_column(Enum(DocStatus), nullable=False, default=DocStatus.pending, index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DocumentChunk(Base):
    """Versioned RAG chunk and embedding with deterministic rebuild metadata."""

    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "chunk_version",
            "content_hash",
            name="uq_document_chunks_version_hash",
        ),
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(VECTOR(1024), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    access_scope: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    section: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    chunk_metadata: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)
    embedding_version: Mapped[str] = mapped_column(String(100), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(100), nullable=False)
    chunk_version: Mapped[str] = mapped_column(String(100), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# Chat Feedback (Human-in-the-Loop RAG Quality Signal)
# ---------------------------------------------------------------------------


class FeedbackRating(StrEnum):
    up = "up"  # ↑ Chính xác
    neutral = "neutral"  # − Phần đúng phần sai / chưa rõ
    down = "down"  # ↓ Sai hoặc không tìm thấy


class ChatFeedback(Base):
    """Đánh giá chất lượng câu trả lời AI từ user (↑ / − / ↓).

    Dùng để phân tích:
    - Câu hỏi nào hay bị ↓ → biết điểm yếu của RAG.
    - rerank_scores thấp + rating ↓ → cần điều chỉnh threshold.
    - Intent nào LLM trả lời không tốt → cải thiện prompt.
    """

    __tablename__ = "chat_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )

    # User context
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    user_role: Mapped[str] = mapped_column(String(50), nullable=False)

    # Query & Response
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # RAG metadata (JSON serialized)
    citations: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON ["doc1", "doc2"]
    rerank_scores: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON [0.84, 0.71]
    rag_confidence: Mapped[float | None] = mapped_column(nullable=True)

    # Feedback signal
    rating: Mapped[FeedbackRating] = mapped_column(Enum(FeedbackRating), nullable=False, index=True)

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
