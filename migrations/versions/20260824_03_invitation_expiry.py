"""Add invitation expiry and acceptance timestamps."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260824_03"
down_revision: str | Sequence[str] | None = "20260824_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("invitations", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("invitations", sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True))
    op.execute(sa.text("UPDATE invitations SET expires_at = CURRENT_TIMESTAMP WHERE expires_at IS NULL"))
    op.alter_column("invitations", "expires_at", nullable=False)


def downgrade() -> None:
    op.drop_column("invitations", "accepted_at")
    op.drop_column("invitations", "expires_at")
