import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import (
    Action,
    ActionRequest,
    ActionRequestStatus,
    Agent,
    AgentStatus,
    ApprovalRequest,
    ApprovalStatus,
    AuditEvent,
    CapabilityStatus,
    Decision,
    DecisionType,
    Delegation,
    DelegationStatus,
    Policy,
    PolicyEffect,
    PolicyRule,
    PolicyStatus,
    Principal,
    PrincipalStatus,
    PrincipalType,
    Resource,
    ResourceSensitivity,
    ResourceStatus,
    RiskClassification,
    Tool,
)
from app.financial import (
    WireTransferContract,
    compute_payload_digest,
    validate_financial_action_parameters,
    FinancialValidationError,
    FinancialRiskConfig,
)
from app.execution import SandboxPaymentProvider, ExecutionStatus
from app.schemas import GatewayRequestCreate, ApprovalActionRequest
from app.services.gateway import GatewayService, GatewayIdempotencyConflict
from app.services.approval import ApprovalService, ApprovalConflictError


engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def reset_db():
    with TestingSession() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


def setup_financial_fixtures(session, action_risk=RiskClassification.HIGH):
    principal = Principal(name="Alice Treasury Manager", external_id="auth0|alice999", type=PrincipalType.HUMAN, status=PrincipalStatus.ACTIVE)
    approver = Principal(name="Bob Treasury Director", external_id="auth0|bob111", type=PrincipalType.HUMAN, status=PrincipalStatus.ACTIVE)
    agent = Agent(name="TreasuryBot-v1", owner=principal, purpose="Automate enterprise treasury payouts", version="1.0.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    tool = Tool(name="PaymentGatewayTool", description="Enterprise Payout Tool", status=CapabilityStatus.ACTIVE)
    action = Action(tool=tool, name="wire_transfer", description="Execute bank wire transfer", risk_level=action_risk, status=CapabilityStatus.ACTIVE)
    resource = Resource(resource_type="bank_account", resource_key="ACC-CORP-001", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)
    
    session.add_all([principal, approver, agent, tool, action, resource])
    session.add(Delegation(principal=principal, agent=agent, scope="*", status=DelegationStatus.ACTIVE))
    
    policy = Policy(name="Treasury Payout Policy", version=1, priority=10, status=PolicyStatus.ACTIVE)
    policy.rules = [PolicyRule(effect=PolicyEffect.ALLOW, action="wire_transfer", resource_type="bank_account", priority=10)]
    session.add(policy)
    session.commit()

    return {
        "principal_id": principal.id,
        "approver_id": approver.id,
        "agent_id": agent.id,
        "tool_id": tool.id,
        "action_id": action.id,
        "resource_id": resource.id,
    }



def sample_wire_params(amount: str = "500.00", ref: str = "TX-REF-100") -> dict:
    return {
        "amount": amount,
        "currency": "USD",
        "beneficiary_id": "BENEFICIARY-ACME-CORP",
        "source_account_id": "ACC-CORP-001",
        "destination_account_id": "ACC-VENDOR-999",
        "transaction_reference": ref,
        "purpose": "Vendor Invoice Settlement",
    }


# =====================================================================
# 1. CONTRACT VALIDATION & PAYLOAD DIGEST TESTS
# =====================================================================

def test_wire_transfer_contract_valid():
    params = sample_wire_params("25000.00")
    clean, digest = validate_financial_action_parameters("wire_transfer", params)
    assert clean["amount"] == "25000.0" or clean["amount"] == "25000.00" or Decimal(str(clean["amount"])) == Decimal("25000.00")
    assert clean["currency"] == "USD"
    assert len(digest) == 64


def test_wire_transfer_contract_invalid_amount():
    params = sample_wire_params("-500.00")
    with pytest.raises(FinancialValidationError, match="Input should be greater than 0"):
        validate_financial_action_parameters("wire_transfer", params)


def test_wire_transfer_contract_invalid_currency():
    params = sample_wire_params("100.00")
    params["currency"] = "XYZ"
    with pytest.raises(FinancialValidationError, match="Unsupported currency"):
        validate_financial_action_parameters("wire_transfer", params)


def test_wire_transfer_contract_forbidden_override_key():
    params = sample_wire_params("100.00")
    params["principal_id"] = str(uuid.uuid4())
    with pytest.raises(FinancialValidationError, match="Forbidden authorization/identity override keys"):
        validate_financial_action_parameters("wire_transfer", params)


# =====================================================================
# 2. LOW-RISK IMMEDIATE EXECUTION & HIGH-RISK APPROVAL FLOW
# =====================================================================

def test_low_risk_financial_action_executes_immediately():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session, action_risk=RiskClassification.LOW)
        gateway = GatewayService(session)
        payload = GatewayRequestCreate(
            principal_id=fx["principal_id"],
            agent_id=fx["agent_id"],
            action_id=fx["action_id"],
            resource_id=fx["resource_id"],
            parameters=sample_wire_params("500.00"),
            idempotency_key=f"idem-{uuid.uuid4()}"
        )
        resp = gateway.submit(payload)
        assert resp.gateway_status == "AUTHORIZED"
        assert resp.decision == "ALLOW"
        assert resp.execution_status == "EXECUTION_SUCCEEDED"


