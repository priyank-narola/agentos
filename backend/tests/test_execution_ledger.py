"""Execution ledger + decision tenant-ownership tests (SQLite structural).

These tests prove that the sandbox execution flow persists FinancialExecution
rows reflecting real provider outcomes (success / failure / duplicate) with
correct server-derived tenant ownership, and that every Decision carries the
tenant of its owning action request.
"""

import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import (
    Tenant, Principal, PrincipalType, PrincipalStatus, Agent, AgentStatus,
    Delegation, DelegationStatus, Tool, Action, CapabilityStatus, Resource,
    ResourceStatus, ResourceSensitivity, RiskClassification, Policy, PolicyStatus,
    PolicyRule, PolicyEffect, ApprovalRequest, Decision, FinancialExecution, ExecutionState,
)
from app.schemas import GatewayRequestCreate, ApprovalActionRequest
from app.services.gateway import GatewayService
from app.services.approval import ApprovalService
from app.services.execution_ledger import persist_execution_result
from app.execution import SandboxPaymentProvider, ExecutionStatus


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


def _provision(db: Session, action_name: str, risk: RiskClassification):
    tenant = Tenant(id=uuid.uuid4(), name="Ledger Tenant", slug=f"ledger-{uuid.uuid4().hex[:6]}")
    requester = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Alice", external_id=f"usr_alice_{uuid.uuid4().hex[:6]}", status=PrincipalStatus.ACTIVE)
    approver = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Bob", external_id=f"usr_bob_{uuid.uuid4().hex[:6]}", status=PrincipalStatus.ACTIVE)
    agent = Agent(id=uuid.uuid4(), tenant_id=tenant.id, name=f"LedgerBot-{uuid.uuid4().hex[:4]}", owner_principal_id=requester.id, purpose="Treasury", version="1.0.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    delegation = Delegation(id=uuid.uuid4(), tenant_id=tenant.id, principal_id=requester.id, agent_id=agent.id, scope=action_name, status=DelegationStatus.ACTIVE)
    tool = Tool(id=uuid.uuid4(), tenant_id=tenant.id, name=f"ledger_tool_{uuid.uuid4().hex[:6]}", description="Treasury tool", status=CapabilityStatus.ACTIVE)
    action = Action(id=uuid.uuid4(), tenant_id=tenant.id, tool_id=tool.id, name=action_name, description="Treasury action", risk_level=risk, status=CapabilityStatus.ACTIVE)
    resource = Resource(id=uuid.uuid4(), tenant_id=tenant.id, resource_type="account", resource_key="ACC-LEDGER-01", sensitivity=ResourceSensitivity.LOW, status=ResourceStatus.ACTIVE)
    policy = Policy(id=uuid.uuid4(), tenant_id=tenant.id, name=f"ledger_policy_{uuid.uuid4().hex[:6]}", version=1, status=PolicyStatus.ACTIVE)
    rule = PolicyRule(id=uuid.uuid4(), policy_id=policy.id, effect=PolicyEffect.ALLOW, action=action_name, resource_type="account", priority=1)
    db.add_all([tenant, requester, approver, agent, delegation, tool, action, resource, policy, rule])
    db.commit()
    return {"tenant": tenant, "requester": requester, "approver": approver, "agent": agent, "action": action, "resource": resource}


def _wire_params(extra: dict | None = None):
    params = {
        "source_account_id": "ACC-LEDGER-01",
        "destination_account_id": "ACC-VENDOR-1",
        "amount": "25000.00",
        "currency": "USD",
        "beneficiary_id": "BEN-LEDGER-1",
        "transaction_reference": f"REF-{uuid.uuid4().hex[:8].upper()}",
    }
    if extra:
        params.update(extra)
    return params


def _ledger_rows(db: Session, request_id) -> list[FinancialExecution]:
    return list(db.scalars(select(FinancialExecution).where(FinancialExecution.action_request_id == request_id)).all())


def test_gateway_auto_exec_persists_success_ledger_with_tenant(db_session):
    """1. Auto-executed low-risk wire_transfer persists a SUCCEEDED ledger row."""
    graph = _provision(db_session, "wire_transfer", RiskClassification.LOW)
    gateway = GatewayService(db_session)
    payload = GatewayRequestCreate(
        principal_id=graph["requester"].id,
        agent_id=graph["agent"].id,
        action_id=graph["action"].id,
        resource_id=graph["resource"].id,
        parameters=_wire_params(),
        idempotency_key=f"idem-ledger-success-{uuid.uuid4()}",
    )
    res = gateway.submit(payload)
    assert res.gateway_status == "AUTHORIZED"

    rows = _ledger_rows(db_session, res.action_request_id)
    assert len(rows) == 1
    assert rows[0].tenant_id == graph["tenant"].id
    assert rows[0].status == ExecutionState.SUCCEEDED
    assert rows[0].provider_name == "SandboxPaymentProvider"
    assert rows[0].payload_digest

    # The decision must carry the owning action request's tenant.
    decision = db_session.scalar(select(Decision).where(Decision.action_request_id == res.action_request_id))
    assert decision is not None
    assert decision.tenant_id == graph["tenant"].id


def test_approved_wire_persists_success_ledger_and_tenant_scoped_decisions(db_session):
    """2. High-risk wire through approval persists a SUCCEEDED ledger row; both
    decisions (gateway + approval) are tenant scoped to the action request."""
    graph = _provision(db_session, "wire_transfer", RiskClassification.HIGH)
    gateway = GatewayService(db_session)
    payload = GatewayRequestCreate(
        principal_id=graph["requester"].id,
        agent_id=graph["agent"].id,
        action_id=graph["action"].id,
        resource_id=graph["resource"].id,
        parameters=_wire_params(),
        idempotency_key=f"idem-ledger-approve-{uuid.uuid4()}",
    )
    res = gateway.submit(payload)
    assert res.gateway_status == "PENDING_APPROVAL"

    approvals = ApprovalService(db_session)
    approval_rec = db_session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == res.action_request_id))
    detail = approvals.approve(approval_rec.id, ApprovalActionRequest(approver_principal_id=graph["approver"].id))
    assert detail.status.value == "APPROVED"

    rows = _ledger_rows(db_session, res.action_request_id)
    assert len(rows) == 1
    assert rows[0].tenant_id == graph["tenant"].id
    assert rows[0].status == ExecutionState.SUCCEEDED

    decisions = list(db_session.scalars(select(Decision).where(Decision.action_request_id == res.action_request_id)))
    assert len(decisions) == 2
    assert all(d.tenant_id == graph["tenant"].id for d in decisions)


