"""API and tenant-boundary coverage for the Workforce planning foundation."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Agent, Principal, PrincipalStatus, PrincipalType, RiskClassification, Tenant
from app.db.session import get_db
from app.main import app
from app.schemas import WorkforceProjectCreate
from app.services.workforce import WorkforceService, WorkforceValidationError


engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_db():
    with TestingSession() as session:
        yield session


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


def new_agent(name: str) -> dict[str, str]:
    principal = client.post(
        "/api/v1/principals",
        json={"name": f"{name} owner", "external_id": f"{name}-owner-{uuid4()}", "type": "HUMAN", "status": "ACTIVE"},
    ).json()
    return client.post(
        "/api/v1/agents",
        json={"name": f"{name}-{uuid4()}", "owner_principal_id": principal["id"], "purpose": "Workforce test agent", "version": "1.0.0", "risk_classification": "LOW"},
    ).json()


def test_workforce_goal_project_and_work_item_lifecycle() -> None:
    agent = new_agent("workforce")
    goal = client.post(
        "/api/v1/workforce/goals",
        json={"title": "Reduce approval turnaround", "description": "Planning target", "status": "ACTIVE", "owner_agent_id": agent["id"]},
    )
    assert goal.status_code == 201
    goal_id = goal.json()["id"]

    child = client.post(
        "/api/v1/workforce/goals",
        json={"title": "Publish queue report", "parent_goal_id": goal_id},
    )
    assert child.status_code == 201
    assert child.json()["parent_goal_id"] == goal_id

    project = client.post(
        "/api/v1/workforce/projects",
        json={"name": f"Approval operations {uuid4()}", "goal_id": goal_id, "owner_agent_id": agent["id"]},
    )
    assert project.status_code == 201
    project_id = project.json()["id"]

    item = client.post(
        "/api/v1/workforce/work-items",
        json={"project_id": project_id, "goal_id": goal_id, "title": "Map pending queue", "priority": "HIGH", "assignee_agent_id": agent["id"]},
    )
    assert item.status_code == 201
    assert item.json()["status"] == "BACKLOG"
    assert item.json()["action_request_id"] is None

    progressed = client.patch(f"/api/v1/workforce/work-items/{item.json()['id']}", json={"status": "IN_PROGRESS"})
    assert progressed.status_code == 200
    assert progressed.json()["status"] == "IN_PROGRESS"
    assert len(client.get(f"/api/v1/workforce/work-items?project_id={project_id}").json()) >= 1


def test_workforce_rejects_unknown_and_cross_tenant_relationships() -> None:
    agent = new_agent("relationship")
    assert client.post("/api/v1/workforce/goals", json={"title": "Invalid owner", "owner_agent_id": str(uuid4())}).status_code == 400
    assert client.post("/api/v1/workforce/projects", json={"name": f"Invalid goal {uuid4()}", "goal_id": str(uuid4())}).status_code == 400
    assert client.post("/api/v1/workforce/work-items", json={"project_id": str(uuid4()), "title": "No project"}).status_code == 400

    with TestingSession() as session:
        other_tenant = Tenant(name="Other Workforce Tenant", slug=f"other-workforce-{uuid4()}", status="ACTIVE")
        session.add(other_tenant)
        session.flush()
        owner = Principal(tenant_id=other_tenant.id, name="Other owner", external_id=f"other-owner-{uuid4()}", type=PrincipalType.HUMAN, status=PrincipalStatus.ACTIVE)
        session.add(owner)
        session.flush()
        other_agent = Agent(tenant_id=other_tenant.id, name=f"Other agent {uuid4()}", owner_principal_id=owner.id, purpose="Other", version="1", risk_classification=RiskClassification.LOW)
        session.add(other_agent)
        session.commit()

        service = WorkforceService(session)
        with pytest.raises(WorkforceValidationError, match="owner_agent_id"):
            service.create_project(WorkforceProjectCreate(name=f"Cross tenant {uuid4()}", owner_agent_id=agent["id"]), other_tenant.id)
        assert service._agent(other_agent.id, other_tenant.id) is not None
