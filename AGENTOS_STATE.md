# AGENTOS — CURRENT STATE LOCK (Canonical Project State)

**Version:** 1.5 — 17 September 2026
**Status:** CURRENT (canonical). Companion to `AGENTOS_OPERATING_PROMPT.md`.
**Verified baseline:** Git `main` @ `332e68c65b2ba1d888707f0031fe83a7be3fbd2b` (governance UX redesign, Intelligence V2, and security-audit fixes).
**Update rule:** This file is authoritative until a new verified audit changes it. Any agent updating it must verify against source, DB, runtime, and executed tests first, and record the new Git checkpoint.

## 0. Review Branch and Reporting Correction — 17 September 2026

- The branch `codex/unverified-working-tree-20260917` contains an **unmerged,
  unverified review snapshot** at
  `2bb652a1cd14fe19256357f54936a43c5c3d126d`. It includes customer-refund,
  account-credit, Stripe-adapter, reconciliation, role, release, UI, and
  product-discovery changes that are not part of `main` and are not an
  accepted product milestone.
- An earlier status report incorrectly described a subset of that uncommitted
  work as completed. The cause was treating targeted local test results as a
  completion checkpoint without first requiring a Git commit and checking this
  state lock. That report is superseded by this record.
- Correction: a milestone is complete only when it has proportionate verified
  evidence **and** an exact commit hash or PR reference. Local/uncommitted work
  is labeled *in progress*; a review-branch snapshot is labeled *unverified*
  until Priyank explicitly accepts it. No merge to `main` occurs before the
  founder Next Decision in section 13.
- The snapshot was created for inspection only. Its contents must not be used
  to change the architecture, test baseline, market claim, or product status
  recorded below without a new verification audit and explicit founder approval.

### Founder delivery directive — 17 September 2026

Priyank explicitly authorized a deadline-driven engineering sprint toward the
strongest possible delivery by **19 September 2026, 10:00 AM Asia/Kolkata**.
Engineering may resume on `codex/unverified-working-tree-20260917` only. This
does not validate market demand, authorize a merge to `main`, permit production
deployment, or authorize customer outreach, live data, payments, spending, or
legal commitments. Every claimed milestone still requires proportionate
verification and an exact commit or PR reference.

### Review-branch verification checkpoint — 17 September 2026

- Commit `f1a78e0e269e0ec3fa988642874f27f6e8364987` closes a hosted-environment
  REST-authentication bypass: every environment other than `development` now
  requires REST authentication regardless of `REST_AUTH_REQUIRED`.
- On the review branch, the complete backend suite has since been re-run with
  `385 passed, 8 skipped, 1 warning` (no failures). Frontend typecheck, lint,
  and the 21-route production build also pass. These are review-branch
  verification facts, not evidence of customer validation or authorization to
  merge/deploy.

## Backlog Closure (W1–W18) — 8 September 2026
The historical/pending-work backlog sprint is closed for engineering. See `docs/OLD_WORK_BACKLOG_CLOSURE_REPORT.md` for the authoritative W1–W18 audit.
- Migration head: `20260909_0005` (adds FK on `audit_events.actor_id`; verified fresh/existing on PG16).
- Migration `0001` retained as historical baseline snapshot by documented decision (`docs/migration-0001-adr.md`).
- REST control-plane authentication enforced in any non-development deployment or when `REST_AUTH_REQUIRED=true`; development demo may run unauthenticated (explicit operator choice). Dev-token endpoint disabled by default (opt-in via `DEV_TOKEN_ENABLED=true`).
- Tenant scoping implemented for gateway, approvals, observability, registry catalog, and policy catalog (server-derived; default-tenant policies are a documented shared baseline).
- Webhook route with durable dedup; scenario harness executions persisted to the ledger; CISO demo repeatable; bounded rate limiting; OAuth protected-resource metadata; SSE deprecation decision explicit.
- Intelligence Engine V1/V2: risk scoring, intent analysis, anomaly detection, threat classification, policy recommendation (advisory only), model provider abstraction, knowledge base (49 entries), benchmark framework, adversarial evaluation.
- Frontend: `/observability` page added; stale copy/types corrected; typecheck/lint/build pass.
- Customer-discovery kit and manufacturing/semiconductor research artifacts created. Customer evidence remains 0; nothing fabricated.
- Hosted demo: repository-side preparation complete — **READY FOR EXTERNAL VALIDATION** (external Render/Vercel credentials + real OAuth IdP required; no live URL fabricated).
- Phase 1 Forensic Gap Audit: all P0/P1/P2 fixes implemented and verified (326 tests pass, 0 failures).

