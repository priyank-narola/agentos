"""MCP discovery / metadata tests.

Covers the OAuth protected-resource metadata document advertised by the MCP
token validator's WWW-Authenticate ``resource_metadata`` parameter, and the
explicit SSE deprecation/sunset state.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_well_known_mcp_metadata():
    response = client.get("/.well-known/mcp")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "AgentOS MCP Server"
    assert "tools" in body["capabilities"]
    assert body["protected_resource"]["resource_id"] == "urn:agentos:mcp:action-gateway"


def test_oauth_protected_resource_metadata():
    response = client.get("/.well-known/oauth-protected-resource")
    assert response.status_code == 200
    body = response.json()
    assert body["resource"] == "urn:agentos:mcp:action-gateway"
    assert "scopes_supported" in body
    assert "agentos:execute" in body["scopes_supported"]
    # Must list at least one authorization server (config-derived).
    assert len(body["authorization_servers"]) >= 1


def test_legacy_sse_endpoint_is_explicitly_deprecated():
    # Decision (W18): SSE remains until its scheduled sunset (2026-12-31) for
    # legacy MCP client compatibility, then must be removed. The endpoint must
    # clearly signal deprecation and point clients at Streamable HTTP.
    response = client.get("/mcp/sse")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "deprecated"
    assert "Deprecation" in response.headers
    assert "Sunset" in response.headers
    assert "/mcp" in body["migration_target"]
