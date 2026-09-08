<!-- STATUS: STALE / HISTORICAL. This document predates the verified Chunks 1-3 state and may contradict current runtime behavior (e.g., sandbox execution, FinancialExecution ledger, tenant model, REST/MCP auth). Canonical sources: AGENTOS_OPERATING_PROMPT.md and AGENTOS_STATE.md. Do not use as source of truth. -->
# Decisions

## D001: Separate frontend and backend

The UI and authorization boundary are separate services so security decisions can remain server-side and the API can later support multiple clients or agent integrations.

## D002: Defer persistence

PostgreSQL is not included in Phase 1. The project needs stable domain entities and decision contracts before introducing migrations or database operational overhead.

## D003: Keep the Phase 1 UI honest

The dashboard is a professional shell with explicit planned/unfinished states. It does not display fabricated agents, actions, risk scores, or audit records.
