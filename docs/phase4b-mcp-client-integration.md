# AgentOS Phase 4B — External MCP Client Integration & Technical Specification

**System Version**: AgentOS MCP Gateway v1.0 (Streamable HTTP Edition)  
**Supported Protocols**: MCP Streamable HTTP (`POST /mcp`, `POST /mcp/v1/messages`), Discovery Metadata (`GET /.well-known/mcp`)  

---

## 1. Protocol Architecture & Authentication

AgentOS implements the Model Context Protocol (MCP) Streamable HTTP specification. Remote AI agents interact via standard JSON-RPC 2.0 requests over HTTP POST.

### Authentication & Token Validation
Clients pass OAuth Bearer tokens in the `Authorization` header:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Unauthenticated requests return HTTP 401 Unauthorized with standard challenge headers:
```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="AgentOS", error="invalid_token", scope="mcp:execute_action"
```

---

## 2. Client Configurations

### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "agentos-control-plane": {
      "url": "https://agentos-api-qm2r.onrender.com/mcp",
      "headers": {
        "Authorization": "Bearer <AGENTOS_OAUTH_TOKEN>",
        "MCP-Protocol-Version": "2024-11-05"
      }
    }
  }
}
```

### Cursor (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "agentos": {
      "url": "https://agentos-api-qm2r.onrender.com/mcp/v1/messages",
      "headers": {
        "Authorization": "Bearer <AGENTOS_OAUTH_TOKEN>",
        "MCP-Protocol-Version": "2024-11-25"
      }
    }
  }
}
```

---

## 3. Integration Health Diagnostic Endpoint (`GET /api/v1/integration/health`)

Read-only status monitoring endpoint for enterprise integration readiness:

```json
{
  "status": "HEALTHY",
  "integration_readiness": "READY_FOR_CUSTOMER_PILOT",
  "components": {
    "mcp_streamable_http_transport": {"status": "ACTIVE", "protocol_version": "2024-11-05"},
    "oauth_bearer_authentication": {"status": "ACTIVE", "challenge_format": "WWW-Authenticate: Bearer"},
    "mcp_tool_discovery": {"status": "ACTIVE", "tools_count": 1},
    "authorization_gateway": {"status": "ACTIVE", "isolation_model": "Strict SecurityContext Scoping"},
    "risk_engine": {"status": "ACTIVE", "risk_tiers": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
    "approval_workflow_engine": {"status": "ACTIVE", "sod_enforcement": "STRICT", "toctou_revalidation": "ENABLED"},
    "execution_sandbox": {"status": "ACTIVE", "provider": "SandboxPaymentProvider", "real_money_movement": false},
    "audit_telemetry": {"status": "ACTIVE", "integrity_checker": "7-Violation Verification Engine"}
  },
  "timestamp": "2026-08-25T16:41:00Z"
}
```
