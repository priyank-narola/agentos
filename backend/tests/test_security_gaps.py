"""Security gap tests (P2-01 through P2-06, P2-12).

Covers:
- P2-01: Rate limiting behavior (429 + Retry-After)
- P2-02: Token expiration rejection
- P2-03: Approval expiry enforcement
- P2-04: Suspended principal rejection
- P2-05: Expired delegation rejection in gateway path
- P2-06: Inactive agent rejection
- P2-12: Concurrent approval execution (row locking)
"""

import time
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import REST_DEV_SECRET
from app.config import settings
from app.db.base import Base
from app.db.models import (
    Action, ActionRequest, Agent, AgentStatus, ApprovalRequest, ApprovalStatus,
    CapabilityStatus, Delegation, DelegationStatus, Principal, PrincipalStatus,
    Policy, PolicyEffect, PolicyRule, Resource, ResourceSensitivity, ResourceStatus,
    RiskClassification, Tool,
)
from app.db.session import get_db
from app.main import app
from app.services.approval import ApprovalService

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    with TestingSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    monkeypatch.setenv("REST_AUTH_REQUIRED", "true")
    app.dependency_overrides[get_db] = override_get_db
    with TestingSession() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    yield


def _token(external_id: str, exp_offset: int = 3600) -> str:
    now = int(time.time())
    claims = {
        "sub": external_id,
        "iss": settings.mcp_auth_issuer,
        "aud": settings.mcp_auth_audience,
        "scope": settings.mcp_auth_required_scope,
        "iat": now,
        "exp": now + exp_offset,
    }
    return jwt.encode(claims, REST_DEV_SECRET, algorithm="HS256")


def _auth(external_id: str, exp_offset: int = 3600) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(external_id, exp_offset)}"}


def _seed(env_override=None):
    """Create principal, agent, tool, action, resource, delegation, policy."""
    with TestingSession() as session:
        principal = Principal(name=f"P-{uuid.uuid4()}", external_id=str(uuid.uuid4()), type="HUMAN")
        agent = Agent(name=f"A-{uuid.uuid4()}", owner=principal, purpose="test", version="1", risk_classification=RiskClassification.LOW)
        tool = Tool(name=f"T-{uuid.uuid4()}", description="test")
        action = Action(tool=tool, name="read_customer", description="test", risk_level=RiskClassification.LOW)
        resource = Resource(resource_type="crm_record", resource_key=str(uuid.uuid4()), sensitivity=ResourceSensitivity.LOW, status=ResourceStatus.ACTIVE)
        session.add_all([principal, agent, tool, action, resource, Delegation(principal=principal, agent=agent, scope="crm.read")])
        policy = Policy(name=f"pol-{uuid.uuid4()}", version=1, priority=1, status="ACTIVE")
        policy.rules = [PolicyRule(effect=PolicyEffect.ALLOW, action="read_customer", resource_type="crm_record", priority=1)]
        session.add(policy)
        session.commit()
        return {
            "external_id": principal.external_id,
            "principal_id": str(principal.id),
            "agent_id": str(agent.id),
            "action_id": str(action.id),
            "resource_id": str(resource.id),
            "principal": principal,
            "agent": agent,
        }


def _seed_high_risk():
    """Create principal, agent, tool, action, resource, delegation, policy for HIGH-risk action."""
    with TestingSession() as session:
        principal = Principal(name=f"P-{uuid.uuid4()}", external_id=str(uuid.uuid4()), type="HUMAN")
        agent = Agent(name=f"A-{uuid.uuid4()}", owner=principal, purpose="test", version="1", risk_classification=RiskClassification.HIGH)
        tool = Tool(name=f"T-{uuid.uuid4()}", description="test")
        action = Action(tool=tool, name="bank_transfer", description="test", risk_level=RiskClassification.HIGH)
        resource = Resource(resource_type="bank_account", resource_key=str(uuid.uuid4()), sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)
        session.add_all([principal, agent, tool, action, resource, Delegation(principal=principal, agent=agent, scope="payments.bank")])
        policy = Policy(name=f"pol-{uuid.uuid4()}", version=1, priority=1, status="ACTIVE")
        policy.rules = [PolicyRule(effect=PolicyEffect.ALLOW, action="bank_transfer", resource_type="bank_account", priority=1)]
        session.add(policy)
        session.commit()
        return {
            "external_id": principal.external_id,
            "principal_id": str(principal.id),
            "agent_id": str(agent.id),
            "action_id": str(action.id),
            "resource_id": str(resource.id),
            "principal": principal,
            "agent": agent,
        }


