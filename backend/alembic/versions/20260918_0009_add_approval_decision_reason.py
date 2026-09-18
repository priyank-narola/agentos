"""Add a durable approver decision reason.

Revision ID: 20260918_0009
Revises: 20260916_0008
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy import inspect


revision: str = "20260918_0009"
down_revision: str | None = "20260916_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if context.is_offline_mode():
        return
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("approval_requests")}
    if "decision_reason" not in columns:
        op.add_column("approval_requests", sa.Column("decision_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    if context.is_offline_mode():
        return
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("approval_requests")}
    if "decision_reason" in columns:
        op.drop_column("approval_requests", "decision_reason")
