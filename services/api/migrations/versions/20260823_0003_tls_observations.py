"""Persist pinned target and TLS observations."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260823_0003"
down_revision: str | Sequence[str] | None = "20260823_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("scan_runs", sa.Column("target_ip", sa.String(45), nullable=True))
    op.add_column("scan_runs", sa.Column("http_status", sa.Integer(), nullable=True))
    op.add_column("scan_runs", sa.Column("tls_version", sa.String(20), nullable=True))
    op.add_column(
        "scan_runs", sa.Column("certificate_expires_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("scan_runs", "certificate_expires_at")
    op.drop_column("scan_runs", "tls_version")
    op.drop_column("scan_runs", "http_status")
    op.drop_column("scan_runs", "target_ip")