---

## 1. One-Sentence State

AgentOS is a technically validated, sandbox-only prototype of an AI-agent action-governance control plane (demonstrated on a $25,000 USD wire transfer); REST authentication enforced in non-development deployments; Intelligence Engine V1/V2 with advisory model provider, 186-scenario corpus, and adversarial evaluation; Phase 1 Forensic Gap Audit complete with all P0/P1/P2 fixes implemented; NOT market-validated (zero customer evidence); a time-boxed review-branch engineering sprint is authorized, but no external launch authority is implied.

## 2. Business State

- Technical validation: YES. Market/customer validation: NO.
- Customer evidence: 0 interviews, 0 responses, 0 pilots, 0 design partners, 0 validated willingness-to-pay.
- Status label: TECHNICALLY VALIDATED PROTOTYPE — NOT MARKET VALIDATED.
- Feature development: review-branch sprint authorized through 19 September
  2026, 10:00 AM Asia/Kolkata. Customer discovery remains required for market
  validation and no work may be merged to `main` without a separate founder
  approval.
- Competing hypotheses (no winner declared): A) AI-agent action governance; B) AI Manufacturing OS; C) Semiconductor Supplier / Quality OS.

## 3. Architecture (actual)

Client → REST (`/api/v1/*`, **authenticated** when `REST_AUTH_REQUIRED=true` or non-development; dev-token endpoint opt-in via `DEV_TOKEN_ENABLED=true`) or MCP (`/mcp`, OAuth2.1 Bearer → `AgentIdentityResolver` → immutable `SecurityContext` {Principal, Agent, Delegation, tenant}) → `GatewayService.submit` (reference + tenant validation, financial parameter validation, SHA-256 payload digest, `RiskEngine`, `DeterministicPolicyEvaluator`, Intelligence Assessment advisory-only) → `Decision` + `AuditEvent`s → REQUIRE_APPROVAL (`ApprovalRequest`: SoD, digest re-check, full TOCTOU re-validation, row-level locking, sandbox execution) or low-risk allowed wire (sandbox execution) → `FinancialExecution` + `AuditEvent`s → Observability (read-only).

## 4. Technology

Next.js (frontend) · FastAPI (backend) · PostgreSQL 16 (authoritative) · SQLAlchemy · Alembic · pytest · MCP · OAuth2.1/JWT (MCP path). SQLite is used for fast unit tests only and does not prove PostgreSQL behavior.

## 5. Database State

- Migration head: `20260909_0005` (adds FK on `audit_events.actor_id`). Fresh-DB and existing-DB upgrades verified on PostgreSQL 16; seed is idempotent; migration is additive/non-destructive.
- Tables (15): tenants, principals, agents, delegations, tools, actions, resources, policies, policy_rules, action_requests, decisions, approval_requests, audit_events, financial_executions, webhook_events.
- Tenant integrity (verified on live DB): 0 tenant mismatches across decisions/approvals/audits/ledger vs owning action request; 0 agent-owner cross-tenant mismatches; every action request has decisions; every APPROVED approval has an EXECUTION_SUCCEEDED audit; every SUCCEEDED ledger row has the execution audit. One historical pre-ledger execution audit exists (executed before the ledger existed) with no ledger row — do not fabricate a backfill.
- `Decision` and `FinancialExecution` are tenant-owned (NOT NULL FK → tenants).
- Risk model distinction: persisted `RiskClassification` enum = LOW/MEDIUM/HIGH; runtime tier string = LOW/MEDIUM/HIGH/CRITICAL (score ≥75). CRITICAL is never a persisted enum.

## 6. Flagship Demo (sandbox, technical evidence only)

