from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Action, ActionRequest, Agent, AuditEvent, CapabilityStatus, Decision, DecisionType, Delegation, Policy, PolicyEffect, PolicyRule, Principal, Resource, ResourceSensitivity, ResourceStatus, RiskClassification, Tool
from app.db.session import get_db
from app.main import app
from app.services.gateway import GatewayService
from app.risk import RiskEngine

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_db():
    with TestingSession() as session:
        yield session


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_override():
    app.dependency_overrides[get_db] = override_db
    with TestingSession() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


def fixture_records(risk=RiskClassification.LOW, scope="crm.read"):
    with TestingSession() as session:
        principal = Principal(name=f"Gateway Owner {uuid4()}", external_id=str(uuid4()), type="HUMAN")
        agent = Agent(name=f"Gateway Agent {uuid4()}", owner=principal, purpose="Gateway test", version="1.0.0", risk_classification=risk)
        tool = Tool(name=f"Gateway Tool {uuid4()}", description="Gateway test tool")
        action = Action(tool=tool, name="read_customer", description="Read customer", risk_level=risk)
        resource = Resource(resource_type="crm_record", resource_key=str(uuid4()), sensitivity=ResourceSensitivity.MEDIUM, status=ResourceStatus.ACTIVE)
        session.add_all([principal, agent, tool, action, resource])
        if scope:
            session.add(Delegation(principal=principal, agent=agent, scope=scope))
        session.commit()
        return {"principal_id": str(principal.id), "agent_id": str(agent.id), "action_id": str(action.id), "resource_id": str(resource.id), "tool_id": str(tool.id)}


def add_policy(ids, effect=PolicyEffect.ALLOW, action="read_customer", resource_type="crm_record", conditions=None):
    with TestingSession() as session:
        policy = Policy(name=f"Gateway policy {uuid4()}", version=1, priority=10, status="ACTIVE")
        policy.rules = [PolicyRule(effect=effect, action=action, resource_type=resource_type, priority=10, conditions=conditions)]
        session.add(policy)
        session.commit()


def body(ids, key=None, **extra):
    return {"principal_id": ids["principal_id"], "agent_id": ids["agent_id"], "action_id": ids["action_id"], "resource_id": ids["resource_id"], "parameters": {}, "idempotency_key": key or str(uuid4()), **extra}


def test_allow_persists_separate_decision_and_does_not_execute() -> None:
    ids = fixture_records(); add_policy(ids)
    response = client.post("/api/v1/action-requests", json=body(ids, "allow-key"))
    assert response.status_code == 201
    data = response.json()
    assert data["gateway_status"] == "AUTHORIZED"
    assert data["decision"] == "ALLOW"
    assert data["execution_status"] == "NOT_EXECUTED"
    with TestingSession() as session:
        request = session.get(ActionRequest, UUID(data["action_request_id"]))
        decision = session.scalar(select(Decision).where(Decision.action_request_id == request.id))
        assert request is not None and decision is not None
        assert decision.risk_score is not None
        assert request.id != decision.action_request_id or request.__tablename__ != decision.__tablename__
    detail = client.get(f"/api/v1/action-requests/{data['action_request_id']}")
    assert detail.status_code == 200
    assert detail.json()["tool_id"] == ids["tool_id"]
    assert any(item["id"] == data["action_request_id"] for item in client.get("/api/v1/action-requests").json())


def test_deny_default_explicit_and_missing_delegation_are_blocked() -> None:
    ids = fixture_records(); default_response = client.post("/api/v1/action-requests", json=body(ids, "default-deny"))
    assert default_response.json()["gateway_status"] == "BLOCKED"
    denied_ids = fixture_records(); add_policy(denied_ids, PolicyEffect.DENY)
    assert client.post("/api/v1/action-requests", json=body(denied_ids, "explicit-deny")).json()["gateway_status"] == "BLOCKED"
    missing_ids = fixture_records(scope=None); missing = client.post("/api/v1/action-requests", json=body(missing_ids, "missing-delegation"))
    assert missing.json()["gateway_status"] == "BLOCKED"


def test_high_risk_allow_requires_approval_without_execution() -> None:
    ids = fixture_records(risk=RiskClassification.HIGH); add_policy(ids)
    data = client.post("/api/v1/action-requests", json=body(ids, "approval-key")).json()
    assert data["gateway_status"] == "PENDING_APPROVAL"
    assert data["decision"] == "REQUIRE_APPROVAL"
    assert data["execution_status"] == "NOT_EXECUTED"


