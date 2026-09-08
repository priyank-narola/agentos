<!-- STATUS: STALE / HISTORICAL. This document predates the verified Chunks 1-3 state and may contradict current runtime behavior (e.g., sandbox execution, FinancialExecution ledger, tenant model, REST/MCP auth). Canonical sources: AGENTOS_OPERATING_PROMPT.md and AGENTOS_STATE.md. Do not use as source of truth. -->
# Phase 3 Registry API

The registry API manages authorization-domain records. It is not an authentication or authorization boundary yet. Runtime action requests must not be sent to these endpoints.

## Common behavior

- Base path: `/api/v1`
- JSON request and response bodies
- Invalid UUIDs and enum values return FastAPI validation responses (`422`)
- Unknown records return `404`
- Duplicate stable identities return `409`
- Invalid relationship references return `400`
- Database stack traces are not returned to clients

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/principals` | Create authorization-domain principal |
| GET | `/principals` | List principals |
| GET | `/principals/{id}` | Retrieve principal |
| POST | `/agents` | Register agent identity |
| GET | `/agents` | List agents |
| GET | `/agents/{id}` | Retrieve agent |
| PATCH | `/agents/{id}` | Update mutable agent metadata |
| POST | `/agents/{id}/suspend` | Set agent status to `SUSPENDED` |
| POST | `/agents/{id}/retire` | Set agent status to `RETIRED` |
| POST | `/tools` | Register tool |
| GET | `/tools` | List tools |
| GET | `/tools/{id}` | Retrieve tool |
| PATCH | `/tools/{id}` | Update tool metadata |
| POST | `/tools/{id}/actions` | Register action under a tool |
| GET | `/tools/{id}/actions` | List actions under a tool |
| GET | `/actions/{id}` | Retrieve action |
| PATCH | `/actions/{id}` | Update action metadata |
| POST | `/resources` | Register logical resource |
| GET | `/resources` | List resources |
| GET | `/resources/{id}` | Retrieve resource |
| PATCH | `/resources/{id}` | Update resource metadata |
| POST | `/delegations` | Record explicit principal-to-agent delegation |
| GET | `/delegations` | List delegations |
| GET | `/delegations/{id}` | Retrieve delegation |

Example agent request:

```json
{
  "name": "FinanceAgent",
  "owner_principal_id": "00000000-0000-0000-0000-000000000001",
  "purpose": "Finance operations",
  "version": "1.0.0",
  "risk_classification": "HIGH",
  "description": "Controlled finance assistant"
}
```

## Limitations

There is no authentication, policy evaluation, delegation evaluation, runtime gateway, risk engine, approval workflow, or action execution in Phase 3.

## Runtime gateway endpoints

Phase 5 adds:

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/action-requests` | Validate, evaluate, persist, and enforce a non-executing action request |
| GET | `/action-requests` | Read joined request and decision evidence |
| GET | `/action-requests/{id}` | Read one joined request and decision |

The POST body accepts principal, agent, action, resource, parameters, and idempotency key. It intentionally rejects caller-provided `tool_id`, decision, risk, policy, or authorization fields. Tool resolution comes from the persisted action relationship.

## Approval endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/approvals` | List approval requests |
| GET | `/approvals/{id}` | Read one bound approval request |
| POST | `/approvals/{id}/approve` | Approve a pending request |
| POST | `/approvals/{id}/reject` | Reject a pending request |
| POST | `/approvals/{id}/cancel` | Cancel a pending request |

Transition endpoints accept only `approver_principal_id` and reject extra decision/action/risk fields. Approval authorizes execution in principle but does not execute external actions.
