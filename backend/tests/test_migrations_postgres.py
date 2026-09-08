"""PostgreSQL migration + seed validation tests (gated).

These tests drive the real Alembic CLI and the real seed entrypoint against a
PostgreSQL database, proving:

- a clean database upgrades to head and matches the application models,
- seeding a clean database succeeds and is idempotent,
- an existing current database (schema present, stamped at an earlier revision,
  with legacy rows lacking decision.tenant_id) upgrades additively without data
  loss and backfills decision tenant ownership from the owning action request.

They are SKIPPED unless AGENTOS_TEST_POSTGRES_URL is set and MUST point to a
dedicated SCRATCH database: each test resets the public schema of that database.
They never run against the application development database.

Run with:
    AGENTOS_TEST_POSTGRES_URL="postgresql+psycopg://postgres:postgres@localhost:5432/agentos_migrations_test" \
        python -m pytest tests/test_migrations_postgres.py
"""

import os
import subprocess
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse

import pytest
import sqlalchemy as sa

BACKEND_DIR = Path(__file__).resolve().parent.parent

POSTGRES_URL = os.getenv("AGENTOS_TEST_POSTGRES_URL")

pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason=(
        "AGENTOS_TEST_POSTGRES_URL is not set. Migration/seed PostgreSQL tests "
        "require a real PostgreSQL database and are destructive on it; they must "
        "target a dedicated scratch database."
    ),
)

# All tables the current models expect.
EXPECTED_TABLES = {
    "tenants",
    "principals",
    "agents",
    "delegations",
    "tools",
    "actions",
    "resources",
    "policies",
    "policy_rules",
    "action_requests",
    "decisions",
    "approval_requests",
    "audit_events",
    "financial_executions",
}

_DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture(scope="module")
def db_url() -> str:
    url = POSTGRES_URL.strip()
    db_name = (urlparse(url).path or "").lstrip("/")
    if db_name in {"agentos", "postgres"}:
        raise RuntimeError(
            f"AGENTOS_TEST_POSTGRES_URL points at protected database '{db_name}'. "
            "Migration tests reset the public schema and must use a dedicated scratch database."
        )
    yield url


def _run_cli(db_url: str, module_args: list[str]) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["DATABASE_URL"] = db_url
    env["PYTHONPATH"] = str(BACKEND_DIR)
    return subprocess.run(
        [sys.executable, "-m", *module_args],
        cwd=str(BACKEND_DIR),
        env=env,
        capture_output=True,
        text=True,
    )