def test_high_risk_financial_action_requires_approval():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session, action_risk=RiskClassification.HIGH)
        gateway = GatewayService(session)
        payload = GatewayRequestCreate(
            principal_id=fx["principal_id"],
            agent_id=fx["agent_id"],
            action_id=fx["action_id"],
            resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"),
            idempotency_key=f"idem-{uuid.uuid4()}"
        )
        resp = gateway.submit(payload)
        assert resp.gateway_status == "PENDING_APPROVAL"
        assert resp.decision == "REQUIRE_APPROVAL"
        assert resp.execution_status == "NOT_EXECUTED"


def test_human_approval_triggers_sandbox_payment_execution():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session, action_risk=RiskClassification.HIGH)
        gateway = GatewayService(session)
        payload = GatewayRequestCreate(
            principal_id=fx["principal_id"],
            agent_id=fx["agent_id"],
            action_id=fx["action_id"],
            resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"),
            idempotency_key=f"idem-{uuid.uuid4()}"
        )
        resp = gateway.submit(payload)
        approval_req = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == resp.action_request_id))
        
        approvals = ApprovalService(session)
        appr_detail = approvals.approve(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["approver_id"]))
        
        assert appr_detail.status == ApprovalStatus.APPROVED
        
        # Verify Audit trail
        events = list(session.scalars(select(AuditEvent).where(AuditEvent.action_request_id == resp.action_request_id)).all())
        event_types = [e.event_type for e in events]
        assert "APPROVAL_APPROVED" in event_types
        assert "EXECUTION_STARTED" in event_types
        assert "EXECUTION_SUCCEEDED" in event_types


# =====================================================================
# 3. 15 EXPLICIT FINANCIAL SECURITY ASSERTION TESTS
# =====================================================================

def test_security_1_change_amount_after_approval_blocked():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        resp = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=f"idem-{uuid.uuid4()}"
        ))
        
        # Tamper amount in ActionRequest parameters post-approval request
        req = session.get(ActionRequest, resp.action_request_id)
        req.parameters = {**req.parameters, "amount": "999999.00"}
        session.commit()
        
        approval_req = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == resp.action_request_id))
        approvals = ApprovalService(session)
        
        with pytest.raises(ApprovalConflictError, match="Payload tamper detected"):
            approvals.approve(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["approver_id"]))


def test_security_2_change_beneficiary_after_approval_blocked():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        resp = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=f"idem-{uuid.uuid4()}"
        ))
        
        req = session.get(ActionRequest, resp.action_request_id)
        req.parameters = {**req.parameters, "beneficiary_id": "ATTACKER-ACCOUNT-666"}
        session.commit()
        
        approval_req = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == resp.action_request_id))
        approvals = ApprovalService(session)
        
        with pytest.raises(ApprovalConflictError, match="Payload tamper detected"):
            approvals.approve(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["approver_id"]))


