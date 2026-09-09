# AGENTOS — CURRENT STATE LOCK (Canonical Project State)

**Version:** 1.1 — 8 September 2026
**Status:** CURRENT (canonical). Companion to `AGENTOS_OPERATING_PROMPT.md`.
**Verified baseline:** Git `main` @ `a8d6ddf6b2b883fef1dbbc8d985a87bb06fb881d` plus local closure commits (HEAD advanced by W1–W18 sprint commits; no push).
**Update rule:** This file is authoritative until a new verified audit changes it. Any agent updating it must verify against source, DB, runtime, and executed tests first, and record the new Git checkpoint.

## Backlog Closure (W1–W18) — 8 September 2026
The historical/pending-work backlog sprint is closed for engineering. See `docs/OLD_WORK_BACKLOG_CLOSURE_REPORT.md` for the authoritative W1–W18 audit.
- Migration head: `20260908_0004` (adds `webhook_events`; verified fresh/existing/downgrade on PG16).
- Migration `0001` retained as historical baseline snapshot by documented decision (`docs/migration-0001-adr.md`).
- REST control-plane authentication enforced in any non-development deployment or when `REST_AUTH_REQUIRED=true`; development demo may run unauthenticated (explicit operator choice). Dev-token endpoint is production-disabled.
- Tenant scoping implemented for gateway, approvals, observability, registry catalog, and policy catalog (server-derived; default-tenant policies are a documented shared baseline).
- Webhook route with durable dedup; scenario harness executions persisted to the ledger; CISO demo repeatable; bounded rate limiting; OAuth protected-resource metadata; SSE deprecation decision explicit.
- Frontend: `/observability` page added; stale copy/types corrected; typecheck/lint/build pass.
- Customer-discovery kit and manufacturing/semiconductor research artifacts created. Customer evidence remains 0; nothing fabricated.
- Hosted demo: repository-side preparation complete — **READY FOR EXTERNAL VALIDATION** (external Render/Vercel credentials + real OAuth IdP required; no live URL fabricated).

---

## 1. One-Sentence State

AgentOS is a technically validated, sandbox-only prototype of an AI-agent action-governance control plane (demonstrated on a $25,000 USD wire transfer); it is NOT production-ready (REST control plane unauthenticated) and NOT market-validated (zero customer evidence); feature development is FROZEN pending customer discovery.

## 2. Business State

- Technical validation: YES. Market/customer validation: NO.
- Customer evidence: 0 interviews, 0 responses, 0 pilots, 0 design partners, 0 validated willingness-to-pay.
- Status label: TECHNICALLY VALIDATED PROTOTYPE — NOT MARKET VALIDATED.
- Feature development: FROZEN. Next phase: customer discovery, using the treasury demo as the technical artifact.
- Competing hypotheses (no winner declared): A) AI-agent action governance; B) AI Manufacturing OS; C) Semiconductor Supplier / Quality OS.

## 3. Architecture (actual)

Client → REST (`/api/v1/*`, **unauthenticated**, caller self-asserts identity) or MCP (`/mcp`, OAuth2.1 Bearer → `AgentIdentityResolver` → immutable `SecurityContext` {Principal, Agent, Delegation, tenant}) → `GatewayService.submit` (reference + tenant validation, financial parameter validation, SHA-256 payload digest, `RiskEngine`, `DeterministicPolicyEvaluator`) → `Decision` + `AuditEvent`s → REQUIRE_APPROVAL (`ApprovalRequest`: SoD, digest re-check, full TOCTOU re-validation, sandbox execution) or low-risk allowed wire (sandbox execution) → `FinancialExecution` + `AuditEvent`s → Observability (read-only).

## 4. Technology

Next.js (frontend) · FastAPI (backend) · PostgreSQL 16 (authoritative) · SQLAlchemy · Alembic · pytest · MCP · OAuth2.1/JWT (MCP path). SQLite is used for fast unit tests only and does not prove PostgreSQL behavior.

## 5. Database State

- Migration head: `20260908_0003`. Fresh-DB and existing-DB upgrades verified on PostgreSQL 16; seed is idempotent; migration is additive/non-destructive; downgrade of 0003 removes only the Decision tenant ownership it introduces.
- Tables (14): tenants, principals, agents, delegations, tools, actions, resources, policies, policy_rules, action_requests, decisions, approval_requests, audit_events, financial_executions.
- Tenant integrity (verified on live DB): 0 tenant mismatches across decisions/approvals/audits/ledger vs owning action request; 0 agent-owner cross-tenant mismatches; every action request has decisions; every APPROVED approval has an EXECUTION_SUCCEEDED audit; every SUCCEEDED ledger row has the execution audit. One historical pre-ledger execution audit exists (executed before the ledger existed) with no ledger row — do not fabricate a backfill.
- `Decision` and `FinancialExecution` are tenant-owned (NOT NULL FK → tenants).
- Risk model distinction: persisted `RiskClassification` enum = LOW/MEDIUM/HIGH; runtime tier string = LOW/MEDIUM/HIGH/CRITICAL (score ≥75). CRITICAL is never a persisted enum.

## 6. Flagship Demo (sandbox, technical evidence only)

