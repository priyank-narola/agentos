# Deterministic Risk Engine

The Risk Engine provides contextual evidence; it does not authorize actions.

Phase 6 adds a pure, deterministic component between gateway context resolution and the existing policy evaluator:

```text
Resolved gateway context
  -> RiskEngine.evaluate
  -> RiskAssessment
  -> DeterministicPolicyEvaluator
  -> authorization decision
```

## Inputs

Only persisted or request-domain fields are used:

- action risk level
- agent risk classification
- resource sensitivity and status
- delegation status and expiry
- resolved tool/action relationship
- numeric `amount` request parameter when present

No external intelligence, model output, identity history, destination reputation, or invented field is used.

## Formula

The score is the sum of applicable positive contributions, bounded to `0..100`.

| Factor | Contribution |
| --- | ---: |
| Action LOW / MEDIUM / HIGH | 5 / 15 / 30 |
| Agent LOW / MEDIUM / HIGH | 0 / 10 / 20 |
| Resource LOW / MEDIUM / HIGH sensitivity | 0 / 15 / 25 |
| Resource not ACTIVE | 20 |
| Tool/action mismatch | 30 |
| Delegation missing | 20 |
| All delegations invalid or expired | 20 |
| Numeric amount over 5,000 | 10 |
| Numeric amount over 10,000 | 20 instead of 10 |

Each non-zero contribution produces a stable factor code and explanation. Engine identifier: `agentos-risk-v1`.

## Classification

| Score | Classification |
| --- | --- |
| 0–24 | LOW |
| 25–49 | MEDIUM |
| 50–74 | HIGH |
| 75–100 | CRITICAL |

## Persistence and audit

The normalized score is stored in the existing `Decision.risk_score` field. No migration is required. Classification, engine version, timestamp, and factors are stored in an append-only `RISK_EVALUATED` audit event. Idempotent retries return existing evidence and do not create duplicate risk events.

## Failure and security boundary

Risk fields are forbidden in caller gateway payloads. If risk evaluation raises an exception, the transaction rolls back and the API returns a non-authorizing error. No request, decision, risk audit, or execution is committed. Risk is passed into evaluator context, but the risk engine has no decision field and the gateway contains no score-based allow/deny branch.

## Limitations and extensions

The current engine uses fixed code-defined weights and supports only numeric amount thresholds. It has no ML scoring, external signals, history, configurable formulas, asynchronous processing, or separate risk evidence table. Future versions can add versioned deterministic factors without changing the authorization boundary.
