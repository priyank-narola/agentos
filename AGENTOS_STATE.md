# AGENTOS — CURRENT STATE LOCK (Canonical Project State)

**Version:** 1.9 — 19 September 2026
**Status:** CURRENT (canonical). Companion to `AGENTOS_OPERATING_PROMPT.md`.
**Verified baseline:** Git `main` @ `332e68c65b2ba1d888707f0031fe83a7be3fbd2b` (governance UX redesign, Intelligence V2, and security-audit fixes).
**Update rule:** This file is authoritative until a new verified audit changes it. Any agent updating it must verify against source, DB, runtime, and executed tests first, and record the new Git checkpoint.

## 0A. Workforce OS / Paperclip-inspired integration — 19 September 2026

- Priyank explicitly authorized research and implementation of a Paperclip-like
  AI-workforce operating layer, integrated with—not replacing—the existing
  AgentOS action-governance product. The recorded assessment is
  `docs/PAPERCLIP_INTEGRATION_ASSESSMENT_V1.md`.
- Official upstream Paperclip code at review pin
  `6d03428682d9c0bc75f620e74c7075b6d9d0d12e` was inspected locally from the
  public `PaperclipAI/paperclip` repository. The code repository is MIT; any
  future copied substantial code must retain its notice and be recorded in a
  third-party notice. Paperclip branding, marketing copy, hosted credentials,
  and separately CC BY-NC-N documentation content are not copied.
- Architecture decision: build a native `Workforce` module in the existing
  Next.js/FastAPI/SQLAlchemy control plane. It will own organization, goal,
  project, work-item, run/routine, and budget domains. The existing gateway,
  policy, approval, execution ledger, reconciliation, and evidence systems
  remain the exclusive protected-action boundary.
- Research checkpoint: commit `7762b93` records the license, architecture,
  user-flow, and integration assessment. It is pushed to the review branch.
- Workforce W1 checkpoint: commit `b81baba` adds additive migration
  `20260919_0010`, tenant-scoped goals, projects, and work items, a planning
  API, idempotent local-only seed data, and the `/workforce` dashboard. It
  reuses existing AgentOS agent identities and has no execution or approval
  path. Verification: a fresh SQLite migration reaches `0010`; seed replay
  creates `2` goals, `1` project, and `3` work items then stays idempotent;
  focused migration/model/API tests pass `9 passed`; the full backend suite
  passes `405 passed, 8 skipped, 3 warnings`; frontend typecheck, lint, and
  production build pass with the `/workforce` route.
- Workforce W2 checkpoint: commit `911c0ae` adds the real-API-backed
  `/workforce/goals` and `/workforce/projects` surfaces and promotes Workforce
  to a grouped product navigation area. Users can create goals, nest them,
  assign existing active governed agents, create projects and work items, and
  update a work item's planning status. These actions are planning-only: they
  do not schedule or start agents, change delegated authority, or invoke an
  action connector. Frontend typecheck, lint, and the production build pass
  with `26` routes. Commit `3edca64` adds an opt-in same-origin Next.js proxy
  for local sandbox development, leaving production direct unless an operator
  explicitly configures it. Browser verification now visibly loads the seeded
  Workforce dashboard: `2` active goals, `1` active project, and `3` work
  items. Backend migration/seed/API verification stays independently verified
  as described above.
- Status: **IMPLEMENTATION AUTHORIZED ON REVIEW BRANCH; W0 and W1 complete as
  review-branch engineering checkpoints.** No merge to `main`, external
  deployment, customer outreach, real account creation, live connector, live
  payment, customer data, or legal commitment is authorized by this decision.
- Public-product checkpoint: the review branch now exposes a distinct public
  layer at `/` with linked `/product`, `/security`, `/pricing`, `/login`, and
  `/signup` pages. The existing control center remains available at
  `/control-center`; Workforce and all existing governance surfaces remain
  intact. The login and signup pages are explicitly sandbox entry surfaces,
  not production account creation or live identity-provider integration. This
  is a local/review-branch product shell only; public deployment remains
  pending the founder decision in section 13.
