<!-- STATUS: STALE / HISTORICAL. This document predates the verified Chunks 1-3 state and may contradict current runtime behavior (e.g., sandbox execution, FinancialExecution ledger, tenant model, REST/MCP auth). Canonical sources: AGENTOS_OPERATING_PROMPT.md and AGENTOS_STATE.md. Do not use as source of truth. -->
# Database Foundation

Phase 2 uses PostgreSQL 14+ with SQLAlchemy 2.x typed declarative models and Alembic migrations. `DATABASE_URL` is required for a deployed database and has no committed default credential.

## Schema scope

The initial migration creates only the twelve domain tables required for the future decision chain: principals, agents, delegations, tools, actions, resources, policies, policy rules, action requests, decisions, approval requests, and audit events.

JSONB is used for request parameters, delegation metadata, policy conditions, and audit event data because these values are domain payloads rather than relational identity. They are not used to bypass foreign keys or authorization rules.

## Constraints and indexes

- Stable UUID primary keys are used across all tables.
- Agent names, principal external identities, tool names, action names within a tool, resource keys within a type, policy name/version pairs, and idempotency keys are unique.
- Foreign keys are explicit and use restrictive deletion behavior for security history.
- Enum-backed status and decision columns are constrained by PostgreSQL enum types.
- Lookup indexes exist for agent requests, request decisions, policy rules, delegations, and audit timelines.

## Testing limitation

The environment does not have a local PostgreSQL client/server available, so model tests use an isolated in-memory SQLite database only for ORM metadata, relationship, and persistence wiring checks. SQLite is not treated as equivalent to PostgreSQL. PostgreSQL-specific DDL is validated by compiling the Alembic migration and should be exercised against PostgreSQL before deployment.
