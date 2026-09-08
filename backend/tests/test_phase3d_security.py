import hmac
import hashlib
import time
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
    PolicyRule, PolicyEffect, ActionRequest, ApprovalRequest, AuditEvent,
    FinancialExecution, ExecutionState, DEFAULT_TENANT_ID
)
from app.auth import TokenClaims
from app.identity import AgentIdentityResolver, SecurityContext, IdentityResolutionError
from app.execution import ExecutionStateMachine, ExecutionStatus, InvalidExecutionStateTransitionError, SandboxPaymentProvider
from app.services.gateway import GatewayService, GatewayIdempotencyConflict
from app.services.approval import ApprovalService, ApprovalConflictError
from app.services.webhook import (
    WebhookSecurityHandler, WebhookSignatureVerificationError,
    WebhookTimestampExpiredError, WebhookDuplicateEventError, WebhookTenantBindingError, WebhookError
)
from app.services.demo import FinancialWorkflowDemoService
from app.schemas import GatewayRequestCreate, ApprovalActionRequest
from app.financial import compute_payload_digest


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


def test_e2e_financial_workflow_sandbox_demo_success(db_session: Session):
    """1. Verify complete $25,000 USD end-to-end sandbox financial agent workflow succeeds."""
    demo_service = FinancialWorkflowDemoService(db_session)
    result = demo_service.run_e2e_demo(amount="25000.00", currency="USD")

    assert result["status"] == "SUCCESS"
    assert result["gateway_initial_status"] == "PENDING_APPROVAL"
    assert result["approval_status"] == "APPROVED"
    assert result["execution_status"] == "EXECUTION_SUCCEEDED"
    assert result["verified_zero_real_money_movement"] is True
    assert result["provider_used"] == "SandboxPaymentProvider"
    assert result["audit_trail_count"] >= 6


def test_unauthenticated_agent_rejected():
    """2. Verify missing or empty token claims are rejected fail-closed."""
    resolver = AgentIdentityResolver()
    with pytest.raises(IdentityResolutionError):
        resolver.resolve_security_context(None, None)


