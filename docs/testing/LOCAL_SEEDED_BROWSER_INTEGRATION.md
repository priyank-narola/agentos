# Local Seeded Browser Integration Check

This check proves one real browser-to-API control path without using a shared
database, customer data, hosted API, or live connector. It is intentionally
separate from the mocked Playwright suite.

## Scope

`npm run test:e2e:integration` opens the Action Preflight page and calls a
locally started API backed by a disposable SQLite database. It selects the
seeded `FinanceAgent`, `bank_transfer`, and `bank_account_001`, then verifies
that the UI renders the actual `REQUIRE_APPROVAL` decision and the human
approval/revalidation route. The execution provider is sandbox-only.

## Run locally

In one terminal, prepare the disposable database and API:

```sh
cd backend
mkdir -p /private/tmp/agentos-e2e-browser
APP_ENV=development DEV_TOKEN_ENABLED=true DATABASE_URL=sqlite:////private/tmp/agentos-e2e-browser/integration.sqlite ./.venv/bin/alembic upgrade head
APP_ENV=development DEV_TOKEN_ENABLED=true DATABASE_URL=sqlite:////private/tmp/agentos-e2e-browser/integration.sqlite ./.venv/bin/python -m app.seed
APP_ENV=development DEV_TOKEN_ENABLED=true FRONTEND_ORIGIN=http://127.0.0.1:3100,http://127.0.0.1:3101 DATABASE_URL=sqlite:////private/tmp/agentos-e2e-browser/integration.sqlite ./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8100
```

In a second terminal:

```sh
cd frontend
npm run test:e2e:integration
```

The Playwright fixture starts its own frontend on `127.0.0.1:3101`; it does
not modify `.env.local`. A development-only browser override selects the
isolated API only for this test and is disabled in production builds.

## Boundaries

- The test is not a PostgreSQL migration rehearsal.
- It does not approve, execute, refund, credit, contact a customer, or invoke
  a live payment/CRM provider.
- It covers one preflight journey only. Approval, reconciliation, policy,
  registry, evidence, and accessibility acceptance flows still need their own
  backend-integrated coverage.
