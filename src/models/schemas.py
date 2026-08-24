from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Chat Schemas (existing)
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000, description="Tin nhắn từ user")
    conversation_id: str = Field(..., min_length=8, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")


class RetrievedDocInfo(BaseModel):
    """Metadata của một chunk đã rerank — dùng để hiển thị source badges trong frontend."""

    doc_name: str = Field(..., description="Tên tài liệu (clean, không extension)")
    section: str = Field(default="", description="Mục/section trong tài liệu")
    rerank_score: float = Field(default=0.0, description="Cross-Encoder score (logit, có thể âm)")
    rrf_score: float = Field(default=0.0, description="Reciprocal Rank Fusion score")
    content_preview: str = Field(default="", description="150 ký tự đầu tiên của nội dung chunk")
    # Video support fields
    content_type: str = Field(default="document", description="'video' | 'document'")
    source_path: str = Field(default="", description="Đường dẫn file gốc (dùng với /api/v1/files/)")
    timestamp_seconds: int | None = Field(
        default=None, description="Giây trong video để auto-seek (None nếu không phải video)"
    )


class ChatResponse(BaseModel):
    conversation_id: str
    response: str = Field(..., description="Phản hồi từ agent")
    analysis: str = Field(default="", description="Phân tích nội bộ của Controller")
    intent: Optional[str] = Field(default=None, description="Intent được phân loại")
    citations: list[str] = Field(default_factory=list, description="Danh sách tài liệu trích dẫn nguồn")
    retrieved_docs: list[RetrievedDocInfo] = Field(
        default_factory=list,
        description="Danh sách chunk đã rerank kèm score và metadata — dùng để debug RAG",
    )
    needs_escalation: bool = Field(default=False, description="Cờ cho biết câu hỏi đã được chuyển tiếp IT/Quản lý")
    ticket_payload: Optional[dict[str, Any]] = Field(
        default=None, description="Payload Ticket hỗ trợ nếu được khởi tạo"
    )


# ---------------------------------------------------------------------------
# Auth Schemas
# ---------------------------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Mật khẩu tối thiểu 8 ký tự")
    full_name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(default="sale", description="owner | accountant | technician | sale | manager")
    agency_id: Optional[str] = Field(default=None, description="Mã đại lý VF")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    agency_id: Optional[str]
    status: str
    onboarding_progress: int
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = Field(..., description="Role được cấp: accountant | technician | sale | manager")


class InviteResponse(BaseModel):
    id: str
    email: str
    role: str
    token: str | None = None
    accepted: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteAcceptRequest(BaseModel):
    token: str = Field(..., min_length=20, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)


# ---------------------------------------------------------------------------
# Onboarding Schemas
# ---------------------------------------------------------------------------
class GuideItem(BaseModel):
    letter: str
    title: str
    desc: str


class OnboardingResource(BaseModel):
    name: str = Field(..., description="Tên hiển thị của tài liệu")
    type: str = Field(..., description="video | doc")
    path: str = Field(..., description="Đường dẫn tương đối trong Data/Data_separate")
    meta: str = Field(default="", description="Loại file & dung lượng, ví dụ 'PDF · 2.1 MB'")
    section_id: str | None = None


class QuizQuestionSchema(BaseModel):
    id: int
    question: str
    options: list[str]
    # camelCase cố ý: đây là khoá JSON mà React đọc trực tiếp (QuizModal.tsx).
    correctIndex: int  # noqa: N815
    explanation: str


class OnboardingStepResponse(BaseModel):
    id: int
    role_target: str
    order: int
    title: str
    short_title: str = ""
    description: str = ""
    step_type: str
    resource_url: Optional[str]
    duration_minutes: int
    is_required: bool
    goal: str = ""
    guides: list[GuideItem] = Field(default_factory=list)
    resources: list[OnboardingResource] = Field(default_factory=list)
    quiz: list[QuizQuestionSchema] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class OnboardingProgressResponse(BaseModel):
    progress: int = Field(..., ge=0, le=100, description="Phần trăm hoàn thành lộ trình")
    completed_step_ids: list[int] = Field(default_factory=list)
    completed_section_ids: list[str] = Field(default_factory=list)
    total_steps: int = 0
    modules: list["ModuleStatusResponse"] = Field(default_factory=list)


class ModuleStatusResponse(BaseModel):
    module_id: int
    unlocked: bool
    completed: bool
    quiz_score: int | None = None
    step_ids: list[int] = Field(default_factory=list)


class QuizSubmitRequest(BaseModel):
    module_id: int = Field(..., ge=1, le=3)
    score: int = Field(..., ge=0, le=100)


class QuizResultResponse(BaseModel):
    module_id: int
    score: int
    passed: bool
    attempts: int
    modules: list[ModuleStatusResponse] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Support Ticket Schemas
# ---------------------------------------------------------------------------
class SupportTicketCreate(BaseModel):
    agency_id: str = Field(..., min_length=1, max_length=100, description="Mã đại lý")
    description: str = Field(..., min_length=10, max_length=2000, description="Mô tả vấn đề")


class SupportTicketResponse(BaseModel):
    id: str
    sender_id: str
    sender_role: str
    sender_name: str
    agency_id: str
    description: str
    attachment_path: Optional[str]
    attachment_mime: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    unread_count: int


# ---------------------------------------------------------------------------
# Manager: Team Progress Schemas
# ---------------------------------------------------------------------------
class TeamMemberProgress(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    agency_id: str
    onboarding_progress: int
    completed_steps: int
    total_steps: int
    status: str  # not_started | in_progress | completed


class TeamProgressResponse(BaseModel):
    total: int
    in_progress: int
    completed: int
    not_started: int
    users: list[TeamMemberProgress]


# ---------------------------------------------------------------------------
# PendingUpdate Schemas
# ---------------------------------------------------------------------------


class PendingUpdateResponse(BaseModel):
    id: int
    step_id: int
    is_completed: bool
    created_at: datetime
    step: OnboardingStepResponse

    model_config = {"from_attributes": True}
