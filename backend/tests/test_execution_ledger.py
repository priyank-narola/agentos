"""Execution ledger + decision tenant-ownership tests (SQLite structural).

These tests prove that the sandbox execution flow persists FinancialExecution
rows reflecting real provider outcomes (success / failure / duplicate) with
correct server-derived tenant ownership, and that every Decision carries the
tenant of its owning action request.
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import (
    Tenant, Principal, PrincipalType, PrincipalStatus, Agent, AgentStatus,
    Delegation, DelegationStatus, Tool, Action, CapabilityStatus, Resource,
    ResourceStatus, ResourceSensitivity, RiskClassification, Policy, PolicyStatus,
    PolicyRule, PolicyEffect, ApprovalRequest, Decision, FinancialExecution, ExecutionState, AuditEvent, TenantRole, ReconciliationJob, ReconciliationJobStatus,
)
from app.schemas import GatewayRequestCreate, ApprovalActionRequest
from app.services.gateway import GatewayService
from app.services.approval import ApprovalRoleForbiddenError, ApprovalService
from app.services.execution_ledger import persist_execution_result
from app.execution import ActionExecutionProvider, ExecutionResult, SandboxPaymentProvider, ExecutionStatus
from app.services.execution_provider_registry import ExecutionProviderRegistry
from app.services.reconciliation import (
    ReconciliationConflictError,
    ReconciliationForbiddenError,
    ReconciliationService,
)
from app.services.authorization import grant_role
from app.config import Settings
import app.services.approval as approval_service_module


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
    db.flush()
    grant_role(db, tenant_id=tenant.id, principal_id=approver.id, role=TenantRole.OPERATOR)
    grant_role(db, tenant_id=tenant.id, principal_id=approver.id, role=TenantRole.APPROVER)
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


class RecordingExecutionProvider(ActionExecutionProvider):
    """Test connector proving service routing without contacting an external system."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def execute(self, request_id, parameters, idempotency_key, tenant_id=None):
        self.calls.append({
            "request_id": request_id,
            "parameters": parameters,
            "idempotency_key": idempotency_key,
            "tenant_id": tenant_id,
        })
        return ExecutionResult(
            execution_id="exec-recording-001",
            status=ExecutionStatus.EXECUTION_SUCCEEDED,
            provider_name="RecordingExecutionProvider",
            transaction_reference="REC-001",
            completed_at=datetime.now(timezone.utc),
            raw_response={"status": "recorded"},
        )

    def get_status(self, execution_id, provider_transaction_id=None):
        return ExecutionStatus.EXECUTION_SUCCEEDED

    def verify_result(self, execution_id, provider_transaction_id=None, expected_digest=None):
        return True

    def cancel(self, execution_id, provider_transaction_id=None):
        return ExecutionResult(
            execution_id=execution_id,
            status=ExecutionStatus.CANCELLED,
            provider_name="RecordingExecutionProvider",
            transaction_reference=provider_transaction_id or "REC-001",
            completed_at=datetime.now(timezone.utc),
        )


class UnknownThenStatusProvider(RecordingExecutionProvider):
    """A deterministic connector double for timeout -> status-read recovery."""

    def __init__(self, observed_status: ExecutionStatus) -> None:
        super().__init__()
        self.observed_status = observed_status
        self.status_checks: list[tuple[str, str | None]] = []

    def execute(self, request_id, parameters, idempotency_key, tenant_id=None):
        self.calls.append({
            "request_id": request_id,
            "parameters": parameters,
            "idempotency_key": idempotency_key,
            "tenant_id": tenant_id,
        })
        return ExecutionResult(
            execution_id="exec-reconcile-001",
            status=ExecutionStatus.TIMEOUT,
            provider_name="UnknownThenStatusProvider",
            transaction_reference="REC-TIMEOUT-001",
            completed_at=datetime.now(timezone.utc),
            error_message="Provider timed out before a definitive result",
            raw_response={"code": "PROVIDER_TIMEOUT"},
        )

    def get_status(self, execution_id, provider_transaction_id=None):
        self.status_checks.append((execution_id, provider_transaction_id))
        return self.observed_status


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


