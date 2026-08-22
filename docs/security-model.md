# Security Model Foundation

## Identity and authority boundaries

AgentOS stores four separate concepts:

1. A `Principal` is the human or organization in the authorization domain.
2. An `Agent` is the software identity acting at runtime.
3. A `Delegation` records authority explicitly granted by a principal to an agent, with scope and validity.
4. A `Policy` and its `PolicyRule` records organizational authorization constraints.

Authentication is deliberately out of scope. A future authenticated request must still resolve to an agent and principal and validate an active delegation before policy evaluation.

## Request and decision separation

`ActionRequest` captures what was requested. `Decision` captures what the authorization pipeline concluded. They have separate records so a request cannot be rewritten to appear authorized and a decision can preserve its policy version, reason, and risk result.

Phase 2 contains no evaluator or execution path. Database persistence alone must never be treated as authorization.

## Versioned policy evidence

Policies use `(name, version)` uniqueness. Decisions retain the policy ID and version used, allowing later policy changes without rewriting historical evidence. Application code should treat active/published policy rules as immutable; retiring a policy is preferred to editing it in place.

## Audit immutability

`AuditEvent` is append-oriented. Historical requests, decisions, and events should not be updated or deleted by application code. Corrections or later outcomes should be represented by additional events.

## Least privilege and retention

Foreign keys use restrictive deletion behavior to avoid orphaning decision evidence. Resource rows hold identifiers and sensitivity metadata, not sensitive business payloads. Delegation expiry is represented explicitly and must be enforced by the future authorization layer.
