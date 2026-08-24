"""Baseline the application schema that predates Alembic."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260824_01"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    user_role = sa.Enum(
        "owner",
        "accountant",
        "technician",
        "sale",
        "manager",
        "vinfast",
        name="userrole",
    )
    user_status = sa.Enum("active", "pending", "inactive", name="userstatus")
    step_type = sa.Enum("document", "video", "quiz", "task", name="steptype")
    ticket_status = sa.Enum("open", "read", "resolved", name="ticketstatus")
    doc_status = sa.Enum("pending", "processing", "processed", "failed", name="docstatus")
    feedback_rating = sa.Enum("up", "neutral", "down", name="feedbackrating")

    op.create_table(
        "document_registry",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("s3_key", sa.String(length=500), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=100), nullable=False),
        sa.Column("status", doc_status, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "onboarding_steps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("role_target", sa.String(length=50), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("short_title", sa.String(length=60), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("step_type", step_type, nullable=False),
        sa.Column("resource_url", sa.String(length=500), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("guides", sa.JSON(), nullable=False),
        sa.Column("resources", sa.JSON(), nullable=False),
        sa.Column("quiz", sa.JSON(), nullable=False),
        sa.Column("content_version", sa.String(length=50), nullable=False),
        sa.Column("processed_md_url", sa.String(length=1000), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("agency_id", sa.String(length=100), nullable=True),
        sa.Column("status", user_status, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("onboarding_progress", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "chat_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("user_role", sa.String(length=50), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(length=50), nullable=True),
        sa.Column("citations", sa.Text(), nullable=True),
        sa.Column("rerank_scores", sa.Text(), nullable=True),
        sa.Column("rag_confidence", sa.Float(), nullable=True),
        sa.Column("rating", feedback_rating, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "invitations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("inviter_id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["inviter_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_table(
        "pending_updates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("step_id", sa.Integer(), nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["step_id"], ["onboarding_steps.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "step_id", name="uq_pending_update_user_step"),
    )
    op.create_table(
        "support_tickets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("sender_id", sa.String(length=36), nullable=False),
        sa.Column("sender_role", sa.String(length=50), nullable=False),
        sa.Column("sender_name", sa.String(length=255), nullable=False),
        sa.Column("agency_id", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("attachment_path", sa.String(length=500), nullable=True),
        sa.Column("attachment_mime", sa.String(length=100), nullable=True),
        sa.Column("status", ticket_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_module_quizzes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "module_id", name="uq_user_module_quiz"),
    )
    op.create_table(
        "user_section_progress",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("section_id", sa.String(length=80), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "section_id", name="uq_user_section"),
    )
    op.create_table(
        "user_step_progress",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("step_id", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["step_id"], ["onboarding_steps.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "step_id", name="uq_user_step"),
    )

    for name, table, columns, unique in (
        ("ix_document_registry_s3_key", "document_registry", ["s3_key"], True),
        ("ix_document_registry_status", "document_registry", ["status"], False),
        ("ix_document_registry_created_at", "document_registry", ["created_at"], False),
        ("ix_document_registry_category", "document_registry", ["category"], False),
        ("ix_onboarding_steps_role_target", "onboarding_steps", ["role_target"], False),
        ("ix_onboarding_steps_content_version", "onboarding_steps", ["content_version"], False),
        ("ix_users_email", "users", ["email"], True),
        ("ix_chat_feedback_created_at", "chat_feedback", ["created_at"], False),
        ("ix_chat_feedback_intent", "chat_feedback", ["intent"], False),
        ("ix_chat_feedback_user_id", "chat_feedback", ["user_id"], False),
        ("ix_chat_feedback_rating", "chat_feedback", ["rating"], False),
        ("ix_pending_updates_user_id", "pending_updates", ["user_id"], False),
        ("ix_support_tickets_sender_id", "support_tickets", ["sender_id"], False),
        ("ix_user_module_quizzes_user_id", "user_module_quizzes", ["user_id"], False),
        ("ix_user_section_progress_user_id", "user_section_progress", ["user_id"], False),
        ("ix_user_step_progress_user_id", "user_step_progress", ["user_id"], False),
    ):
        op.create_index(name, table, columns, unique=unique)


def downgrade() -> None:
    for table_name in (
        "user_step_progress",
        "user_section_progress",
        "user_module_quizzes",
        "support_tickets",
        "pending_updates",
        "invitations",
        "chat_feedback",
        "users",
        "onboarding_steps",
        "document_registry",
    ):
        op.drop_table(table_name)
