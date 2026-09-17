from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Action, ActionRequest, Agent, ApprovalRequest, ApprovalStatus, AuditEvent, Decision, DecisionType, Delegation, Policy, PolicyEffect, PolicyRule, Principal, Resource, ResourceSensitivity, RiskClassification, Tool
from app.db.session import get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_db():
    with TestingSession() as session:
        yield session


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    app.dependency_overrides[get_db] = override_db
    with TestingSession() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


def pending_approval(key="approval-key", action_context=None):
    with TestingSession() as session:
        principal = Principal(name="Approval Owner", external_id=str(uuid4()), type="HUMAN")
        approver = Principal(name="Approval Reviewer", external_id=str(uuid4()), type="HUMAN")
        agent = Agent(name=str(uuid4()), owner=principal, purpose="Approval test", version="1", risk_classification=RiskClassification.HIGH)
        tool = Tool(name=str(uuid4()), description="Payments")
        action = Action(tool=tool, name="bank_transfer", description="Transfer", risk_level=RiskClassification.HIGH)
        resource = Resource(resource_type="bank_account", resource_key=str(uuid4()), sensitivity=ResourceSensitivity.HIGH)
        session.add_all([principal, approver, agent, tool, action, resource, Delegation(principal=principal, agent=agent, scope="payments.bank")])
        policy = Policy(name=str(uuid4()), version=1, priority=1, status="ACTIVE")
        policy.rules = [PolicyRule(effect=PolicyEffect.ALLOW, action="bank_transfer", resource_type="bank_account", priority=1)]
        session.add(policy); session.commit()
        ids = {"principal_id": str(principal.id), "agent_id": str(agent.id), "action_id": str(action.id), "resource_id": str(resource.id)}
        approver_id = str(approver.id)
    gateway = client.post("/api/v1/action-requests", json={**ids, "parameters": {"amount": 18000}, "action_context": action_context, "idempotency_key": key})
    assert gateway.status_code == 201 and gateway.json()["gateway_status"] == "PENDING_APPROVAL"
    approval = client.get("/api/v1/approvals").json()[0]
    return ids, approver_id, gateway.json(), approval


def action_payload(principal_id):
    return {"approver_principal_id": principal_id}


def test_gateway_creates_exactly_one_bound_pending_approval() -> None:
    ids, approver_id, gateway, approval = pending_approval()
    retry = client.post("/api/v1/action-requests", json={**ids, "parameters": {"amount": 18000}, "idempotency_key": "approval-key"})
    assert retry.json()["action_request_id"] == gateway["action_request_id"]
    detail = client.get(f"/api/v1/approvals/{approval['id']}").json()
    assert detail["status"] == "PENDING"
    assert detail["action_request_id"] == gateway["action_request_id"]
    assert detail["action_id"] == ids["action_id"] and detail["resource_id"] == ids["resource_id"]
    assert detail["parameters"] == {"amount": 18000}
    assert detail["risk_score"] == gateway["risk_score"]
    with TestingSession() as session:
        assert session.scalar(select(func.count()).select_from(ApprovalRequest)) == 1


def test_approve_creates_final_allow_without_execution() -> None:
    ids, approver_id, gateway, approval = pending_approval()
    result = client.post(f"/api/v1/approvals/{approval['id']}/approve", json=action_payload(approver_id))
    assert result.status_code == 200 and result.json()["status"] == "APPROVED"
    with TestingSession() as session:
        decisions = session.scalars(select(Decision).where(Decision.action_request_id == UUID(gateway["action_request_id"])).order_by(Decision.decided_at)).all()
        assert [item.decision for item in decisions] == [DecisionType.REQUIRE_APPROVAL, DecisionType.ALLOW]
        assert "HUMAN_APPROVAL" in decisions[-1].reason
        assert decisions[-1].risk_score == decisions[0].risk_score
        events = session.scalars(select(AuditEvent).where(AuditEvent.action_request_id == UUID(gateway["action_request_id"]))).all()
        assert "APPROVAL_APPROVED" in [item.event_type for item in events]
        assert all(item.event_data.get("execution_status") != "EXECUTED" for item in events)


