import pytest
from fastapi.testclient import TestClient
from mcp import MCPError
from app.main import app
from app.api.mcp import mcp_server

client = TestClient(app)

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
    # Find /mcp mount route
    mcp_mount = next((route for route in app.routes if getattr(route, "path", None) == "/mcp"), None)
    assert mcp_mount is not None, "MCP app not mounted at /mcp"
    
    # Verify sub-routes on mounted app
    mounted_app = mcp_mount.app
    paths = [r.path for r in mounted_app.routes]
    assert "/sse" in paths
    assert "/messages" in paths

@pytest.mark.asyncio
async def test_mcp_server_initializes_correctly():
    """Verify that the MCP server metadata and tool discovery are correct."""
    assert mcp_server.name == "AgentOS MCP Server"
    assert mcp_server.version == "0.1.0"
    
    tools = await mcp_server.list_tools()
    tool_names = [t.name for t in tools]
    assert "execute_action" in tool_names

@pytest.mark.asyncio
async def test_unauthenticated_mcp_action_fails_closed():
    """Verify that calling execute_action fails closed with MCPError/ValueErrors."""
    with pytest.raises(MCPError) as exc_info:
        await mcp_server.call_tool(
            "execute_action",
            arguments={
                "action_id": "97862a8a-8fa4-4a6e-a874-dfb52b394290",
                "resource_id": "0802886b-1263-49fa-9360-193d1332fae3",
                "parameters": {}
            }
        )
    assert "Authentication required" in str(exc_info.value)
    assert exc_info.value.code == -32000
