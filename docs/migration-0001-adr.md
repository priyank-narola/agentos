# W12 — Migration `0001` Architectural Decision Record

**Status:** ADOPTED — 8 September 2026.
**Decision owner:** Founder + principal engineer. Recorded in this document as the explicit disposition closing W12.

## Decision
**Preserve migration `0001` as the historical baseline snapshot; do not rewrite it.** Later schema evolution continues through explicit, guarded, additive Alembic revisions (`0002`–`0004`), and parity is guarded by automated PostgreSQL migration tests.

## Rationale
- `0001` was originally authored as `Base.metadata.create_all` and is already applied to existing databases. Rewriting it would either (a) break upgrade compatibility for any deployment stamped at `0001`, or (b) require a coordinated re-stamp that risks data/schema corruption with no product benefit.
- Current architecture (this repository) has no production deployment; the only real databases are the local dev DB and disposable scratch DBs. The risk of rewriting history outweighs the cosmetic benefit.
- Guarded forward migrations plus a parity test give the properties that matter: a fresh DB is fully constructible via `alembic upgrade head`, an existing DB upgrades non-destructively, downgrades behave sensibly where supported, and drift is caught on every PostgreSQL-gated run.

## Validation performed (PostgreSQL 16)
1. Empty DB → `alembic upgrade head`: 15 domain tables + enums + tenant ownership + financial_executions + webhook_events created.
2. DB at prior state → head: additive, no data loss.
3. Downgrade: 0004 → drops webhook_events; →0002 removes Decision tenant ownership (tested).
4. Fresh schema matches expected tables/FKs/NOT NULL (asserted in `tests/test_migrations_postgres.py`).
5. Enums, tenant ownership, financial_executions, webhook_events, FKs verified.

## When this may change
Only if (1) a production-style DB exists that cannot reach head safely, or (2) the founder authorizes a disposable-DB re-baseline experiment. Until then the historical snapshot remains and is clearly documented.