def test_gateway_routes_an_action_to_an_injected_connector(db_session):
    """A future connector is chosen by action name, while all other actions
    retain the explicit safe default until product configuration changes."""
    graph = _provision(db_session, "wire_transfer", RiskClassification.LOW)
    recording_provider = RecordingExecutionProvider()
    providers = ExecutionProviderRegistry(SandboxPaymentProvider())
    providers.register("WIRE_TRANSFER", recording_provider)
    gateway = GatewayService(db_session, execution_providers=providers)
    payload = GatewayRequestCreate(
        principal_id=graph["requester"].id,
        agent_id=graph["agent"].id,
        action_id=graph["action"].id,
        resource_id=graph["resource"].id,
        parameters=_wire_params(),
        idempotency_key=f"idem-connector-routing-{uuid.uuid4()}",
    )

    result = gateway.submit(payload)

    assert result.gateway_status == "AUTHORIZED"
    assert len(recording_provider.calls) == 1
    assert recording_provider.calls[0]["tenant_id"] == graph["tenant"].id
    assert recording_provider.calls[0]["parameters"]["amount"] == "25000.00"
    rows = _ledger_rows(db_session, result.action_request_id)
    assert len(rows) == 1
    assert rows[0].provider_name == "RecordingExecutionProvider"
    assert providers.resolve("some_other_action").__class__ is SandboxPaymentProvider


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


def test_action_request_detail_exposes_authoritative_execution_and_principal(db_session):
    """Contract: action-request detail carries authoritative execution_status and
    the initiating principal's display name (no client-side prose inference)."""
    graph = _provision(db_session, "wire_transfer", RiskClassification.LOW)
    gateway = GatewayService(db_session)
    payload = GatewayRequestCreate(
        principal_id=graph["requester"].id,
        agent_id=graph["agent"].id,
        action_id=graph["action"].id,
        resource_id=graph["resource"].id,
        parameters=_wire_params(),
        idempotency_key=f"idem-contract-exec-{uuid.uuid4()}",
    )
    res = gateway.submit(payload)
    assert res.gateway_status == "AUTHORIZED"

    detail = gateway.get_request(res.action_request_id)
    assert detail is not None
    # Decision and execution status stay separate concepts.
    assert detail.decision == "ALLOW"
    assert detail.execution_status == "EXECUTED"
    assert detail.principal_name == "Alice"

    listed = [r for r in gateway.list_requests() if r.id == res.action_request_id]
    assert listed and listed[0].execution_status == "EXECUTED"
    assert listed[0].principal_name == "Alice"


def test_approval_detail_exposes_execution_and_principal(db_session):
    """Contract: approval detail carries authoritative execution_status and the
    acting-for principal's display name after an approved execution."""
    graph = _provision(db_session, "wire_transfer", RiskClassification.HIGH)
    gateway = GatewayService(db_session)
    payload = GatewayRequestCreate(
        principal_id=graph["requester"].id,
        agent_id=graph["agent"].id,
        action_id=graph["action"].id,
        resource_id=graph["resource"].id,
        parameters=_wire_params(),
        idempotency_key=f"idem-contract-approve-{uuid.uuid4()}",
    )
    res = gateway.submit(payload)
    assert res.gateway_status == "PENDING_APPROVAL"

    approvals = ApprovalService(db_session)
    approval_rec = db_session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == res.action_request_id))
    detail = approvals.approve(approval_rec.id, ApprovalActionRequest(approver_principal_id=graph["approver"].id))
    assert detail.status.value == "APPROVED"
    assert detail.execution_status == "EXECUTED"
    assert detail.principal_name == "Alice"

    # Reject path must never claim execution.
    graph2 = _provision(db_session, "bulk_payout", RiskClassification.HIGH)
    payload2 = GatewayRequestCreate(
        principal_id=graph2["requester"].id,
        agent_id=graph2["agent"].id,
        action_id=graph2["action"].id,
        resource_id=graph2["resource"].id,
        parameters={"amount": "25000.00", "currency": "USD", "beneficiary_id": "BEN-Z"},
        idempotency_key=f"idem-contract-reject-{uuid.uuid4()}",
    )
    res2 = gateway.submit(payload2)
    approval_rec2 = db_session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == res2.action_request_id))
    rejected = approvals.reject(approval_rec2.id, ApprovalActionRequest(approver_principal_id=graph2["approver"].id))
    assert rejected.status.value == "REJECTED"
    assert rejected.execution_status == "NOT_EXECUTED"