- Public motion checkpoint: the landing page now has an original AgentOS
  motion and interaction layer: staged content entry, animated visual depth,
  responsive command-card feedback, CTA and navigation hover states, feature
  card elevation, and a `prefers-reduced-motion` fallback. It is inspired by
  high-level design qualities observed in supplied Paperclip and product-site
  recordings but does not copy their code, branding, visual assets, or copy.
- Public landing redesign: the former lightweight marketing surface has been
  replaced with a full AgentOS command-center story: a responsive sandbox
  control-center visual, connected Workforce-to-governance diagram, operating
  loop cards, explicit control claims, and accessible responsive styling.

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
- Commit `58bcaf6` closes the remaining staging startup-configuration gap:
  both `staging` and `production` now fail closed at startup without explicit
  PostgreSQL, HTTPS browser origins, identity verifier, non-sandbox webhook
  secret, safe limits, and JSON logging. Development and test remain usable
  for local verification. The configuration regression suite now covers both
  safe and unsafe staging settings.
- Commit `aea82b0` closes a structured-log data-minimisation gap: JSON logs now
  allow only a small operational field set (`event`, request ID, method, path,
  status, duration) and ignore arbitrary logging extras such as authorization
  headers, action parameters, or provider payloads.
- Commit `573bd44` extends the same boundary to exception handling: hosted JSON
  logs retain only an exception type, never a raw exception message or stack
  that could contain provider, request, or connection detail.
- On the review branch, the complete backend suite has since been re-run with
  `399 passed, 8 skipped, 1 warning` (no failures). Frontend typecheck, lint,
  and the 24-route production build also pass. These are review-branch
  verification facts, not evidence of customer validation or authorization to
  merge/deploy.

### Review-branch UI evidence checkpoint — 18 September 2026

- Commit `c9843a654f3c2416b6d3c1e2f64ac2008f1241a3` adds `/evidence`, a
  current-tenant Evidence / Audit Explorer built only on the existing
  action-request, approval, observability-timeline, and server-produced
  evidence-export contracts. It supports search plus outcome/risk/time
  filtering, causal-chain inspection, integrity metadata, and JSON export.
  The UI labels the environment sandbox/test-only and never implies live money
  movement.
- Commit `7646950553be207c2378f8f0eeaf72877f5b6780` upgrades
  `/action-requests` using the existing gateway/ledger request contract. It
  adds searchable decision evidence, decision/risk/execution filtering,
  visible routing and risk summaries, and direct preflight/test-action entry
  points while preserving the existing detail case file.
- Commit `db6d37965aa7ca77ed77d1cf29cdee6a95117686` upgrades
  `/policy-evaluation` to refresh a safe preflight prediction after valid
  action fields change. It remains non-persistent, uses the existing
  action-preflight endpoint, exposes policy/risk/approval-route reasoning,
  and labels its sandbox/test-only connector plan truthfully.
- Commit `08e602d6afc06604f818b3d600207919ba60e492` clarifies the
  `/reconciliation` operator workflow: it only checks a durable provider
  outcome and never retries or claims to reverse an action. Where remediation
  is required, it hands the operator to a distinct correction-action preflight
  so that any follow-up is separately governed and evidenced.
- Commit `46f3925a4a2c083e7e848752b6a19df05f99b6c7` resolves the approval
  decision-reason contract gap with nullable storage, migration `0009`,
  approve/reject API validation, response/evidence inclusion, and audit-event
  capture. Commit `11c93ddaab2596947b0a31d95a9778295ffce9fc` makes the
  Approval Workbench require the persisted reason and display it after decision.
- Verification for this UI checkpoint: `npm run typecheck`, `npm run lint`,
  and `npm run build` pass. The production build completes 25 routes.
- This remains review-branch UI work, not production readiness, customer
  validation, permission for external exposure, or permission to merge.

### Review-branch governance completion checkpoint — 18 September 2026

