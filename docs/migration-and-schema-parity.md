# Migration & Schema Parity Notes (W12 review)

**Status:** REVIEWED — repository-side parity validated; legacy baseline documented.

## Current head
`20260908_0004` (0001 initial snapshot → 0002 CANCELLED enum → 0003 tenant integrity + ledger → 0004 webhook events).

## Verified (PostgreSQL 16)
- Fresh DB: `alembic upgrade head` produces the full model schema (14 core tables + `webhook_events`).
- Existing DB upgrade: additive/non-destructive (0003/0004 guard columns/tables; default-tenant bootstrap).
- Downgrade: 0004 drops webhook table; 0003 removes Decision tenant ownership (verified in tests).
- Seed idempotency and Decision/FinancialExecution tenant ownership verified.

## Known legacy limitation (documented, not refactored)
Migration `0001` was created as `Base.metadata.create_all` snapshot, so history is not a pure column-by-column record of early schema evolution. It is intentionally left intact to avoid rewriting applied history; new changes use explicit guarded migrations. A future task may replace 0001 with an explicit frozen baseline only with founder authorization and a disposable-DB validation plan.

## Parity guard
PostgreSQL-gated tests (`tests/test_migrations_postgres.py`) assert the migration-produced schema includes all expected tables and key NOT NULL/FK properties, giving an automated drift check on every run.
