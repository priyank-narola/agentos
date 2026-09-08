import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.db.models import (
    Tenant, Principal, PrincipalType, PrincipalStatus, Agent, AgentStatus,
    Delegation, DelegationStatus, Tool, Action, CapabilityStatus, Resource,
    ResourceStatus, ResourceSensitivity, RiskClassification, Policy, PolicyStatus,
    PolicyRule, PolicyEffect, ActionRequest, ActionRequestStatus, ApprovalRequest,
    ApprovalStatus, AuditEvent, ActorType, FinancialExecution, ExecutionState
)
from app.main import app
from app.services.observability import ObservabilityService
from app.financial import compute_payload_digest


engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    with TestingSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    with TestingSession() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


@pytest.fixture
def db_session():
    with TestingSession() as session:
        yield session


@pytest.fixture
def multi_tenant_obs_setup(db_session):
    t1 = Tenant(id=uuid.uuid4(), name="Tenant A", slug=f"ta-{uuid.uuid4().hex[:6]}")
    t2 = Tenant(id=uuid.uuid4(), name="Tenant B", slug=f"tb-{uuid.uuid4().hex[:6]}")

    p1 = Principal(id=uuid.uuid4(), tenant_id=t1.id, type=PrincipalType.HUMAN, name="Alice A", external_id="usr_a", status=PrincipalStatus.ACTIVE)
    p2 = Principal(id=uuid.uuid4(), tenant_id=t2.id, type=PrincipalType.HUMAN, name="Bob B", external_id="usr_b", status=PrincipalStatus.ACTIVE)

    a1 = Agent(id=uuid.uuid4(), tenant_id=t1.id, name="Agent A", owner_principal_id=p1.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    a2 = Agent(id=uuid.uuid4(), tenant_id=t2.id, name="Agent B", owner_principal_id=p2.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)

    tool1 = Tool(id=uuid.uuid4(), tenant_id=t1.id, name="tool1", description="desc", status=CapabilityStatus.ACTIVE)
    act1 = Action(id=uuid.uuid4(), tenant_id=t1.id, tool_id=tool1.id, name="wire_transfer", description="desc", risk_level=RiskClassification.HIGH, status=CapabilityStatus.ACTIVE)
    res1 = Resource(id=uuid.uuid4(), tenant_id=t1.id, resource_type="account", resource_key="ACC_A", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)

    tool2 = Tool(id=uuid.uuid4(), tenant_id=t2.id, name="tool2", description="desc", status=CapabilityStatus.ACTIVE)
    act2 = Action(id=uuid.uuid4(), tenant_id=t2.id, tool_id=tool2.id, name="wire_transfer", description="desc", risk_level=RiskClassification.HIGH, status=CapabilityStatus.ACTIVE)
    res2 = Resource(id=uuid.uuid4(), tenant_id=t2.id, resource_type="account", resource_key="ACC_B", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)

    req1 = ActionRequest(id=uuid.uuid4(), tenant_id=t1.id, principal_id=p1.id, agent_id=a1.id, action_id=act1.id, resource_id=res1.id, parameters={"amount": "100.00"}, status=ActionRequestStatus.COMPLETED, idempotency_key=f"idem-{uuid.uuid4()}")
    req2 = ActionRequest(id=uuid.uuid4(), tenant_id=t2.id, principal_id=p2.id, agent_id=a2.id, action_id=act2.id, resource_id=res2.id, parameters={"amount": "500.00"}, status=ActionRequestStatus.COMPLETED, idempotency_key=f"idem-{uuid.uuid4()}")

    evt1 = AuditEvent(id=uuid.uuid4(), tenant_id=t1.id, actor_type=ActorType.AGENT, actor_id=a1.id, action_request_id=req1.id, event_type="ACTION_REQUEST_RECEIVED", event_data={"amount": "100.00"})
    evt2 = AuditEvent(id=uuid.uuid4(), tenant_id=t2.id, actor_type=ActorType.AGENT, actor_id=a2.id, action_request_id=req2.id, event_type="ACTION_REQUEST_RECEIVED", event_data={"amount": "500.00"})

    db_session.add_all([t1, t2, p1, p2, a1, a2, tool1, act1, res1, tool2, act2, res2, req1, req2, evt1, evt2])
    db_session.commit()

    return {
        "t1": t1, "t2": t2, "p1": p1, "p2": p2, "a1": a1, "a2": a2, "req1": req1, "req2": req2
    }


def test_cross_tenant_header_query_mismatch_forbidden(multi_tenant_obs_setup):
    """1 & 2. Verify header and query tenant_id mismatch triggers 403 Forbidden."""
    t1 = multi_tenant_obs_setup["t1"]
    t2 = multi_tenant_obs_setup["t2"]

    response = client.get(
        f"/api/v1/observability/metrics?tenant_id={t1.id}",
        headers={"X-Tenant-ID": str(t2.id)}
    )
    assert response.status_code == 403
    assert "Cross-tenant access forbidden" in response.json()["detail"]


def test_zero_cross_tenant_data_leakage_in_timeline_and_aggregations(db_session, multi_tenant_obs_setup):
    """3, 10, 11. Verify zero data leakage across tenants in timeline, metrics, and pagination."""
    t1 = multi_tenant_obs_setup["t1"]
    t2 = multi_tenant_obs_setup["t2"]

    service = ObservabilityService(db_session)

    # Timeline for Tenant 1
    t1_timeline = service.get_security_timeline(tenant_id=t1.id)
    assert t1_timeline["total"] == 1
    assert t1_timeline["events"][0]["event_data"]["amount"] == "100.00"

    # Timeline for Tenant 2
    t2_timeline = service.get_security_timeline(tenant_id=t2.id)
    assert t2_timeline["total"] == 1
    assert t2_timeline["events"][0]["event_data"]["amount"] == "500.00"

    # Metrics for Tenant 1
    t1_metrics = service.get_security_dashboard_metrics(tenant_id=t1.id)
    assert t1_metrics["total_action_requests"] == 1

    # Metrics for Tenant 2
    t2_metrics = service.get_security_dashboard_metrics(tenant_id=t2.id)
    assert t2_metrics["total_action_requests"] == 1


def test_agent_posture_cross_tenant_access_blocked(db_session, multi_tenant_obs_setup):
    """12. Verify querying agent posture across tenant boundaries returns 404/None."""
    t1 = multi_tenant_obs_setup["t1"]
    a2 = multi_tenant_obs_setup["a2"]  # Agent A2 belongs to Tenant 2

    # Query Agent A2 using Tenant 1 scope -> returns None / 404
    service = ObservabilityService(db_session)
    posture = service.get_agent_security_posture(tenant_id=t1.id, agent_id=a2.id)
    assert posture is None

    response = client.get(f"/api/v1/observability/agents/{a2.id}/posture?tenant_id={t1.id}")
    assert response.status_code == 404


def test_action_request_detail_cross_tenant_blocked(multi_tenant_obs_setup):
    """4. Verify accessing ActionRequest from another tenant returns 404 Not Found."""
    t1 = multi_tenant_obs_setup["t1"]
    req2 = multi_tenant_obs_setup["req2"]  # Request 2 belongs to Tenant 2

    response = client.get(f"/api/v1/observability/action-requests/{req2.id}?tenant_id={t1.id}")
    assert response.status_code == 404


def test_audit_integrity_verification_execution_without_approval(db_session):
    """5. Verify audit integrity checker detects high-risk execution without human approval."""
    t = Tenant(id=uuid.uuid4(), name="Corp", slug=f"corp-{uuid.uuid4().hex[:6]}")
    p = Principal(id=uuid.uuid4(), tenant_id=t.id, type=PrincipalType.HUMAN, name="Alice", external_id="usr_a", status=PrincipalStatus.ACTIVE)
    a = Agent(id=uuid.uuid4(), tenant_id=t.id, name="Agent", owner_principal_id=p.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    tool = Tool(id=uuid.uuid4(), tenant_id=t.id, name="tool", description="desc", status=CapabilityStatus.ACTIVE)
    act = Action(id=uuid.uuid4(), tenant_id=t.id, tool_id=tool.id, name="wire_transfer", description="desc", risk_level=RiskClassification.HIGH, status=CapabilityStatus.ACTIVE)
    res = Resource(id=uuid.uuid4(), tenant_id=t.id, resource_type="account", resource_key="ACC1", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)

    req = ActionRequest(id=uuid.uuid4(), tenant_id=t.id, principal_id=p.id, agent_id=a.id, action_id=act.id, resource_id=res.id, parameters={"amount": "25000.00"}, status=ActionRequestStatus.COMPLETED, idempotency_key=f"idem-{uuid.uuid4()}")
    evt = AuditEvent(id=uuid.uuid4(), tenant_id=t.id, actor_type=ActorType.AGENT, actor_id=a.id, action_request_id=req.id, event_type="EXECUTION_SUCCEEDED", event_data={})
    exec_rec = FinancialExecution(id=uuid.uuid4(), tenant_id=t.id, action_request_id=req.id, provider_name="Sandbox", provider_transaction_id="TX1", provider_request_id="REQ1", status=ExecutionState.SUCCEEDED, payload_digest="digest1")

    db_session.add_all([t, p, a, tool, act, res, req, evt, exec_rec])
    db_session.commit()

    service = ObservabilityService(db_session)
    report = service.verify_audit_integrity(tenant_id=t.id)

    assert report["audit_integrity_status"] == "VIOLATIONS_DETECTED"
    violation_types = [v["type"] for v in report["violations"]]
    assert "EXECUTION_WITHOUT_APPROVAL" in violation_types


def test_audit_integrity_verification_execution_after_revoked_delegation(db_session):
    """6. Verify audit integrity checker detects execution completed under revoked delegation."""
    t = Tenant(id=uuid.uuid4(), name="Corp", slug=f"corp-{uuid.uuid4().hex[:6]}")
    p = Principal(id=uuid.uuid4(), tenant_id=t.id, type=PrincipalType.HUMAN, name="Alice", external_id="usr_a", status=PrincipalStatus.ACTIVE)
    a = Agent(id=uuid.uuid4(), tenant_id=t.id, name="Agent", owner_principal_id=p.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    d = Delegation(id=uuid.uuid4(), tenant_id=t.id, principal_id=p.id, agent_id=a.id, scope="wire_transfer", status=DelegationStatus.REVOKED)
    tool = Tool(id=uuid.uuid4(), tenant_id=t.id, name="tool", description="desc", status=CapabilityStatus.ACTIVE)
    act = Action(id=uuid.uuid4(), tenant_id=t.id, tool_id=tool.id, name="wire_transfer", description="desc", risk_level=RiskClassification.HIGH, status=CapabilityStatus.ACTIVE)
    res = Resource(id=uuid.uuid4(), tenant_id=t.id, resource_type="account", resource_key="ACC1", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)

    req = ActionRequest(id=uuid.uuid4(), tenant_id=t.id, principal_id=p.id, agent_id=a.id, action_id=act.id, resource_id=res.id, parameters={"amount": "100.00"}, status=ActionRequestStatus.COMPLETED, idempotency_key=f"idem-{uuid.uuid4()}")
    exec_rec = FinancialExecution(id=uuid.uuid4(), tenant_id=t.id, action_request_id=req.id, provider_name="Sandbox", provider_transaction_id="TX1", provider_request_id="REQ1", status=ExecutionState.SUCCEEDED, payload_digest="digest1")

    db_session.add_all([t, p, a, d, tool, act, res, req, exec_rec])
    db_session.commit()

    service = ObservabilityService(db_session)
    report = service.verify_audit_integrity(tenant_id=t.id)

    assert report["audit_integrity_status"] == "VIOLATIONS_DETECTED"
    violation_types = [v["type"] for v in report["violations"]]
    assert "EXECUTION_AFTER_REVOKED_DELEGATION" in violation_types


def test_audit_integrity_verification_payload_digest_mismatch(db_session):
    """7. Verify audit integrity checker detects mismatched payload digests."""
    t = Tenant(id=uuid.uuid4(), name="Corp", slug=f"corp-{uuid.uuid4().hex[:6]}")
    p = Principal(id=uuid.uuid4(), tenant_id=t.id, type=PrincipalType.HUMAN, name="Alice", external_id="usr_a", status=PrincipalStatus.ACTIVE)
    a = Agent(id=uuid.uuid4(), tenant_id=t.id, name="Agent", owner_principal_id=p.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    tool = Tool(id=uuid.uuid4(), tenant_id=t.id, name="tool", description="desc", status=CapabilityStatus.ACTIVE)
    act = Action(id=uuid.uuid4(), tenant_id=t.id, tool_id=tool.id, name="wire_transfer", description="desc", risk_level=RiskClassification.HIGH, status=CapabilityStatus.ACTIVE)
    res = Resource(id=uuid.uuid4(), tenant_id=t.id, resource_type="account", resource_key="ACC1", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)

    req = ActionRequest(id=uuid.uuid4(), tenant_id=t.id, principal_id=p.id, agent_id=a.id, action_id=act.id, resource_id=res.id, parameters={"amount": "100.00"}, status=ActionRequestStatus.COMPLETED, idempotency_key=f"idem-{uuid.uuid4()}")
    evt = AuditEvent(id=uuid.uuid4(), tenant_id=t.id, actor_type=ActorType.AGENT, actor_id=a.id, action_request_id=req.id, event_type="APPROVAL_REQUESTED", event_data={"payload_digest": "TAMPERED_DIGEST_HASH"})

    db_session.add_all([t, p, a, tool, act, res, req, evt])
    db_session.commit()

    service = ObservabilityService(db_session)
    report = service.verify_audit_integrity(tenant_id=t.id)

    assert report["audit_integrity_status"] == "VIOLATIONS_DETECTED"
    violation_types = [v["type"] for v in report["violations"]]
    assert "PAYLOAD_DIGEST_MISMATCH" in violation_types



def test_observability_apis_strictly_read_only():
    """8. Verify all observability endpoints operate strictly via GET and do not mutate state."""
    # Attempt POST/PATCH/DELETE on observability endpoints -> 405 Method Not Allowed
    routes = [
        "/api/v1/observability/timeline",
        "/api/v1/observability/metrics",
        "/api/v1/observability/risk",
        "/api/v1/observability/tenant/posture",
        "/api/v1/observability/audit/verify"
    ]
    for route in routes:
        assert client.post(route, json={}).status_code == 405
        assert client.patch(route, json={}).status_code == 405
        assert client.delete(route).status_code == 405
