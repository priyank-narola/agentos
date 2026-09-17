# Production Foundation Audit V1

## Scope and method

Repository audit performed 15 September 2026 against Milestone M2 in `PRODUCT_TO_MARKET_BLUEPRINT_V1.md`. This is an engineering readiness assessment, not a penetration test, compliance audit, legal opinion, or production certification.

## Executive result

The repository has a strong sandbox/control-plane foundation but is **not production-launch ready**. Its current posture is appropriate for local demonstration and product discovery. It must not be presented as a hosted SaaS until the P0 launch blockers below are resolved and validated against a selected pilot workflow.

## What is already in place

| Area | Evidence | Readiness |
| --- | --- | --- |
| Deterministic action controls | Policy, risk, approval binding, separation of duties, revalidation, idempotency, and audit events exist with automated tests | Useful foundation |
| Action evidence | Typed context, execution receipt, recovery posture, evidence export, causal audit sequence | Useful foundation |
| Authentication design | JWT validation checks signature, issuer, audience, expiry, and scope; REST routes derive tenant from authenticated principal when enforcement is enabled | Requires production configuration and IdP validation |
| Database code | SQLAlchemy/Alembic with PostgreSQL dialect support and migration tests gated for real PostgreSQL | Dedicated PostgreSQL rehearsal still required |
| Basic runtime safety | Health endpoint, CORS configuration, signed sandbox webhook contract, in-process rate limit | Local/single-instance only |
| Code quality | Backend test suite and frontend lint/type-check pass in local verification | CI/release pipeline missing |

## Launch blockers

| ID | Gap | Why it blocks launch | Required remediation |
| --- | --- | --- | --- |
| PF-01 | No startup production-configuration validation | A deployment can start with unsafe/missing database, auth, webhook, or origin configuration and fail later | Fail closed at startup; test production settings matrix |
| PF-02 | REST auth path currently relies on HMAC secret fallback logic | A production external JWKS/public-key identity-provider path needs explicit validation end to end | Support configured asymmetric/JWKS verifier in REST path; integration-test it |
| PF-03 | No managed secret/configuration model | Connector keys and webhook secrets need environment isolation, rotation, and access controls | Adopt secret manager and configuration contract after hosting choice |
| PF-04 | No container, CI/CD, infrastructure-as-code, staging, or release process | Cannot reproduce or safely deploy/roll back a SaaS release | Add build pipeline, staging, migrations, deploy, rollback, and approvals |
| PF-05 | PostgreSQL migration rehearsal not completed | SQLite tests cannot prove production database migration safety | Dedicated PostgreSQL scratch DB: clean install, upgrade, existing-data backfill, restore rehearsal |
| PF-06 | No durable queue/reconciliation worker | In-process execution/retry cannot safely handle provider timeouts, webhook delay, or multi-instance scaling | Durable jobs, retry policy, dead-letter/reconciliation workflow, idempotent consumer |
| PF-07 | Single-instance in-memory rate limiter | Limits are not shared across instances and cannot support reliable abuse control/quotas | Edge/distributed limiter selected with hosting design |
| PF-08 | No observability/incident operating system | Health alone cannot detect failed/unknown action outcomes, queue failures, or customer impact | Structured logs, traces, metrics, alerts, error monitor, runbooks, incident process |
| PF-09 | No real selected connector | Sandbox provider cannot demonstrate real system result, OAuth scope, webhook, or recovery | Build only after wedge/partner selection |
| PF-10 | No privacy/legal/commercial artefacts | Paid customer processing cannot launch responsibly without data/contract/support terms | Data map, retention, privacy notice, DPA, subprocessor list, terms, support and incident policies |

## Priority implementation sequence

### M2-A — fail-closed runtime configuration

1. Validate allowed environment modes, database URL, HTTPS production origins, webhook secret, auth verifier, no dev-token issuance, and safe rate-limit values at production startup.
2. Make REST authentication work with a configured HMAC secret, public key, or JWKS verifier; no insecure non-production fallback in production.
3. Add automated configuration tests.

### M2-B — release repeatability

1. Add Docker/container runtime, production dependencies, non-root process, health/readiness endpoint, and structured JSON logging.
2. Add CI for backend tests, frontend lint/type/build, dependency/security scans, and migration lint.
3. Add staging/production configuration templates and deployment runbook.

### M2-C — database and operational durability

1. Rehearse Alembic chain on dedicated PostgreSQL including audit-sequence backfill.
2. Add PostgreSQL connection/pool configuration, migration gate, backup/restore checklist.
3. Add durable queue/reconciliation architecture before a real connector.

### M2-D — pilot security/data readiness

1. Selected-workflow threat model and connector data map.
2. Secret manager, least-privilege OAuth/service account, webhook signature/replay tests.
3. Privacy retention/deletion, support/incident runbooks, and external security review scope.

## Current work decision

Begin M2-A now because it is reusable across every viable market wedge. Do not build connector, queue, or hosting infrastructure until customer evidence and a pilot system are selected.