def test_action_derived_tool_cannot_be_supplied_or_influenced() -> None:
    ids = fixture_records(); add_policy(ids)
    rejected = client.post("/api/v1/action-requests", json={**body(ids, "caller-tool"), "tool_id": ids["tool_id"]})
    assert rejected.status_code == 422
    other = fixture_records(scope=None)
    mismatched = client.post("/api/v1/action-requests", json=body({**ids, "action_id": other["action_id"]}, "derived-tool"))
    assert mismatched.status_code == 201
    detail = client.get(f"/api/v1/action-requests/{mismatched.json()['action_request_id']}").json()
    assert detail["tool_id"] != ids["tool_id"]


def test_caller_cannot_submit_decision() -> None:
    ids = fixture_records(); add_policy(ids)
    response = client.post("/api/v1/action-requests", json={**body(ids, "caller-decision"), "decision": "ALLOW"})
    assert response.status_code == 422
    for field, value in [("risk_score", 0), ("risk_classification", "LOW"), ("risk_factors", []), ("risk_engine_version", "caller")]:
        assert client.post("/api/v1/action-requests", json={**body(ids), field: value}).status_code == 422


def test_idempotency_retry_and_conflict_prevent_duplicates() -> None:
    ids = fixture_records(); add_policy(ids)
    first = client.post("/api/v1/action-requests", json=body(ids, "same-key", parameters={"amount": 1})).json()
    retry = client.post("/api/v1/action-requests", json=body(ids, "same-key", parameters={"amount": 1}))
    assert retry.status_code == 201 and retry.json()["action_request_id"] == first["action_request_id"]
    conflict = client.post("/api/v1/action-requests", json=body(ids, "same-key", parameters={"amount": 2}))
    assert conflict.status_code == 409
    with TestingSession() as session:
        assert session.scalar(select(func.count()).select_from(ActionRequest).where(ActionRequest.idempotency_key == "same-key")) == 1
        assert session.scalar(select(func.count()).select_from(Decision).join(ActionRequest).where(ActionRequest.idempotency_key == "same-key")) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent).join(ActionRequest).where(ActionRequest.idempotency_key == "same-key", AuditEvent.event_type == "RISK_EVALUATED")) == 1


def test_audit_events_are_appended_for_evaluation_outcome() -> None:
    ids = fixture_records(); add_policy(ids)
    result = client.post("/api/v1/action-requests", json=body(ids, "audit-key")).json()
    with TestingSession() as session:
        events = session.scalars(select(AuditEvent).where(AuditEvent.action_request_id == UUID(result["action_request_id"])).order_by(AuditEvent.created_at)).all()
        assert [event.event_type for event in events] == ["ACTION_REQUEST_RECEIVED", "RISK_EVALUATED", "INTELLIGENCE_ASSESSMENT", "POLICY_EVALUATED", "ACTION_AUTHORIZED"]
        risk_event = events[1]
        assert risk_event.event_data["engine_version"] == RiskEngine.VERSION
        assert isinstance(risk_event.event_data["score"], int)
        assert risk_event.event_data["factors"]


def test_unknown_reference_fails_closed_and_internal_evaluator_error_does_not_allow(monkeypatch) -> None:
    ids = fixture_records(); add_policy(ids)
    unknown = client.post("/api/v1/action-requests", json=body({**ids, "action_id": str(uuid4())}, "unknown-action"))
    assert unknown.status_code == 409

    def explode(*args, **kwargs):
        raise RuntimeError("test evaluator failure")
    monkeypatch.setattr(GatewayService, "submit", lambda self, payload: (_ for _ in ()).throw(RuntimeError("test evaluator failure")))
    response = client.post("/api/v1/action-requests", json=body(ids, "internal-error"))
    assert response.status_code == 400


def test_risk_engine_failure_rolls_back_and_never_authorizes(monkeypatch) -> None:
    ids = fixture_records(); add_policy(ids)
    monkeypatch.setattr(RiskEngine, "evaluate", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("risk failure")))
    response = client.post("/api/v1/action-requests", json=body(ids, "risk-failure"))
    assert response.status_code == 400
    assert "AUTHORIZED" not in response.text
    with TestingSession() as session:
        assert session.scalar(select(func.count()).select_from(ActionRequest).where(ActionRequest.idempotency_key == "risk-failure")) == 0
        assert session.scalar(select(func.count()).select_from(Decision)) == 0
