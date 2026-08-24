# AgentOS

AgentOS is an AI Action Governance and Control Plane that evaluates identity, delegated authority, risk, policy, and human approval before an AI-initiated action reaches the real world. External execution is intentionally disabled in the competition MVP.

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
