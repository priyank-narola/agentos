# AgentOS

AgentOS is an AI Action Governance and Control Plane that evaluates identity, delegated authority, risk, policy, and human approval before an AI-initiated action is allowed, blocked, or escalated. Authorized high-risk actions execute only inside a sandbox provider (no real money movement); every execution is recorded in a FinancialExecution ledger and an audit trail.

> **Canonical references:** `AGENTOS_OPERATING_PROMPT.md` (operating constitution) and `AGENTOS_STATE.md` (verified current state). Legacy competition-era docs are retained as historical and may contradict current runtime behavior.

## Development

Prerequisites: Node.js 20+, npm, and Python 3.11+.

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend, in another terminal
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:3000`. The backend runs at `http://localhost:8000`. See `docs/development.md` for verification commands and configuration details.

## Deployment

Production deployment targets Vercel for `frontend/`, Render for `backend/`, and managed PostgreSQL. See `docs/DEPLOYMENT.md` for exact environment variables, migrations, seeding, and smoke tests.