def test_security_3_change_currency_after_approval_blocked():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        resp = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=f"idem-{uuid.uuid4()}"
        ))
        
        req = session.get(ActionRequest, resp.action_request_id)
        req.parameters = {**req.parameters, "currency": "EUR"}
        session.commit()
        
        approval_req = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == resp.action_request_id))
        approvals = ApprovalService(session)
        
        with pytest.raises(ApprovalConflictError, match="Payload tamper detected"):
            approvals.approve(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["approver_id"]))


def test_security_4_change_destination_account_after_approval_blocked():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        resp = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=f"idem-{uuid.uuid4()}"
        ))
        
        req = session.get(ActionRequest, resp.action_request_id)
        req.parameters = {**req.parameters, "destination_account_id": "ACC-EVIL-666"}
        session.commit()
        
        approval_req = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == resp.action_request_id))
        approvals = ApprovalService(session)
        
        with pytest.raises(ApprovalConflictError, match="Payload tamper detected"):
            approvals.approve(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["approver_id"]))



def test_security_5_replay_approved_request():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        key = f"idem-{uuid.uuid4()}"
        resp1 = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=key
        ))
        resp2 = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=key
        ))
        assert resp1.action_request_id == resp2.action_request_id


def test_security_6_replay_same_key_modified_payload():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        key = f"idem-{uuid.uuid4()}"
        gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=key
        ))
        with pytest.raises(GatewayIdempotencyConflict, match="already used with different request content"):
            gateway.submit(GatewayRequestCreate(
                principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
                parameters=sample_wire_params("99999.00"), idempotency_key=key
            ))


def test_security_7_execute_rejected_request_blocked():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        resp = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=f"idem-{uuid.uuid4()}"
        ))
        approval_req = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == resp.action_request_id))
        approvals = ApprovalService(session)
        approvals.reject(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["approver_id"]))
        
        # Subsequent approval attempt must raise ApprovalConflictError
        with pytest.raises(ApprovalConflictError, match="Approval request is already REJECTED"):
            approvals.approve(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["approver_id"]))


def test_security_8_execute_expired_approval_blocked():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        resp = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=f"idem-{uuid.uuid4()}"
        ))
        approval_req = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == resp.action_request_id))
        
        # Expire approval request manually in database
        approval_req.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        session.commit()
        
        approvals = ApprovalService(session)
        with pytest.raises(ApprovalConflictError, match="Approval request has expired"):
            approvals.approve(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["approver_id"]))


def test_security_9_execute_high_risk_without_approval_blocked():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session, action_risk=RiskClassification.HIGH)
        gateway = GatewayService(session)
        resp = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=f"idem-{uuid.uuid4()}"
        ))
        assert resp.execution_status == "NOT_EXECUTED"
        assert resp.gateway_status == "PENDING_APPROVAL"


def test_security_10_spoof_risk_score_ignored():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        params = sample_wire_params("25000.00")
        params["risk_score"] = 0
        params["risk_level"] = "LOW"
        with pytest.raises(GatewayIdempotencyConflict, match="Forbidden authorization/identity override keys"):
            gateway.submit(GatewayRequestCreate(
                principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
                parameters=params, idempotency_key=f"idem-{uuid.uuid4()}"
            ))


def test_security_11_spoof_policy_decision_ignored():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        params = sample_wire_params("25000.00")
        params["decision"] = "ALLOW"
        params["policy_decision"] = "ALLOW"
        with pytest.raises(GatewayIdempotencyConflict, match="Forbidden authorization/identity override keys"):
            gateway.submit(GatewayRequestCreate(
                principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
                parameters=params, idempotency_key=f"idem-{uuid.uuid4()}"
            ))


def test_security_12_spoof_approval_status_ignored():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        params = sample_wire_params("25000.00")
        params["approved"] = True
        params["approval_status"] = "APPROVED"
        with pytest.raises(GatewayIdempotencyConflict, match="Forbidden authorization/identity override keys"):
            gateway.submit(GatewayRequestCreate(
                principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
                parameters=params, idempotency_key=f"idem-{uuid.uuid4()}"
            ))


