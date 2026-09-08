"""Sandbox payment webhook endpoint tests (signature, replay, dedup, tenant)."""

import hashlib
import hmac
import json
import time
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.db.models import (
    Tenant, Principal, PrincipalType, PrincipalStatus, Agent, AgentStatus,
    Tool, Action, CapabilityStatus, Resource, ResourceStatus, ResourceSensitivity,
    RiskClassification, ActionRequest, ActionRequestStatus, FinancialExecution, ExecutionState, WebhookEvent,
)
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    with TestingSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

SECRET = settings.webhook_secret


@pytest.fixture(autouse=True)
def reset_db():
    with TestingSession() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


@pytest.fixture(autouse=True)
def ensure_override():
    # Test modules mutate the shared get_db override at import time; re-assert the
    # module override so this module's HTTP calls target its own SQLite engine.
    app.dependency_overrides[get_db] = override_get_db
    yield


@pytest.fixture
def db_session():
    with TestingSession() as session:
        yield session


def _provision(db, status=ExecutionState.PENDING):
    tenant = Tenant(id=uuid.uuid4(), name="Webhook Tenant", slug=f"wh-{uuid.uuid4().hex[:6]}")
    principal = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name="Alice", external_id=f"usr_{uuid.uuid4().hex[:6]}", status=PrincipalStatus.ACTIVE)
    agent = Agent(id=uuid.uuid4(), tenant_id=tenant.id, name="WebhookBot", owner_principal_id=principal.id, purpose="Treasury", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    tool = Tool(id=uuid.uuid4(), tenant_id=tenant.id, name=f"wh_tool_{uuid.uuid4().hex[:6]}", description="tool", status=CapabilityStatus.ACTIVE)
    action = Action(id=uuid.uuid4(), tenant_id=tenant.id, tool_id=tool.id, name="wire_transfer", description="desc", risk_level=RiskClassification.HIGH, status=CapabilityStatus.ACTIVE)
    resource = Resource(id=uuid.uuid4(), tenant_id=tenant.id, resource_type="account", resource_key="ACC-WH", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)
    request = ActionRequest(id=uuid.uuid4(), tenant_id=tenant.id, principal_id=principal.id, agent_id=agent.id, action_id=action.id, resource_id=resource.id, parameters={"amount": "100.00"}, status=ActionRequestStatus.COMPLETED, idempotency_key=f"idem-{uuid.uuid4()}")
    execution = FinancialExecution(id=uuid.uuid4(), tenant_id=tenant.id, action_request_id=request.id, provider_name="SandboxPaymentProvider", provider_transaction_id="TX-1", provider_request_id="REQ-1", status=status, payload_digest="digest")
    db.add_all([tenant, principal, agent, tool, action, resource, request, execution])
    db.commit()
    return tenant, request, execution


def sign(body: bytes, secret: str, t: int | None = None) -> str:
    ts = int(time.time()) if t is None else t
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def payload_for(request_id, tenant_id, status="SUCCEEDED", event_id=None):
    return {
        "event_id": event_id or f"evt-{uuid.uuid4()}",
        "event_type": "payment.settled",
        "source": "SandboxPaymentProvider",
        "action_request_id": str(request_id),
        "tenant_id": str(tenant_id),
        "status": status,
    }


def test_valid_webhook_processes_and_updates_execution(db_session):
    tenant, request, execution = _provision(db_session)
    body = json.dumps(payload_for(request.id, tenant.id)).encode()
    header = sign(body, SECRET)
    response = client.post("/api/v1/webhooks/payment", content=body, headers={"X-AgentOS-Signature": header})
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "processed"

    db_session.expire_all()
    updated = db_session.get(FinancialExecution, execution.id)
    assert updated.status == ExecutionState.SUCCEEDED
    events = db_session.scalar(select(func.count(WebhookEvent.id)))
    assert events == 1


def test_invalid_signature_rejected(db_session):
    tenant, request, execution = _provision(db_session)
    body = json.dumps(payload_for(request.id, tenant.id)).encode()
    header = sign(body, "wrong-secret")
    response = client.post("/api/v1/webhooks/payment", content=body, headers={"X-AgentOS-Signature": header})
    assert response.status_code == 401


def test_replay_with_stale_timestamp_rejected(db_session):
    tenant, request, execution = _provision(db_session)
    body = json.dumps(payload_for(request.id, tenant.id)).encode()
    header = sign(body, SECRET, t=int(time.time()) - 3600)
    response = client.post("/api/v1/webhooks/payment", content=body, headers={"X-AgentOS-Signature": header})
    assert response.status_code == 400


def test_duplicate_event_id_is_idempotent(db_session):
    tenant, request, execution = _provision(db_session)
    ev = payload_for(request.id, tenant.id, event_id="evt-dupe-1")
    body = json.dumps(ev).encode()
    header = sign(body, SECRET)
    first = client.post("/api/v1/webhooks/payment", content=body, headers={"X-AgentOS-Signature": header})
    assert first.status_code == 200 and first.json()["status"] == "processed"
    second = client.post("/api/v1/webhooks/payment", content=body, headers={"X-AgentOS-Signature": header})
    assert second.status_code == 200 and second.json()["status"] == "duplicate"
    count = db_session.scalar(select(func.count(WebhookEvent.id)))
    assert count == 1


def test_cross_tenant_payload_rejected(db_session):
    tenant, request, execution = _provision(db_session)
    foreign = str(uuid.uuid4())
    ev = payload_for(request.id, tenant.id)
    ev["tenant_id"] = foreign
    body = json.dumps(ev).encode()
    header = sign(body, SECRET)
    response = client.post("/api/v1/webhooks/payment", content=body, headers={"X-AgentOS-Signature": header})
    assert response.status_code == 403


def test_malformed_payload_rejected(db_session):
    response = client.post("/api/v1/webhooks/payment", content=b"{not json", headers={"X-AgentOS-Signature": "t=1,v1=abc"})
    assert response.status_code == 400


def test_out_of_order_terminal_update_rejected(db_session):
    tenant, request, execution = _provision(db_session, status=ExecutionState.SUCCEEDED)
    ev = payload_for(request.id, tenant.id, status="FAILED", event_id=f"evt-{uuid.uuid4()}")
    body = json.dumps(ev).encode()
    header = sign(body, SECRET)
    response = client.post("/api/v1/webhooks/payment", content=body, headers={"X-AgentOS-Signature": header})
    assert response.status_code == 400
