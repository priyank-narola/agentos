<!-- STATUS: STALE / HISTORICAL. This document predates the verified Chunks 1-3 state and may contradict current runtime behavior (e.g., sandbox execution, FinancialExecution ledger, tenant model, REST/MCP auth). Canonical sources: AGENTOS_OPERATING_PROMPT.md and AGENTOS_STATE.md. Do not use as source of truth. -->
# Runtime Action Gateway

Phase 5 adds the single server-side interception boundary for hypothetical agent actions:

```text
Agent request
  -> Runtime Gateway
  -> ActionRequest
  -> Deterministic Policy Evaluator
  -> Decision
  -> AUTHORIZED / BLOCKED / PENDING_APPROVAL
  -> NO EXTERNAL EXECUTION
```

## Pipeline

1. Receive and validate `principal_id`, `agent_id`, `action_id`, `resource_id`, `parameters`, and `idempotency_key`.
2. Check the idempotency key and return the existing result for an identical canonical request.
3. Resolve principal, agent, action, and resource.
4. Derive the tool exclusively from `Action.tool_id`; `tool_id` is not accepted in the gateway request schema.
5. Persist `ActionRequest`.
6. Append `ACTION_REQUEST_RECEIVED`.
7. Calculate deterministic risk and append `RISK_EVALUATED`.
8. Pass risk context to the Phase 4 deterministic evaluator.
9. Persist a separate `Decision`, including `risk_score`, using `BLOCK` for the evaluation contract's `DENY` result.
10. Append policy and outcome audit events.
11. Return `NOT_EXECUTED` for every outcome.

When the result is `REQUIRE_APPROVAL`, the gateway also creates one bound `ApprovalRequest` with a 15-minute expiry and appends `APPROVAL_REQUESTED`. Approval processing remains a separate workflow and never executes the action.

## Decision mapping

| Evaluator | Gateway | Persistence |
| --- | --- | --- |
| `ALLOW` | `AUTHORIZED` | `ALLOW` |
| `DENY` | `BLOCKED` | `BLOCK` |
| `REQUIRE_APPROVAL` | `PENDING_APPROVAL` | `REQUIRE_APPROVAL` |

No external or simulated tool is called in Phase 5.

Risk provides contextual evidence; it does not authorize actions. The deterministic policy evaluator remains authoritative.

## Security boundary

The caller cannot provide a decision, risk result, matched policy, or tool ID. Internal errors are returned as non-authorizing client errors and the transaction is rolled back. This phase does not authenticate callers, so the API is not a complete production access boundary yet.
