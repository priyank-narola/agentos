# Hosted Demo & Deployment (W17) — Repository-Side Preparation

**Status:** READY FOR EXTERNAL DEPLOYMENT — no external credentials/access available to the coding agent; no live URL fabricated.

## Intended architecture
- Backend API: Render (or equivalent), `render.yaml` web service `agentos-api` (FastAPI/uvicorn, `/health`).
- Frontend: Vercel (or equivalent) with `NEXT_PUBLIC_API_BASE_URL` set at build time to the backend HTTPS origin.
- Database: managed PostgreSQL; run `alembic upgrade head` then `python -m app.seed`.

## Security on a hosted deployment
- `APP_ENV=production` (render.yaml) automatically enforces REST bearer authentication (see `app/api/deps.py`); REST_AUTH_REQUIRED can force it in any environment.
- Provide real secrets as environment variables: `DATABASE_URL`, `FRONTEND_ORIGIN` (exact origin), `MCP_AUTH_SECRET_KEY`, `WEBHOOK_SECRET`; never commit secrets.
- Access tokens for REST come from the configured OAuth identity provider in production; the `/api/v1/auth/dev-token` endpoint is disabled when `APP_ENV=production`.
- CORS is restricted to `FRONTEND_ORIGIN`. Rate limiting is enabled on control-plane/MCP surfaces. Execution remains sandbox-only; no real payment rails.
- Frontend must send `Authorization: Bearer <token>` on control-plane calls.

## Verification checklist (founder/external)
1. Deploy backend; confirm `/health` 200 and `/api/v1/version` 200.
2. Run migrations + seed.
3. Confirm unauthenticated `/api/v1/action-requests` returns 401 (auth enforced).
4. Configure a real IdP or service token and confirm authenticated access returns 200.
5. Build + deploy frontend with the correct API base URL; run the `/demo` flow.
6. Verify observability endpoints and tenant isolation with two test identities.

## Missing (external step)
Actual Render/Vercel credentials, a real OAuth IdP, and a live URL. Without them the deployment remains repository-side ready and externally unverified.
