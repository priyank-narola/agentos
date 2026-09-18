from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import Action, Agent, Delegation, Principal, Resource, Tool
from app.db.session import get_db
from app.main import app
from app.seed import seed_demo

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_db():
    with TestingSession() as session:
        yield session


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


def principal_payload(external_id: str = "registry-principal") -> dict[str, str]:
    return {"name": "Registry Owner", "external_id": external_id, "type": "HUMAN", "status": "ACTIVE"}


def agent_payload(owner_id: str, name: str = "RegistryAgent") -> dict[str, str]:
    return {"name": name, "owner_principal_id": owner_id, "purpose": "Registry testing", "version": "1.0.0", "risk_classification": "MEDIUM"}


def test_registry_crud_and_lifecycle() -> None:
    app.dependency_overrides[get_db] = override_db
    principal = client.post("/api/v1/principals", json=principal_payload()).json()
    created = client.post("/api/v1/agents", json=agent_payload(principal["id"])).json()
    assert client.post("/api/v1/agents", json=agent_payload(principal["id"])).status_code == 409
    assert client.get(f"/api/v1/agents/{created['id']}").json()["name"] == "RegistryAgent"
    assert client.post(f"/api/v1/agents/{created['id']}/suspend").json()["status"] == "SUSPENDED"
    assert client.post(f"/api/v1/agents/{created['id']}/activate").json()["status"] == "ACTIVE"
    assert client.post(f"/api/v1/agents/{created['id']}/retire").json()["status"] == "RETIRED"
    assert client.post(f"/api/v1/agents/{created['id']}/activate").status_code == 400
    assert client.patch(f"/api/v1/agents/{created['id']}", json={"status": "ACTIVE"}).status_code == 400

    tool = client.post("/api/v1/tools", json={"name": "RegistryTool", "description": "Test tool", "status": "ACTIVE"}).json()
    action_payload = {"name": "inspect", "description": "Inspect data", "risk_level": "LOW", "status": "ACTIVE"}
    action = client.post(f"/api/v1/tools/{tool['id']}/actions", json=action_payload).json()
    assert action["tool_id"] == tool["id"]
    assert client.post(f"/api/v1/tools/{tool['id']}/actions", json=action_payload).status_code == 409

    resource = client.post("/api/v1/resources", json={"resource_type": "dataset", "resource_key": "registry-dataset", "sensitivity": "LOW", "status": "ACTIVE"}).json()
    assert client.get(f"/api/v1/resources/{resource['id']}").status_code == 200
    delegation_agent = client.post("/api/v1/agents", json=agent_payload(principal["id"], "DelegationAgent")).json()
    delegation = client.post("/api/v1/delegations", json={"principal_id": principal["id"], "agent_id": delegation_agent["id"], "scope": "registry.read", "issued_at": "2026-08-22T12:00:00Z", "metadata": {"source": "test"}}).json()
    assert delegation["scope"] == "registry.read"
    revoked = client.post(f"/api/v1/delegations/{delegation['id']}/revoke")
    assert revoked.status_code == 200 and revoked.json()["status"] == "REVOKED"
    assert client.post(f"/api/v1/delegations/{delegation['id']}/revoke").status_code == 409


def test_registry_rejects_unknown_relationships() -> None:
    app.dependency_overrides[get_db] = override_db
    response = client.post("/api/v1/agents", json=agent_payload(str(uuid4()), "UnknownOwnerAgent"))
    assert response.status_code == 400


def test_delegation_requires_active_human_and_active_agent() -> None:
    principal = client.post("/api/v1/principals", json=principal_payload("delegation-guard-principal")).json()
    agent = client.post("/api/v1/agents", json=agent_payload(principal["id"], "DelegationGuardAgent")).json()
    payload = {"principal_id": principal["id"], "agent_id": agent["id"], "scope": "guarded.read", "issued_at": "2026-08-22T12:00:00Z"}

    assert client.post("/api/v1/delegations", json={**payload, "expires_at": "2026-08-22T12:00:00Z"}).status_code == 400
    assert client.post("/api/v1/delegations", json={**payload, "scope": "   "}).status_code == 400
    assert client.post(f"/api/v1/agents/{agent['id']}/suspend").status_code == 200
    assert client.post("/api/v1/delegations", json=payload).status_code == 400

    suspended_principal = client.post("/api/v1/principals", json={**principal_payload("suspended-delegator"), "status": "SUSPENDED"}).json()
    another_agent = client.post("/api/v1/agents", json=agent_payload(suspended_principal["id"], "SuspendedDelegatorAgent")).json()
    assert client.post("/api/v1/delegations", json={**payload, "principal_id": suspended_principal["id"], "agent_id": another_agent["id"]}).status_code == 400
    response = client.post("/api/v1/delegations", json={"principal_id": str(uuid4()), "agent_id": str(uuid4()), "scope": "none", "issued_at": "2026-08-22T12:00:00Z"})
    assert response.status_code == 400


def test_seed_demo_is_idempotent() -> None:
    with TestingSession() as session:
        before = {
            "principals": session.scalar(select(func.count()).select_from(Principal)),
            "agents": session.scalar(select(func.count()).select_from(Agent)),
            "tools": session.scalar(select(func.count()).select_from(Tool)),
            "actions": session.scalar(select(func.count()).select_from(Action)),
            "resources": session.scalar(select(func.count()).select_from(Resource)),
            "delegations": session.scalar(select(func.count()).select_from(Delegation)),
        }
        first = seed_demo(session)
        second = seed_demo(session)
        assert first == {"principals": 1, "agents": 3, "tools": 4, "actions_created": 6, "resources_created": 4, "delegations_created": 3, "policies_created": 3}
        assert second == {"principals": 1, "agents": 3, "tools": 4, "actions_created": 0, "resources_created": 0, "delegations_created": 0, "policies_created": 0}
        assert session.scalar(select(func.count()).select_from(Principal)) == before["principals"] + 1
        assert session.scalar(select(func.count()).select_from(Agent)) == before["agents"] + 3
        assert session.scalar(select(func.count()).select_from(Tool)) == before["tools"] + 4
        assert session.scalar(select(func.count()).select_from(Action)) == before["actions"] + 6
        assert session.scalar(select(func.count()).select_from(Resource)) == before["resources"] + 4
        assert session.scalar(select(func.count()).select_from(Delegation)) == before["delegations"] + 3


def test_get_principal_by_id_regression() -> None:
    app.dependency_overrides[get_db] = override_db
    # 1. Create a principal
    payload = principal_payload(external_id="regression-test-principal")
    created = client.post("/api/v1/principals", json=payload).json()
    p_id = created["id"]
    
    # 2. List principals and verify the created principal is returned
    listed = client.get("/api/v1/principals").json()
    listed_ids = [p["id"] for p in listed]
    assert p_id in listed_ids

    # 3. GET the principal by ID directly and verify it returns 200
    response = client.get(f"/api/v1/principals/{p_id}")
    assert response.status_code == 200
    assert response.json()["id"] == p_id
