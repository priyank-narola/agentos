"""Add tenant-scoped product role grants.

Revision ID: 20260915_0007
Revises: 20260914_0006
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision: str = "20260915_0007"
down_revision: str | None = "20260914_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The repository's bootstrap revision renders current metadata for offline
    # SQL. The explicit operation below is for online upgrades of legacy DBs.
    if context.is_offline_mode():
        return
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    inspector = inspect(bind)
    if "principal_roles" in inspector.get_table_names():
        return
    role_enum = postgresql.ENUM("ADMIN", "POLICY_AUTHOR", "APPROVER", "OPERATOR", "AUDITOR", name="tenantrole")
    role_enum.create(bind, checkfirst=True)
    op.create_table(
        "principal_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("principal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("granted_by_principal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["principal_id"], ["principals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by_principal_id"], ["principals.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("tenant_id", "principal_id", "role", name="uq_principal_roles_tenant_principal_role"),
    )
    op.create_index("ix_principal_roles_tenant_principal", "principal_roles", ["tenant_id", "principal_id"])


def downgrade() -> None:
    if context.is_offline_mode():
        return
    bind = op.get_bind()
    inspector = inspect(bind)
    if "principal_roles" not in inspector.get_table_names():
        return
    op.drop_index("ix_principal_roles_tenant_principal", table_name="principal_roles")
    op.drop_table("principal_roles")
    postgresql.ENUM(name="tenantrole").drop(bind, checkfirst=True)
