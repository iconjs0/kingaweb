"""Audit and rate-limit domain verification attempts."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260901_0004"
down_revision: str | Sequence[str] | None = "20260823_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    outcome = sa.Enum(
        "VERIFIED",
        "NOT_FOUND",
        "EXPIRED",
        "RATE_LIMITED",
        name="verificationoutcome",
        native_enum=False,
    )
    op.create_table(
        "verification_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("verification_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("outcome", outcome, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["verification_id"], ["domain_verifications.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_verification_attempts_verification_id",
        "verification_attempts",
        ["verification_id"],
    )
    op.create_index(
        "ix_verification_attempts_requested_by_user_id",
        "verification_attempts",
        ["requested_by_user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_verification_attempts_requested_by_user_id", table_name="verification_attempts"
    )
    op.drop_index(
        "ix_verification_attempts_verification_id", table_name="verification_attempts"
    )
    op.drop_table("verification_attempts")
