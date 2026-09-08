import hmac
import hashlib
import time
import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session

from app.db.models import (
    Agent, AgentStatus, Delegation, DelegationStatus, ExecutionState,
    Principal, PrincipalStatus, PrincipalType, Resource, ResourceStatus, ResourceSensitivity, RiskClassification, Tool, Action, CapabilityStatus,
    Policy, PolicyRule, PolicyStatus, PolicyEffect, ApprovalRequest,
    Tenant, DEFAULT_TENANT_ID
)





from app.auth import TokenClaims
from app.identity import AgentIdentityResolver, SecurityContext, IdentityResolutionError, DefaultAgentClientResolver
from app.execution import ExecutionStateMachine, ExecutionStatus, InvalidExecutionStateTransitionError, SandboxPaymentProvider
from app.services.gateway import GatewayService, GatewayIdempotencyConflict
from app.services.approval import ApprovalService, ApprovalConflictError
from app.services.webhook import (
    WebhookSecurityHandler, WebhookSignatureVerificationError,
    WebhookTimestampExpiredError, WebhookDuplicateEventError, WebhookTenantBindingError, WebhookError
)
from app.schemas import GatewayRequestCreate, ApprovalActionRequest



from app.db.base import Base
from sqlalchemy import create_engine, select

from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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


@pytest.fixture
def tenants(db_session: Session):
    t1 = Tenant(id=uuid.UUID("00000000-0000-0000-0000-000000000001"), name="Tenant One", slug="tenant-1")
    t2 = Tenant(id=uuid.UUID("00000000-0000-0000-0000-000000000002"), name="Tenant Two", slug="tenant-2")
    db_session.add(t1)
    db_session.add(t2)
    db_session.commit()
    return t1, t2