- Commit `f6c64f430dcfc235c27cbb36cb25d9deeef20bab` adds source-backed search
  and status filtering to the Agents registry. Commit
  `ad3e9f891c4b6beaad6c77ae003e96a7fc674a80` does the same for the Tools /
  Capabilities registry. Neither change invents registry data or connector
  state.
- Commit `609c46a96d0c6e85856f76f92ef72fd9348229e1` exposes the existing
  persisted delegation-revocation endpoint in the UI. Commit
  `eee1f94` exposes the existing persisted issuance endpoint with a
  least-privilege form; commit `d0df25b` adds backend enforcement so direct
  API callers must use an active human principal, active agent, and a later
  expiry when one is supplied. Commit `e4bf448` rejects whitespace-only
  scope. The focused
  `tests/test_registry_api.py` check passes **5 passed, 1 upstream warning**.
- Commit `88a8559d8d07d455166641589665db7873bf3df3` adds `/settings`, a
  truthful, read-only tenant posture workspace based on existing identity,
  role, launch-readiness, and connector-readiness contracts. It intentionally
  does not pretend that mutable IdP, retention, credential, or break-glass
  administration exists.
- Commit `146a4887f974b08d9976edddb8952ca372751c3a` adds a draft-only,
  tenant-scoped policy simulation endpoint. Commit
  `858a9d1c08a6c2702f980833368b200aaa748ce2` wires its real prediction into
  the draft-policy workbench. The targeted policy/API suite passed **16
  passed**.
- Commit `cd3f88d` adds an Observability operational-attention section driven
  by real reconciliation, execution-ledger, audit-integrity, and
  process-local runtime data. It explicitly labels this a derived view rather
  than a durable alerting or paging system.
- Frontend `npm run typecheck`, `npm run lint`, and `npm run build` passed for
  the observability and delegation UI checkpoints. All of the above is on
  `codex/unverified-working-tree-20260917`, pushed, unmerged, and not a
  production or market-validation claim.

### Review-branch browser, accessibility, and dependency checkpoint — 18 September 2026

- Commit `627371a` introduces local Playwright and axe-core browser coverage
  for two critical mocked-API journeys: non-persistent action preflight and
  an approval decision that remains disabled until a reason is supplied, then
  records that reason through the client contract. The preflight test runs an
  axe scan over the application `main` region. This is browser regression
  coverage, not a live-backend or customer-workflow E2E claim.
- The checkpoint corrects WCAG AA contrast failures detected by axe in shared
  metadata tokens and the preflight decision summary. It verifies **2/2
  browser tests**, `npm run typecheck`, `npm run lint`, and the 23-route
  production build.
- The production dependency audit initially exposed critical Next.js 15.5.23
  advisories. The checkpoint upgrades Next.js and its ESLint configuration to
  15.5.24 and applies narrowly scoped PostCSS 8.5.28 and Sharp 0.35.4
  overrides. `npm audit --omit=dev --json` then returned **0 production
  vulnerabilities**. This is a dependency snapshot, not a substitute for a
  continuing release-time audit or an independent security review.

### Review-branch seeded-backend browser checkpoint — 18 September 2026

- Commit `934b731a8ed1d8444a164701488ed1859f764924` adds a separate Playwright integration route for the
  Action Preflight workspace. It provisions no shared state: the verification
  uses a disposable, locally migrated and seeded SQLite sandbox API, then
  drives the browser through the actual catalog and `/action-preflight` API.
  The assertion proves that a `FinanceAgent` bank transfer is rendered as
  `REQUIRE_APPROVAL` with the real human-revalidation execution route. The
  ordinary mocked browser suite deliberately excludes this fixture-dependent
  test and remains independently runnable.
- Verification for this checkpoint: the fresh local migration chain reached
  `20260918_0009`; the idempotent seed produced allow, deny, approved,
  rejected, and pending flows using only the in-process sandbox provider;
  `npm run test:e2e:integration` passed **1/1**, while `npm run test:e2e`
  passed **2/2**, `npm run typecheck` and `npm run lint` passed, and the
  23-route production build passed. This is one browser/API contract path,
  not a claim that all backend-integrated browser journeys, PostgreSQL E2E, or
  screen-reader testing are complete.

