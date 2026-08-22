# Architecture

Phase 1 uses a two-service architecture:

```text
Browser -> Next.js frontend -> FastAPI backend
```

The frontend is responsible for presentation and browser interaction. The backend owns the API boundary and is the future enforcement point for identity, delegated authority, policy, risk, execution, and audit decisions. PostgreSQL is intentionally deferred until the domain model is defined in Phase 2.

## Current stack

- Next.js 14 App Router, React 18, TypeScript
- Tailwind CSS 3
- FastAPI, Uvicorn, Python
- pytest and HTTPX for API tests

## Phase 1 boundary

`NEXT_PUBLIC_API_BASE_URL` and `FRONTEND_ORIGIN` are environment-configured placeholders for the service boundary. No credentials or persistence configuration is included.