@pytest.fixture
def multi_tenant_setup(db_session: Session, tenants):
    t1, t2 = tenants

    # Tenant 1 Setup
    p1 = Principal(id=uuid.uuid4(), tenant_id=t1.id, type=PrincipalType.HUMAN, name="User T1", external_id="usr_t1", status=PrincipalStatus.ACTIVE)
    a1 = Agent(id=uuid.uuid4(), tenant_id=t1.id, name="Agent T1", owner_principal_id=p1.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    d1 = Delegation(id=uuid.uuid4(), tenant_id=t1.id, principal_id=p1.id, agent_id=a1.id, scope="wire_transfer", status=DelegationStatus.ACTIVE)
    tool1 = Tool(id=uuid.uuid4(), tenant_id=t1.id, name="wire_tool_t1", description="Wire tool 1", status=CapabilityStatus.ACTIVE)
    act1 = Action(id=uuid.uuid4(), tenant_id=t1.id, tool_id=tool1.id, name="wire_transfer", description="Wire transfer action", risk_level="HIGH", status=CapabilityStatus.ACTIVE)
    res1 = Resource(id=uuid.uuid4(), tenant_id=t1.id, resource_type="account", resource_key="acc_t1", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)
    pol1 = Policy(id=uuid.uuid4(), tenant_id=t1.id, name="wire_policy_t1", version=1, status=PolicyStatus.ACTIVE)

    rule1 = PolicyRule(id=uuid.uuid4(), policy_id=pol1.id, effect=PolicyEffect.ALLOW, action="wire_transfer", resource_type="account", priority=1)

    # Tenant 2 Setup
    p2 = Principal(id=uuid.uuid4(), tenant_id=t2.id, type=PrincipalType.HUMAN, name="User T2", external_id="usr_t2", status=PrincipalStatus.ACTIVE)
    a2 = Agent(id=uuid.uuid4(), tenant_id=t2.id, name="Agent T2", owner_principal_id=p2.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)

    d2 = Delegation(id=uuid.uuid4(), tenant_id=t2.id, principal_id=p2.id, agent_id=a2.id, scope="wire_transfer", status=DelegationStatus.ACTIVE)
    tool2 = Tool(id=uuid.uuid4(), tenant_id=t2.id, name="wire_tool_t2", description="Wire tool 2", status=CapabilityStatus.ACTIVE)
    act2 = Action(id=uuid.uuid4(), tenant_id=t2.id, tool_id=tool2.id, name="wire_transfer", description="Wire transfer action", risk_level="HIGH", status=CapabilityStatus.ACTIVE)

    res2 = Resource(id=uuid.uuid4(), tenant_id=t2.id, resource_type="account", resource_key="acc_t2", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)

    db_session.add_all([p1, a1, d1, tool1, act1, res1, pol1, rule1, p2, a2, d2, tool2, act2, res2])
    db_session.commit()

    return {
        "t1": {"p": p1, "a": a1, "d": d1, "tool": tool1, "act": act1, "res": res1},
        "t2": {"p": p2, "a": a2, "d": d2, "tool": tool2, "act": act2, "res": res2},
    }


def test_cross_tenant_identity_resolution_rejected(db_session: Session, multi_tenant_setup):
    """Verify AgentIdentityResolver rejects cross-tenant Principal and Agent pairing."""
    t1_p = multi_tenant_setup["t1"]["p"]
    t2_a = multi_tenant_setup["t2"]["a"]

    resolver = AgentIdentityResolver()
    claims = TokenClaims(
        sub=t1_p.external_id,
        client_id=str(t2_a.id),
        scope="wire_transfer",
        iss="https://auth.agentos.ai",
        aud="https://api.agentos.ai",
        exp=int(time.time()) + 3600,
        iat=int(time.time())
    )

    with pytest.raises(IdentityResolutionError) as exc:
        resolver.resolve_security_context(claims, db_session)
    assert "Tenant mismatch" in str(exc.value)


def test_cross_tenant_gateway_request_blocked(db_session: Session, multi_tenant_setup):
    """Verify GatewayService blocks action request referencing cross-tenant resource."""
    t1_p = multi_tenant_setup["t1"]["p"]
    t1_a = multi_tenant_setup["t1"]["a"]
    t1_act = multi_tenant_setup["t1"]["act"]
    t2_res = multi_tenant_setup["t2"]["res"]  # Resource belongs to Tenant 2!

    gateway = GatewayService(db_session)
    req = GatewayRequestCreate(
        principal_id=t1_p.id,
        agent_id=t1_a.id,
        action_id=t1_act.id,
        resource_id=t2_res.id,
        parameters={
            "source_account_id": "ACC-101",
            "destination_account_id": "ACC-202",
            "amount": "100.00",
            "currency": "USD",
            "transaction_reference": f"REF-{uuid.uuid4().hex[:8]}"
        },
        idempotency_key=f"idem-cross-tenant-{uuid.uuid4()}"
    )

    with pytest.raises(GatewayIdempotencyConflict) as exc:
        gateway.submit(req)
    assert "Tenant mismatch" in str(exc.value)


def test_cross_tenant_approval_execution_blocked(db_session: Session, multi_tenant_setup):
    """Verify Approver from Tenant B cannot approve an ApprovalRequest belonging to Tenant A."""
    t1 = multi_tenant_setup["t1"]
    t2 = multi_tenant_setup["t2"]

    # Create approval request for Tenant 1
    gateway = GatewayService(db_session)
    req = GatewayRequestCreate(
        principal_id=t1["p"].id,
        agent_id=t1["a"].id,
        action_id=t1["act"].id,
        resource_id=t1["res"].id,
        parameters={
            "source_account_id": "ACC-101",
            "destination_account_id": "ACC-202",
            "amount": "100.00",
            "currency": "USD",
            "beneficiary_id": "BEN-123",
            "transaction_reference": f"REF-{uuid.uuid4().hex[:8]}"
        },

        idempotency_key=f"idem-approval-t1-{uuid.uuid4()}"
    )
    res = gateway.submit(req)
    assert res.approval_required is True

    # Find created ApprovalRequest
    approval_svc = ApprovalService(db_session)
    t1_approval = db_session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == res.action_request_id))
    assert t1_approval is not None


    # Tenant 2 principal tries to approve Tenant 1 request!
    t2_approver = t2["p"]
    with pytest.raises(ApprovalConflictError) as exc:
        approval_svc.approve(
            t1_approval.id,
            ApprovalActionRequest(approver_principal_id=t2_approver.id)
        )
    assert "no longer active or valid for tenant" in str(exc.value)




