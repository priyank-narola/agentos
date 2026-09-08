"""PostgreSQL regression tests for the observability service enum handling.

LIMITATION (documented on purpose)
---------------------------------
The repository's standard test architecture is SQLite-only. SQLite does not
enforce PostgreSQL-native enum values, so string literals such as
"EXECUTION_SUCCEEDED" or non-existent members such as
ActionRequestStatus.BLOCKED silently pass on SQLite but raise
psycopg.errors.InvalidTextRepresentation / AttributeError on PostgreSQL.

These tests therefore run ONLY against a real PostgreSQL database and are
skipped unless AGENTOS_TEST_POSTGRES_URL is set, e.g.:

    AGENTOS_TEST_POSTGRES_URL="postgresql+psycopg://postgres:postgres@localhost:5432/agentos_observability_test" \
        python -m pytest tests/test_observability_postgres_regression.py

They create and drop the schema inside the target database and never touch the
application development database. SQLite runs are NOT treated as proof of
PostgreSQL correctness.
"""

import os
import uuid

import pytest
from sqlalchemy import create_engine, select

from app.db.base import Base
from app.db import models  # noqa: F401 - registers all models with metadata
from app.db.models import (
    Tenant, Principal, PrincipalType, PrincipalStatus, Agent, AgentStatus,
    Delegation, DelegationStatus, Tool, Action, CapabilityStatus, Resource,
    ResourceStatus, ResourceSensitivity, RiskClassification, ActionRequest,
    ActionRequestStatus, ApprovalRequest, ApprovalStatus, FinancialExecution,
    ExecutionState,
)
from app.services.observability import ObservabilityService

POSTGRES_URL = os.getenv("AGENTOS_TEST_POSTGRES_URL")

pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason=(
        "AGENTOS_TEST_POSTGRES_URL is not set. PostgreSQL regression test requires "
        "a real PostgreSQL database because SQLite cannot reproduce native enum "
        "conversion errors."
    ),
)


@pytest.fixture(scope="module")
def pg_engine():
    engine = create_engine(POSTGRES_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="module")
