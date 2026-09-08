<!-- STATUS: STALE / HISTORICAL. This document predates the verified Chunks 1-3 state and may contradict current runtime behavior (e.g., sandbox execution, FinancialExecution ledger, tenant model, REST/MCP auth). Canonical sources: AGENTOS_OPERATING_PROMPT.md and AGENTOS_STATE.md. Do not use as source of truth. -->
# Action Request Lifecycle

An action request is the immutable-in-meaning input record. The decision is a separate server-generated record.

```text
RECEIVED
  -> EVALUATED       (ALLOW or BLOCK)
  -> APPROVAL_PENDING (REQUIRE_APPROVAL)
```

Every gateway response also reports `execution_status: NOT_EXECUTED`. Phase 5 deliberately stops at authorization persistence.

Before policy evaluation, Phase 6 appends one `RISK_EVALUATED` event and stores its normalized score with the eventual decision. Risk evidence does not change the request identity and does not independently authorize it.

## Idempotency

`idempotency_key` is unique in the database. The gateway canonicalizes principal, agent, action, resource, and parameters with sorted JSON keys. A retry with the same key and identical canonical content returns the existing request/decision. Reuse with different content returns `409 Conflict`. No duplicate request or decision is created.

## Audit evidence

The gateway appends:

- `ACTION_REQUEST_RECEIVED`
- `RISK_EVALUATED`
- `POLICY_EVALUATED`
- `ACTION_AUTHORIZED`
- `ACTION_BLOCKED`
- `APPROVAL_REQUIRED`

When a request requires approval, `ApprovalRequest` remains bound to the original request, risk evidence, and policy decision. A later human approval creates a separate final `ALLOW` decision with `HUMAN_APPROVAL`; the original evaluation is not rewritten.

Events reference request and decision IDs where available and are never updated as part of a retry.
