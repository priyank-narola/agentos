# Development

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload --port 8000
```

## Frontend

```bash
cd frontend
npm install
npm run typecheck
npm run build
npm run dev
```

Copy `.env.example` to a local environment file when overriding defaults. Never commit local `.env` files or credentials.

## Phase 1 scope

Included: repository setup, service scaffolding, environment configuration, a dashboard shell, system endpoints, and baseline tests.

Deliberately not implemented: authentication, PostgreSQL, agent/tool registries, policy evaluation, risk scoring, runtime action execution, human approval, audit records, MCP/A2A integration, and operational dashboard data.
