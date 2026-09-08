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
    Delegation, DelegationStatus, Tool, Action, ActionRequest, CapabilityStatus, Resource,
    ResourceStatus, ResourceSensitivity, RiskClassification, Policy, PolicyStatus,
    PolicyRule, PolicyEffect, AuditEvent
)
from app.schemas import GatewayRequestCreate, PolicyEvaluationRequest
from app.services.mcp_benchmark import MCPPerformanceBenchmark

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)

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


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_mcp_auth_validator():
    token_validator.secret_key = SECRET_KEY
    token_validator.expected_issuer = "https://auth.agentos.com"
    token_validator.expected_audience = "https://agentos-api-qm2r.onrender.com"
    token_validator.required_scope = "mcp:execute_action"

    with Session(engine) as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


@pytest.fixture
def db_session():
    with Session(engine) as session:
        tok = request_db_session_var.set(session)
        def override_get_db():
            yield session
        app.dependency_overrides[get_db] = override_get_db
        yield session
        app.dependency_overrides.pop(get_db, None)
        request_db_session_var.reset(tok)


@pytest.fixture
def mcp_setup(db_session):
    """Seed test entities for MCP tests."""
    t = Tenant(id=uuid.uuid4(), name="MCP Corp", slug=f"mcp-{uuid.uuid4().hex[:6]}")
    p = Principal(id=uuid.uuid4(), tenant_id=t.id, type=PrincipalType.HUMAN, name="Alice", external_id=f"usr_mcp_{uuid.uuid4().hex[:6]}", status=PrincipalStatus.ACTIVE)
    a = Agent(id=uuid.uuid4(), tenant_id=t.id, name=f"Agent-MCP-{uuid.uuid4().hex[:4]}", owner_principal_id=p.id, purpose="Fin", version="1.0", risk_classification=RiskClassification.LOW, status=AgentStatus.ACTIVE)
    d = Delegation(id=uuid.uuid4(), tenant_id=t.id, principal_id=p.id, agent_id=a.id, scope="wire_transfer", status=DelegationStatus.ACTIVE)
    tool = Tool(id=uuid.uuid4(), tenant_id=t.id, name=f"tool_mcp_{uuid.uuid4().hex[:6]}", description="desc", status=CapabilityStatus.ACTIVE)
    act = Action(id=uuid.uuid4(), tenant_id=t.id, tool_id=tool.id, name="wire_transfer", description="desc", risk_level=RiskClassification.LOW, status=CapabilityStatus.ACTIVE)
    res = Resource(id=uuid.uuid4(), tenant_id=t.id, resource_type="account", resource_key="ACC-MCP-01", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)

    pol = Policy(id=uuid.uuid4(), tenant_id=t.id, name="mcp_policy", version=1, status=PolicyStatus.ACTIVE)
    rule = PolicyRule(id=uuid.uuid4(), policy_id=pol.id, effect=PolicyEffect.ALLOW, action="wire_transfer", resource_type="account", priority=1)

    db_session.add_all([t, p, a, d, tool, act, res, pol, rule])
    db_session.commit()

    token = create_test_jwt(sub=p.external_id, client_id=str(a.id), scope="mcp:execute_action")

    return {
        "tenant": t, "principal": p, "agent": a, "delegation": d,
        "tool": tool, "action": act, "resource": res, "token": token
    }


def make_params(amount: str = "100.00", ref_suffix: str = "") -> dict:
    return {
        "source_account_id": "ACC-01",
        "destination_account_id": "ACC-02",
        "amount": amount,
        "currency": "USD",
        "beneficiary_id": "BEN-1",
        "transaction_reference": f"REF-MCP-{ref_suffix or uuid.uuid4().hex[:6]}"
    }


def test_mcp_protected_resource_metadata():
    """Verify MCP Protected Resource Discovery Metadata endpoint."""
    res = client.get("/.well-known/mcp")
    assert res.status_code == 200
    data = res.json()
    assert data["transport"] == "Streamable-HTTP"
    assert data["protected_resource"]["authorization_type"] == "Bearer"
    assert "mcp:execute_action" in data["protected_resource"]["scopes"]


def test_claude_style_mcp_client_flow(mcp_setup):
    """Verify Claude-style MCP Client handshake, discovery, and execution."""
    token = mcp_setup["token"]
    act = mcp_setup["action"]
    res = mcp_setup["resource"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 1. Initialize
    res_init = client.post("/mcp", headers=headers, json={
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "Claude-Desktop", "version": "1.0.0"}}
    })
    assert res_init.status_code == 200
    assert res_init.json()["result"]["serverInfo"]["name"] == "AgentOS MCP Server"

    # 2. List tools
    res_tools = client.post("/mcp", headers=headers, json={
        "jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}
    })
    assert res_tools.status_code == 200
    tool_names = [t["name"] for t in res_tools.json()["result"]["tools"]]
    assert "execute_action" in tool_names

    # 3. Call tool
    res_call = client.post("/mcp", headers=headers, json={
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {
            "name": "execute_action",
            "arguments": {
                "action_id": str(act.id),
                "resource_id": str(res.id),
                "parameters": make_params("100.00", "claude")
            }
        }
    })
    assert res_call.status_code == 200
    output_text = res_call.json()["result"]["content"][0]["text"]
    assert "decision" in output_text or "action_request_id" in output_text


