"""Add FK constraint on audit_events.actor_id.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-09
"""

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Set nullable first (actor_id was NOT NULL without FK).
    op.alter_column("audit_events", "actor_id", existing_type=sa.Uuid(), nullable=True)
    # Delete orphaned rows referencing non-existent principals.
    op.execute(
        "DELETE FROM audit_events WHERE actor_id IS NOT NULL "
        "AND actor_id NOT IN (SELECT id FROM principals)"
    )
    # Add FK constraint (SET NULL on delete so audit trail survives principal removal).
    op.create_foreign_key(
        "fk_audit_events_actor_id_principal",
        "audit_events",
        "principals",
        ["actor_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_audit_events_actor_id_principal", "audit_events", type_="foreignkey")
    op.alter_column("audit_events", "actor_id", existing_type=sa.Uuid(), nullable=False)