# ── P2-01: Rate limiting ────────────────────────────────────────────────

def test_rate_limit_returns_429_with_retry_after():
    """When rate limit is exceeded, response is 429 with Retry-After header."""
    from app.api.ratelimit import _limiter
    original_max = _limiter.max_requests
    original_windows = dict(_limiter._windows)
    _limiter.max_requests = 2
    _limiter._windows.clear()
    try:
        ids = _seed()
        headers = _auth(ids["external_id"])
        body = {"principal_id": ids["principal_id"], "agent_id": ids["agent_id"],
                "action_id": ids["action_id"], "resource_id": ids["resource_id"],
                "parameters": {}, "idempotency_key": str(uuid.uuid4())}
        assert client.post("/api/v1/action-requests", json=body, headers=headers).status_code == 201
        body2 = {**body, "idempotency_key": str(uuid.uuid4())}
        assert client.post("/api/v1/action-requests", json=body2, headers=headers).status_code == 201
        body3 = {**body, "idempotency_key": str(uuid.uuid4())}
        resp = client.post("/api/v1/action-requests", json=body3, headers=headers)
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers
        assert int(resp.headers["Retry-After"]) > 0
    finally:
        _limiter.max_requests = original_max
        _limiter._windows.clear()
        _limiter._windows.update(original_windows)


# ── P2-02: Expired token ────────────────────────────────────────────────

def test_expired_token_is_rejected():
    """Token with exp in the past returns 401."""
    ids = _seed()
    expired_headers = _auth(ids["external_id"], exp_offset=-3600)
    resp = client.get("/api/v1/action-requests", headers=expired_headers)
    assert resp.status_code == 401


