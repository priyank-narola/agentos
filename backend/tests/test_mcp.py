import asyncio
import json
import time
import uuid
import jwt
import pytest
from fastapi.testclient import TestClient
from mcp import MCPError
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.api.mcp as mcp_module
from app.api.mcp import (
    mcp_server,
    token_validator,
    identity_resolver,
    request_authorization_var,
    request_db_session_var,
    sanitize_parameters,
    generate_deterministic_idempotency_key,
    MCPTransportContextMiddleware,
)
from app.db.base import Base
from app.db.models import (
    Action,
    ActionRequest,
    Agent,
    AgentStatus,
    CapabilityStatus,
    Decision,
    DecisionType,
    Delegation,
    DelegationStatus,
    Policy,
    PolicyEffect,
    PolicyRule,
    PolicyStatus,
    Principal,
    PrincipalStatus,
    PrincipalType,
    Resource,
    ResourceSensitivity,
    ResourceStatus,
    RiskClassification,
    Tool,
)
from app.main import app
from app.services.gateway import GatewayService

client = TestClient(app)
SECRET_KEY = "test-mcp-secret-key-999"


@pytest.fixture
def db_engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    with Session(db_engine) as session:
        tok = request_db_session_var.set(session)
        yield session
        request_db_session_var.reset(tok)


@pytest.fixture(autouse=True)
def setup_mcp_auth_validator():
    # Configure token_validator with secret key for test tokens
    token_validator.secret_key = SECRET_KEY
    token_validator.expected_issuer = "https://auth.agentos.com"
    token_validator.expected_audience = "https://agentos-api-qm2r.onrender.com"
    token_validator.required_scope = "agentos:execute"


def create_test_jwt(
    sub: str = "auth0|alice123",
    client_id: str = "FinanceBot-v1",
    scope: str = "agentos:read agentos:execute",
    iss: str = "https://auth.agentos.com",
    aud: str = "https://agentos-api-qm2r.onrender.com",
    secret: str = SECRET_KEY,
    expires_in: int = 900
) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "iss": iss,
        "aud": aud,
        "exp": now + expires_in,
        "nbf": now - 10,
        "iat": now,
        "scope": scope,
        "client_id": client_id
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def mcp_graph(db_session: Session):
    # Principal
    principal = Principal(
        id=uuid.uuid4(),
        type=PrincipalType.HUMAN,
        name="Alice Admin",
        external_id="auth0|alice123",
        status=PrincipalStatus.ACTIVE
    )
    db_session.add(principal)
    db_session.flush()

    # Agent
    agent = Agent(
        id=uuid.uuid4(),
        name="FinanceBot-v1",
        owner_principal_id=principal.id,
        purpose="Process financial requests",
        version="1.0.0",
        status=AgentStatus.ACTIVE,
        risk_classification=RiskClassification.LOW
    )
    db_session.add(agent)
    db_session.flush()

    # Delegation
    delegation = Delegation(
        id=uuid.uuid4(),
        principal_id=principal.id,
        agent_id=agent.id,
        scope="*",
        status=DelegationStatus.ACTIVE
    )
    db_session.add(delegation)
    db_session.flush()

    # Tool & Low-Risk Action
    tool = Tool(
        id=uuid.uuid4(),
        name="FinanceTool",
        description="Tool for financial operations",
        status=CapabilityStatus.ACTIVE
    )
    db_session.add(tool)
    db_session.flush()

    action_low = Action(
        id=uuid.uuid4(),
        tool_id=tool.id,
        name="process_invoice",
        description="Process low-risk invoice",
        risk_level=RiskClassification.LOW,
        status=CapabilityStatus.ACTIVE
    )
    db_session.add(action_low)

    action_high = Action(
        id=uuid.uuid4(),
        tool_id=tool.id,
        name="wire_funds",
        description="Wire funds out of account",
        risk_level=RiskClassification.HIGH,
        status=CapabilityStatus.ACTIVE
    )
    db_session.add(action_high)
    db_session.flush()

    # Resource
    resource = Resource(
        id=uuid.uuid4(),
        resource_type="invoice",
        resource_key="INV-2026-001",
        sensitivity=ResourceSensitivity.MEDIUM,
        status=ResourceStatus.ACTIVE
    )
    db_session.add(resource)
    db_session.flush()

    # Allow Policy
    policy = Policy(
        name="Allow Finance Actions",
        version=1,
        priority=10,
        status=PolicyStatus.ACTIVE
    )
    policy.rules = [
        PolicyRule(
            effect=PolicyEffect.ALLOW,
            action="process_invoice",
            resource_type="invoice",
            priority=10
        ),
        PolicyRule(
            effect=PolicyEffect.ALLOW,
            action="wire_funds",
            resource_type="invoice",
            priority=10
        )
    ]
    db_session.add(policy)
    db_session.commit()

    return {
        "principal": principal,
        "agent": agent,
        "delegation": delegation,
        "tool": tool,
        "action_low": action_low,
        "action_high": action_high,
        "resource": resource,
        "policy": policy
    }