@pytest.mark.parametrize(("operation", "expected"), [("reject", ApprovalStatus.REJECTED), ("cancel", ApprovalStatus.CANCELLED)])
def test_reject_and_cancel_create_final_block(operation, expected) -> None:
    ids, approver_id, gateway, approval = pending_approval(f"{operation}-key")
    response = client.post(f"/api/v1/approvals/{approval['id']}/{operation}", json=action_payload(approver_id))
    assert response.json()["status"] == expected.value
    with TestingSession() as session:
        final = session.scalars(select(Decision).where(Decision.action_request_id == UUID(gateway["action_request_id"])).order_by(Decision.decided_at)).all()[-1]
        assert final.decision == DecisionType.BLOCK


def test_expired_approval_cannot_be_approved_or_rejected() -> None:
    ids, approver_id, gateway, approval = pending_approval("expired-key")
    with TestingSession() as session:
        record = session.get(ApprovalRequest, UUID(approval["id"])); record.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1); session.commit()
    first = client.post(f"/api/v1/approvals/{approval['id']}/approve", json=action_payload(approver_id))
    assert first.status_code == 409
    second = client.post(f"/api/v1/approvals/{approval['id']}/reject", json=action_payload(approver_id))
    assert second.status_code == 409
    assert client.get(f"/api/v1/approvals/{approval['id']}").json()["status"] == "EXPIRED"


@pytest.mark.parametrize(("first", "second"), [("approve", "reject"), ("approve", "cancel"), ("reject", "approve")])
def test_only_one_terminal_transition_wins(first, second) -> None:
    ids, approver_id, _, approval = pending_approval(f"race-{first}-{second}")
    assert client.post(f"/api/v1/approvals/{approval['id']}/{first}", json=action_payload(approver_id)).status_code == 200
    assert client.post(f"/api/v1/approvals/{approval['id']}/{second}", json=action_payload(approver_id)).status_code == 409




def test_approval_endpoint_cannot_modify_original_evidence() -> None:
    ids, approver_id, gateway, approval = pending_approval("immutable-key")
    response = client.post(f"/api/v1/approvals/{approval['id']}/approve", json={"approver_principal_id": approver_id, "action_id": str(uuid4()), "risk_score": 0, "decision": "ALLOW"})
    assert response.status_code == 422
    detail = client.get(f"/api/v1/approvals/{approval['id']}").json()

    assert detail["action_id"] == ids["action_id"]
    assert detail["risk_score"] == gateway["risk_score"]
    assert detail["status"] == "PENDING"


def test_approval_rejects_when_payload_bound_action_context_is_tampered() -> None:
    context = {
        "summary": "Apply a $25 account credit for a missed delivery promise",
        "target_system": "support-platform",
        "before": {"account_credit": "0.00"},
        "proposed_change": {"account_credit": "25.00"},
        "recovery_class": "COMPENSATABLE",
        "recovery_plan": "Create an offsetting debit if the credit was issued incorrectly.",
    }
    _, approver_id, gateway, approval = pending_approval("context-tamper-key", action_context=context)
    assert approval["action_context"] == context

    with TestingSession() as session:
        request = session.get(ActionRequest, UUID(gateway["action_request_id"]))
        request.parameters = {
            **request.parameters,
            "_action_context": {**context, "summary": "Apply a $2,500 account credit"},
        }
        session.commit()

    result = client.post(f"/api/v1/approvals/{approval['id']}/approve", json=action_payload(approver_id))
    assert result.status_code == 409
    assert "Payload tamper detected" in result.json()["detail"]


def test_approved_action_returns_provider_receipt_and_declared_recovery_posture() -> None:
    context = {
        "summary": "Apply a $25 account credit for a missed delivery promise",
        "target_system": "support-platform",
        "before": {"account_credit": "0.00"},
        "proposed_change": {"account_credit": "25.00"},
        "recovery_class": "COMPENSATABLE",
        "recovery_plan": "Create an offsetting debit if the credit was issued incorrectly.",
    }
    _, approver_id, _, approval = pending_approval("receipt-key", action_context=context)
    result = client.post(f"/api/v1/approvals/{approval['id']}/approve", json=action_payload(approver_id))
    assert result.status_code == 200
    receipt = result.json()["execution_receipt"]
    assert receipt["status"] == "EXECUTED"
    assert receipt["evidence_status"] == "RECORDED"
    assert receipt["provider_name"] == "SandboxPaymentProvider"
    assert receipt["recovery_status"] == "AVAILABLE"
    assert receipt["recovery_plan"] == context["recovery_plan"]
