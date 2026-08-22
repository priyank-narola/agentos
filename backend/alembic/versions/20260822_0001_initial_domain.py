"""Create the initial AgentOS domain schema.

Revision ID: 20260822_0001
Revises:
"""
from collections.abc import Sequence

from alembic import op

from app.db.base import Base
from app.db import models  # noqa: F401 - registers all models with metadata

revision: str = "20260822_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all Phase 2 tables from the declarative schema."""
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    """Remove all Phase 2 tables and their PostgreSQL enum types."""
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, checkfirst=True)
