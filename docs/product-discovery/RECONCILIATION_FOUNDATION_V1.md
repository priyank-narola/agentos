# Execution Reconciliation Foundation V1

## Outcome

An action whose provider outcome is uncertain is now treated as an operational case, not a silent failure or an automatic retry.

The product provides a tenant-scoped **Reconciliation** inbox. An independent active human can perform a provider status readback using the durable provider request/reference IDs. The system records the result with a causally ordered audit event:

```text
timeout / unknown provider result
  → persisted UNKNOWN execution state + durable status-readback job
  → bounded worker status checks OR independent human check
  → confirmed succeeded / failed / cancelled
  → otherwise rescheduled with bounded backoff, then escalated for human review
```

## Safety invariants

1. A reconciliation check never re-submits or retries the original business action.
2. The action requester cannot reconcile their own uncertain action.
3. The inbox and check route require an `ADMIN` or `OPERATOR` role outside
   local development; the checker must also be an active human in the same tenant.
4. The provider's status readback is the only input that can resolve to a terminal result.
5. An ambiguous readback remains `RECONCILIATION_REQUIRED`; it is not presented as success.
6. Every check emits an append-only, per-action ordered audit event.
7. The inbox only includes the trusted tenant's `UNKNOWN` and `RECONCILIATION_REQUIRED` executions.

## What is implemented

| Layer | Implementation |
| --- | --- |
| Lifecycle rules | Shared persisted-execution state machine used by webhook and reconciliation paths |
| Backend service | Tenant-scoped list and provider status-readback reconciliation workflow |
| API | `GET /api/v1/reconciliation`, `POST /api/v1/reconciliation/{action_request_id}/check` |
| Product UI | `/reconciliation` operator inbox with case context, provider references, independent-operator selection, and clear unresolved messaging |
| Durable worker | `python -m app.workers.reconciliation` runs one bounded batch of due **status-only** checks; it has no execution/retry capability |
| Tests | Timeout → confirmed success; self-reconciliation refusal; worker readback with no resubmission; bounded escalation; webhook regression coverage |

## Deliberate limitations before pilot launch

- The current connector is still sandbox-only. A real connector must implement its own durable `get_status` lookup and be selected only after customer discovery.
- The durable job record and bounded worker now exist, but a hosted scheduler,
  alerting, and dead-letter/support integration must be configured with the
  selected production host. The worker remains an explicit separate process;
  it does not run in the API process.
- Current operator eligibility is a conservative active-human plus separation-of-duties rule. Product roles and SSO-backed authorization are still required before customer deployment.
- This foundation does not authorize a recovery action. Any corrective write must become a separately governed action with its own policy, approval, provider receipt, and recovery posture.
