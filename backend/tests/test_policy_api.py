from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from uuid import uuid4

from app.db.base import Base
from app.db.models import Action, Agent, AuditEvent, CapabilityStatus, Delegation, Policy, Principal, Resource, ResourceSensitivity, ResourceStatus, RiskClassification, Tool
from app.db.session import get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_db():
    with TestingSession() as session:
        yield session


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


def test_policy_crud_and_server_side_evaluation() -> None:
    app.dependency_overrides[get_db] = override_db
    with TestingSession() as session:
        principal = Principal(name="Policy Owner", external_id="policy-owner", type="HUMAN")
        agent = Agent(name="PolicyAgent", owner=principal, purpose="Policy test", version="1.0.0", risk_classification=RiskClassification.LOW)
        tool = Tool(name="PolicyTool", description="Policy test tool")
        action = Action(tool=tool, name="read_customer", description="Read customer", risk_level=RiskClassification.LOW, status=CapabilityStatus.ACTIVE)
        resource = Resource(resource_type="crm_record", resource_key="policy-record", sensitivity=ResourceSensitivity.LOW, status=ResourceStatus.ACTIVE)
        session.add_all([principal, agent, tool, action, resource])
        session.commit()
        ids = {"principal": str(principal.id), "agent": str(agent.id), "tool": str(tool.id), "action": str(action.id), "resource": str(resource.id)}

    policy = client.post("/api/v1/policies", json={"name": "Customer read", "version": 1, "priority": 10})
    assert policy.status_code == 201
    policy_id = policy.json()["id"]
    assert policy.json()["status"] == "DRAFT"
    rule = client.post(f"/api/v1/policies/{policy_id}/rules", json={"effect": "ALLOW", "action": "read_customer", "resource_type": "crm_record", "priority": 10})
    assert rule.status_code == 201
    client.post("/api/v1/delegations", json={"principal_id": ids["principal"], "agent_id": ids["agent"], "scope": "*", "issued_at": "2026-08-22T12:00:00Z"})
    payload = {"principal_id": ids["principal"], "agent_id": ids["agent"], "tool_id": ids["tool"], "action_id": ids["action"], "resource_id": ids["resource"], "evaluated_at": "2026-08-22T12:00:00Z"}
    simulated = client.post(f"/api/v1/policies/{policy_id}/simulate", json=payload)
    assert simulated.status_code == 200 and simulated.json()["decision"] == "ALLOW"
    published = client.post(f"/api/v1/policies/{policy_id}/publish")
    assert published.status_code == 200
    assert published.json()["status"] == "ACTIVE"
    assert client.get("/api/v1/policies").json()[0]["rules"]
    result = client.post("/api/v1/policy-evaluations", json=payload)
    assert result.status_code == 200
    assert result.json()["decision"] == "ALLOW", result.json()
    assert result.json()["trace"]


def test_policy_lifecycle_preserves_live_history_and_requires_a_draft() -> None:
    name = f"Lifecycle policy {uuid4()}"
    active_payload = {"name": name, "version": 1, "priority": 10, "status": "ACTIVE"}
    assert client.post("/api/v1/policies", json=active_payload).status_code == 422

    draft = client.post("/api/v1/policies", json={"name": name, "version": 1, "priority": 10})
    assert draft.status_code == 201
    draft_id = draft.json()["id"]
    # A policy with no rules cannot silently become live.
    assert client.post(f"/api/v1/policies/{draft_id}/publish").status_code == 409
    rule = client.post(f"/api/v1/policies/{draft_id}/rules", json={"effect": "ALLOW", "action": "issue_credit", "resource_type": "customer_account", "priority": 10})
    assert rule.status_code == 201
    assert client.post(f"/api/v1/policies/{draft_id}/publish").status_code == 200
    # Live rules are immutable. A change must branch into the next version.
    assert client.post(f"/api/v1/policies/{draft_id}/rules", json={"effect": "DENY", "action": "issue_credit", "resource_type": "customer_account", "priority": 1}).status_code == 409

    version_two = client.post(f"/api/v1/policies/{draft_id}/versions")
    assert version_two.status_code == 201
    version_two_id = version_two.json()["id"]
    assert version_two.json()["status"] == "DRAFT"
    assert version_two.json()["version"] == 2
    assert len(version_two.json()["rules"]) == 1
    assert client.post(f"/api/v1/policies/{version_two_id}/publish").status_code == 200

    first = client.get(f"/api/v1/policies/{draft_id}").json()
    second = client.get(f"/api/v1/policies/{version_two_id}").json()
    assert first["status"] == "RETIRED"
    assert second["status"] == "ACTIVE"
    with TestingSession() as session:
        events = [event for event in session.query(AuditEvent).all() if event.event_data.get("policy_name") == name]
    assert {event.event_type for event in events} >= {"POLICY_PUBLISHED", "POLICY_RETIRED", "POLICY_VERSION_DRAFTED"}
