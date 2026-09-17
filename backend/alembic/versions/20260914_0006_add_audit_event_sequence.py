"""Add durable causal ordering to action audit events.

Revision ID: 20260914_0006
Revises: 0005
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy import inspect, text


revision: str = "20260914_0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Offline SQL starts with revision 0001's current metadata snapshot, which
    # already contains event_sequence and its constraints. Keep the real,
    # inspector-backed backfill path exclusively for online migrations.
    if context.is_offline_mode():
        return
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("audit_events")}
    if "event_sequence" not in columns:
        op.add_column("audit_events", sa.Column("event_sequence", sa.Integer(), nullable=True))
        # Existing rows retain their history and receive deterministic sequence
        # values per action. System events without an action remain unsequenced.
        bind.execute(text("""
            WITH ranked AS (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY action_request_id
                    ORDER BY created_at, id
                ) AS sequence
                FROM audit_events
                WHERE action_request_id IS NOT NULL
            )
            UPDATE audit_events
            SET event_sequence = ranked.sequence
            FROM ranked
            WHERE audit_events.id = ranked.id
        """))
    inspector = inspect(bind)
    unique_names = {item.get("name") for item in inspector.get_unique_constraints("audit_events")}
    if "uq_audit_events_action_request_sequence" not in unique_names:
        op.create_unique_constraint(
            "uq_audit_events_action_request_sequence",
            "audit_events",
            ["action_request_id", "event_sequence"],
        )
    index_names = {item.get("name") for item in inspector.get_indexes("audit_events")}
    if "ix_audit_events_action_request_sequence" not in index_names:
        op.create_index(
            "ix_audit_events_action_request_sequence",
            "audit_events",
            ["action_request_id", "event_sequence"],
        )


def downgrade() -> None:
    if context.is_offline_mode():
        return
    op.drop_index("ix_audit_events_action_request_sequence", table_name="audit_events")
    op.drop_constraint("uq_audit_events_action_request_sequence", "audit_events", type_="unique")
    op.drop_column("audit_events", "event_sequence")
