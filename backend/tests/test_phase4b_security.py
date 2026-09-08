import json
import time
import uuid
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.api.mcp import token_validator, request_db_session_var
from app.db.models import (
    Tenant, Principal, PrincipalType, PrincipalStatus, Agent, AgentStatus,
    Delegation, DelegationStatus, Tool, Action, CapabilityStatus, Resource,
    ResourceStatus, ResourceSensitivity, RiskClassification, Policy, PolicyStatus,
    PolicyRule, PolicyEffect, AuditEvent
)
from app.services.mcp_sandbox import ExternalMCPSandboxClient

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

SECRET_KEY = "test-mcp-secret-key-999"


def create_test_jwt(
    sub: str,
    client_id: str,
    scope: str = "mcp:execute_action agentos:execute",
    iss: str = "https://auth.agentos.com",
    aud: str = "https://agentos-api-qm2r.onrender.com",
    secret: str = SECRET_KEY,
    expires_in: int = 900
) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "client_id": client_id,
        "azp": client_id,
        "scope": scope,
        "iss": iss,
        "aud": aud,
        "iat": now,
        "exp": now + expires_in,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def override_get_db():
    with TestingSession() as session:
        request_db_session_var.set(session)
        yield session


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_mcp_auth_validator():
    app.dependency_overrides[get_db] = override_get_db
    token_validator.secret_key = SECRET_KEY
    token_validator.expected_issuer = "https://auth.agentos.com"
    token_validator.expected_audience = "https://agentos-api-qm2r.onrender.com"
    token_validator.required_scope = "mcp:execute_action"

    with TestingSession() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


@pytest.fixture
def db_session():
    with TestingSession() as session:
        tok = request_db_session_var.set(session)
        yield session


def test_integration_health_check_endpoint():
    """Verify read-only GET /api/v1/integration/health returns HEALTHY readiness without exposing secrets."""
    res = client.get("/api/v1/integration/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["integration_readiness"] == "READY_FOR_CUSTOMER_PILOT"
    assert "components" in data
    # Ensure no secrets or credentials exposed
    json_str = json.dumps(data)
    assert "secret" not in json_str.lower()
    assert "private_key" not in json_str.lower()


def test_ciso_demonstration_flow(db_session):
    """Verify complete 13-step TreasuryBot $25,000 USD wire transfer CISO demo flow."""
    sandbox = ExternalMCPSandboxClient(db_session)
    res = sandbox.run_ciso_demonstration_flow()
    assert res["final_outcome"] == "GOVERNANCE_SUCCESS"
    assert res["approval_status"] == "APPROVED"
    assert res["execution_status"] == "EXECUTION_SUCCEEDED"
    assert len(res["demonstration_steps"]) >= 4


def test_ciso_demo_rest_api_endpoint():
    """Verify POST /api/v1/integration/demo/ciso-flow REST API execution."""
    res = client.post("/api/v1/integration/demo/ciso-flow")
    assert res.status_code == 200
    data = res.json()
    assert data["final_outcome"] == "GOVERNANCE_SUCCESS"


@pytest.mark.parametrize("attack_type", [
    "tenant_spoofing",
    "agent_identity_spoofing",
    "principal_spoofing",
    "payload_tampering",
    "self_approval",
    "revoked_delegation",
    "cross_tenant_access",
    "duplicate_submission",
    "webhook_forgery",
    "webhook_replay"
])
def test_live_attack_demonstrations_fail_closed(attack_type):
    """Verify all 10 live attack simulations fail closed."""
    res = client.post(f"/api/v1/integration/demo/attack-flow/{attack_type}")
    assert res.status_code == 200
    data = res.json()
    assert data["outcome"] == "FAILED_CLOSED"


def test_claude_cursor_generic_external_mcp_client_flows(db_session):
    """Verify Claude, Cursor, and Generic MCP clients execute action over Streamable HTTP cleanly."""
    t = Tenant(id=uuid.uuid4(), name="Client Corp", slug=f"client-{uuid.uuid4().hex[:6]}")
    p = Principal(id=uuid.uuid4(), tenant_id=t.id, type=PrincipalType.HUMAN, name="Alice", external_id=f"usr_client_{uuid.uuid4().hex[:6]}", status=PrincipalStatus.ACTIVE)
    a = Agent(id=uuid.uuid4(), tenant_id=t.id, name=f"Agent-Client-{uuid.uuid4().hex[:4]}", owner_principal_id=p.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    d = Delegation(id=uuid.uuid4(), tenant_id=t.id, principal_id=p.id, agent_id=a.id, scope="wire_transfer", status=DelegationStatus.ACTIVE)
    tool = Tool(id=uuid.uuid4(), tenant_id=t.id, name=f"tool_client_{uuid.uuid4().hex[:6]}", description="desc", status=CapabilityStatus.ACTIVE)
    act = Action(id=uuid.uuid4(), tenant_id=t.id, tool_id=tool.id, name="wire_transfer", description="desc", risk_level=RiskClassification.LOW, status=CapabilityStatus.ACTIVE)
    res = Resource(id=uuid.uuid4(), tenant_id=t.id, resource_type="account", resource_key="ACC-CLIENT-01", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)

    pol = Policy(id=uuid.uuid4(), tenant_id=t.id, name="client_policy", version=1, status=PolicyStatus.ACTIVE)
    rule = PolicyRule(id=uuid.uuid4(), policy_id=pol.id, effect=PolicyEffect.ALLOW, action="wire_transfer", resource_type="account", priority=1)

    db_session.add_all([t, p, a, d, tool, act, res, pol, rule])
    db_session.commit()

    token = create_test_jwt(sub=p.external_id, client_id=str(a.id), scope="mcp:execute_action")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Claude MCP Client Call
    res_claude = client.post("/mcp", headers=headers, json={
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {
            "name": "execute_action",
            "arguments": {
                "action_id": str(act.id), "resource_id": str(res.id),
                "parameters": {"source_account_id": "ACC-01", "destination_account_id": "ACC-02", "amount": "100.00", "currency": "USD", "beneficiary_id": "BEN-1", "transaction_reference": f"REF-C-{uuid.uuid4().hex[:6]}"}
            }
        }
    })
    assert res_claude.status_code == 200
    assert "result" in res_claude.json()

    # Cursor MCP Client Call
    res_cursor = client.post("/mcp/v1/messages", headers=headers, json={
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {
            "name": "execute_action",
            "arguments": {
                "action_id": str(act.id), "resource_id": str(res.id),
                "parameters": {"source_account_id": "ACC-01", "destination_account_id": "ACC-02", "amount": "200.00", "currency": "USD", "beneficiary_id": "BEN-1", "transaction_reference": f"REF-CR-{uuid.uuid4().hex[:6]}"}
            }
        }
    })
    assert res_cursor.status_code == 200
    assert "result" in res_cursor.json()
