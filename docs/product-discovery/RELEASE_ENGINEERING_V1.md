# Release Engineering Foundation V1

## Purpose

This document records the repeatable build and release foundation added after the production-foundation audit. It is deliberately provider-neutral: we must not choose a hosting account, spend money, or configure customer secrets before the selected pilot workflow and founder decisions exist.

It is **not** a launch certificate. The product remains a sandbox/control-plane foundation until the open P0 blockers in `PRODUCTION_FOUNDATION_AUDIT_V1.md` are completed.

## What now exists

| Capability | Repository artefact | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Backend packaging | `backend/Dockerfile` | A non-root Python runtime can be built reproducibly | That a cloud deployment is secure or scaled |
| Frontend packaging | `frontend/Dockerfile`, standalone Next output | A build-time public API origin and production frontend image are reproducible | End-user OAuth login or a public domain |
| Local integration | `compose.yaml` | PostgreSQL, migrations, backend, and frontend can be started as a single local environment | Backup, restore, cluster, or cloud networking behavior |
| Runtime operations | `/health`, `/ready`, request correlation, structured logs, and protected runtime metrics | Liveness can be separated from database readiness; process-local request/error/latency posture is available without logging bodies/tokens | Central log retention, aggregation, alerts, traces, or incident response |
| Verification | `.github/workflows/verify.yml` | Push/PR checks will run when the repository is connected to GitHub Actions | A release pipeline, deployment approval, or production smoke test |
| Migration review | Offline PostgreSQL SQL rendering test | Historical migrations can be rendered for release review without a live-connection inspection failure | That backfills work on real legacy data |

## Environment contract

### Local integration

`docker compose up --build` starts the local stack. The only credential in `compose.yaml` is an intentionally local, disposable PostgreSQL password. It must never be reused in a hosted environment.

The backend service runs migrations before starting in this local-only compose setup. A hosted release must use an explicit, observable migration job instead of performing migration implicitly in every application instance.

### Hosted runtime

For a real hosted environment, set values through the chosen platform's secret/configuration system:

| Variable | Requirement |
| --- | --- |
| `APP_ENV` | `production` |
| `DATABASE_URL` | Managed PostgreSQL SQLAlchemy/Psycopg URL |
| `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, `DATABASE_POOL_RECYCLE_SECONDS` | Bounded per-process PostgreSQL connection-pool settings; size them after the selected host's connection limits are known |
| `FRONTEND_ORIGIN` | One or more exact HTTPS browser origins |
| `MCP_AUTH_ISSUER`, `MCP_AUTH_AUDIENCE` | Explicit values from the selected OAuth/OIDC provider |
| One verifier: `MCP_AUTH_JWKS_URL`, `MCP_AUTH_PUBLIC_KEY`, or `MCP_AUTH_SECRET_KEY` | Prefer an asymmetric/JWKS verifier for external identity |
| `WEBHOOK_SECRET` | Secret-manager value, unique to the environment |
| `DEV_TOKEN_ENABLED` | `false` |
| `LOG_FORMAT` | `json` |
| `NEXT_PUBLIC_API_BASE_URL` | Public API HTTPS origin at frontend build time |

The API fails closed at startup if a production configuration lacks these safety properties. No actual values are committed in this repository.

`render.yaml` remains a provider-specific example for a future Render deployment and now declares the same required configuration keys. It cannot deploy safely until a founder selects an identity provider, a secret-management setup, the public domains, and a managed database; those are intentional external decisions, not placeholders to guess in source code.

## Release gate sequence

1. CI succeeds: backend tests, frontend lint/type-check/build.
2. Container images build from the commit being released.
3. A migration job is rehearsed against a disposable PostgreSQL database, including upgrade and restore validation.
4. Deployment uses staged secrets and production startup validation passes.
5. `/health` and `/ready` pass; the latter verifies a live database query.
6. The real OIDC/JWKS authentication path is tested with a non-development principal and tenant.
7. The selected pilot connector's happy path, timeout, duplicate delivery, approval, and recovery paths pass in staging.
8. An authorized release owner approves the production rollout, and rollback steps are ready.

## Open work after this foundation

- Add provider-specific infrastructure-as-code and explicit release/migration workflow once hosting is selected.
- Run the Alembic chain and audit-sequence backfill against a dedicated PostgreSQL environment. Static PostgreSQL SQL rendering now passes; the local Docker daemon was unavailable on 15 September 2026, so this is explicitly **not** a completed live-database rehearsal.
- Add central logs, metrics, traces, alerting, backups, restoration rehearsal, and an incident runbook.
- Follow the pilot operating baseline in `OPERATIONS_AND_DATA_CONTROLS_V1.md`
  for data minimisation, retention/deletion, connector credential handling,
  and incident response. Provider-enforced retention and contractual/legal
  review remain external release gates.
- Build an actual OAuth/OIDC browser sign-in and role/tenant provisioning path. The current development-token interface is intentionally unavailable in production; it is not a customer login experience.
- Choose the first evidence-backed workflow before connecting to any customer or third-party system.