def test_reconciliation_check_resolves_unknown_execution_with_provider_readback(db_session):
    """A timeout stays uncertain until an independent operator checks the provider.

    The check never re-executes the action; it changes ledger state only from a
    provider status readback and produces a causally ordered audit record.
    """
    graph = _provision(db_session, "wire_transfer", RiskClassification.LOW)
    provider = UnknownThenStatusProvider(ExecutionStatus.EXECUTION_SUCCEEDED)
    providers = ExecutionProviderRegistry(SandboxPaymentProvider())
    providers.register("wire_transfer", provider)
    gateway = GatewayService(db_session, execution_providers=providers)
    response = gateway.submit(GatewayRequestCreate(
        principal_id=graph["requester"].id,
        agent_id=graph["agent"].id,
        action_id=graph["action"].id,
        resource_id=graph["resource"].id,
        parameters=_wire_params(),
        idempotency_key=f"idem-reconcile-{uuid.uuid4()}",
    ))

    ledger = _ledger_rows(db_session, response.action_request_id)[0]
    assert ledger.status == ExecutionState.UNKNOWN
    reconciliation = ReconciliationService(db_session, execution_providers=providers)
    inbox = reconciliation.list(graph["tenant"].id)
    assert [case.action_request_id for case in inbox] == [response.action_request_id]

    result = reconciliation.reconcile(response.action_request_id, graph["approver"].id, graph["tenant"].id)

    assert result.previous_state == "UNKNOWN"
    assert result.observed_provider_status == "EXECUTION_SUCCEEDED"
    assert result.execution_state == "SUCCEEDED"
    assert provider.calls and len(provider.calls) == 1
    assert provider.status_checks == [("exec-reconcile-001", "REC-TIMEOUT-001")]
    assert db_session.get(FinancialExecution, ledger.id).status == ExecutionState.SUCCEEDED
    events = list(db_session.scalars(select(AuditEvent).where(AuditEvent.action_request_id == response.action_request_id)).all())
    assert any(event.event_type == "EXECUTION_RECONCILIATION_CHECKED" for event in events)


def test_reconciliation_refuses_self_review_and_leaves_unknown_outcome_visible(db_session):
    graph = _provision(db_session, "wire_transfer", RiskClassification.LOW)
    provider = UnknownThenStatusProvider(ExecutionStatus.UNKNOWN)
    providers = ExecutionProviderRegistry(SandboxPaymentProvider())
    providers.register("wire_transfer", provider)
    response = GatewayService(db_session, execution_providers=providers).submit(GatewayRequestCreate(
        principal_id=graph["requester"].id,
        agent_id=graph["agent"].id,
        action_id=graph["action"].id,
        resource_id=graph["resource"].id,
        parameters=_wire_params(),
        idempotency_key=f"idem-reconcile-safety-{uuid.uuid4()}",
    ))
    reconciliation = ReconciliationService(db_session, execution_providers=providers)

    with pytest.raises(ReconciliationForbiddenError, match="Requester"):
        reconciliation.reconcile(response.action_request_id, graph["requester"].id, graph["tenant"].id)
    assert _ledger_rows(db_session, response.action_request_id)[0].status == ExecutionState.UNKNOWN

    result = reconciliation.reconcile(response.action_request_id, graph["approver"].id, graph["tenant"].id)
    assert result.execution_state == "RECONCILIATION_REQUIRED"
    assert "unconfirmed" in (result.error_message or "")
    # An unresolved case remains reviewable; repeated status checks never retry
    # the write and must keep the durable reconciliation state visible.
    repeated = reconciliation.reconcile(response.action_request_id, graph["approver"].id, graph["tenant"].id)
    assert repeated.execution_state == "RECONCILIATION_REQUIRED"
    assert len(provider.calls) == 1


