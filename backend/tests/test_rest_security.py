"""REST control-plane authentication + tenant authorization tests (W1-W3).

These tests force REST authentication on (REST_AUTH_REQUIRED=true) and verify the
real enforcement path with signed tokens: unauthenticated requests fail closed,
callers cannot impersonate another principal, and observability/gateway/approval
surfaces are tenant-isolated with server-derived tenant scope.
"""

import json
import time
import uuid

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.deps as rest_deps
import app.auth as auth_module
from app.api.deps import REST_DEV_SECRET
from app.config import Settings, settings
from app.db.base import Base
from app.db.session import get_db
from app.db.models import (
    Tenant, Principal, PrincipalType, PrincipalStatus, Agent, AgentStatus,
    Delegation, DelegationStatus, Tool, Action, CapabilityStatus, Resource,
    ResourceStatus, ResourceSensitivity, RiskClassification, Policy, PolicyStatus,
    PolicyRule, PolicyEffect, ActionRequest, ActionRequestStatus, ApprovalRequest,
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


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("REST_AUTH_REQUIRED", "true")
    with TestingSession() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    yield


@pytest.fixture(autouse=True)
def _override():
    app.dependency_overrides[get_db] = override_get_db
    yield


def token_for(external_id: str) -> str:
    now = int(time.time())
    claims = {
        "sub": external_id,
        "iss": settings.mcp_auth_issuer,
        "aud": settings.mcp_auth_audience,
        "scope": settings.mcp_auth_required_scope,
        "iat": now,
        "exp": now + 3600,
    }
    return jwt.encode(claims, REST_DEV_SECRET, algorithm="HS256")


def auth(external_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_for(external_id)}"}


@pytest.fixture
def db_session():
    with TestingSession() as session:
        yield session


def _provision(db, tenant_slug: str, req_status: ActionRequestStatus = ActionRequestStatus.EVALUATED):
    tenant = Tenant(id=uuid.uuid4(), name=f"Tenant {tenant_slug}", slug=tenant_slug)
    principal = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name=f"User {tenant_slug}", external_id=f"usr_{tenant_slug}", status=PrincipalStatus.ACTIVE)
    approver = Principal(id=uuid.uuid4(), tenant_id=tenant.id, type=PrincipalType.HUMAN, name=f"Approver {tenant_slug}", external_id=f"appr_{tenant_slug}", status=PrincipalStatus.ACTIVE)
    agent = Agent(id=uuid.uuid4(), tenant_id=tenant.id, name=f"Bot {tenant_slug}", owner_principal_id=principal.id, purpose="Treasury", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    delegation = Delegation(id=uuid.uuid4(), tenant_id=tenant.id, principal_id=principal.id, agent_id=agent.id, scope="wire_transfer", status=DelegationStatus.ACTIVE)
    tool = Tool(id=uuid.uuid4(), tenant_id=tenant.id, name=f"tool_{tenant_slug}", description="tool", status=CapabilityStatus.ACTIVE)
    action = Action(id=uuid.uuid4(), tenant_id=tenant.id, tool_id=tool.id, name="wire_transfer", description="desc", risk_level=RiskClassification.HIGH, status=CapabilityStatus.ACTIVE)
    resource = Resource(id=uuid.uuid4(), tenant_id=tenant.id, resource_type="account", resource_key=f"ACC-{tenant_slug}", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)
    request = ActionRequest(id=uuid.uuid4(), tenant_id=tenant.id, principal_id=principal.id, agent_id=agent.id, action_id=action.id, resource_id=resource.id, parameters={"amount": "25000.00"}, status=req_status, idempotency_key=f"idem-{uuid.uuid4()}")
    db.add_all([tenant, principal, approver, agent, delegation, tool, action, resource, request])
    db.commit()
    return tenant, principal, approver, request


def test_unauthenticated_request_is_rejected(db_session):
    _provision(db_session, "ta")
    response = client.get("/api/v1/action-requests")
    assert response.status_code == 401


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_rest_auth_cannot_be_disabled_outside_development(monkeypatch, environment):
    """REST_AUTH_REQUIRED=false must never create an anonymous hosted API."""
    import app.api.deps as auth_deps

    monkeypatch.setenv("REST_AUTH_REQUIRED", "false")
    monkeypatch.setattr(auth_deps, "settings", Settings(app_env=environment))
    assert auth_deps.is_rest_auth_required() is True


def test_invalid_token_is_rejected(db_session):
    _provision(db_session, "ta")
    response = client.get("/api/v1/action-requests", headers={"Authorization": "Bearer not.a.token"})
    assert response.status_code == 401


def test_rest_route_accepts_configured_rs256_public_key(db_session, monkeypatch):
    """REST auth must use an external asymmetric verifier, not the dev HMAC.

    This covers the actual router dependency path rather than only validating a
    TokenValidator in isolation. An eventual OIDC/JWKS provider integration
    still needs staging validation with a real issuer.
    """
    _, principal, _, _ = _provision(db_session, "rs256")
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    production_identity = Settings(
        app_env="production",
        mcp_auth_issuer="https://identity.example.test",
        mcp_auth_audience="https://api.example.test",
        mcp_auth_public_key=public_pem,
        mcp_auth_secret_key="",
        mcp_auth_jwks_url="",
    )
    monkeypatch.setattr(rest_deps, "settings", production_identity)
    monkeypatch.setattr(auth_module, "settings", production_identity)
    now = int(time.time())
    token = jwt.encode(
        {
            "sub": principal.external_id,
            "iss": production_identity.mcp_auth_issuer,
            "aud": production_identity.mcp_auth_audience,
            "scope": production_identity.mcp_auth_required_scope,
            "iat": now,
            "exp": now + 3600,
        },
        private_pem,
        algorithm="RS256",
    )
    response = client.get("/api/v1/action-requests", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_authenticated_request_is_tenant_scoped(db_session):
    t_a, p_a, _, req_a = _provision(db_session, "ta")
    _provision(db_session, "tb")
    response = client.get("/api/v1/action-requests", headers=auth(p_a.external_id))
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert str(req_a.id) in ids
    # Tenant B's request must never appear in Tenant A's list.
    from app.db.models import ActionRequest as AR
    b_ids = db_session.scalars(select(AR.id).where(AR.tenant_id != p_a.tenant_id)).all()
    assert all(str(bid) not in ids for bid in b_ids)


def test_cannot_impersonate_another_principal(db_session):
    t_a, p_a, _, _ = _provision(db_session, "ta")
    t_b, p_b, _, _ = _provision(db_session, "tb")
    # Valid graph for tenant A so the body passes validation; but principal_id
    # claims Tenant B's identity while the token authenticates Tenant A.
    payload = {
        "principal_id": str(p_b.id),
        "agent_id": str(db_session.scalars(select(Agent.id).where(Agent.tenant_id == p_a.tenant_id)).one()),
        "action_id": str(db_session.scalars(select(Action.id).where(Action.tenant_id == p_a.tenant_id)).one()),
        "resource_id": str(db_session.scalars(select(Resource.id).where(Resource.tenant_id == p_a.tenant_id)).one()),
        "parameters": {"amount": "100.00", "currency": "USD", "beneficiary_id": "B1", "source_account_id": "S1", "destination_account_id": "D1", "transaction_reference": "REF1"},
        "idempotency_key": f"idem-{uuid.uuid4()}",
    }
    response = client.post("/api/v1/action-requests", json=payload, headers=auth(p_a.external_id))
    assert response.status_code == 403


def test_observability_uses_authenticated_tenant(db_session):
    t_a, p_a, _, req_a = _provision(db_session, "ta")
    t_b, p_b, _, req_b = _provision(db_session, "tb")
    headers = auth(p_a.external_id)

    # Default scope is Tenant A (no client tenant input).
    r = client.get(f"/api/v1/observability/action-requests/{req_a.id}", headers=headers)
    assert r.status_code == 200

    # Tenant B's request is invisible to Tenant A.
    r = client.get(f"/api/v1/observability/action-requests/{req_b.id}", headers=headers)
    assert r.status_code == 404

    # Client-supplied tenant header conflicting with the authenticated tenant is 403.
    r = client.get("/api/v1/observability/metrics", headers={**headers, "X-Tenant-ID": str(t_b.id)})
    assert r.status_code == 403


def test_cross_tenant_approval_access_denied(db_session):
    t_a, p_a, appr_a, req_a = _provision(db_session, "ta", req_status=ActionRequestStatus.APPROVAL_PENDING)
    t_b, p_b, appr_b, req_b = _provision(db_session, "tb", req_status=ActionRequestStatus.APPROVAL_PENDING)
    # Create approvals in each tenant.
    for req, appr, p in ((req_a, appr_a, p_a), (req_b, appr_b, p_b)):
        db_session.add(ApprovalRequest(id=uuid.uuid4(), tenant_id=req.tenant_id, action_request_id=req.id, requested_by=p.id, status="PENDING", reason="HIGH_RISK_APPROVAL: requires approval"))
    db_session.commit()
    b_approval = db_session.scalars(select(ApprovalRequest).where(ApprovalRequest.tenant_id == t_b.id)).one()

    # Tenant A principal cannot act on Tenant B's approval.
    response = client.post(f"/api/v1/approvals/{str(b_approval.id)}/reject", json={"approver_principal_id": str(p_a.id)}, headers=auth(p_a.external_id))
    assert response.status_code in (403, 404)


def test_registry_catalog_is_tenant_scoped(db_session):
    t_a, p_a, _, _ = _provision(db_session, "ta")
    t_b, p_b, _, _ = _provision(db_session, "tb")
    agent_a = db_session.scalars(select(Agent).where(Agent.tenant_id == p_a.tenant_id)).one()
    agent_b = db_session.scalars(select(Agent).where(Agent.tenant_id == p_b.tenant_id)).one()
    headers_a = auth(p_a.external_id)

    # List is tenant-scoped.
    r = client.get("/api/v1/agents", headers=headers_a)
    ids = [item["id"] for item in r.json()]
    assert str(agent_a.id) in ids and str(agent_b.id) not in ids

    # Detail by foreign ID fails closed.
    r = client.get(f"/api/v1/agents/{agent_b.id}", headers=headers_a)
    assert r.status_code == 404
    # Mutation of a foreign tenant's record fails closed.
    r = client.patch(f"/api/v1/agents/{agent_b.id}", json={"purpose": "hacked"}, headers=headers_a)
    assert r.status_code == 404
    r = client.post(f"/api/v1/agents/{agent_b.id}/suspend", headers=headers_a)
    assert r.status_code == 404

    # Creating an agent attaches to the authenticated tenant.
    new_agent_name = f"BotNew-{uuid.uuid4().hex[:6]}"
    r = client.post("/api/v1/agents", json={"name": new_agent_name, "owner_principal_id": str(p_a.id), "purpose": "X", "version": "1.0", "risk_classification": "LOW"}, headers=headers_a)
    assert r.status_code == 201
    created = db_session.scalar(select(Agent).where(Agent.name == new_agent_name))
    assert created is not None and created.tenant_id == p_a.tenant_id


def test_policy_catalog_is_tenant_scoped(db_session):
    t_a, p_a, _, _ = _provision(db_session, "ta")
    t_b, p_b, _, _ = _provision(db_session, "tb")
    headers_a = auth(p_a.external_id)
    # Create one policy per tenant.
    pa = client.post("/api/v1/policies", json={"name": f"pol_a_{uuid.uuid4().hex[:6]}", "version": 1, "priority": 10}, headers=headers_a)
    pb = client.post("/api/v1/policies", json={"name": f"pol_b_{uuid.uuid4().hex[:6]}", "version": 1, "priority": 10}, headers=auth(p_b.external_id))
    assert pa.status_code == 201 and pb.status_code == 201
    pid_a = pa.json()["id"]
    pid_b = pb.json()["id"]

    listed = client.get("/api/v1/policies", headers=headers_a).json()
    listed_ids = [p["id"] for p in listed]
    assert pid_a in listed_ids and pid_b not in listed_ids
    # Detail by foreign ID fails closed.
    assert client.get(f"/api/v1/policies/{pid_b}", headers=headers_a).status_code == 404
    # Cannot add a rule to a foreign policy.
    assert client.post(f"/api/v1/policies/{pid_b}/rules", json={"effect": "ALLOW", "action": "x", "resource_type": "y", "priority": 1}, headers=headers_a).status_code == 404
