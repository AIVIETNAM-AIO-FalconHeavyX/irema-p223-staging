"""Add durable R2 ingestion run and document job state."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260825_04"
down_revision: str | Sequence[str] | None = "20260824_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    run_status = postgresql.ENUM("queued", "running", "completed", "failed", "dry_run", name="ingestionrunstatus")
    run_status.create(op.get_bind(), checkfirst=True)
    job_status = postgresql.ENUM("pending", "processing", "processed", "failed", name="docstatus", create_type=False)

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("status", run_status, nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("total_documents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_documents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_documents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_documents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_document", sa.String(length=500), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingestion_runs_status", "ingestion_runs", ["status"])
    op.create_index("ix_ingestion_runs_created_at", "ingestion_runs", ["created_at"])

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("status", job_status, nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["document_registry.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "document_id", name="uq_ingestion_job_run_document"),
    )
    op.create_index("ix_ingestion_jobs_run_id", "ingestion_jobs", ["run_id"])
    op.create_index("ix_ingestion_jobs_document_id", "ingestion_jobs", ["document_id"])
    op.create_index("ix_ingestion_jobs_status", "ingestion_jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_ingestion_jobs_status", table_name="ingestion_jobs")
    op.drop_index("ix_ingestion_jobs_document_id", table_name="ingestion_jobs")
    op.drop_index("ix_ingestion_jobs_run_id", table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
    op.drop_index("ix_ingestion_runs_created_at", table_name="ingestion_runs")
    op.drop_index("ix_ingestion_runs_status", table_name="ingestion_runs")
    op.drop_table("ingestion_runs")
    postgresql.ENUM(name="ingestionrunstatus").drop(op.get_bind(), checkfirst=True)
