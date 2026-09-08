"""CISO demo repeatability (W6)."""

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Tenant, Tool, FinancialExecution
from app.services.mcp_sandbox import ExternalMCPSandboxClient

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def reset_db():
    with TestingSession() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


@pytest.fixture
def db_session():
    with TestingSession() as session:
        yield session


def test_ciso_demo_is_repeatable(db_session):
    first = ExternalMCPSandboxClient(db_session).run_ciso_demonstration_flow()
    assert first["final_outcome"] == "GOVERNANCE_SUCCESS"
    second = ExternalMCPSandboxClient(db_session).run_ciso_demonstration_flow()
    assert second["final_outcome"] == "GOVERNANCE_SUCCESS"
    assert second["execution_status"] == "EXECUTION_SUCCEEDED"

    # No uncontrolled accumulation of tenants/tools across runs.
    tenants = db_session.scalar(select(func.count(Tenant.id)).where(Tenant.slug == "treasury-demo"))
    tools = db_session.scalar(select(func.count(Tool.id)).where(Tool.name == "treasury_wire_tool"))
    assert tenants == 1
    assert tools == 1
    # Each successful approved transfer persists exactly one SUCCEEDED ledger row.
    executions = db_session.scalar(select(func.count(FinancialExecution.id)).where(FinancialExecution.status == "SUCCEEDED"))
    assert executions == 2
