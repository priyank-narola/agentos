"""Add tenant-scoped Workforce planning foundation.

Revision ID: 20260919_0010
Revises: 20260918_0009
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy import inspect


revision: str = "20260919_0010"
down_revision: str | None = "20260918_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_names() -> set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    if context.is_offline_mode():
        return
    tables = _table_names()
    if "workforce_goals" not in tables:
        op.create_table(
            "workforce_goals",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("title", sa.String(length=240), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.Enum("PLANNED", "ACTIVE", "AT_RISK", "ACHIEVED", "CANCELLED", name="workforcegoalstatus"), nullable=False),
            sa.Column("parent_goal_id", sa.Uuid(), sa.ForeignKey("workforce_goals.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("owner_agent_id", sa.Uuid(), sa.ForeignKey("agents.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_workforce_goals_tenant_status", "workforce_goals", ["tenant_id", "status"])
        op.create_index("ix_workforce_goals_tenant_parent", "workforce_goals", ["tenant_id", "parent_goal_id"])
    if "workforce_projects" not in tables:
        op.create_table(
            "workforce_projects",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("goal_id", sa.Uuid(), sa.ForeignKey("workforce_goals.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("owner_agent_id", sa.Uuid(), sa.ForeignKey("agents.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("tenant_id", "name", name="uq_workforce_projects_tenant_name"),
        )
        op.create_index("ix_workforce_projects_tenant_status", "workforce_projects", ["tenant_id", "status"])
    if "workforce_work_items" not in tables:
        op.create_table(
            "workforce_work_items",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("project_id", sa.Uuid(), sa.ForeignKey("workforce_projects.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("goal_id", sa.Uuid(), sa.ForeignKey("workforce_goals.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("title", sa.String(length=280), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.Enum("BACKLOG", "READY", "IN_PROGRESS", "IN_REVIEW", "BLOCKED", "DONE", "CANCELLED", name="workforceworkitemstatus"), nullable=False),
            sa.Column("priority", sa.String(length=32), nullable=False),
            sa.Column("assignee_agent_id", sa.Uuid(), sa.ForeignKey("agents.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("action_request_id", sa.Uuid(), sa.ForeignKey("action_requests.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_workforce_work_items_tenant_status", "workforce_work_items", ["tenant_id", "status"])
        op.create_index("ix_workforce_work_items_tenant_project", "workforce_work_items", ["tenant_id", "project_id"])
        op.create_index("ix_workforce_work_items_tenant_assignee", "workforce_work_items", ["tenant_id", "assignee_agent_id"])
        op.create_index("ix_workforce_work_items_action_request", "workforce_work_items", ["action_request_id"])


def downgrade() -> None:
    if context.is_offline_mode():
        return
    tables = _table_names()
    for table in ("workforce_work_items", "workforce_projects", "workforce_goals"):
        if table in tables:
            op.drop_table(table)