def get_tool_text(res) -> str:
    if hasattr(res, "content") and res.content:
        item = res.content[0]
        return getattr(item, "text", str(item))
    return str(res)


def test_health_still_works():
    """Verify that existing REST /health endpoint is unaffected."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "agentos-api"}


def test_version_still_works():
    """Verify that existing REST /api/v1/version endpoint is unaffected."""
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert response.json()["name"] == "AgentOS API"


def test_mcp_endpoints_registered():
    """Verify that MCP SSE endpoints are mounted at /mcp/sse and /mcp/messages."""
    mcp_mount = next((route for route in app.routes if getattr(route, "path", None) == "/mcp"), None)
    assert mcp_mount is not None, "MCP app not mounted at /mcp"
    mounted_app = mcp_mount.app
    paths = [r.path for r in mounted_app.routes]
    assert "/sse" in paths
    assert "/messages" in paths


def test_rest_endpoints_do_not_execute_mcp_middleware():
    """Verify that non-MCP REST endpoints do not execute MCP transport middleware."""
    # Ensure request_authorization_var starts clean
    assert request_authorization_var.get() is None
    res = client.get("/health", headers={"Authorization": "Bearer rest-token-123"})
    assert res.status_code == 200
    # REST endpoint does not use or alter request_authorization_var
    assert request_authorization_var.get() is None


@pytest.mark.asyncio
async def test_mcp_server_initializes_correctly():
    """Verify that the MCP server metadata and tool discovery are correct."""
    assert mcp_server.name == "AgentOS MCP Server"
    assert mcp_server.version == "0.1.0"
    
    tools = await mcp_server.list_tools()
    tool_names = [t.name for t in tools]
    assert "execute_action" in tool_names


@pytest.mark.asyncio
async def test_missing_authorization_header_fails_closed():
    """Verify that calling execute_action without any transport authorization header fails closed."""
    tok = request_authorization_var.set(None)
    try:
        with pytest.raises(MCPError) as exc_info:
            await mcp_server.call_tool(
                "execute_action",
                arguments={
                    "action_id": str(uuid.uuid4()),
                    "resource_id": str(uuid.uuid4())
                }
            )
        assert "Authentication failed" in str(exc_info.value)
        assert exc_info.value.code == -32000
    finally:
        request_authorization_var.reset(tok)


@pytest.mark.asyncio
async def test_tool_argument_authorization_cannot_authenticate():
    """Verify that supplying authorization in tool arguments MUST NOT authenticate the request."""
    valid_token = create_test_jwt()
    # Explicitly ensure HTTP transport header is missing
    tok = request_authorization_var.set(None)
    try:
        with pytest.raises(MCPError) as exc_info:
            await mcp_server.call_tool(
                "execute_action",
                arguments={
                    "action_id": str(uuid.uuid4()),
                    "resource_id": str(uuid.uuid4()),
                    "authorization": f"Bearer {valid_token}"  # Passed as tool argument!
                }
            )
        # Must fail closed because transport header is missing!
        assert "Authentication failed: Missing Authorization header in request context" in str(exc_info.value)
    finally:
        request_authorization_var.reset(tok)


@pytest.mark.asyncio
async def test_mcp_metadata_authorization_cannot_authenticate():
    """Verify that authorization-like parameters inside tool parameters or metadata cannot authenticate."""
    valid_token = create_test_jwt()
    tok = request_authorization_var.set(None)
    try:
        with pytest.raises(MCPError) as exc_info:
            await mcp_server.call_tool(
                "execute_action",
                arguments={
                    "action_id": str(uuid.uuid4()),
                    "resource_id": str(uuid.uuid4()),
                    "parameters": {
                        "authorization": f"Bearer {valid_token}",
                        "meta": {"auth": valid_token}
                    }
                }
            )
        assert "Authentication failed: Missing Authorization header in request context" in str(exc_info.value)
    finally:
        request_authorization_var.reset(tok)


@pytest.mark.asyncio
async def test_malformed_bearer_token_rejected():
    """Verify that malformed bearer tokens are rejected cleanly."""
    tok = request_authorization_var.set("NotABearerTokenFormat")
    try:
        with pytest.raises(MCPError) as exc_info:
            await mcp_server.call_tool(
                "execute_action",
                arguments={
                    "action_id": str(uuid.uuid4()),
                    "resource_id": str(uuid.uuid4())
                }
            )
        assert "Authentication failed" in str(exc_info.value)
    finally:
        request_authorization_var.reset(tok)


@pytest.mark.asyncio
async def test_invalid_signature_rejected():
    """Verify that tokens signed with wrong secret key are rejected."""
    bad_token = create_test_jwt(secret="wrong-secret-key-123")
    tok = request_authorization_var.set(f"Bearer {bad_token}")
    try:
        with pytest.raises(MCPError) as exc_info:
            await mcp_server.call_tool(
                "execute_action",
                arguments={
                    "action_id": str(uuid.uuid4()),
                    "resource_id": str(uuid.uuid4())
                }
            )
        assert "Signature verification failed" in str(exc_info.value)
    finally:
        request_authorization_var.reset(tok)


@pytest.mark.asyncio
async def test_expired_token_rejected():
    """Verify that expired tokens are rejected."""
    expired_token = create_test_jwt(expires_in=-3600)
    tok = request_authorization_var.set(f"Bearer {expired_token}")
    try:
        with pytest.raises(MCPError) as exc_info:
            await mcp_server.call_tool(
                "execute_action",
                arguments={
                    "action_id": str(uuid.uuid4()),
                    "resource_id": str(uuid.uuid4())
                }
            )
        assert "Token has expired" in str(exc_info.value)
    finally:
        request_authorization_var.reset(tok)


@pytest.mark.asyncio
async def test_authorization_header_via_contextvar_authorized(db_session, mcp_graph):
    """Verify that HTTP Authorization header populated via request contextvar authorizes tool call."""
    token = create_test_jwt(client_id=str(mcp_graph["agent"].id))
    tok = request_authorization_var.set(f"Bearer {token}")
    try:
        res = await mcp_server.call_tool(
            "execute_action",
            arguments={
                "action_id": str(mcp_graph["action_low"].id),
                "resource_id": str(mcp_graph["resource"].id),
                "parameters": {"amount": 500}
            }
        )
        data = json.loads(get_tool_text(res))
        assert data["gateway_status"] == "AUTHORIZED"
        assert data["decision"] == "ALLOW"
        assert data["execution_status"] == "NOT_EXECUTED"
    finally:
        request_authorization_var.reset(tok)


@pytest.mark.asyncio
async def test_authenticated_missing_delegation_denied(db_session, mcp_graph):
    """Verify that missing delegation fails closed at identity resolution layer."""
    db_session.delete(mcp_graph["delegation"])
    db_session.commit()

    token = create_test_jwt(client_id=str(mcp_graph["agent"].id))
    tok = request_authorization_var.set(f"Bearer {token}")
    try:
        with pytest.raises(MCPError) as exc_info:
            await mcp_server.call_tool(
                "execute_action",
                arguments={
                    "action_id": str(mcp_graph["action_low"].id),
                    "resource_id": str(mcp_graph["resource"].id)
                }
            )
        assert "No delegation relationship exists" in str(exc_info.value)
    finally:
        request_authorization_var.reset(tok)


@pytest.mark.asyncio
async def test_authenticated_agent_unauthorized_action_blocked(db_session, mcp_graph):
    """Verify that an action with no matching allow policy evaluates to BLOCKED/DENY."""
    db_session.delete(mcp_graph["policy"])
    db_session.commit()

    token = create_test_jwt(client_id=str(mcp_graph["agent"].id))
    tok = request_authorization_var.set(f"Bearer {token}")
    try:
        res = await mcp_server.call_tool(
            "execute_action",
            arguments={
                "action_id": str(mcp_graph["action_low"].id),
                "resource_id": str(mcp_graph["resource"].id)
            }
        )
        data = json.loads(get_tool_text(res))
        assert data["gateway_status"] == "BLOCKED"
        assert data["decision"] == "DENY"
    finally:
        request_authorization_var.reset(tok)


@pytest.mark.asyncio
async def test_high_risk_action_requires_approval(db_session, mcp_graph):
    """Verify that high-risk action requires approval via Gateway."""
    token = create_test_jwt(client_id=str(mcp_graph["agent"].id))
    tok = request_authorization_var.set(f"Bearer {token}")
    try:
        res = await mcp_server.call_tool(
            "execute_action",
            arguments={
                "action_id": str(mcp_graph["action_high"].id),
                "resource_id": str(mcp_graph["resource"].id)
            }
        )
        data = json.loads(get_tool_text(res))
        assert data["gateway_status"] == "PENDING_APPROVAL"
        assert data["decision"] == "REQUIRE_APPROVAL"
        assert data["approval_required"] is True
        assert data["execution_status"] == "NOT_EXECUTED"
    finally:
        request_authorization_var.reset(tok)


@pytest.mark.asyncio
async def test_principal_and_agent_spoofing_in_args_ignored(db_session, mcp_graph):
    """Verify that client attempting to supply principal_id or agent_id in tool params is ignored."""
    token = create_test_jwt(client_id=str(mcp_graph["agent"].id))
    tok = request_authorization_var.set(f"Bearer {token}")
    fake_uuid = str(uuid.uuid4())

    try:
        res = await mcp_server.call_tool(
            "execute_action",
            arguments={
                "action_id": str(mcp_graph["action_low"].id),
                "resource_id": str(mcp_graph["resource"].id),
                "parameters": {
                    "principal_id": fake_uuid,
                    "agent_id": fake_uuid,
                    "amount": 100
                }
            }
        )
        data = json.loads(get_tool_text(res))
        assert data["gateway_status"] == "AUTHORIZED"

        # Inspect ActionRequest in DB to verify trusted Principal/Agent were used
        req = db_session.get(ActionRequest, uuid.UUID(data["action_request_id"]))
        assert req.principal_id == mcp_graph["principal"].id
        assert req.agent_id == mcp_graph["agent"].id
        assert req.principal_id != uuid.UUID(fake_uuid)
        assert req.agent_id != uuid.UUID(fake_uuid)
        assert "principal_id" not in req.parameters
        assert "agent_id" not in req.parameters
    finally:
        request_authorization_var.reset(tok)


@pytest.mark.asyncio
async def test_nested_parameter_spoofing_stripped(db_session, mcp_graph):
    """Verify that deeply nested forbidden override keys are recursively stripped."""
    token = create_test_jwt(client_id=str(mcp_graph["agent"].id))
    tok = request_authorization_var.set(f"Bearer {token}")

    try:
        res = await mcp_server.call_tool(
            "execute_action",
            arguments={
                "action_id": str(mcp_graph["action_high"].id),  # High risk
                "resource_id": str(mcp_graph["resource"].id),
                "parameters": {
                    "payload": {
                        "amount": 100,
                        "agent_id": "fake",
                        "meta": {
                            "approved": True,
                            "decision": "ALLOW",
                            "risk_score": 0,
                            "valid_note": "legitimate note"
                        }
                    }
                }
            }
        )
        data = json.loads(get_tool_text(res))
        # High risk action MUST still require approval!
        assert data["gateway_status"] == "PENDING_APPROVAL"
        assert data["decision"] == "REQUIRE_APPROVAL"

        req = db_session.get(ActionRequest, uuid.UUID(data["action_request_id"]))
        assert req.parameters == {
            "payload": {
                "amount": 100,
                "meta": {
                    "valid_note": "legitimate note"
                }
            }
        }
    finally:
        request_authorization_var.reset(tok)


@pytest.mark.asyncio
async def test_safe_error_responses_no_internal_exception_leakage(db_session, mcp_graph, monkeypatch):
    """Verify that unexpected internal exceptions do not leak stack trace or internal details."""
    token = create_test_jwt(client_id=str(mcp_graph["agent"].id))
    tok = request_authorization_var.set(f"Bearer {token}")

    def explode(*args, **kwargs):
        raise RuntimeError("Internal DB secret connection string postgresql://user:pass@localhost:5432/db")

    monkeypatch.setattr(GatewayService, "submit", explode)

    try:
        with pytest.raises(MCPError) as exc_info:
            await mcp_server.call_tool(
                "execute_action",
                arguments={
                    "action_id": str(mcp_graph["action_low"].id),
                    "resource_id": str(mcp_graph["resource"].id)
                }
            )
        err_msg = str(exc_info.value)
        assert "Internal server error during action execution" in err_msg
        assert "postgresql://" not in err_msg
        assert "secret" not in err_msg
        assert "RuntimeError" not in err_msg
    finally:
        request_authorization_var.reset(tok)


@pytest.mark.asyncio
async def test_deterministic_idempotency_key_generation(db_session, mcp_graph):
    """Verify that missing idempotency_key generates a deterministic SHA-256 key preventing duplicates."""
    token = create_test_jwt(client_id=str(mcp_graph["agent"].id))
    tok = request_authorization_var.set(f"Bearer {token}")

    try:
        # First call without explicit idempotency key
        res1 = await mcp_server.call_tool(
            "execute_action",
            arguments={
                "action_id": str(mcp_graph["action_low"].id),
                "resource_id": str(mcp_graph["resource"].id),
                "parameters": {"amount": 250}
            }
        )

        # Retry exact same request without idempotency key
        res2 = await mcp_server.call_tool(
            "execute_action",
            arguments={
                "action_id": str(mcp_graph["action_low"].id),
                "resource_id": str(mcp_graph["resource"].id),
                "parameters": {"amount": 250}
            }
        )

        data1 = json.loads(get_tool_text(res1))
        data2 = json.loads(get_tool_text(res2))
        assert data1["action_request_id"] == data2["action_request_id"]

        # Verify DB has exactly 1 ActionRequest
        expected_key = generate_deterministic_idempotency_key(
            principal_id=mcp_graph["principal"].id,
            agent_id=mcp_graph["agent"].id,
            action_id=mcp_graph["action_low"].id,
            resource_id=mcp_graph["resource"].id,
            parameters={"amount": 250}
        )
        count = db_session.scalar(
            select(func.count())
            .select_from(ActionRequest)
            .where(ActionRequest.idempotency_key == expected_key)
        )
        assert count == 1
    finally:
        request_authorization_var.reset(tok)


@pytest.mark.asyncio
async def test_concurrent_requests_authorization_context_isolation():
    """Verify that concurrent requests with different Authorization headers remain completely task-isolated."""
    auth_header_1 = "Bearer token-user-1"
    auth_header_2 = "Bearer token-user-2"

    async def task_user_1():
        t1 = request_authorization_var.set(auth_header_1)
        await asyncio.sleep(0.01)
        assert request_authorization_var.get() == auth_header_1
        request_authorization_var.reset(t1)

    async def task_user_2():
        t2 = request_authorization_var.set(auth_header_2)
        await asyncio.sleep(0.01)
        assert request_authorization_var.get() == auth_header_2
        request_authorization_var.reset(t2)

    await asyncio.gather(task_user_1(), task_user_2())
    # Verify cleanup
    assert request_authorization_var.get() is None


@pytest.mark.asyncio
async def test_concurrent_safe_contextvar_db_session(db_engine):
    """Verify that request_db_session_var is isolated per task under concurrency."""
    with Session(db_engine) as session1, Session(db_engine) as session2:
        async def task1():
            t1 = request_db_session_var.set(session1)
            await asyncio.sleep(0.01)
            assert request_db_session_var.get() is session1
            request_db_session_var.reset(t1)

        async def task2():
            t2 = request_db_session_var.set(session2)
            await asyncio.sleep(0.01)
            assert request_db_session_var.get() is session2
            request_db_session_var.reset(t2)

        await asyncio.gather(task1(), task2())