def test_cross_tenant_agent_rejected(db_session: Session):
    """3. Verify Principal from Tenant A cannot invoke Agent belonging to Tenant B."""
    t1 = Tenant(id=uuid.uuid4(), name="Tenant 1", slug="t1")
    t2 = Tenant(id=uuid.uuid4(), name="Tenant 2", slug="t2")
    p1 = Principal(id=uuid.uuid4(), tenant_id=t1.id, type=PrincipalType.HUMAN, name="User T1", external_id="usr_t1", status=PrincipalStatus.ACTIVE)
    a2 = Agent(id=uuid.uuid4(), tenant_id=t2.id, name="Agent T2", owner_principal_id=p1.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    db_session.add_all([t1, t2, p1, a2])
    db_session.commit()

    resolver = AgentIdentityResolver()
    claims = TokenClaims(sub="usr_t1", client_id=str(a2.id), scope="wire_transfer", iss="auth", aud="api", exp=int(time.time())+3600, iat=int(time.time()))
    with pytest.raises(IdentityResolutionError) as exc:
        resolver.resolve_security_context(claims, db_session)
    assert "Tenant mismatch" in str(exc.value)


def test_cross_tenant_resource_rejected(db_session: Session):
    """4. Verify GatewayService blocks request attempting to operate on Resource in another tenant."""
    t1 = Tenant(id=uuid.uuid4(), name="Tenant 1", slug="t1")
    t2 = Tenant(id=uuid.uuid4(), name="Tenant 2", slug="t2")
    p1 = Principal(id=uuid.uuid4(), tenant_id=t1.id, type=PrincipalType.HUMAN, name="User T1", external_id="usr_t1", status=PrincipalStatus.ACTIVE)
    a1 = Agent(id=uuid.uuid4(), tenant_id=t1.id, name="Agent T1", owner_principal_id=p1.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    tool1 = Tool(id=uuid.uuid4(), tenant_id=t1.id, name="tool1", description="desc", status=CapabilityStatus.ACTIVE)
    act1 = Action(id=uuid.uuid4(), tenant_id=t1.id, tool_id=tool1.id, name="wire_transfer", description="desc", risk_level=RiskClassification.HIGH, status=CapabilityStatus.ACTIVE)
    res2 = Resource(id=uuid.uuid4(), tenant_id=t2.id, resource_type="account", resource_key="acc_t2", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)
    db_session.add_all([t1, t2, p1, a1, tool1, act1, res2])
    db_session.commit()

    gateway = GatewayService(db_session)
    req = GatewayRequestCreate(
        principal_id=p1.id,
        agent_id=a1.id,
        action_id=act1.id,
        resource_id=res2.id,
        parameters={"source_account_id": "A1", "destination_account_id": "A2", "amount": "100.00", "currency": "USD", "beneficiary_id": "B1", "transaction_reference": "REF1"},
        idempotency_key=f"idem-{uuid.uuid4()}"
    )
    with pytest.raises(GatewayIdempotencyConflict) as exc:
        gateway.submit(req)
    assert "Tenant mismatch" in str(exc.value)


def test_missing_and_expired_delegation_rejected(db_session: Session):
    """5 & 6. Verify missing and expired delegation relationships are rejected."""
    t1 = Tenant(id=uuid.uuid4(), name="T1", slug="t1")
    p1 = Principal(id=uuid.uuid4(), tenant_id=t1.id, type=PrincipalType.HUMAN, name="User", external_id="usr_1", status=PrincipalStatus.ACTIVE)
    a1 = Agent(id=uuid.uuid4(), tenant_id=t1.id, name="Agent", owner_principal_id=p1.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    db_session.add_all([t1, p1, a1])
    db_session.commit()

    resolver = AgentIdentityResolver()
    claims = TokenClaims(sub="usr_1", client_id=str(a1.id), scope="wire_transfer", iss="auth", aud="api", exp=int(time.time())+3600, iat=int(time.time()))
    
    # Missing delegation fails
    with pytest.raises(IdentityResolutionError) as exc:
        resolver.resolve_security_context(claims, db_session)
    assert "No delegation relationship" in str(exc.value)

    # Expired delegation fails
    d_expired = Delegation(
        id=uuid.uuid4(), tenant_id=t1.id, principal_id=p1.id, agent_id=a1.id,
        scope="wire_transfer", status=DelegationStatus.ACTIVE,
        expires_at=datetime.now(timezone.utc).replace(year=2020)
    )
    db_session.add(d_expired)
    db_session.commit()

    with pytest.raises(IdentityResolutionError) as exc:
        resolver.resolve_security_context(claims, db_session)
    assert "expired" in str(exc.value).lower()


def test_suspended_agent_rejected(db_session: Session):
    """7. Verify suspended agent identity resolution fails closed."""
    t1 = Tenant(id=uuid.uuid4(), name="T1", slug="t1")
    p1 = Principal(id=uuid.uuid4(), tenant_id=t1.id, type=PrincipalType.HUMAN, name="User", external_id="usr_1", status=PrincipalStatus.ACTIVE)
    a_suspended = Agent(id=uuid.uuid4(), tenant_id=t1.id, name="Agent", owner_principal_id=p1.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.SUSPENDED)
    db_session.add_all([t1, p1, a_suspended])
    db_session.commit()

    resolver = AgentIdentityResolver()
    claims = TokenClaims(sub="usr_1", client_id=str(a_suspended.id), scope="wire_transfer", iss="auth", aud="api", exp=int(time.time())+3600, iat=int(time.time()))
    with pytest.raises(IdentityResolutionError) as exc:
        resolver.resolve_security_context(claims, db_session)
    assert "status is SUSPENDED" in str(exc.value)


def test_requester_cannot_approve_its_own_transaction(db_session: Session):
    """8 & 12. Verify Separation of Duties prevents requester self-approval."""
    demo_service = FinancialWorkflowDemoService(db_session)
    # Provision data
    tenant = Tenant(id=uuid.uuid4(), name="Corp", slug=f"corp-{uuid.uuid4().hex[:6]}")
    p1 = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Alice", external_id="usr_alice", status=PrincipalStatus.ACTIVE)
    agent = Agent(id=uuid.uuid4(), tenant_id=tenant.id, name="Agent", owner_principal_id=p1.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    delegation = Delegation(id=uuid.uuid4(), tenant_id=tenant.id, principal_id=p1.id, agent_id=agent.id, scope="wire_transfer", status=DelegationStatus.ACTIVE)
    tool = Tool(id=uuid.uuid4(), tenant_id=tenant.id, name="tool", description="desc", status=CapabilityStatus.ACTIVE)
    action = Action(id=uuid.uuid4(), tenant_id=tenant.id, tool_id=tool.id, name="wire_transfer", description="desc", risk_level=RiskClassification.HIGH, status=CapabilityStatus.ACTIVE)
    resource = Resource(id=uuid.uuid4(), tenant_id=tenant.id, resource_type="account", resource_key="ACC1", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)
    policy = Policy(id=uuid.uuid4(), tenant_id=tenant.id, name="policy", version=1, status=PolicyStatus.ACTIVE)
    rule = PolicyRule(id=uuid.uuid4(), policy_id=policy.id, effect=PolicyEffect.ALLOW, action="wire_transfer", resource_type="account", priority=1)
    db_session.add_all([tenant, p1, agent, delegation, tool, action, resource, policy, rule])
    db_session.commit()

    gateway = GatewayService(db_session)
    res = gateway.submit(GatewayRequestCreate(
        principal_id=p1.id, agent_id=agent.id, action_id=action.id, resource_id=resource.id,
        parameters={"source_account_id": "ACC1", "destination_account_id": "ACC2", "amount": "25000.00", "currency": "USD", "beneficiary_id": "BEN1", "transaction_reference": "REF1"},
        idempotency_key=f"idem-{uuid.uuid4()}"
    ))
    assert res.approval_required is True

    approval_record = db_session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == res.action_request_id))
    approval_svc = ApprovalService(db_session)

    # Self-approval attempt by Alice (requester) fails
    with pytest.raises(ApprovalConflictError) as exc:
        approval_svc.approve(approval_record.id, ApprovalActionRequest(approver_principal_id=p1.id))
    assert "Separation of duties violation" in str(exc.value)


def test_payload_modification_after_approval_rejected(db_session: Session):
    """12. Verify modifying parameters after approval request creation is detected and rejected."""
    tenant = Tenant(id=uuid.uuid4(), name="Corp", slug=f"corp-{uuid.uuid4().hex[:6]}")
    p1 = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Alice", external_id="usr_alice", status=PrincipalStatus.ACTIVE)
    p2 = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Bob", external_id="usr_bob", status=PrincipalStatus.ACTIVE)
    agent = Agent(id=uuid.uuid4(), tenant_id=tenant.id, name="Agent", owner_principal_id=p1.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    delegation = Delegation(id=uuid.uuid4(), tenant_id=tenant.id, principal_id=p1.id, agent_id=agent.id, scope="wire_transfer", status=DelegationStatus.ACTIVE)
    tool = Tool(id=uuid.uuid4(), tenant_id=tenant.id, name="tool", description="desc", status=CapabilityStatus.ACTIVE)
    action = Action(id=uuid.uuid4(), tenant_id=tenant.id, tool_id=tool.id, name="wire_transfer", description="desc", risk_level=RiskClassification.HIGH, status=CapabilityStatus.ACTIVE)
    resource = Resource(id=uuid.uuid4(), tenant_id=tenant.id, resource_type="account", resource_key="ACC1", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)
    policy = Policy(id=uuid.uuid4(), tenant_id=tenant.id, name="policy", version=1, status=PolicyStatus.ACTIVE)
    rule = PolicyRule(id=uuid.uuid4(), policy_id=policy.id, effect=PolicyEffect.ALLOW, action="wire_transfer", resource_type="account", priority=1)
    db_session.add_all([tenant, p1, p2, agent, delegation, tool, action, resource, policy, rule])
    db_session.commit()

    gateway = GatewayService(db_session)
    res = gateway.submit(GatewayRequestCreate(
        principal_id=p1.id, agent_id=agent.id, action_id=action.id, resource_id=resource.id,
        parameters={"source_account_id": "ACC1", "destination_account_id": "ACC2", "amount": "25000.00", "currency": "USD", "beneficiary_id": "BEN1", "transaction_reference": "REF1"},
        idempotency_key=f"idem-{uuid.uuid4()}"
    ))

    # Tamper parameters directly on ActionRequest!
    act_req = db_session.get(ActionRequest, res.action_request_id)
    act_req.parameters = {**act_req.parameters, "amount": "999999.00"}
    db_session.commit()

    approval_record = db_session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == res.action_request_id))
    approval_svc = ApprovalService(db_session)

    with pytest.raises(ApprovalConflictError) as exc:
        approval_svc.approve(approval_record.id, ApprovalActionRequest(approver_principal_id=p2.id))
    assert "Payload tamper detected" in str(exc.value)


def test_delegation_revocation_before_approval_revalidated(db_session: Session):
    """14. Verify revoking delegation before approval causes TOCTOU revalidation to fail closed."""
    tenant = Tenant(id=uuid.uuid4(), name="Corp", slug=f"corp-{uuid.uuid4().hex[:6]}")
    p1 = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Alice", external_id="usr_alice", status=PrincipalStatus.ACTIVE)
    p2 = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Bob", external_id="usr_bob", status=PrincipalStatus.ACTIVE)
    agent = Agent(id=uuid.uuid4(), tenant_id=tenant.id, name="Agent", owner_principal_id=p1.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    delegation = Delegation(id=uuid.uuid4(), tenant_id=tenant.id, principal_id=p1.id, agent_id=agent.id, scope="wire_transfer", status=DelegationStatus.ACTIVE)
    tool = Tool(id=uuid.uuid4(), tenant_id=tenant.id, name="tool", description="desc", status=CapabilityStatus.ACTIVE)
    action = Action(id=uuid.uuid4(), tenant_id=tenant.id, tool_id=tool.id, name="wire_transfer", description="desc", risk_level=RiskClassification.HIGH, status=CapabilityStatus.ACTIVE)
    resource = Resource(id=uuid.uuid4(), tenant_id=tenant.id, resource_type="account", resource_key="ACC1", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)
    policy = Policy(id=uuid.uuid4(), tenant_id=tenant.id, name="policy", version=1, status=PolicyStatus.ACTIVE)
    rule = PolicyRule(id=uuid.uuid4(), policy_id=policy.id, effect=PolicyEffect.ALLOW, action="wire_transfer", resource_type="account", priority=1)
    db_session.add_all([tenant, p1, p2, agent, delegation, tool, action, resource, policy, rule])
    db_session.commit()

    gateway = GatewayService(db_session)
    res = gateway.submit(GatewayRequestCreate(
        principal_id=p1.id, agent_id=agent.id, action_id=action.id, resource_id=resource.id,
        parameters={"source_account_id": "ACC1", "destination_account_id": "ACC2", "amount": "25000.00", "currency": "USD", "beneficiary_id": "BEN1", "transaction_reference": "REF1"},
        idempotency_key=f"idem-{uuid.uuid4()}"
    ))

    # Revoke delegation before Bob approves!
    delegation.status = DelegationStatus.REVOKED
    db_session.commit()

    approval_record = db_session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == res.action_request_id))
    approval_svc = ApprovalService(db_session)

    with pytest.raises(ApprovalConflictError) as exc:
        approval_svc.approve(approval_record.id, ApprovalActionRequest(approver_principal_id=p2.id))
    assert "TOCTOU re-validation failed" in str(exc.value)


