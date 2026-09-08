"""Add tenant integrity and execution ledger alignment.

Revision ID: 20260908_0003
Revises: 20260824_0002

WHY
---
Revision 0001 snapshotted the schema with Base.metadata.create_all and the
application schema subsequently grew (Tenant model + tenant_id ownership on
domain tables, FinancialExecution ledger, additional enums). This migration
aligns any database state with the application models:

- guarantees the ``tenants`` table and its default tenant row exist,
- guarantees tenant ownership columns / FKs exist on tenant-owned tables,
- creates the ``financial_executions`` ledger table when absent,
- adds ``decisions.tenant_id`` with a deterministic backfill from the owning
  ``action_requests.tenant_id`` (never from client input).

It is additive and guarded (idempotent), so it is safe on:
- a fresh database (post-0001/0002 current schema),
- the existing development database (which already carries the current schema),
- an older pre-tenant database that still needs the tenant model applied.

Existing rows are preserved and backfilled to the canonical default tenant
only where a tenant column is newly introduced.

Downgrade removes only the ``decisions.tenant_id`` ownership column/FK that this
revision introduces on an already-current database.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Connection

from alembic import op

revision: str = "20260908_0003"
down_revision: str | None = "20260824_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"

# Tables that are tenant-owned with a NOT NULL tenant_id in the current models.
TENANT_OWNED_NOT_NULL = [
    "principals",
    "agents",
    "delegations",
    "resources",
    "policies",
    "action_requests",
    "approval_requests",
    "audit_events",
]

# Tables that are tenant-ownable with a nullable tenant_id in the current models.
TENANT_OWNED_NULLABLE = [
    "tools",
    "actions",
]

UUID_TYPE = postgresql.UUID(as_uuid=True)


def _table_exists(inspector, table: str) -> bool:
    return table in inspector.get_table_names()


def _column_exists(inspector, table: str, column: str) -> bool:
    if not _table_exists(inspector, table):
        return False
    return any(col["name"] == column for col in inspector.get_columns(table))


def _ensure_enum_type(bind: Connection, enum_name: str, values: list[str]) -> None:
    """Create a PostgreSQL enum type if it does not already exist."""
    existing = bind.execute(
        text("SELECT 1 FROM pg_type WHERE typname = :name"), {"name": enum_name}
    ).scalar()
    if existing is None:
        value_list = ", ".join(f"'{value}'" for value in values)
        bind.execute(text(f"CREATE TYPE {enum_name} AS ENUM ({value_list})"))


def _ensure_tenants_table(bind: Connection, inspector) -> None:
    if not _table_exists(inspector, "tenants"):
        op.create_table(
            "tenants",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("slug", sa.String(100), nullable=False, unique=True),
            sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )


def _ensure_financial_executions_table(bind: Connection, inspector) -> None:
    if not _table_exists(inspector, "financial_executions"):
        _ensure_enum_type(
            bind,
            "executionstate",
            [
                "PENDING",
                "SUBMITTED",
                "PROCESSING",
                "SUCCEEDED",
                "FAILED",
                "CANCELLED",
                "UNKNOWN",
                "RECONCILIATION_REQUIRED",
            ],
        )
        op.create_table(
            "financial_executions",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("tenant_id", UUID_TYPE, nullable=False),
            sa.Column("action_request_id", UUID_TYPE, nullable=False),
            sa.Column("provider_name", sa.String(100), nullable=False),
            sa.Column("provider_transaction_id", sa.String(200), nullable=False),
            sa.Column("provider_request_id", sa.String(200), nullable=False),
            sa.Column(
                "status",
                postgresql.ENUM(
                    name="executionstate",
                    create_type=False,
                ),
                nullable=False,
                server_default="PENDING",
            ),
            sa.Column("payload_digest", sa.String(100), nullable=False),
            sa.Column("error_code", sa.String(100), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_financial_executions_tenant_status", "financial_executions", ["tenant_id", "status"])
        op.create_index(
            "ix_financial_executions_provider_tx",
            "financial_executions",
            ["provider_name", "provider_transaction_id"],
        )


def _ensure_tenant_column(bind: Connection, inspector, table: str, *, nullable: bool) -> None:
    if not _column_exists(inspector, table, "tenant_id"):
        op.add_column(table, sa.Column("tenant_id", UUID_TYPE, nullable=True))
        bind.execute(
            text(f"UPDATE {table} SET tenant_id = :tenant_id WHERE tenant_id IS NULL"),
            {"tenant_id": DEFAULT_TENANT_ID},
        )
    if nullable is False:
        op.alter_column(table, "tenant_id", nullable=False)


def _ensure_tenant_fk(bind: Connection, inspector, table: str) -> None:
    if not _table_exists(inspector, table):
        return
    fks = inspector.get_foreign_keys(table)
    if any(fk.get("referred_table") == "tenants" and "tenant_id" in fk.get("constrained_columns", []) for fk in fks):
        return
    op.create_foreign_key(
        f"fk_{table}_tenant_id",
        table,
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    _ensure_tenants_table(bind, inspector)

    # Canonical default tenant referenced by model-level tenant_id defaults.
    bind.execute(
        text(
            "INSERT INTO tenants (id, name, slug, status) "
            "SELECT :tenant_id, 'Default Demo Tenant', 'default-demo-tenant', 'ACTIVE' "
            "WHERE NOT EXISTS (SELECT 1 FROM tenants WHERE id = :tenant_id)"
        ),
        {"tenant_id": DEFAULT_TENANT_ID},
    )

    # Refresh inspector state after creating tables/columns.
    inspector = inspect(bind)

    for table in TENANT_OWNED_NOT_NULL:
        _ensure_tenant_column(bind, inspector, table, nullable=False)
        _ensure_tenant_fk(bind, inspector, table)

    for table in TENANT_OWNED_NULLABLE:
        _ensure_tenant_column(bind, inspector, table, nullable=True)
        _ensure_tenant_fk(bind, inspector, table)

    _ensure_financial_executions_table(bind, inspector)

    # Refresh inspector state after creating the financial executions table.
    inspector = inspect(bind)
    _ensure_tenant_fk(bind, inspector, "financial_executions")
    if _table_exists(inspector, "financial_executions") and _table_exists(inspector, "action_requests"):
        fks = inspector.get_foreign_keys("financial_executions")
        if not any(fk.get("referred_table") == "action_requests" for fk in fks):
            op.create_foreign_key(
                "fk_financial_executions_action_request_id",
                "financial_executions",
                "action_requests",
                ["action_request_id"],
                ["id"],
                ondelete="RESTRICT",
            )

    # decisions.tenant_id: backfill from the owning action request, never client input.
    if not _column_exists(inspector, "decisions", "tenant_id"):
        op.add_column("decisions", sa.Column("tenant_id", UUID_TYPE, nullable=True))
        bind.execute(
            text(
                "UPDATE decisions d SET tenant_id = ar.tenant_id "
                "FROM action_requests ar WHERE d.action_request_id = ar.id AND d.tenant_id IS NULL"
            )
        )
        # Any decision whose action request somehow has no tenant falls back to the
        # canonical default tenant so the NOT NULL constraint can be applied safely.
        bind.execute(
            text("UPDATE decisions SET tenant_id = :tenant_id WHERE tenant_id IS NULL"),
            {"tenant_id": DEFAULT_TENANT_ID},
        )
        op.alter_column("decisions", "tenant_id", nullable=False)

    inspector = inspect(bind)
    fks = inspector.get_foreign_keys("decisions")
    if not any(fk.get("referred_table") == "tenants" for fk in fks):
        op.create_foreign_key(
            "fk_decisions_tenant_id",
            "decisions",
            "tenants",
            ["tenant_id"],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade() -> None:
    """Remove the tenant ownership added by this revision on decisions.

    Tables/columns that pre-dated this revision on an already-current database
    are intentionally left intact to avoid destructive data loss. Full rollback
    of the tenant model on a legacy pre-tenant database is not supported by
    design (see revision docstring).
    """
    bind = op.get_bind()
    inspector = inspect(bind)

    if _table_exists(inspector, "decisions"):
        fks = inspector.get_foreign_keys("decisions")
        tenant_fk = next(
            (fk for fk in fks if fk.get("referred_table") == "tenants" and "tenant_id" in fk.get("constrained_columns", [])),
            None,
        )
        if tenant_fk is not None and tenant_fk.get("name"):
            op.drop_constraint(tenant_fk["name"], "decisions", type_="foreignkey")
        if _column_exists(inspector, "decisions", "tenant_id"):
            op.drop_column("decisions", "tenant_id")