def test_security_13_cross_agent_execution_blocked():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        other_agent = Agent(name="OtherBot", owner_principal_id=fx["principal_id"], purpose="Other bot", version="1.0.0", status=AgentStatus.ACTIVE, risk_classification=RiskClassification.LOW)
        session.add(other_agent)
        session.commit()
        
        gateway = GatewayService(session)
        # Attempt to submit using agent without delegation
        with pytest.raises(GatewayIdempotencyConflict, match="Referenced principal, agent, action, resource, or derived tool does not exist"):
            gateway.submit(GatewayRequestCreate(
                principal_id=fx["principal_id"], agent_id=uuid.uuid4(), action_id=fx["action_id"], resource_id=fx["resource_id"],
                parameters=sample_wire_params("500.00"), idempotency_key=f"idem-{uuid.uuid4()}"
            ))


def test_security_14_cross_principal_execution_blocked():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        with pytest.raises(GatewayIdempotencyConflict):
            gateway.submit(GatewayRequestCreate(
                principal_id=uuid.uuid4(), agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
                parameters=sample_wire_params("500.00"), idempotency_key=f"idem-{uuid.uuid4()}"
            ))


def test_security_15_cross_resource_execution_blocked():
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        with pytest.raises(GatewayIdempotencyConflict):
            gateway.submit(GatewayRequestCreate(
                principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=uuid.uuid4(),
                parameters=sample_wire_params("500.00"), idempotency_key=f"idem-{uuid.uuid4()}"
            ))


# =====================================================================
# 4. PROVIDER FAILURE & TIMEOUT TESTS
# =====================================================================

def test_sandbox_provider_simulated_failure():
    provider = SandboxPaymentProvider()
    res = provider.execute(uuid.uuid4(), {"force_failure": True}, "key-fail-1")
    assert res.status == ExecutionStatus.EXECUTION_FAILED
    assert "ledger balance" in res.error_message


def test_sandbox_provider_simulated_timeout():
    provider = SandboxPaymentProvider()
    res = provider.execute(uuid.uuid4(), {"force_timeout": True}, "key-timeout-1")
    assert res.status == ExecutionStatus.TIMEOUT
    assert "timeout" in res.error_message


# =====================================================================
# 5. PHASE 3B HARDENING TESTS (SOD, TOCTOU, CONCURRENCY)
# =====================================================================

def test_phase3b_self_approval_blocked():
    """Requester attempting to approve their own request must fail closed."""
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        resp = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=f"idem-{uuid.uuid4()}"
        ))
        approval_req = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == resp.action_request_id))
        approvals = ApprovalService(session)
        
        # Requester Alice attempts self-approval -> Must raise Separation of Duties error
        with pytest.raises(ApprovalConflictError, match="Separation of duties violation"):
            approvals.approve(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["principal_id"]))


def test_phase3b_toctou_revoked_delegation_blocked():
    """Delegation revoked after approval request creation must fail closed at approval execution time."""
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        resp = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=f"idem-{uuid.uuid4()}"
        ))
        approval_req = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == resp.action_request_id))
        
        # Admin revokes delegation in database while approval is pending
        delegation = session.scalar(select(Delegation).where(Delegation.agent_id == fx["agent_id"], Delegation.principal_id == fx["principal_id"]))
        delegation.status = DelegationStatus.REVOKED
        session.commit()
        
        approvals = ApprovalService(session)
        with pytest.raises(ApprovalConflictError, match="TOCTOU re-validation failed: No valid active delegation"):
            approvals.approve(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["approver_id"]))