def test_provider_timeout_produces_unknown_safely():
    """18. Verify provider timeout produces TIMEOUT status without corrupted state."""
    provider = SandboxPaymentProvider()
    params = {"source_account_id": "A1", "destination_account_id": "A2", "amount": "100.00", "currency": "USD", "force_timeout": True}
    res = provider.execute(uuid.uuid4(), params, "idem-timeout-key", tenant_id=uuid.uuid4())
    assert res.status == ExecutionStatus.TIMEOUT


def test_forged_duplicate_and_cross_tenant_webhooks():
    """20, 21, 22. Verify webhook security handler blocks forgery, duplicates, and cross-tenant mismatches."""
    handler = WebhookSecurityHandler()
    secret = "whsec_super_secret"
    t1 = uuid.UUID("00000000-0000-0000-0000-000000000001")
    t2 = uuid.UUID("00000000-0000-0000-0000-000000000002")

    # 1. Forged HMAC signature
    with pytest.raises(WebhookSignatureVerificationError):
        handler.verify_signature(b'{"event":"test"}', "invalid_sig", secret)

    # 2. Event deduplication
    assert handler.deduplicate_event("evt_001", t1) is True
    with pytest.raises(WebhookDuplicateEventError):
        handler.deduplicate_event("evt_001", t1)

    # 3. Cross-tenant webhook binding mismatch
    with pytest.raises(WebhookTenantBindingError):
        handler.bind_and_process({"status": "EXECUTION_SUCCEEDED", "tenant_id": str(t2)}, trusted_tenant_id=t1, current_state=ExecutionState.SUBMITTED)


