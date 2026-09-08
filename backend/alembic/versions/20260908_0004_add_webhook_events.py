"""Add durable webhook event ledger.

Revision ID: 20260908_0004
Revises: 20260908_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260908_0004"
down_revision: str | None = "20260908_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "webhook_events" in inspector.get_table_names():
        return
    op.create_table(
        "webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", sa.String(200), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("outcome", sa.String(50), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "event_id", name="uq_webhook_events_tenant_event"),
    )
    op.create_index("ix_webhook_events_tenant_created", "webhook_events", ["tenant_id", "created_at"])
    # Ensure the canonical default tenant row exists before adding the FK.
    bind.execute(
        text(
            "INSERT INTO tenants (id, name, slug, status) "
            "SELECT '00000000-0000-0000-0000-000000000001', 'Default Demo Tenant', 'default-demo-tenant', 'ACTIVE' "
            "WHERE NOT EXISTS (SELECT 1 FROM tenants WHERE id = '00000000-0000-0000-0000-000000000001')"
        )
    )
    op.create_foreign_key(
        "fk_webhook_events_tenant_id",
        "webhook_events",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "webhook_events" not in inspector.get_table_names():
        return
    op.drop_table("webhook_events")