- Flow: $25,000 USD wire transfer. Agent `TreasuryBot-v1` → requester `Alice Smith` (Treasury Manager) → policy `Treasury Wire Transfer Policy v1` → risk 75 / tier CRITICAL → decision REQUIRE_APPROVAL → approver `Bob Jones` (VP Finance, independent; SoD enforced) → APPROVED → TOCTOU PASS → sandbox execution SUCCEEDED → FinancialExecution PERSISTED → 8-event audit chain → observability.
- Guided UI: `/demo`. Rejection path: REJECTED, no execution, no ledger row. Tamper path: reuses Scenario D (payload digest mismatch → BLOCKED_TAMPER_DETECTED / NOT_EXECUTED). Repeatable: treasury bootstrap is idempotent (stable tenant slug, tool, principals).
- Recorded runtime evidence (historical, 2026-09-08): approve request `ac4bdd59-10fb-4842-a6e9-2be3beff5e8d`, approval `d65910de-f9b7-47cc-8693-0260917ed7f4`, provider tx `REF-5A0CEFA4`. Reject request `7f432159-0f10-48b1-9388-35912bcbbece`. Tamper request `dbf80db6-97f3-48af-b184-dbabca809293`.
- NO REAL MONEY. Sandbox provider only.

## 7. Test Truth

- Review branch: backend suite: **385 passed / 8 skipped / 1 warning / 0
  failed**. The remaining warning is Starlette's upstream `BlockingPortal`
  deprecation; test code no longer uses deprecated `datetime.utcnow()`.
- Frontend: `npm run typecheck`, `npm run lint`, and `npm run build` PASS; the
  production build completes all 21 routes.
- Historical note: the Phase 1 forensic-audit checkpoint recorded 326 passing
  tests. It is not the current review-branch test count. Security gap tests
  cover rate limiting, token expiry, approval expiry, suspended principal,
  expired delegation, inactive agent, concurrent approval, and deactivated
  principal.
- Honest limits: majority of automated coverage is SQLite; not comprehensive PostgreSQL E2E; no automated true-E2E or frontend E2E; MCP runtime E2E with a real IdP token unproven. SQLite does not prove PG behavior.

## 8. Security State

- MCP: authenticated (bearer, claim-derived). REST: authenticated when `REST_AUTH_REQUIRED=true` or non-development deployment.
- Identity: token-derived principal (JWT `sub` → DB lookup); gateway enforces `principal_id == authenticated principal.id`.
- Tenant isolation: enforced at API, service, repository, and DB layers; all domain tables have `tenant_id` FK with RESTRICT.
- Separation of duties: requester cannot approve own request (enforced in approval service + verified in tests).
- Payload integrity: SHA-256 digest computed at submission, verified at approval execution; tamper detection proven.
- TOCTOU protection: row-level locking on approval fetch; full security context revalidation at approval time.
- Gateway idempotency: `SELECT FOR UPDATE` on idempotency key check prevents concurrent duplicate insertion (P1-01 fix).
- Webhook security: HMAC-SHA256 signature verification, timestamp replay protection; production requires `WEBHOOK_SECRET` env var (P1-02 fix).
- CORS: restricted to `Authorization`, `Content-Type`, `X-Tenant-ID`, `X-Request-ID`, `X-Idempotency-Key` headers (P2-08 fix).
- Rate limiting: 429 responses include `Retry-After` header (P2-09 fix).
- Dev-token endpoint: disabled by default; requires `DEV_TOKEN_ENABLED=true` to opt in (P1-04 fix).
- Intelligence boundary: model provider output is advisory only (`is_advisory=True`); model cannot authorize, execute, or approve; provider failure → deterministic fallback (P1-05 fix: failures now logged).
- Audit trail: `audit_events.actor_id` now has FK → `principals.id` with SET NULL on delete (P2-10 fix, migration 0005).

## 9. Known Debt (see AGENTOS_OPERATING_PROMPT §18)