def test_execution_state_machine_legal_transitions():
    """Verify valid state machine transitions in ExecutionStateMachine."""
    ExecutionStateMachine.validate_transition(ExecutionStatus.NOT_EXECUTED, ExecutionStatus.EXECUTION_SUCCEEDED)
    ExecutionStateMachine.validate_transition(ExecutionStatus.NOT_EXECUTED, ExecutionStatus.EXECUTION_FAILED)
    ExecutionStateMachine.validate_transition(ExecutionStatus.NOT_EXECUTED, ExecutionStatus.TIMEOUT)
    ExecutionStateMachine.validate_transition(ExecutionStatus.UNKNOWN, ExecutionStatus.RECONCILIATION_REQUIRED)
    ExecutionStateMachine.validate_transition(ExecutionStatus.RECONCILIATION_REQUIRED, ExecutionStatus.EXECUTION_SUCCEEDED)


def test_execution_state_machine_illegal_transitions():
    """Verify illegal transitions raise InvalidExecutionStateTransitionError."""
    with pytest.raises(InvalidExecutionStateTransitionError):
        ExecutionStateMachine.validate_transition(ExecutionStatus.EXECUTION_SUCCEEDED, ExecutionStatus.NOT_EXECUTED)

    with pytest.raises(InvalidExecutionStateTransitionError):
        ExecutionStateMachine.validate_transition(ExecutionStatus.EXECUTION_SUCCEEDED, ExecutionStatus.EXECUTION_FAILED)

    with pytest.raises(InvalidExecutionStateTransitionError):
        ExecutionStateMachine.validate_transition(ExecutionStatus.CANCELLED, ExecutionStatus.EXECUTION_SUCCEEDED)


def test_sandbox_provider_idempotency_and_timeout():
    """Verify SandboxPaymentProvider handles duplicate execution requests and simulated timeouts cleanly."""
    provider = SandboxPaymentProvider()
    req_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    idem_key = "idem-test-123"
    params = {"amount": "50.00", "currency": "USD", "beneficiary_id": "BEN-999"}

    res1 = provider.execute(req_id, params, idem_key, tenant_id=tenant_id)
    assert res1.status == ExecutionStatus.EXECUTION_SUCCEEDED

    # Duplicate execution attempt returns DUPLICATE status
    res2 = provider.execute(req_id, params, idem_key, tenant_id=tenant_id)
    assert res2.status == ExecutionStatus.DUPLICATE
    assert res2.execution_id == res1.execution_id

    # Simulated timeout request
    timeout_params = {**params, "force_timeout": True}
    res_timeout = provider.execute(uuid.uuid4(), timeout_params, "idem-timeout-1", tenant_id=tenant_id)
    assert res_timeout.status == ExecutionStatus.TIMEOUT


def test_webhook_signature_verification_and_replay_protection():
    """Verify WebhookSecurityHandler signature verification and timestamp replay protection."""
    handler = WebhookSecurityHandler(max_skew_seconds=300)
    secret = "whsec_test_secret_12345"
    raw_body = b'{"event":"payment_cleared","tenant_id":"00000000-0000-0000-0000-000000000001"}'

    # Compute valid signature
    sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    # Valid signature passes
    assert handler.verify_signature(raw_body, sig, secret) is True

    # Tampered body fails signature check
    tampered_body = b'{"event":"payment_cleared","amount":"999999.00"}'
    with pytest.raises(WebhookSignatureVerificationError):
        handler.verify_signature(tampered_body, sig, secret)

    # Valid current timestamp passes
    assert handler.validate_timestamp(time.time()) is True

    # Replay attack (> 300 seconds old) fails
    old_timestamp = time.time() - 600
    with pytest.raises(WebhookTimestampExpiredError):
        handler.validate_timestamp(old_timestamp)


def test_webhook_deduplication_and_cross_tenant_binding():
    """Verify WebhookSecurityHandler deduplicates event IDs and enforces tenant binding."""
    handler = WebhookSecurityHandler()
    tenant_1 = uuid.UUID("00000000-0000-0000-0000-000000000001")
    tenant_2 = uuid.UUID("00000000-0000-0000-0000-000000000002")
    event_id = "evt_tx_1001"

    # First event processing succeeds
    assert handler.deduplicate_event(event_id, tenant_1) is True

    # Reused event ID for same tenant fails
    with pytest.raises(WebhookDuplicateEventError):
        handler.deduplicate_event(event_id, tenant_1)

    # Cross-tenant payload binding mismatch fails
    payload = {"status": "EXECUTION_SUCCEEDED", "tenant_id": str(tenant_2)}
    with pytest.raises(WebhookTenantBindingError):
        handler.bind_and_process(payload, trusted_tenant_id=tenant_1, current_state=ExecutionState.SUBMITTED)