- Commit `6e57ebdd3a10691a3c93cb892adb28c2ae491927` extends that local,
  seeded-sandbox browser coverage through the Approval Workbench. It creates a
  fresh high-risk request, proves that the requester is excluded from eligible
  approvers, requires a non-empty decision reason, approves as the distinct
  human reviewer, then verifies both the persisted reason and sandbox
  execution result. The mock suite now supports either local API port so its
  isolated regression coverage does not depend on another project’s service.

## Backlog Closure (W1–W18) — 8 September 2026
The historical/pending-work backlog sprint is closed for engineering. See `docs/OLD_WORK_BACKLOG_CLOSURE_REPORT.md` for the authoritative W1–W18 audit.
- Migration head: `20260909_0005` (adds FK on `audit_events.actor_id`; verified fresh/existing on PG16).
- Migration `0001` retained as historical baseline snapshot by documented decision (`docs/migration-0001-adr.md`).
- REST control-plane authentication enforced in any non-development deployment or when `REST_AUTH_REQUIRED=true`; development demo may run unauthenticated (explicit operator choice). The local REST HMAC development secret is available only in `development`; hosted environments require an explicitly configured verifier and otherwise fail closed. Dev-token issuance is disabled by default and is available only with the `DEV_TOKEN_ENABLED=true` opt-in in `development`; staging and production fail closed.
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

Client → REST (`/api/v1/*`, **authenticated** when `REST_AUTH_REQUIRED=true` or non-development; dev-token endpoint is an opt-in available only in `development`) or MCP (`/mcp`, OAuth2.1 Bearer → `AgentIdentityResolver` → immutable `SecurityContext` {Principal, Agent, Delegation, tenant}) → `GatewayService.submit` (reference + tenant validation, financial parameter validation, SHA-256 payload digest, `RiskEngine`, `DeterministicPolicyEvaluator`, Intelligence Assessment advisory-only) → `Decision` + `AuditEvent`s → REQUIRE_APPROVAL (`ApprovalRequest`: SoD, digest re-check, full TOCTOU re-validation, row-level locking, sandbox execution) or low-risk allowed wire (sandbox execution) → `FinancialExecution` + `AuditEvent`s → Observability (read-only).

## 4. Technology

Next.js (frontend) · FastAPI (backend) · PostgreSQL 16 (authoritative) · SQLAlchemy · Alembic · pytest · MCP · OAuth2.1/JWT (MCP path). SQLite is used for fast unit tests only and does not prove PostgreSQL behavior.

## 5. Database State

- Migration head: `20260918_0009` (adds nullable `approval_requests.decision_reason`). Static migration tests now cover fresh schema expectations and an upgrade path through `0009`; actual PostgreSQL execution through that head remains required before Phase 0 closure because the configured scratch PostgreSQL environment is unavailable. Seed is idempotent; migrations are additive/non-destructive.
- Tables (17): tenants, principals, principal_roles, agents, delegations, tools, actions, resources, policies, policy_rules, action_requests, decisions, approval_requests, audit_events, financial_executions, reconciliation_jobs, webhook_events.
- Tenant integrity (verified on live DB): 0 tenant mismatches across decisions/approvals/audits/ledger vs owning action request; 0 agent-owner cross-tenant mismatches; every action request has decisions; every APPROVED approval has an EXECUTION_SUCCEEDED audit; every SUCCEEDED ledger row has the execution audit. One historical pre-ledger execution audit exists (executed before the ledger existed) with no ledger row — do not fabricate a backfill.
- `Decision` and `FinancialExecution` are tenant-owned (NOT NULL FK → tenants).
- Risk model distinction: persisted `RiskClassification` enum = LOW/MEDIUM/HIGH; runtime tier string = LOW/MEDIUM/HIGH/CRITICAL (score ≥75). CRITICAL is never a persisted enum.

## 6. Flagship Demo (sandbox, technical evidence only)

