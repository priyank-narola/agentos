# AgentOS Phase 4A — External MCP Client Integration & Security Guide

**Target Audience**: AI Engineering Leads, Systems Integrators, External Developer Partners  
**System Version**: AgentOS MCP Gateway v1.0 (Streamable HTTP Edition)  
**Supported Clients**: Claude Desktop, Cursor, Custom LangChain / AutoGen / CrewAI MCP Clients  

---

## 1. Connecting an MCP Client to AgentOS

To connect an external AI application to AgentOS over MCP Streamable HTTP, configure the client's MCP configuration JSON:

### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "agentos-control-plane": {
      "command": "curl",
      "args": [
        "-s",
        "-X", "POST",
        "-H", "Authorization: Bearer <AGENTOS_OAUTH_BEARER_TOKEN>",
        "-H", "Content-Type: application/json",
        "-H", "MCP-Protocol-Version: 2024-11-05",
        "https://agentos-api-qm2r.onrender.com/mcp"
      ]
    }
  }
}
```

### Cursor (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "agentos": {
      "url": "https://agentos-api-qm2r.onrender.com/mcp",
      "headers": {
        "Authorization": "Bearer <AGENTOS_OAUTH_BEARER_TOKEN>",
        "MCP-Protocol-Version": "2024-11-25"
      }
    }
  }
}
```

---

## 2. Standard Protocol Workflow

1. **Discovery & Handshake**: Client sends `POST /mcp` with method `initialize`. AgentOS responds with server capabilities and protocol version `2024-11-05`.
2. **Tool Discovery**: Client sends method `tools/list`. AgentOS returns the `execute_action` tool schema:
   ```json
   {
     "name": "execute_action",
     "description": "Request execution of a formal action on a resource via the AgentOS Action Gateway",
     "inputSchema": {
       "type": "object",
       "properties": {
         "action_id": {"type": "string"},
         "resource_id": {"type": "string"},
         "parameters": {"type": "object"},
         "idempotency_key": {"type": "string"}
       },
       "required": ["action_id", "resource_id"]
     }
   }
   ```
3. **Action Execution**: Client invokes `tools/call` with argument payload:
   ```json
   {
     "jsonrpc": "2.0",
     "id": 1,
     "method": "tools/call",
     "params": {
       "name": "execute_action",
       "arguments": {
         "action_id": "00000000-0000-0000-0000-000000000002",
         "resource_id": "00000000-0000-0000-0000-000000000003",
         "parameters": {
           "source_account_id": "ACC-01",
           "destination_account_id": "ACC-02",
           "amount": "2500.00",
           "currency": "USD"
         }
       }
     }
   }
   ```

---

## 3. Important Integration Rules for Developers

1. **Identity is Derived Strictly from Token**: Never pass `principal_id` or `agent_id` inside tool arguments or parameters. AgentOS strips all caller-supplied identity claims and resolves identity strictly from verified JWT token claims.
2. **Handle Approval Responses**: If an action requires human approval (e.g. high-risk wire transfers), AgentOS returns `decision: "PENDING_APPROVAL"`. The client must check `action_request_id` and wait for out-of-band approval via the Control Plane Dashboard.
3. **Idempotency Keys**: Clients can optionally supply an `idempotency_key`. If omitted, AgentOS deterministically generates a SHA-256 idempotency hash over the trusted identity, action, resource, and canonical business parameters.
