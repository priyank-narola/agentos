"""Add CANCELLED to approval status enum.

Revision ID: 20260824_0002
Revises: 20260822_0001
"""
from collections.abc import Sequence

from alembic import op

revision: str = "20260824_0002"
down_revision: str | None = "20260822_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE approvalstatus ADD VALUE IF NOT EXISTS 'CANCELLED'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in-place. Existing rows
    # must be migrated before a future destructive enum replacement.
    pass
