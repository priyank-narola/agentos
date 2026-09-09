# DEMO READINESS & HOSTING REPORT

**Date:** 8 September 2026
**Baseline preserved:** `c2a4eaa` (canonical docs) and `f5172f6` (product transformation) — unchanged, additional local commits only.
**Scope:** Human-presenter browser readiness · production REST-auth UI compatibility · hosted deployment readiness · hosted-demo security checks. No new product capabilities added.

## 1. Browser QA result
No browser-automation tooling is available in this environment, so a full in-browser click-through could not be automated. Performed instead:
- Every product route verified serving HTTP 200 on the running frontend: `/`, `/demo`, `/action-requests`, `/approvals`, `/delegations`, `/tools`, `/observability`, plus dynamic detail routes.
- Flagship demo and all seven failure scenarios executed and verified against the live PostgreSQL backend (approve as distinct approver, revalidation, sandbox execution, ledger, 8-event audit; unauthorized/tamper/revocation/cross-tenant/duplicate/timeout outcomes).
- Frontend typecheck/lint/production build pass; no stale-copy or dead-button findings remain from prior review.
**Exact remaining human QA step:** a presenter must click through the `/demo` flow and identity switcher on a real browser (recommend: Chrome desktop) and confirm visual polish, because no screenshots could be captured.

## 2. Authentication architecture / result
- MCP path: OAuth2.1 Bearer (unchanged). REST path: `require_rest_auth` enforced whenever `APP_ENV != development` or `REST_AUTH_REQUIRED=true`; tenant always server-derived from the authenticated Principal; `/api/v1/auth/dev-token` is disabled in production.
- Added `GET /api/v1/auth/me` (auth-gated) returning the authenticated principal + tenant name for UI context.
- Verified live (enforced mode): no-token → 401; invalid token → 401; valid dev token → 200; authenticated action-requests → 200; conflicting `X-Tenant-ID` → 403.

## 3. Frontend production-auth result
- `lib/api.ts`: token store with `setAccessToken`/`getAccessToken`, `Authorization: Bearer` on every request, typed `ApiError(status)`, and a one-time auto-login retry that obtains a development token (only where the backend permits it) after a 401 — so the same code path is exercised against an enforced backend.
- `components/identity-bar.tsx`: "Acting as <principal> · <tenant>" indicator plus a development identity switcher (Alice / Bob / Demo Admin) and sign-out; mounted on every shell page and the dashboard.
- `app/demo/page.tsx`: the flagship demo switches identity to the requester before submission and to the chosen eligible approver before approve/reject — the exact requirement for SoD to hold under enforced auth.
- 401 → auto-login (or sign-out prompt); 403 surfaces the API detail verbatim. Tenant is never sent as authorization; the backend derives it.
- **External contract:** in a hosted production deployment the host must supply a real IdP access token at the same injection point (see §4). Development mode remains available locally and never silently bypasses production enforcement (dev-token is absent in production).

## 4. Hosting configuration
- `render.yaml`: backend web service (`agentos-api`, uvicorn, `/health`); `DATABASE_URL` + `FRONTEND_ORIGIN` as secrets; `MCP_AUTH_SECRET_KEY` and `WEBHOOK_SECRET` as secrets. `APP_ENV=production` in blueprint ⇒ REST auth enforced automatically.
- Frontend (Vercel-equivalent): build-time `NEXT_PUBLIC_API_BASE_URL` = backend HTTPS origin; `NEXT_PUBLIC_AUTH_DEV_PRINCIPAL`/auto-login must NOT be used in production (documented).
- CORS restricted to `FRONTEND_ORIGIN`; sandbox-only financial execution; no committed secrets; migrations `alembic upgrade head` then `python -m app.seed` documented; health endpoint `/health`; no localhost production dependency.
- Environment variables required (backend): `DATABASE_URL`, `FRONTEND_ORIGIN`, `MCP_AUTH_SECRET_KEY`, `WEBHOOK_SECRET`, `APP_ENV=production`; (frontend): `NEXT_PUBLIC_API_BASE_URL`.
- Docs: `docs/hosted-demo-deployment.md`, `docs/DEPLOYMENT.md`, `docs/OLD_WORK_BACKLOG_CLOSURE_REPORT.md`.

## 5. Deployment result
Repository-side deployment work is complete. External deployment credentials (Render/Vercel) and a real OAuth IdP are not available in this environment, so **no hosted URL was created or claimed**. Status: **READY FOR EXTERNAL VALIDATION**.
Exact remaining external steps: (1) create Render backend + PostgreSQL + Vercel frontend; (2) set the env vars above; (3) run `alembic upgrade head` + `python -m app.seed`; (4) configure a real IdP client and inject its access token into the frontend auth store; (5) verify `/health`, unauthenticated→401, authenticated→200, cross-tenant→403 against the hosted API; (6) run the flagship demo + failure scenarios against the hosted environment.

## 6. Security verification (hosted-demo check)
Verified live against PostgreSQL (enforced REST mode): unauthenticated REST → 401; invalid token → 401; cross-tenant access → 403; tenant header cannot impersonate another tenant → 403; approval SoD enforced (requester excluded, self-approval rejected); TOCTOU revalidation enforced; payload tampering → blocked; duplicate execution → prevented; sandbox-only execution (provider `SandboxPaymentProvider`, no real rails); audit trail intact (8 events; ledger/audit consistent).

## 7. Demo walkthrough result
Live walkthrough executed via the running app/API: Control Center → Run Treasury Governance Demo → agent/principal visible → $25,000 action → risk 75/CRITICAL → approval required → approve as Bob Jones (distinct, SoD) → revalidation → sandbox execution SUCCEEDED → execution record + 8-event audit shown → failure scenarios render truthful outcomes. Reset/rerun works (idempotent demo tenant).

## 8. Screenshots
None captured — no browser tooling available. Not fabricated.

## 9. Remaining external dependencies
Render/Vercel credentials; a real OAuth IdP client for hosted production tokens; one human presenter pass in a real browser; optionally a CI hook for the PostgreSQL-gated suite.

## 10. Final readiness verdict
**READY FOR EXTERNAL VALIDATION.** The experience is runnable locally end-to-end, authenticated (production enforcement verified, UI plumbing in place), secure (hosted-demo checks pass), presentable, and deployment-ready on the repository side. External deployment + one human browser pass remain before it can be shown from a live URL.
