from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.models import Action, Agent, CapabilityStatus, Delegation, Policy, Principal, Resource, ResourceSensitivity, ResourceStatus, RiskClassification, Tool
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

    policy = client.post("/api/v1/policies", json={"name": "Customer read", "version": 1, "priority": 10, "status": "ACTIVE"})
    assert policy.status_code == 201
    policy_id = policy.json()["id"]
    rule = client.post(f"/api/v1/policies/{policy_id}/rules", json={"effect": "ALLOW", "action": "read_customer", "resource_type": "crm_record", "priority": 10})
    assert rule.status_code == 201
    assert client.get("/api/v1/policies").json()[0]["rules"]
    client.post("/api/v1/delegations", json={"principal_id": ids["principal"], "agent_id": ids["agent"], "scope": "crm.read", "issued_at": "2026-08-22T12:00:00Z"})
    result = client.post("/api/v1/policy-evaluations", json={"principal_id": ids["principal"], "agent_id": ids["agent"], "tool_id": ids["tool"], "action_id": ids["action"], "resource_id": ids["resource"], "evaluated_at": "2026-08-22T12:00:00Z"})
    assert result.status_code == 200
    assert result.json()["decision"] == "ALLOW", result.json()
    assert result.json()["trace"]
