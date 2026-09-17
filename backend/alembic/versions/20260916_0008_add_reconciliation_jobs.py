"""Add durable status-readback jobs for uncertain provider outcomes.

Revision ID: 20260916_0008
Revises: 20260915_0007
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy import inspect


revision: str = "20260916_0008"
down_revision: str | None = "20260915_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if context.is_offline_mode():
        return
    bind = op.get_bind()
    if "reconciliation_jobs" in inspect(bind).get_table_names():
        return
    op.create_table(
        "reconciliation_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("action_request_id", sa.Uuid(), sa.ForeignKey("action_requests.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_check_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("action_request_id", name="uq_reconciliation_jobs_action_request"),
    )
    op.create_index("ix_reconciliation_jobs_tenant_status_due", "reconciliation_jobs", ["tenant_id", "status", "next_check_at"])


def downgrade() -> None:
    if context.is_offline_mode():
        return
    bind = op.get_bind()
    if "reconciliation_jobs" not in inspect(bind).get_table_names():
        return
    op.drop_index("ix_reconciliation_jobs_tenant_status_due", table_name="reconciliation_jobs")
    op.drop_table("reconciliation_jobs")