def test_due_reconciliation_worker_reads_provider_status_without_resubmitting_action(db_session):
    graph = _provision(db_session, "wire_transfer", RiskClassification.LOW)
    provider = UnknownThenStatusProvider(ExecutionStatus.EXECUTION_SUCCEEDED)
    providers = ExecutionProviderRegistry(SandboxPaymentProvider())
    providers.register("wire_transfer", provider)
    response = GatewayService(db_session, execution_providers=providers).submit(GatewayRequestCreate(
        principal_id=graph["requester"].id,
        agent_id=graph["agent"].id,
        action_id=graph["action"].id,
        resource_id=graph["resource"].id,
        parameters=_wire_params(),
        idempotency_key=f"idem-reconciliation-worker-{uuid.uuid4()}",
    ))
    job = db_session.scalar(select(ReconciliationJob).where(ReconciliationJob.action_request_id == response.action_request_id))
    assert job is not None and job.status == ReconciliationJobStatus.PENDING.value

    report = ReconciliationService(db_session, execution_providers=providers).run_due_checks(now=job.next_check_at)

    assert report == {"claimed": 1, "completed": 1, "rescheduled": 0, "escalated": 0}
    assert db_session.get(FinancialExecution, _ledger_rows(db_session, response.action_request_id)[0].id).status == ExecutionState.SUCCEEDED
    assert db_session.get(ReconciliationJob, job.id).status == ReconciliationJobStatus.COMPLETED.value
    assert len(provider.calls) == 1  # gateway submission only; worker did not execute again
    assert provider.status_checks == [("exec-reconcile-001", "REC-TIMEOUT-001")]


def test_due_reconciliation_worker_escalates_after_bounded_ambiguous_readbacks(db_session):
    graph = _provision(db_session, "wire_transfer", RiskClassification.LOW)
    provider = UnknownThenStatusProvider(ExecutionStatus.UNKNOWN)
    providers = ExecutionProviderRegistry(SandboxPaymentProvider())
    providers.register("wire_transfer", provider)
    response = GatewayService(db_session, execution_providers=providers).submit(GatewayRequestCreate(
        principal_id=graph["requester"].id,
        agent_id=graph["agent"].id,
        action_id=graph["action"].id,
        resource_id=graph["resource"].id,
        parameters=_wire_params(),
        idempotency_key=f"idem-reconciliation-escalation-{uuid.uuid4()}",
    ))
    worker = ReconciliationService(db_session, execution_providers=providers)
    job = db_session.scalar(select(ReconciliationJob).where(ReconciliationJob.action_request_id == response.action_request_id))
    assert job is not None

    for _ in range(3):
        worker.run_due_checks(now=job.next_check_at)
        db_session.refresh(job)

    assert job.status == ReconciliationJobStatus.ESCALATED.value
    assert job.attempt_count == 3
    assert _ledger_rows(db_session, response.action_request_id)[0].status == ExecutionState.RECONCILIATION_REQUIRED
    assert len(provider.calls) == 1
    events = list(db_session.scalars(select(AuditEvent).where(AuditEvent.action_request_id == response.action_request_id)).all())
    assert any(event.event_type == "EXECUTION_RECONCILIATION_ESCALATED" for event in events)


def test_production_approval_requires_explicit_approver_role(db_session, monkeypatch):
    graph = _provision(db_session, "wire_transfer", RiskClassification.HIGH)
    response = GatewayService(db_session).submit(GatewayRequestCreate(
        principal_id=graph["requester"].id,
        agent_id=graph["agent"].id,
        action_id=graph["action"].id,
        resource_id=graph["resource"].id,
        parameters=_wire_params(),
        idempotency_key=f"idem-production-role-{uuid.uuid4()}",
    ))
    approval = db_session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == response.action_request_id))
    assert approval is not None
    # Remove the test fixture's grant so production enforcement is exercised.
    from app.db.models import PrincipalRole
    db_session.delete(db_session.scalar(select(PrincipalRole).where(
        PrincipalRole.principal_id == graph["approver"].id,
        PrincipalRole.role == TenantRole.APPROVER,
    )))
    db_session.commit()
    monkeypatch.setattr(approval_service_module, "settings", Settings(app_env="production"))

    with pytest.raises(ApprovalRoleForbiddenError, match="APPROVER"):
        ApprovalService(db_session).approve(
            approval.id,
            ApprovalActionRequest(approver_principal_id=graph["approver"].id),
        )
    assert db_session.get(ApprovalRequest, approval.id).status.value == "PENDING"

    grant_role(db_session, tenant_id=graph["tenant"].id, principal_id=graph["approver"].id, role=TenantRole.APPROVER)
    db_session.commit()
    detail = ApprovalService(db_session).approve(
        approval.id,
        ApprovalActionRequest(approver_principal_id=graph["approver"].id),
    )
    assert detail.status.value == "APPROVED"