- Flow: $25,000 USD wire transfer. Agent `TreasuryBot-v1` → requester `Alice Smith` (Treasury Manager) → policy `Treasury Wire Transfer Policy v1` → risk 75 / tier CRITICAL → decision REQUIRE_APPROVAL → approver `Bob Jones` (VP Finance, independent; SoD enforced) → APPROVED → TOCTOU PASS → sandbox execution SUCCEEDED → FinancialExecution PERSISTED → 8-event audit chain → observability.
- Guided UI: `/demo`. Rejection path: REJECTED, no execution, no ledger row. Tamper path: reuses Scenario D (payload digest mismatch → BLOCKED_TAMPER_DETECTED / NOT_EXECUTED). Repeatable: treasury bootstrap is idempotent (stable tenant slug, tool, principals).
- Recorded runtime evidence (historical, 2026-09-08): approve request `ac4bdd59-10fb-4842-a6e9-2be3beff5e8d`, approval `d65910de-f9b7-47cc-8693-0260917ed7f4`, provider tx `REF-5A0CEFA4`. Reject request `7f432159-0f10-48b1-9388-35912bcbbece`. Tamper request `dbf80db6-97f3-48af-b184-dbabca809293`.
- NO REAL MONEY. Sandbox provider only.

## 7. Test Truth

- Current full review-branch backend checkpoint after `e4bf448`: **402 passed
  / 8 skipped / 3 warnings / 0 failed** in 40.29 seconds. The warnings are one
  upstream AnyIO `BlockingPortal` deprecation and two Starlette status-constant
  deprecations exercised by approval API tests. Later focused registry
  safeguards through `e4bf448` also pass **5 tests**.
- Frontend: `npm run typecheck`, `npm run lint`, and `npm run build` passed at
  the later seeded-backend browser checkpoint, alongside 2 mocked-API browser
  flows with a scoped axe scan and 2 seeded-sandbox backend-integrated flows
  (preflight and approval). Other critical workflows,
  screen-reader testing, and broad coverage remain absent and are not claimed
  complete.
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
- Hosted REST verifier: staging and production never fall back to the known local development HMAC secret; an explicit HMAC/public-key/JWKS verifier is required or requests fail closed.
- Dev-token endpoint: disabled by default; requires `DEV_TOKEN_ENABLED=true` to opt in **only in development**. Staging and production reject configuration and endpoint access (P1-04 hardening).
- Hosted startup validation: staging and production require explicit PostgreSQL,
  HTTPS origins, a configured identity verifier, non-sandbox webhook secret,
  positive bounded limits, and JSON logging before the process starts;
  development/test remain available for local verification.
- Structured JSON logs are data-minimised through an explicit operational-field
  allowlist; arbitrary `extra` values such as authorization headers, action
  parameters, and provider payloads are omitted by regression-tested default.
  Exception messages and stacks are also excluded from hosted JSON logs; only
  their class is retained for safe aggregation.
- Intelligence boundary: model provider output is advisory only (`is_advisory=True`); model cannot authorize, execute, or approve; provider failure → deterministic fallback (P1-05 fix: failures now logged).
- Audit trail: `audit_events.actor_id` now has FK → `principals.id` with SET NULL on delete (P2-10 fix, migration 0005).

## 9. Known Debt (see AGENTOS_OPERATING_PROMPT §18)

- ~~P0: REST control-plane authentication/authorization~~ — RESOLVED (enforced in non-development deployments).
- P1: demo scenario engines bypassing governance/ledger in some synthetic paths. The CISO sandbox demo is repeatable (`test_ciso_repeatability.py` verifies two consecutive runs without tenant/tool duplication and with one ledger row per successful run). Approval reads now finalize due pending approvals under the existing guarded expiry transition; no reviewer action is required to make an expired approval terminal. Audit presentations now order action events by durable causal sequence with stable timestamp/ID tie-breakers.
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
historical; do not use them as source of truth. Legacy Phase 5 outreach logs
that claim messages were sent/delivered are explicitly marked historical and
unverified: no communication source in this workspace proves those claims, so
they are preparation only and not customer evidence. `AGENTOS_OPERATING_PROMPT.md`
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