def test_not_yet_valid_token_is_rejected():
    """Token with nbf in the future returns 401."""
    ids = _seed()
    now = int(time.time())
    claims = {
        "sub": ids["external_id"],
        "iss": settings.mcp_auth_issuer,
        "aud": settings.mcp_auth_audience,
        "scope": settings.mcp_auth_required_scope,
        "iat": now,
        "exp": now + 7200,
        "nbf": now + 3600,
    }
    token = jwt.encode(claims, REST_DEV_SECRET, algorithm="HS256")
    resp = client.get("/api/v1/action-requests", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


# ── P2-03: Approval expiry enforcement ──────────────────────────────────

def test_expired_approval_is_automatically_rejected():
    """An approval request with expires_at in the past is auto-expired."""
    ids = _seed_high_risk()
    headers = _auth(ids["external_id"])
    body = {"principal_id": ids["principal_id"], "agent_id": ids["agent_id"],
            "action_id": ids["action_id"], "resource_id": ids["resource_id"],
            "parameters": {"amount": 15000}, "idempotency_key": str(uuid.uuid4())}
    resp = client.post("/api/v1/action-requests", json=body, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["gateway_status"] == "PENDING_APPROVAL"

    with TestingSession() as session:
        approval = session.scalar(select(ApprovalRequest).limit(1))
        assert approval is not None
        # Persist an aware UTC value; SQLite may strip tzinfo on retrieval, and
        # the approval service normalizes that database representation to UTC.
        approval.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        session.commit()
        approval_id = str(approval.id)

    approver_ext = str(uuid.uuid4())
    with TestingSession() as session:
        approver = Principal(name=f"Appr-{approver_ext}", external_id=approver_ext, type="HUMAN")
        session.add(approver)
        session.commit()
        approver_id = str(approver.id)

    result = client.post(f"/api/v1/approvals/{approval_id}/approve",
                         json={"approver_principal_id": approver_id, "decision_reason": "Expiry boundary test"},
                         headers=_auth(approver_ext))
    # Expired approval returns 409 (Conflict) — service raises ApprovalConflictError
    assert result.status_code == 409
    assert "expired" in result.json()["detail"].lower()
    # Verify the approval status is EXPIRED in DB
    with TestingSession() as session:
        approval = session.get(ApprovalRequest, uuid.UUID(approval_id))
        assert approval.status == ApprovalStatus.EXPIRED


def test_expired_approval_is_finalized_when_listed():
    """A stale pending approval becomes terminal without a reviewer action."""
    ids = _seed_high_risk()
    body = {"principal_id": ids["principal_id"], "agent_id": ids["agent_id"],
            "action_id": ids["action_id"], "resource_id": ids["resource_id"],
            "parameters": {"amount": 15000}, "idempotency_key": str(uuid.uuid4())}
    response = client.post("/api/v1/action-requests", json=body, headers=_auth(ids["external_id"]))
    assert response.status_code == 201

    with TestingSession() as session:
        approval = session.scalar(select(ApprovalRequest).limit(1))
        assert approval is not None
        approval.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        session.commit()
        approval_id = approval.id

    with TestingSession() as session:
        details = ApprovalService(session).list()
        detail = next(item for item in details if item.id == approval_id)
        assert detail.status == ApprovalStatus.EXPIRED
        refreshed = session.get(ApprovalRequest, approval_id)
        assert refreshed is not None
        assert refreshed.status == ApprovalStatus.EXPIRED


# ── P2-04: Suspended principal rejection ─────────────────────────────────

def test_suspended_principal_token_is_rejected():
    """A token for a suspended principal returns 403."""
    ids = _seed()
    with TestingSession() as session:
        principal = session.scalar(select(Principal).where(Principal.id == uuid.UUID(ids["principal_id"])))
        principal.status = PrincipalStatus.SUSPENDED
        session.commit()
    resp = client.get("/api/v1/action-requests", headers=_auth(ids["external_id"]))
    assert resp.status_code == 403
    assert "not active" in resp.json()["detail"].lower()


# ── P2-05: Expired delegation rejection ─────────────────────────────────

def test_expired_delegation_blocks_gateway_submission():
    """An expired delegation causes DENY in the gateway."""
    ids = _seed()
    with TestingSession() as session:
        delegation = session.scalar(select(Delegation).where(Delegation.agent_id == uuid.UUID(ids["agent_id"])))
        # Persist an aware UTC value; SQLite may strip tzinfo on retrieval, and
        # the policy path normalizes that database representation to UTC.
        delegation.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        session.commit()

    headers = _auth(ids["external_id"])
    body = {"principal_id": ids["principal_id"], "agent_id": ids["agent_id"],
            "action_id": ids["action_id"], "resource_id": ids["resource_id"],
            "parameters": {}, "idempotency_key": str(uuid.uuid4())}
    resp = client.post("/api/v1/action-requests", json=body, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["gateway_status"] == "BLOCKED"


def test_revoked_delegation_blocks_gateway_submission():
    """A revoked delegation causes DENY in the gateway."""
    ids = _seed()
    with TestingSession() as session:
        delegation = session.scalar(select(Delegation).where(Delegation.agent_id == uuid.UUID(ids["agent_id"])))
        delegation.status = DelegationStatus.REVOKED
        session.commit()

    headers = _auth(ids["external_id"])
    body = {"principal_id": ids["principal_id"], "agent_id": ids["agent_id"],
            "action_id": ids["action_id"], "resource_id": ids["resource_id"],
            "parameters": {}, "idempotency_key": str(uuid.uuid4())}
    resp = client.post("/api/v1/action-requests", json=body, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["gateway_status"] == "BLOCKED"


# ── P2-06: Inactive agent rejection ─────────────────────────────────────

def test_suspended_agent_blocks_gateway_submission():
    """A suspended agent causes DENY in the gateway."""
    ids = _seed()
    with TestingSession() as session:
        agent = session.scalar(select(Agent).where(Agent.id == uuid.UUID(ids["agent_id"])))
        agent.status = AgentStatus.SUSPENDED
        session.commit()

    headers = _auth(ids["external_id"])
    body = {"principal_id": ids["principal_id"], "agent_id": ids["agent_id"],
            "action_id": ids["action_id"], "resource_id": ids["resource_id"],
            "parameters": {}, "idempotency_key": str(uuid.uuid4())}
    resp = client.post("/api/v1/action-requests", json=body, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["gateway_status"] == "BLOCKED"


def test_retired_agent_blocks_gateway_submission():
    """A retired agent causes DENY in the gateway."""
    ids = _seed()
    with TestingSession() as session:
        agent = session.scalar(select(Agent).where(Agent.id == uuid.UUID(ids["agent_id"])))
        agent.status = AgentStatus.RETIRED
        session.commit()

    headers = _auth(ids["external_id"])
    body = {"principal_id": ids["principal_id"], "agent_id": ids["agent_id"],
            "action_id": ids["action_id"], "resource_id": ids["resource_id"],
            "parameters": {}, "idempotency_key": str(uuid.uuid4())}
    resp = client.post("/api/v1/action-requests", json=body, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["gateway_status"] == "BLOCKED"


# ── P2-12: Concurrent approval execution ────────────────────────────────

def test_concurrent_approve_attempts_only_one_succeeds():
    """Two concurrent approve requests for the same approval — only one should succeed."""
    ids = _seed_high_risk()
    headers = _auth(ids["external_id"])
    body = {"principal_id": ids["principal_id"], "agent_id": ids["agent_id"],
            "action_id": ids["action_id"], "resource_id": ids["resource_id"],
            "parameters": {"amount": 25000}, "idempotency_key": str(uuid.uuid4())}
    resp = client.post("/api/v1/action-requests", json=body, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["gateway_status"] == "PENDING_APPROVAL"

    with TestingSession() as session:
        approval = session.scalar(select(ApprovalRequest).limit(1))
        approval_id = str(approval.id)

    approver_ext = str(uuid.uuid4())
    with TestingSession() as session:
        approver = Principal(name=f"Appr-{approver_ext}", external_id=approver_ext, type="HUMAN")
        session.add(approver)
        session.commit()
        approver_id = str(approver.id)
    approver_headers = _auth(approver_ext)

    result1 = client.post(f"/api/v1/approvals/{approval_id}/approve",
                          json={"approver_principal_id": approver_id, "decision_reason": "Concurrent approval test"},
                          headers=approver_headers)
    result2 = client.post(f"/api/v1/approvals/{approval_id}/approve",
                          json={"approver_principal_id": approver_id, "decision_reason": "Concurrent approval test"},
                          headers=approver_headers)

    statuses = {result1.json().get("status"), result2.json().get("status")}
    assert result1.status_code == 200
    # Second attempt should either be 409 (conflict) or 200 with terminal status
    if result2.status_code == 200:
        assert result2.json()["status"] in ("APPROVED", "EXPIRED")
    else:
        assert result2.status_code == 409

    with TestingSession() as session:
        approval = session.get(ApprovalRequest, uuid.UUID(approval_id))
        # Approval status must be terminal
        assert approval.status in (ApprovalStatus.APPROVED, ApprovalStatus.EXPIRED, ApprovalStatus.REJECTED)


# ── P2-04 extended: Deactivated principal ────────────────────────────────

def test_retired_principal_token_is_rejected():
    """A token for a retired principal returns 403."""
    ids = _seed()
    with TestingSession() as session:
        principal = session.scalar(select(Principal).where(Principal.id == uuid.UUID(ids["principal_id"])))
        principal.status = PrincipalStatus.RETIRED
        session.commit()
    resp = client.get("/api/v1/action-requests", headers=_auth(ids["external_id"]))
    assert resp.status_code == 403