def test_failed_execution_persists_failed_ledger(db_session):
    """3. Approved execution that fails at the sandbox persists a FAILED ledger row
    with error metadata and is never marked SUCCEEDED."""
    graph = _provision(db_session, "bulk_payout", RiskClassification.HIGH)
    gateway = GatewayService(db_session)
    payload = GatewayRequestCreate(
        principal_id=graph["requester"].id,
        agent_id=graph["agent"].id,
        action_id=graph["action"].id,
        resource_id=graph["resource"].id,
        parameters={"amount": "25000.00", "currency": "USD", "beneficiary_id": "BEN-X", "force_failure": True},
        idempotency_key=f"idem-ledger-fail-{uuid.uuid4()}",
    )
    res = gateway.submit(payload)
    assert res.gateway_status == "PENDING_APPROVAL"

    approvals = ApprovalService(db_session)
    approval_rec = db_session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == res.action_request_id))
    detail = approvals.approve(approval_rec.id, ApprovalActionRequest(approver_principal_id=graph["approver"].id))
    assert detail.status.value == "APPROVED"

    rows = _ledger_rows(db_session, res.action_request_id)
    assert len(rows) == 1
    assert rows[0].tenant_id == graph["tenant"].id
    assert rows[0].status == ExecutionState.FAILED
    assert rows[0].error_code == "ERR_INSUFFICIENT_FUNDS"
    assert rows[0].status != ExecutionState.SUCCEEDED


def test_duplicate_or_idempotent_execution_never_creates_duplicate_ledger(db_session):
    """4. Re-persisting the same action request outcome never duplicates ledger truth."""
    graph = _provision(db_session, "wire_transfer", RiskClassification.LOW)
    gateway = GatewayService(db_session)
    payload = GatewayRequestCreate(
        principal_id=graph["requester"].id,
        agent_id=graph["agent"].id,
        action_id=graph["action"].id,
        resource_id=graph["resource"].id,
        parameters=_wire_params(),
        idempotency_key=f"idem-ledger-dupe-{uuid.uuid4()}",
    )
    res = gateway.submit(payload)
    assert len(_ledger_rows(db_session, res.action_request_id)) == 1

    # Gateway-level idempotency: re-submitting the same key returns the same request
    # and never re-executes or re-persists.
    res_again = gateway.submit(payload)
    assert res_again.action_request_id == res.action_request_id
    assert len(_ledger_rows(db_session, res.action_request_id)) == 1

    # Provider-level duplicate on a shared provider instance reports DUPLICATE.
    provider = SandboxPaymentProvider()
    first = provider.execute(res.action_request_id, payload.parameters, payload.idempotency_key, tenant_id=graph["tenant"].id)
    assert first.status == ExecutionStatus.EXECUTION_SUCCEEDED
    duplicate = provider.execute(res.action_request_id, payload.parameters, payload.idempotency_key, tenant_id=graph["tenant"].id)
    assert duplicate.status == ExecutionStatus.DUPLICATE

    # Ledger idempotency guard: neither re-persist call may add a second row.
    persist_execution_result(
        db_session,
        action_request_id=res.action_request_id,
        tenant_id=graph["tenant"].id,
        result=duplicate,
        parameters=payload.parameters,
    )
    assert len(_ledger_rows(db_session, res.action_request_id)) == 1


def test_not_executed_outcome_creates_no_ledger_row(db_session):
    """5. NOT_EXECUTED / DUPLICATE provider outcomes must not fabricate a ledger row."""
    graph = _provision(db_session, "vendor_payout", RiskClassification.LOW)
    gateway = GatewayService(db_session)
    payload = GatewayRequestCreate(
        principal_id=graph["requester"].id,
        agent_id=graph["agent"].id,
        action_id=graph["action"].id,
        resource_id=graph["resource"].id,
        parameters={"amount": "500.00", "currency": "USD", "beneficiary_id": "BEN-Y"},
        idempotency_key=f"idem-ledger-none-{uuid.uuid4()}",
    )
    # vendor_payout is not auto-executed by the gateway (only wire_transfer is).
    res = gateway.submit(payload)
    assert res.gateway_status == "AUTHORIZED"
    assert len(_ledger_rows(db_session, res.action_request_id)) == 0