- Flow: $25,000 USD wire transfer. Agent `TreasuryBot-v1` → requester `Alice Smith` (Treasury Manager) → policy `Treasury Wire Transfer Policy v1` → risk 75 / tier CRITICAL → decision REQUIRE_APPROVAL → approver `Bob Jones` (VP Finance, independent; SoD enforced) → APPROVED → TOCTOU PASS → sandbox execution SUCCEEDED → FinancialExecution PERSISTED → 8-event audit chain → observability.
- Guided UI: `/demo`. Rejection path: REJECTED, no execution, no ledger row. Tamper path: reuses Scenario D (payload digest mismatch → BLOCKED_TAMPER_DETECTED / NOT_EXECUTED). Repeatable: treasury bootstrap is idempotent (stable tenant slug, tool, principals).
- Recorded runtime evidence (historical, 2026-09-08): approve request `ac4bdd59-10fb-4842-a6e9-2be3beff5e8d`, approval `d65910de-f9b7-47cc-8693-0260917ed7f4`, provider tx `REF-5A0CEFA4`. Reject request `7f432159-0f10-48b1-9388-35912bcbbece`. Tamper request `dbf80db6-97f3-48af-b184-dbabca809293`.
- NO REAL MONEY. Sandbox provider only.

## 7. Test Truth

- Backend: 224 collected / 217 passed / 0 failed / 7 PostgreSQL-gated skipped in standard SQLite run / 0 collection errors. PostgreSQL-gated tests: 7/7 pass when enabled (3 migration + 4 observability).
- Frontend: typecheck PASS, lint PASS, production build PASS.
- Honest limits: majority of automated coverage is SQLite; not comprehensive PostgreSQL E2E; no automated true-E2E or frontend E2E; MCP runtime E2E with a real IdP token unproven. SQLite does not prove PG behavior.

## 8. Security State

- MCP: authenticated (bearer, claim-derived). REST: NOT authenticated.
- REST accepts client-supplied principal_id / agent_id / approver_principal_id without proof of caller identity; observability trusts `X-Tenant-ID` / `?tenant_id=` without membership proof; REST list/read endpoints are insufficiently tenant-scoped.
- NOT production-ready. Must not be exposed to customer production environments, real financial rails, or privileged systems until REST authentication + tenant authorization exist. Sandbox + localhost currently prevent real-money impact.
- Invariants preserved (see AGENTOS_OPERATING_PROMPT §14). No known live-endpoint 500s at last audit.

## 9. Known Debt (see AGENTOS_OPERATING_PROMPT §18)

- P0: REST control-plane authentication/authorization (critical if deployed beyond localhost or bound to real consequential actions).
- P1: REST tenant authorization; demo scenario engines bypassing governance/ledger in some synthetic paths; legacy CISO demo not repeatable; lazy approval expiry; audit same-instant timestamp ordering; legacy migration-0001 snapshot limitations.
- P2: majority SQLite-only coverage; no comprehensive PG E2E; API error semantics (409-for-validation, 404-for-missing-approver, 201-on-replay); execution_status weakly represented in the action-request schema; stale frontend types/copy; documentation drift; demo-data accumulation.
- P3: unwired webhook handler + in-memory dedup; resource `owner_reference` never enforced; some unused/dead endpoints; cosmetic UI gaps.
- P4: premature infrastructure/features without evidence (see Do-Not-Build list).

## 10. Do-Not-Build (defer unless customer evidence changes the decision)

Generic LLM gateway, prompt filtering/prompt-injection product, generic chatbot/RAG/CRM/AI automation, dynamic MCP discovery, SPIFFE, DPoP, SCIM, Slack/Teams approvals, Redis, unwired rate limiting, OPA/Rego second policy engine, real banking connectors / real-money movement, multi-region, visual policy builder, frontend redesign for aesthetics, additional canned demo scenarios.

## 11. Documentation State

Documentation is substantially stale. Known contradictions: "external execution disabled" / "NOT_EXECUTED" claims; old MCP identity model; old risk model; old tenant model; old delegation scopes; obsolete test counts; obsolete Render claims; obsolete competition/demo descriptions. Customer-discovery docs are accurate (0 evidence; FROZEN). Legacy competition docs (`AGENTOS_MASTER_PROMPT.md`, `AGENTOS_PROJECT_CONTEXT.md`) are marked historical; do not use them as source of truth. `AGENTOS_OPERATING_PROMPT.md` + this file are canonical.

## 12. Evidence Ledger (conceptual labels)

- VERIFIED FACT (code/DB/runtime/test): pipeline, migration head, test numbers, demo flow, security invariants.
- HYPOTHESIS: finance/treasury wedge; agent-action governance market need; manufacturing/semiconductor alternatives.
- UNPROVEN: market demand, buyer, WTP, competitive commercial position, production readiness, PG E2E.
- CUSTOMER EVIDENCE: none.
- Inference vs fact: always label; never present one as the other.

## 13. Next Decision

Before further development or before hosting the demo beyond localhost, decide (founder): (1) begin customer discovery with the treasury demo as the artifact (no code needed), and/or (2) authorize the P0 REST authentication + tenant authorization work as a prerequisite for any external/customer-hosted exposure. Do not start either automatically.

---

*Canonical until a new verified audit supersedes it. Any update requires verification against source, DB, runtime, and tests, plus a new Git checkpoint.*