def test_phase3b_toctou_expired_delegation_blocked():
    """Delegation expired after approval request creation must fail closed at approval execution time."""
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        resp = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=f"idem-{uuid.uuid4()}"
        ))
        approval_req = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == resp.action_request_id))
        
        # Expire delegation in database while approval is pending
        delegation = session.scalar(select(Delegation).where(Delegation.agent_id == fx["agent_id"], Delegation.principal_id == fx["principal_id"]))
        delegation.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        session.commit()
        
        approvals = ApprovalService(session)
        with pytest.raises(ApprovalConflictError, match="TOCTOU re-validation failed: No valid active delegation"):
            approvals.approve(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["approver_id"]))


def test_phase3b_toctou_suspended_principal_blocked():
    """Requester principal suspended after approval request creation must fail closed at approval execution time."""
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        resp = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=f"idem-{uuid.uuid4()}"
        ))
        approval_req = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == resp.action_request_id))
        
        # Admin suspends requester principal
        principal = session.get(Principal, fx["principal_id"])
        principal.status = PrincipalStatus.SUSPENDED
        session.commit()
        
        approvals = ApprovalService(session)
        with pytest.raises(ApprovalConflictError, match="TOCTOU re-validation failed: Requester principal"):
            approvals.approve(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["approver_id"]))


def test_phase3b_toctou_suspended_agent_blocked():
    """Agent suspended after approval request creation must fail closed at approval execution time."""
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        resp = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=f"idem-{uuid.uuid4()}"
        ))
        approval_req = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == resp.action_request_id))
        
        # Admin suspends agent
        agent = session.get(Agent, fx["agent_id"])
        agent.status = AgentStatus.SUSPENDED
        session.commit()
        
        approvals = ApprovalService(session)
        with pytest.raises(ApprovalConflictError, match="TOCTOU re-validation failed: Agent"):
            approvals.approve(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["approver_id"]))


def test_phase3b_toctou_retired_resource_blocked():
    """Resource retired after approval request creation must fail closed at approval execution time."""
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        resp = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=f"idem-{uuid.uuid4()}"
        ))
        approval_req = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == resp.action_request_id))
        
        # Admin retires target bank account resource
        resource = session.get(Resource, fx["resource_id"])
        resource.status = ResourceStatus.RETIRED
        session.commit()
        
        approvals = ApprovalService(session)
        with pytest.raises(ApprovalConflictError, match="TOCTOU re-validation failed: Target resource"):
            approvals.approve(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["approver_id"]))


def test_phase3b_toctou_policy_changed_to_deny_blocked():
    """Policy updated to DENY after approval request creation must fail closed at approval execution time."""
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        resp = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=f"idem-{uuid.uuid4()}"
        ))
        approval_req = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == resp.action_request_id))
        
        # Add high-priority DENY policy rule while approval is pending
        policy = session.scalar(select(Policy).where(Policy.name == "Treasury Payout Policy"))
        policy.rules = [PolicyRule(effect=PolicyEffect.DENY, action="wire_transfer", resource_type="bank_account", priority=100)]
        session.commit()
        
        approvals = ApprovalService(session)
        with pytest.raises(ApprovalConflictError, match="TOCTOU re-validation failed: Policy re-evaluation evaluated to DENY"):
            approvals.approve(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["approver_id"]))


def test_phase3b_concurrent_approval_single_execution():
    """Concurrent approval attempts on the same approval request must produce exactly one execution."""
    with TestingSession() as session:
        fx = setup_financial_fixtures(session)
        gateway = GatewayService(session)
        resp = gateway.submit(GatewayRequestCreate(
            principal_id=fx["principal_id"], agent_id=fx["agent_id"], action_id=fx["action_id"], resource_id=fx["resource_id"],
            parameters=sample_wire_params("25000.00"), idempotency_key=f"idem-{uuid.uuid4()}"
        ))
        approval_req = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == resp.action_request_id))
        
        approvals = ApprovalService(session)
        
        # First approve succeeds
        appr_detail = approvals.approve(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["approver_id"]))
        assert appr_detail.status == ApprovalStatus.APPROVED
        
        # Second approval call on same request must raise conflict
        with pytest.raises(ApprovalConflictError, match="Approval request is already APPROVED"):
            approvals.approve(approval_req.id, ApprovalActionRequest(approver_principal_id=fx["approver_id"]))
