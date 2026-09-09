# FOUNDER DEMO QUICKSTART

Target audience: the founder, opening AgentOS on this machine and (optionally) sharing over the local network.
Environment already running (dev mode): backend on `http://localhost:8000`, frontend on `http://localhost:3000`.

## 1. Start the application (from scratch)

Requirements already present: PostgreSQL 16 (Docker `postgres_db`, port 5432), backend `.venv`, frontend `node_modules`.

```bash
# Terminal 1 — backend (from the repo root)
cd backend
set -a && source ./.env && set +a
export FRONTEND_ORIGIN="http://localhost:3000,http://<YOUR_LAN_IP>:3100"   # optional: add LAN origin for a friend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — frontend (local browser)
cd frontend
npm run dev
```

- Frontend URL: **http://localhost:3000**
- Backend URL:  **http://localhost:8000** (health: `http://localhost:8000/health`)
- Find your LAN IP: `ipconfig getifaddr en0` (macOS) → e.g. `192.168.1.110`

## 2. Open the demo

1. Open **http://localhost:3000** in a normal browser (Chrome recommended).
2. You should see the AgentOS control center ("Before an AI agent can perform a consequential action…") with a **Run Treasury Governance Demo** button.
3. Identity bar (top right) shows "Acting as …" — in development mode no login is required; the identity switcher can act as Alice Smith / Bob Jones / Demo Admin for demonstration.

## 3. Demo walkthrough (exact steps)

1. Click **Run Treasury Governance Demo** (or open **http://localhost:3000/demo**).
2. Read the explainer; the amount defaults to $25,000 USD.
3. Click **Run Treasury Governance Demo**.
4. Watch the lifecycle stages advance: Request → Identify → Authorize (policy) → Evaluate (risk 75/CRITICAL) → **Approve**.
5. In the approval panel confirm the approver shown is **Bob Jones** (independent — the requester Alice can never self-approve), then click **Approve as Bob Jones**.
6. Stages continue: Revalidate → Execute → Audit. The final green proof reads **ACTION GOVERNED — AUTHORIZED → APPROVED → EXECUTED IN SANDBOX → AUDITED**, with an execution record (FinancialExecution ledger line) and the audit event list.
7. Scroll to **AgentOS blocks unsafe actions**: run any scenario (Unauthorized, Payload tampering, Revoked delegation, Cross-tenant, Duplicate, Provider timeout) and read why it was blocked/prevented/handled.
8. Use **Reset & run again** to rerun (each run adds one governed request + ledger + audit row in the demo tenant — bounded).

## 4. Sharing with a friend on the same network (LAN)

The friend needs only a browser — no source, Python, Node, Docker, or database.

Prerequisite on this machine:
```bash
export FRONTEND_ORIGIN="http://localhost:3000,http://<YOUR_LAN_IP>:3100"   # backend running with this
```
Then start a second, LAN-bound frontend that points at the machine's API:
```bash
cd frontend
NEXT_PUBLIC_API_BASE_URL="http://<YOUR_LAN_IP>:8000" npm run dev -- -H 0.0.0.0 -p 3100
```
Give the friend: **http://<YOUR_LAN_IP>:3100** (e.g., http://192.168.1.110:3100).
Hand them `docs/FRIEND_DEMO_TEST_GUIDE.md`.

Security note for LAN sharing:
- Demo is **sandbox-only — no real money**. No production credentials are used or committed.
- The backend REST API is unauthenticated in development mode by design; keep the demo to your trusted LAN and stop the `-p 3100` frontend + the backend when done.
- **Do not** share the database connection or expose PostgreSQL (port 5432) to others; if it is reachable beyond this machine, stop it first (`docker stop postgres_db`).

## 5. Remote friend (not on your LAN)

Minimum safe temporary option (manual founder action, you run it):
```bash
# Option A — Cloudflare quick tunnel to the LOCAL frontend (fastest)
cd frontend
npx localtunnel --port 3000
# or
npx cloudflared tunnel --url http://localhost:3000
```
Cloudflare/localtunnel prints a public HTTPS URL you can send. Note:
- This exposes the **development-mode** backend surface over the internet; it is demo data only (sandbox, no real rails), but **remove the tunnel as soon as the test is done**.
- For a safer remote test you may restart the backend with `REST_AUTH_REQUIRED=true` (frontend auto-logs-in as Demo Admin via the dev token path) — still demo-grade, not production.
- The command outputs the exact URL; do not paste any URL below as if it were already verified.

## 6. Troubleshooting

- Backend down → `curl http://localhost:8000/health`; restart Terminal 1.
- Pages load but data empty → confirm backend running and CORS origin includes the origin you are on (restart backend after changing `FRONTEND_ORIGIN`).
- Demo approve fails with "Authenticated principal cannot…" → you are in enforced mode but acting as the wrong identity; use the identity switcher or the demo's auto-switch (dev mode is the default and needs no token).
- Friend sees API errors → they opened `:3000`/`localhost`; use the LAN URL `http://<YOUR_LAN_IP>:3100` from step 4 and confirm the backend origin allow-list includes it.
- Port 3000 busy → use `npm run dev -- -p 3100` and open http://localhost:3100 locally.