def _run_alembic(db_url: str, *args: str) -> subprocess.CompletedProcess:
    # The backend directory contains a local ``alembic/`` migrations package that
    # shadows the installed alembic distribution. Invoke the installed package by
    # inserting site-packages ahead of the current directory on sys.path.
    env = dict(os.environ)
    env["DATABASE_URL"] = db_url
    code = (
        "import sys, sysconfig; "
        "sys.path.insert(0, sysconfig.get_paths()['purelib']); "
        "from alembic.config import main; "
        f"main({list(args)!r})"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(BACKEND_DIR),
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"alembic {' '.join(args)} failed:\n{proc.stdout}\n{proc.stderr}"
    return proc


def _reset_schema(db_url: str) -> None:
    engine = sa.create_engine(db_url, isolation_level="AUTOCOMMIT")
    with engine.begin() as conn:
        conn.execute(sa.text("DROP SCHEMA public CASCADE"))
        conn.execute(sa.text("CREATE SCHEMA public"))
    engine.dispose()


def _engine(db_url: str):
    return sa.create_engine(db_url)


def _count(conn, table: str) -> int:
    return conn.execute(sa.text(f"SELECT count(*) FROM {table}")).scalar()


def test_fresh_database_upgrades_and_seed_is_idempotent(db_url):
    _reset_schema(db_url)
    _run_alembic(db_url, "upgrade", "head")

    engine = _engine(db_url)
    with engine.begin() as conn:
        tables = set(sa.inspect(conn).get_table_names())
        assert EXPECTED_TABLES <= tables, f"missing tables: {EXPECTED_TABLES - tables}"

        # Tenant ownership columns are NOT NULL and tenant FKs exist.
        decision_cols = {c["name"]: c["nullable"] for c in sa.inspect(conn).get_columns("decisions")}
        assert decision_cols.get("tenant_id") is False
        fin_cols = {c["name"]: c["nullable"] for c in sa.inspect(conn).get_columns("financial_executions")}
        assert fin_cols.get("tenant_id") is False
        principal_fks = sa.inspect(conn).get_foreign_keys("principals")
        assert any(fk["referred_table"] == "tenants" and "tenant_id" in fk["constrained_columns"] for fk in principal_fks)
        decision_fks = sa.inspect(conn).get_foreign_keys("decisions")
        assert any(fk["referred_table"] == "tenants" and "tenant_id" in fk["constrained_columns"] for fk in decision_fks)

        # Default tenant row is bootstrapped by the migration itself.
        tenant_count = conn.execute(sa.text("SELECT count(*) FROM tenants WHERE id = :id"), {"id": _DEFAULT_TENANT_ID}).scalar()
        assert tenant_count == 1

    # Seed twice: must succeed and be idempotent.
    first = _run_cli(db_url, ["app.seed"])
    assert first.returncode == 0, f"seed failed:\n{first.stdout}\n{first.stderr}"
    with engine.begin() as conn:
        counts_after_first = {t: _count(conn, t) for t in ["tenants", "principals", "agents", "tools", "actions", "resources", "delegations", "policies"]}

    second = _run_cli(db_url, ["app.seed"])
    assert second.returncode == 0, f"re-seed failed:\n{second.stdout}\n{second.stderr}"
    with engine.begin() as conn:
        assert all(_count(conn, t) == counts_after_first[t] for t in counts_after_first), "repeated seed created duplicates"
        tenants = conn.execute(sa.text("SELECT count(*) FROM tenants")).scalar()
        assert tenants == 1, "repeated seed created duplicate tenants"
    engine.dispose()


def test_existing_current_database_upgrades_additively_and_backfills_decision_tenant(db_url):
    # Build the state of the current dev database: schema current at HEAD but
    # stamped at 0002 and with legacy decisions rows lacking tenant ownership.
    _reset_schema(db_url)
    _run_alembic(db_url, "upgrade", "20260824_0002")

    engine = _engine(db_url)
    with engine.begin() as conn:
        # Emulate the legacy decisions table (no tenant_id / no tenant FK).
        fks = sa.inspect(conn).get_foreign_keys("decisions")
        tenant_fk = next(
            (fk for fk in fks if fk["referred_table"] == "tenants" and "tenant_id" in fk["constrained_columns"]),
            None,
        )
        assert tenant_fk is not None and tenant_fk["name"] is not None
        conn.execute(sa.text(f"ALTER TABLE decisions DROP CONSTRAINT {tenant_fk['name']}"))
        conn.execute(sa.text("ALTER TABLE decisions DROP COLUMN tenant_id"))

        # Insert legacy rows across two tenants (including decisions with no tenant).
        tenant_a = str(uuid.uuid4())
        conn.execute(
            sa.text(
                "INSERT INTO tenants (id, name, slug, status) VALUES (:id, :name, :slug, 'ACTIVE')"
            ),
            {"id": tenant_a, "name": "Acme A", "slug": f"acme-a-{uuid.uuid4().hex[:6]}"},
        )
        principal_a = str(uuid.uuid4())
        conn.execute(
            sa.text("INSERT INTO principals (id, tenant_id, type, name, external_id, status) VALUES (:id, :t, 'HUMAN', :name, :ext, 'ACTIVE')"),
            {"id": principal_a, "t": tenant_a, "name": "Alice", "ext": f"usr_{uuid.uuid4().hex[:6]}"},
        )
        agent_a = str(uuid.uuid4())
        conn.execute(
            sa.text("INSERT INTO agents (id, tenant_id, name, owner_principal_id, purpose, version, status, risk_classification) VALUES (:id, :t, :name, :owner, 'Fin', '1.0', 'ACTIVE', 'LOW')"),
            {"id": agent_a, "t": tenant_a, "name": f"FinBot-{uuid.uuid4().hex[:4]}", "owner": principal_a},
        )
        tool_a = str(uuid.uuid4())
        conn.execute(
            sa.text("INSERT INTO tools (id, name, description, status) VALUES (:id, :name, 'desc', 'ACTIVE')"),
            {"id": tool_a, "name": f"tool_{uuid.uuid4().hex[:6]}"},
        )
        action_a = str(uuid.uuid4())
        conn.execute(
            sa.text("INSERT INTO actions (id, tool_id, name, description, risk_level, status) VALUES (:id, :tool, 'wire_transfer', 'desc', 'HIGH', 'ACTIVE')"),
            {"id": action_a, "tool": tool_a},
        )
        resource_a = str(uuid.uuid4())
        conn.execute(
            sa.text("INSERT INTO resources (id, tenant_id, resource_type, resource_key, sensitivity, status) VALUES (:id, :t, 'account', :key, 'HIGH', 'ACTIVE')"),
            {"id": resource_a, "t": tenant_a, "key": "ACC-A"},
        )
        req_a = str(uuid.uuid4())
        conn.execute(
            sa.text(
                "INSERT INTO action_requests (id, tenant_id, agent_id, principal_id, action_id, resource_id, parameters, status, idempotency_key) "
                "VALUES (:id, :t, :agent, :principal, :action, :resource, '{}', 'COMPLETED', :key)"
            ),
            {"id": req_a, "t": tenant_a, "agent": agent_a, "principal": principal_a, "action": action_a, "resource": resource_a, "key": f"key-{uuid.uuid4()}"},
        )
        decision_a = str(uuid.uuid4())
        # No tenant_id column exists yet -> legacy decision insert.
        conn.execute(
            sa.text("INSERT INTO decisions (id, action_request_id, decision, reason) VALUES (:id, :req, 'ALLOW', 'legacy allow')"),
            {"id": decision_a, "req": req_a},
        )

        counts_before = {t: _count(conn, t) for t in EXPECTED_TABLES}

    _run_alembic(db_url, "upgrade", "head")

    with engine.begin() as conn:
        # No data lost. The default-tenant bootstrap row is an intentional addition.
        for table, before in counts_before.items():
            if table == "tenants":
                assert _count(conn, table) == before + 1, "tenants row count mismatch"
            else:
                assert _count(conn, table) == before, f"data loss on {table}"
        # Decision tenant backfilled from the owning action request's tenant.
        row = conn.execute(
            sa.text("SELECT d.tenant_id FROM decisions d WHERE d.id = :id"),
            {"id": decision_a},
        ).first()
        assert row is not None and str(row[0]) == tenant_a
        decision_cols = {c["name"]: c["nullable"] for c in sa.inspect(conn).get_columns("decisions")}
        assert decision_cols.get("tenant_id") is False
        decision_fks = sa.inspect(conn).get_foreign_keys("decisions")
        assert any(fk["referred_table"] == "tenants" and "tenant_id" in fk["constrained_columns"] for fk in decision_fks)
        # Default tenant row exists for model-level defaults.
        tenant_count = conn.execute(sa.text("SELECT count(*) FROM tenants WHERE id = :id"), {"id": _DEFAULT_TENANT_ID}).scalar()
        assert tenant_count == 1
    engine.dispose()


def test_downgrade_after_head_removes_decision_tenant_ownership(db_url):
    _reset_schema(db_url)
    _run_alembic(db_url, "upgrade", "head")
    _run_alembic(db_url, "downgrade", "-1")

    engine = _engine(db_url)
    with engine.begin() as conn:
        cols = {c["name"] for c in sa.inspect(conn).get_columns("decisions")}
        assert "tenant_id" not in cols
    engine.dispose()