- ~~P0: REST control-plane authentication/authorization~~ — RESOLVED (enforced in non-development deployments).
- P1: demo scenario engines bypassing governance/ledger in some synthetic paths; legacy CISO demo not repeatable; audit same-instant timestamp ordering. Approval reads now finalize due pending approvals under the existing guarded expiry transition; no reviewer action is required to make an expired approval terminal.
- P2: majority SQLite-only coverage; no comprehensive PG E2E; API error semantics (409-for-validation, 404-for-missing-approver, 201-on-replay); execution_status weakly represented in the action-request schema; demo-data accumulation; concurrent approval test added but SQLite concurrency proof is limited.
- P3: unwired webhook handler + in-memory dedup; resource `owner_reference` never enforced; some unused/dead endpoints; cosmetic UI gaps.
- P4: premature infrastructure/features without evidence (see Do-Not-Build list).

## 10. Do-Not-Build (defer unless customer evidence changes the decision)

Generic LLM gateway, prompt filtering/prompt-injection product, generic chatbot/RAG/CRM/AI automation, dynamic MCP discovery, SPIFFE, DPoP, SCIM, Slack/Teams approvals, Redis, unwired rate limiting, OPA/Rego second policy engine, real banking connectors / real-money movement, multi-region, visual policy builder, frontend redesign for aesthetics, additional canned demo scenarios.

## 11. Documentation State

Documentation is substantially stale. Known contradictions: "external execution
disabled" / unconditional `NOT_EXECUTED` claims; old MCP identity model; old
risk model; old tenant model; old delegation scopes; obsolete Render claims;
obsolete competition/demo descriptions. The current review-branch test count
is recorded in section 7; individual historical reports may retain their
original counts and must label them as historical. Customer-discovery docs are
accurate (0 evidence; FROZEN). Legacy competition docs
(`AGENTOS_MASTER_PROMPT.md`, `AGENTOS_PROJECT_CONTEXT.md`) are marked
historical; do not use them as source of truth. `AGENTOS_OPERATING_PROMPT.md`
and this file are canonical.

## 12. Evidence Ledger (conceptual labels)

- VERIFIED FACT (code/DB/runtime/test): pipeline, migration head, test numbers, demo flow, security invariants.
- HYPOTHESIS: finance/treasury wedge; agent-action governance market need; manufacturing/semiconductor alternatives.
- UNPROVEN: market demand, buyer, WTP, competitive commercial position, production readiness, PG E2E.
- CUSTOMER EVIDENCE: none.
- Inference vs fact: always label; never present one as the other.

## Product Experience (God-Mode demo sprint — 8 September 2026)
- Unified product navigation (grouped, active-state): Flagship demo / Control center / Action gateway / Agent governance / Observability.
- Flagship `/demo` is a guided lifecycle experience: pre-run explainer, stage tracker (Request → Identify → Authorize → Evaluate → Approve → Revalidate → Execute → Audit), Action Card, distinct-approver approval step, "ACTION GOVERNED" proof view, reset/rerun, and an integrated attack/failure scenario board (unauthorized, tamper, revocation, cross-tenant, duplicate, timeout) — all reusing the verified governance engine.
- Delegations page and Tools-as-capabilities page added; action-request detail now drills down to Execution record, Approval, Policy decision, and per-action Audit trail via a server-derived `tenant_id` on the detail API.
- Observability page surfaces security/blocked events with per-action tracing.
- Verified live on PostgreSQL: flagship approve path (request `8a1334ba-fd1f-4f27-af86-fe37efb61bde`, approval `95d90b69-7f50-4d9e-a222-f1a62add46f4`, risk 75/CRITICAL, execution SUCCEEDED, 8 audit events) and all seven failure scenarios. Frontend typecheck/lint/build pass. See `docs/GOD_MODE_PRODUCT_DEMO_REPORT.md`.

## 13. Next Decision

The founder delivery directive on 17 September 2026 authorizes review-branch
engineering, testing, documentation, and local/sandbox verification through
the stated deadline. The following decisions remain explicitly pending: (1)
send customer-discovery outreach using the treasury demo as the artifact, (2)
authorize external/customer-hosted exposure and its P0 identity/tenant work,
and (3) approve any merge to `main`. Do not start, deploy, contact, or merge
automatically.

---

*Canonical until a new verified audit supersedes it. Any update requires verification against source, DB, runtime, and tests, plus a new Git checkpoint.*