def test_cursor_style_mcp_client_flow(mcp_setup):
    """Verify Cursor-style MCP Client handshake and action execution."""
    token = mcp_setup["token"]
    act = mcp_setup["action"]
    res = mcp_setup["resource"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "MCP-Protocol-Version": "2024-11-25"}

    res_call = client.post("/mcp/v1/messages", headers=headers, json={
        "jsonrpc": "2.0", "id": 100, "method": "tools/call",
        "params": {
            "name": "execute_action",
            "arguments": {
                "action_id": str(act.id),
                "resource_id": str(res.id),
                "parameters": make_params("250.00", "cursor")
            }
        }
    })
    assert res_call.status_code == 200
    assert "result" in res_call.json()


def test_streamable_http_missing_and_invalid_auth():
    """Verify missing/invalid Authorization header fails closed with WWW-Authenticate header."""
    # Missing auth
    res_no_auth = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert res_no_auth.status_code == 401
    assert "WWW-Authenticate" in res_no_auth.headers

    # Malformed token
    res_bad_auth = client.post("/mcp", headers={"Authorization": "Bearer BAD_TOKEN_STRING"}, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert res_bad_auth.status_code == 401
    assert "WWW-Authenticate" in res_bad_auth.headers


def test_streamable_http_unsupported_protocol_version(mcp_setup):
    """Verify unsupported MCP-Protocol-Version returns 400 Bad Request."""
    headers = {"Authorization": f"Bearer {mcp_setup['token']}", "MCP-Protocol-Version": "1999-01-01"}
    res = client.post("/mcp", headers=headers, json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
    assert res.status_code == 400
    assert "Unsupported MCP-Protocol-Version" in res.json()["error"]["message"]


def test_streamable_http_invalid_content_type(mcp_setup):
    """Verify invalid Content-Type returns 415 Unsupported Media Type."""
    headers = {"Authorization": f"Bearer {mcp_setup['token']}", "Content-Type": "text/plain"}
    res = client.post("/mcp", headers=headers, content="RAW_TEXT")
    assert res.status_code == 415


def test_mcp_tool_argument_identity_spoofing_ignored(db_session, mcp_setup):
    """Verify identity claims supplied in tool arguments are stripped & ignored."""
    token = mcp_setup["token"]
    act = mcp_setup["action"]
    res = mcp_setup["resource"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    params = make_params("100.00", "spoof")
    params.update({
        "principal_id": str(uuid.uuid4()),
        "risk_level": "LOW",
        "approval_status": "APPROVED"
    })

    res_call = client.post("/mcp", headers=headers, json={
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {
            "name": "execute_action",
            "arguments": {
                "action_id": str(act.id),
                "resource_id": str(res.id),
                "parameters": params
            }
        }
    })
    assert res_call.status_code == 200
    output = json.loads(res_call.json()["result"]["content"][0]["text"])
    req_id = uuid.UUID(output["action_request_id"])

    act_req = db_session.get(ActionRequest, req_id)
    assert act_req is not None
    assert str(act_req.principal_id) == str(mcp_setup["principal"].id)
    assert "principal_id" not in act_req.parameters
    assert "risk_level" not in act_req.parameters
    assert "approval_status" not in act_req.parameters


def test_transport_authorization_parity(db_session, mcp_setup):
    """Prove REST Gateway and MCP Streamable HTTP produce identical authorization outcomes."""
    token = mcp_setup["token"]
    act = mcp_setup["action"]
    res = mcp_setup["resource"]
    p_params = make_params("500.00", "parity")

    # 1. Submit via REST Gateway
    headers = {"Authorization": f"Bearer {token}"}
    rest_res = client.post("/api/v1/action-requests", headers=headers, json={
        "principal_id": str(mcp_setup["principal"].id),
        "agent_id": str(mcp_setup["agent"].id),
        "action_id": str(act.id),
        "resource_id": str(res.id),
        "parameters": p_params,
        "idempotency_key": f"idem-parity-rest-{uuid.uuid4()}"
    })
    assert rest_res.status_code == 201
    rest_decision = rest_res.json()["decision"]

    # 2. Submit via MCP Streamable HTTP
    mcp_res = client.post("/mcp", headers=headers, json={
        "jsonrpc": "2.0", "id": 50, "method": "tools/call",
        "params": {
            "name": "execute_action",
            "arguments": {
                "action_id": str(act.id),
                "resource_id": str(res.id),
                "parameters": p_params,
                "idempotency_key": f"idem-parity-mcp-{uuid.uuid4()}"
            }
        }
    })
    assert mcp_res.status_code == 200
    mcp_output = json.loads(mcp_res.json()["result"]["content"][0]["text"])
    mcp_decision = mcp_output["decision"]

    assert rest_decision == mcp_decision


def test_mcp_performance_baseline_benchmark(db_session, mcp_setup):
    """Measure latency metrics (p50, p95, p99, max) across 100 synthetic requests."""
    benchmark = MCPPerformanceBenchmark(db_session, token_validator=token_validator)
    dummy_req = PolicyEvaluationRequest(
        principal_id=mcp_setup["principal"].id,
        agent_id=mcp_setup["agent"].id,
        tool_id=mcp_setup["tool"].id,
        action_id=mcp_setup["action"].id,
        resource_id=mcp_setup["resource"].id,
        parameters=make_params("100.00", "bench")
    )
    report = benchmark.run_benchmark(mcp_setup["token"], dummy_req, num_requests=100)

    metrics = report["metrics"]
    assert "token_validation_latency" in metrics
    assert "identity_resolution_latency" in metrics
    assert "policy_evaluation_latency" in metrics
    assert "risk_evaluation_latency" in metrics
    assert "complete_mcp_authorization_latency" in metrics