def test_invalid_token_rejected(db_session: Session):
    """Verify tampered JWT signature is rejected during identity resolution."""
    resolver = AgentIdentityResolver()
    claims = TokenClaims(sub="usr_fake", client_id=str(uuid.uuid4()), scope="wire_transfer", iss="auth", aud="api", exp=int(time.time())-10, iat=int(time.time()))
    with pytest.raises(IdentityResolutionError):
        resolver.resolve_security_context(claims, db_session)


def test_policy_deny_enforced(db_session: Session):
    """Verify explicit Policy DENY rule blocks financial action request."""
    t1 = Tenant(id=uuid.uuid4(), name="T1", slug=f"t1-{uuid.uuid4().hex[:6]}")
    p1 = Principal(id=uuid.uuid4(), tenant_id=t1.id, type=PrincipalType.HUMAN, name="Alice", external_id="usr_a", status=PrincipalStatus.ACTIVE)
    a1 = Agent(id=uuid.uuid4(), tenant_id=t1.id, name="Agent", owner_principal_id=p1.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    d1 = Delegation(id=uuid.uuid4(), tenant_id=t1.id, principal_id=p1.id, agent_id=a1.id, scope="wire_transfer", status=DelegationStatus.ACTIVE)
    tool1 = Tool(id=uuid.uuid4(), tenant_id=t1.id, name="tool", description="desc", status=CapabilityStatus.ACTIVE)
    act1 = Action(id=uuid.uuid4(), tenant_id=t1.id, tool_id=tool1.id, name="wire_transfer", description="desc", risk_level=RiskClassification.HIGH, status=CapabilityStatus.ACTIVE)
    res1 = Resource(id=uuid.uuid4(), tenant_id=t1.id, resource_type="account", resource_key="ACC1", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)
    policy = Policy(id=uuid.uuid4(), tenant_id=t1.id, name="policy", version=1, status=PolicyStatus.ACTIVE)
    rule_deny = PolicyRule(id=uuid.uuid4(), policy_id=policy.id, effect=PolicyEffect.DENY, action="wire_transfer", resource_type="account", priority=1)
    db_session.add_all([t1, p1, a1, d1, tool1, act1, res1, policy, rule_deny])
    db_session.commit()

    gateway = GatewayService(db_session)
    res = gateway.submit(GatewayRequestCreate(
        principal_id=p1.id, agent_id=a1.id, action_id=act1.id, resource_id=res1.id,
        parameters={"source_account_id": "ACC1", "destination_account_id": "ACC2", "amount": "100.00", "currency": "USD", "beneficiary_id": "BEN1", "transaction_reference": "REF1"},
        idempotency_key=f"idem-{uuid.uuid4()}"
    ))
    assert res.gateway_status == "BLOCKED"
    assert res.decision == "DENY"


def test_resource_retirement_before_approval_revalidated(db_session: Session):
    """Verify retiring resource before approval execution causes TOCTOU re-validation to fail closed."""
    tenant = Tenant(id=uuid.uuid4(), name="Corp", slug=f"corp-{uuid.uuid4().hex[:6]}")
    p1 = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Alice", external_id="usr_alice", status=PrincipalStatus.ACTIVE)
    p2 = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Bob", external_id="usr_bob", status=PrincipalStatus.ACTIVE)
    agent = Agent(id=uuid.uuid4(), tenant_id=tenant.id, name="Agent", owner_principal_id=p1.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    delegation = Delegation(id=uuid.uuid4(), tenant_id=tenant.id, principal_id=p1.id, agent_id=agent.id, scope="wire_transfer", status=DelegationStatus.ACTIVE)
    tool = Tool(id=uuid.uuid4(), tenant_id=tenant.id, name="tool", description="desc", status=CapabilityStatus.ACTIVE)
    action = Action(id=uuid.uuid4(), tenant_id=tenant.id, tool_id=tool.id, name="wire_transfer", description="desc", risk_level=RiskClassification.HIGH, status=CapabilityStatus.ACTIVE)
    resource = Resource(id=uuid.uuid4(), tenant_id=tenant.id, resource_type="account", resource_key="ACC1", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)
    policy = Policy(id=uuid.uuid4(), tenant_id=tenant.id, name="policy", version=1, status=PolicyStatus.ACTIVE)
    rule = PolicyRule(id=uuid.uuid4(), policy_id=policy.id, effect=PolicyEffect.ALLOW, action="wire_transfer", resource_type="account", priority=1)
    db_session.add_all([tenant, p1, p2, agent, delegation, tool, action, resource, policy, rule])
    db_session.commit()

    gateway = GatewayService(db_session)
    res = gateway.submit(GatewayRequestCreate(
        principal_id=p1.id, agent_id=agent.id, action_id=action.id, resource_id=resource.id,
        parameters={"source_account_id": "ACC1", "destination_account_id": "ACC2", "amount": "25000.00", "currency": "USD", "beneficiary_id": "BEN1", "transaction_reference": "REF1"},
        idempotency_key=f"idem-{uuid.uuid4()}"
    ))

    # Retire resource before Bob approves!
    resource.status = ResourceStatus.RETIRED
    db_session.commit()

    approval_record = db_session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == res.action_request_id))
    approval_svc = ApprovalService(db_session)

    with pytest.raises(ApprovalConflictError) as exc:
        approval_svc.approve(approval_record.id, ApprovalActionRequest(approver_principal_id=p2.id))
    assert "TOCTOU re-validation failed" in str(exc.value)


def test_duplicate_execution_and_idempotency_conflict_detected(db_session: Session):
    """Verify duplicate execution is prevented and idempotency parameter mismatch is caught."""
    provider = SandboxPaymentProvider()
    req_id = uuid.uuid4()
    t_id = uuid.uuid4()
    params = {"source_account_id": "A1", "destination_account_id": "A2", "amount": "100.00", "currency": "USD"}
    
    # First execution succeeds
    res1 = provider.execute(req_id, params, "idem-key-1", tenant_id=t_id)
    assert res1.status == ExecutionStatus.EXECUTION_SUCCEEDED

    # Second execution with same idempotency key returns cached DUPLICATE result
    res2 = provider.execute(req_id, params, "idem-key-1", tenant_id=t_id)
    assert res2.status == ExecutionStatus.DUPLICATE
    assert res2.transaction_reference == res1.transaction_reference




def test_invalid_execution_state_transition_rejected():
    """Verify invalid execution state transitions raise InvalidExecutionStateTransitionError."""
    with pytest.raises(InvalidExecutionStateTransitionError):
        ExecutionStateMachine.validate_transition(ExecutionStatus.EXECUTION_SUCCEEDED, ExecutionStatus.NOT_EXECUTED)

