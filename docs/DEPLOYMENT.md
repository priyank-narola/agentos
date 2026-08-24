# AgentOS Deployment

This guide deploys the existing competition MVP without enabling external action execution.

## 1. PostgreSQL Setup

Provision a managed PostgreSQL database through Render or another PostgreSQL provider. Copy its private/internal connection string for the Render backend when both services share the provider network.

AgentOS expects a SQLAlchemy-compatible URL using the Psycopg 3 driver:

```text
postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE
```

Do not commit the URL or database credentials.

## 2. Render Backend Setup

The repository includes `render.yaml`. Create a Render Blueprint from the repository, or configure a Python Web Service manually:

```text
Root directory: backend
Build command: pip install -r requirements.txt
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health check path: /health
```

Render supplies `PORT`; do not define or hardcode it.

## 3. Backend Environment Variables

Configure these in Render:

| Variable | Required | Value |
| --- | --- | --- |
| `DATABASE_URL` | Yes | Managed PostgreSQL connection URL |
| `FRONTEND_ORIGIN` | Yes | Final Vercel origin, including `https://` and no trailing path |
| `APP_ENV` | Yes | `production` |
| `APP_NAME` | No | `AgentOS API` |
| `APP_VERSION` | No | Release identifier, currently `0.1.0` |

`FRONTEND_ORIGIN` is the only allowed browser origin. Do not use wildcard CORS in production.

## 4. Database Migration

After `DATABASE_URL` is configured, open a Render Shell or run a one-off job from the `backend` directory:

```bash
alembic upgrade head
```

Run migrations before seeding or opening the application to demo traffic.

## 5. Demo Seed

From the same Render Shell:

```bash
python -m app.seed
```

The seed is idempotent. It creates deterministic competition agents, actions, resources, delegations, and policies without credentials or real business data.

## 6. Vercel Frontend Setup

Import the repository into Vercel and configure:

```text
Framework preset: Next.js
Root directory: frontend
Install command: npm install
Build command: npm run build
Output: Next.js default
```

No `vercel.json` is required for this standard Next.js deployment.

## 7. Frontend Environment Variable

Set this for Production and Preview environments as appropriate:

| Variable | Required | Value |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Yes | Public HTTPS origin of the Render API, with no trailing path |

The frontend uses no other public runtime configuration.

Because `NEXT_PUBLIC_*` variables are embedded at build time, redeploy the frontend after changing the API URL.

## 8. CORS Finalization

Once Vercel assigns the production frontend URL:

1. Set Render `FRONTEND_ORIGIN` to that exact origin.
2. Trigger a backend restart/redeploy.
3. Confirm browser requests from Vercel succeed.
4. Confirm requests from unrelated origins do not receive permissive CORS headers.

## 9. Health Check

Render checks:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok",
  "service": "agentos-api"
}
```

The endpoint intentionally requires no authentication and reveals no secrets or database details.

## 10. Post-Deployment Smoke Test

1. Open the backend `/health` URL and confirm HTTP 200.
2. Open `/api/v1/version` and confirm the production environment.
3. Open the Vercel Control Center and confirm agents, tools, resources, and policies load.
4. Submit the safe demo action and verify `AUTHORIZED / NOT_EXECUTED`.
5. Submit the blocked demo action and verify `BLOCKED / NOT_EXECUTED`.
6. Submit the high-risk transfer and verify `PENDING_APPROVAL`.
7. Open `/approvals`, approve the request, and verify `AUTHORIZED FOR EXECUTION / NOT EXECUTED`.
8. Refresh the dashboard and confirm persisted counts and recent activity.

## 11. Security Checklist

- Keep `DATABASE_URL` only in Render secrets.
- Set exact `FRONTEND_ORIGIN`; never use `*` in production.
- Set only the public backend origin in `NEXT_PUBLIC_API_BASE_URL`.
- Do not expose PostgreSQL publicly unless provider operations require it.
- Run migrations before seed data.
- Confirm no `.env` files or credentials are committed.
- Confirm external execution remains disabled.
- Confirm the browser cannot submit decisions, risk results, policy results, or `tool_id` overrides.
- Treat the current principal selector as competition/demo identity, not production authentication.
- Rotate any credential immediately if it is ever pasted into source, logs, or screenshots.

## Deployment Order

Use this order because each later step needs the previous service URL:

1. Provision PostgreSQL.
2. Create Render backend and configure `DATABASE_URL` plus a temporary exact frontend origin if available.
3. Run `alembic upgrade head`.
4. Run `python -m app.seed`.
5. Verify Render `/health`.
6. Create Vercel frontend with `NEXT_PUBLIC_API_BASE_URL` set to the Render HTTPS origin.
7. Set Render `FRONTEND_ORIGIN` to the final Vercel origin and redeploy/restart the backend.
8. Run the complete smoke test.
