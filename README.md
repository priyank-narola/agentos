# AgentOS

AgentOS is a runtime trust layer for autonomous AI-agent actions. The Phase 1 foundation establishes a separate Next.js frontend and FastAPI backend for the Autonomous Action Firewall MVP.

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

## Phase 1 status

This foundation intentionally does not include authentication, persistence, registries, policy evaluation, risk scoring, action execution, or audit functionality. Those capabilities are planned for later phases and are not represented as working features in the interface.
