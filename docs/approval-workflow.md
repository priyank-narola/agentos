<!-- STATUS: STALE / HISTORICAL. This document predates the verified Chunks 1-3 state and may contradict current runtime behavior (e.g., sandbox execution, FinancialExecution ledger, tenant model, REST/MCP auth). Canonical sources: AGENTOS_OPERATING_PROMPT.md and AGENTOS_STATE.md. Do not use as source of truth. -->
# Human Approval Workflow

Phase 7 handles actions that the policy evaluator returns as `REQUIRE_APPROVAL`.

```text
Action Request
  -> Risk
  -> Policy
  -> REQUIRE_APPROVAL
  -> Approval Request
  -> Human Decision
  -> Authorization
  -> NOT EXECUTED
```

## State machine

```text
PENDING -> APPROVED
PENDING -> REJECTED
PENDING -> EXPIRED
PENDING -> CANCELLED
```

Terminal states cannot transition again. Approval is bound to the original `ActionRequest`; the reviewer cannot change action, resource, parameters, risk, or policy context.

## Expiry

Pending approvals expire after 15 minutes. Expiry is checked when a reviewer attempts a transition. An expired approval becomes `EXPIRED`, receives a final non-authorizing `BLOCK` decision, and cannot be approved or rejected afterward.

## Decisions

Approval creates a new final `Decision(ALLOW)` with `HUMAN_APPROVAL` in the reason. Rejection, cancellation, and expiry create a final `Decision(BLOCK)`. The original `REQUIRE_APPROVAL` decision is preserved. Every outcome remains `NOT_EXECUTED`.

## Race protection

Approval transitions are performed inside one transaction and use `SELECT FOR UPDATE` on PostgreSQL. A second transition sees a terminal state and receives `409 Conflict`. SQLite tests validate the lifecycle/state guard; PostgreSQL provides the row lock in production.

## Audit events

The workflow appends:

- `APPROVAL_REQUESTED`
- `APPROVAL_APPROVED`
- `APPROVAL_REJECTED`
- `APPROVAL_EXPIRED`
- `APPROVAL_CANCELLED`

Each event includes approval ID, action-request ID, actor, resulting status, and timestamp context. Historical events are not mutated.

## Limitations

The project has no production authentication yet. The approver principal is supplied by the demo client and represents authorization-domain identity only. There are no multi-approver rules, notifications, external execution, or OAuth/JWT controls.
