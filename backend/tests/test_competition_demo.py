from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Action, Agent, ApprovalRequest, Policy, Principal, Resource
from app.schemas import ApprovalActionRequest, GatewayRequestCreate
from app.seed import seed_demo
from app.services.approval import ApprovalService
from app.services.gateway import GatewayService


def demo_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def records(session, agent_name, action_name, resource_key):
    principal = session.scalar(select(Principal).where(Principal.external_id == "demo-admin"))
    agent = session.scalar(select(Agent).where(Agent.name == agent_name))
    action = session.scalar(select(Action).where(Action.name == action_name))
    resource = session.scalar(select(Resource).where(Resource.resource_key == resource_key))
    return principal, agent, action, resource


def test_three_competition_scenarios_are_real_and_deterministic() -> None:
    with demo_session() as session:
        seed_demo(session)
        gateway = GatewayService(session)

        principal, agent, action, resource = records(session, "SalesAgent", "read_customer", "customer_record_001")
        safe = gateway.submit(GatewayRequestCreate(principal_id=principal.id, agent_id=agent.id, action_id=action.id, resource_id=resource.id, idempotency_key="demo-safe", parameters={}))
        assert safe.gateway_status == "AUTHORIZED" and safe.execution_status == "NOT_EXECUTED"

        principal, agent, action, resource = records(session, "ResearchAgent", "read_sensitive_payroll", "payroll_dataset")
        blocked = gateway.submit(GatewayRequestCreate(principal_id=principal.id, agent_id=agent.id, action_id=action.id, resource_id=resource.id, idempotency_key="demo-blocked", parameters={}))
        assert blocked.gateway_status == "BLOCKED" and blocked.reason_code == "POLICY_DENY"
        assert blocked.risk_score is not None and blocked.risk_classification in {"HIGH", "CRITICAL"}
        assert blocked.execution_status == "NOT_EXECUTED"

        principal, agent, action, resource = records(session, "FinanceAgent", "bank_transfer", "bank_account_001")
        approval_result = gateway.submit(GatewayRequestCreate(principal_id=principal.id, agent_id=agent.id, action_id=action.id, resource_id=resource.id, idempotency_key="demo-approval", parameters={"amount": 18000, "currency": "USD"}))
        assert approval_result.gateway_status == "PENDING_APPROVAL"
        pending = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == approval_result.action_request_id))
        approved = ApprovalService(session).approve(pending.id, ApprovalActionRequest(approver_principal_id=principal.id))
        assert approved.status.value == "APPROVED"

        rejection_result = gateway.submit(GatewayRequestCreate(principal_id=principal.id, agent_id=agent.id, action_id=action.id, resource_id=resource.id, idempotency_key=f"demo-reject-{uuid4()}", parameters={"amount": 18000, "currency": "USD"}))
        pending_reject = session.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == rejection_result.action_request_id))
        rejected = ApprovalService(session).reject(pending_reject.id, ApprovalActionRequest(approver_principal_id=principal.id))
        assert rejected.status.value == "REJECTED"