def obs_seed(pg_engine):
    """Seed a tenant containing HIGH-risk approval-pending and rejected requests
    plus SUCCEEDED and FAILED FinancialExecution rows to exercise every
    previously-broken observability query against native PostgreSQL enums."""
    from sqlalchemy.orm import Session

    with Session(pg_engine) as db:
        tenant = Tenant(id=uuid.uuid4(), name="Obs PG Regression", slug=f"obs-pg-{uuid.uuid4().hex[:6]}")
        requester = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Alice", external_id="usr_alice_pg", status=PrincipalStatus.ACTIVE)
        approver = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Bob", external_id="usr_bob_pg", status=PrincipalStatus.ACTIVE)
        agent = Agent(id=uuid.uuid4(), tenant_id=tenant.id, name="TreasuryBotPG", owner_principal_id=requester.id, purpose="Treasury", version="1.0.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
        delegation = Delegation(id=uuid.uuid4(), tenant_id=tenant.id, principal_id=requester.id, agent_id=agent.id, scope="wire_transfer", status=DelegationStatus.ACTIVE)
        tool = Tool(id=uuid.uuid4(), tenant_id=tenant.id, name="treasury_tool_pg", description="Wire tool", status=CapabilityStatus.ACTIVE)
        action = Action(id=uuid.uuid4(), tenant_id=tenant.id, tool_id=tool.id, name="wire_transfer", description="Outbound wire", risk_level=RiskClassification.HIGH, status=CapabilityStatus.ACTIVE)
        resource = Resource(id=uuid.uuid4(), tenant_id=tenant.id, resource_type="account", resource_key="ACC-PG-01", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)

        req_pending = ActionRequest(id=uuid.uuid4(), tenant_id=tenant.id, principal_id=requester.id, agent_id=agent.id, action_id=action.id, resource_id=resource.id, parameters={"amount": "25000.00", "currency": "USD"}, status=ActionRequestStatus.APPROVAL_PENDING, idempotency_key=f"idem-pg-pending-{uuid.uuid4()}")
        req_rejected = ActionRequest(id=uuid.uuid4(), tenant_id=tenant.id, principal_id=requester.id, agent_id=agent.id, action_id=action.id, resource_id=resource.id, parameters={"amount": "25000.00", "currency": "USD"}, status=ActionRequestStatus.REJECTED, idempotency_key=f"idem-pg-rejected-{uuid.uuid4()}")
        approval = ApprovalRequest(id=uuid.uuid4(), tenant_id=tenant.id, action_request_id=req_pending.id, requested_by=requester.id, status=ApprovalStatus.PENDING, reason="Approval pending [payload_digest:abc]")
        exec_ok = FinancialExecution(id=uuid.uuid4(), tenant_id=tenant.id, action_request_id=req_pending.id, provider_name="SandboxPaymentProvider", provider_transaction_id="TX-PG-OK", provider_request_id="REQ-PG-OK", status=ExecutionState.SUCCEEDED, payload_digest="digest-ok")
        exec_failed = FinancialExecution(id=uuid.uuid4(), tenant_id=tenant.id, action_request_id=req_rejected.id, provider_name="SandboxPaymentProvider", provider_transaction_id="TX-PG-FAIL", provider_request_id="REQ-PG-FAIL", status=ExecutionState.FAILED, payload_digest="digest-fail")

        db.add_all([tenant, requester, approver, agent, delegation, tool, action, resource, req_pending, req_rejected, approval, exec_ok, exec_failed])
        db.commit()

        yield {"tenant_id": tenant.id, "agent_id": agent.id}
        db.close()


def test_metrics_queries_run_on_postgres_enums(pg_engine, obs_seed):
    from sqlalchemy.orm import Session

    with Session(pg_engine) as db:
        metrics = ObservabilityService(db).get_security_dashboard_metrics(obs_seed["tenant_id"])

    assert metrics["total_action_requests"] == 2
    assert metrics["pending_approvals"] == 1
    assert metrics["approved_executions"] == 1
    assert metrics["execution_failures_timeouts"] == 1
    assert metrics["rejected_actions"] == 1


def test_agent_posture_runs_on_postgres_enums(pg_engine, obs_seed):
    from sqlalchemy.orm import Session

    with Session(pg_engine) as db:
        posture = ObservabilityService(db).get_agent_security_posture(obs_seed["tenant_id"], obs_seed["agent_id"])

    assert posture is not None
    assert posture["agent_id"] == str(obs_seed["agent_id"])
    assert posture["recent_action_count"] == 2
    assert posture["rejected_action_count"] == 1


def test_risk_dashboard_runs_on_postgres_enums(pg_engine, obs_seed):
    from sqlalchemy.orm import Session

    with Session(pg_engine) as db:
        risk = ObservabilityService(db).get_risk_dashboard(obs_seed["tenant_id"])

    assert risk["risk_distribution"]["HIGH"] == 2
    assert len(risk["approval_required_actions"]) == 1
    assert len(risk["rejected_high_risk_actions"]) == 1
    assert risk["approval_required_actions"][0]["risk_level"] == "HIGH"
    assert risk["rejected_high_risk_actions"][0]["risk_level"] == "HIGH"


def test_tenant_posture_runs_on_postgres_with_valid_risk_enum(pg_engine, obs_seed):
    from sqlalchemy.orm import Session

    with Session(pg_engine) as db:
        posture = ObservabilityService(db).get_tenant_security_posture(obs_seed["tenant_id"])

    # Regression: tenant posture previously raised AttributeError on the
    # non-existent RiskClassification.CRITICAL member. It must aggregate using
    # the real domain enum (RiskClassification.HIGH only).
    assert posture["high_risk_activity"] == 2
    assert posture["action_volume"] == 2
    assert posture["active_agents"] == 1
    assert posture["active_principals"] == 2
