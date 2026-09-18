# Phase 0 Completion Matrix

**Status vocabulary:** verified work is a **Verified Fact** only when backed by
source, executed checks, and a commit. Market claims remain **Hypothesis**.
Anything requiring a founder, external party, production credential, or legal
approval is **Blocked**.

## Phase 0 UI / contract audit — 18 September 2026

| Required workspace | Current implementation evidence | Phase 0 state | Remaining work / constraint |
| --- | --- | --- | --- |
| Dashboard | `/` uses observability and governance data | In progress | Validate the full dashboard acceptance journey and accessibility flow. |
| Action requests | `7646950` plus existing case file | Verified Fact | Browser/E2E coverage remains required. |
| Preflight | `db6d379` uses `/action-preflight`; `627371a` adds mocked-API browser + axe coverage; `934b731` adds a seeded-sandbox browser/API path | Verified Fact | One backend-integrated path is verified. Broader screen-reader coverage and non-preflight browser paths remain required. |
| Approval workbench | `46f3925`, `11c93dd` persist a required decision reason; `627371a` browser-tests reason gating/recording; `6e57ebd` verifies the independent sandbox approval route | Verified Fact | Cancellation/expiry and broader accessibility coverage remain required. |
| Policies | `146a488` draft-only simulation endpoint; `858a9d1` real draft workbench | Verified Fact | Browser/E2E/accessibility coverage and saved regression suites remain required. |
| Agents and tools | Existing lifecycle routes; `f6c64f4` / `ad3e9f8` source-backed filtering | In progress | Validate lifecycle journeys and accessible keyboard paths. |
| Delegations | `609c46a` revoke UI; `eee1f94` issue UI; `d0df25b` direct-API safeguards; `e4bf448` rejects blank scope | Verified Fact | Browser/E2E/accessibility coverage remains required; record-level audit provenance is a release-review question. |
| Evidence / audit explorer | `c9843a6` uses action, approval, timeline, and evidence APIs | Verified Fact | Add browser/E2E/accessibility coverage. |
| Observability | Existing metrics/runtime/timeline; `cd3f88d` derives attention from reconciliation, ledger, audit, and current-process data | In progress | Existing API provides process-local request latency and counters, not durable decision-latency, provider unknown-outcome rate, or alert delivery. |
| Reconciliation | `08e602d` uses reconciliation checks and correction-action handoff | Verified Fact | A correction action is deliberately a separate governed action; browser/E2E coverage remains required. |
| Tenant settings | `/access` provides real role assignment; `88a8559` provides a secret-free posture workspace | In progress | No current API/model covers mutable IdP configuration, retention, API/MCP credential lifecycle, or emergency break-glass. These must not be rendered as fake working controls. |

## Test matrix status

- Backend unit/API/service/security: **Verified Fact** — `46f3925` ran 401
  passing tests, 8 skipped, with 3 upstream/deprecation warnings. `e4bf448`
  subsequently ran `tests/test_registry_api.py`: 5 passed, 1 upstream warning.
  A current full-suite run after `e4bf448` is **Verified Fact**: 402 passed, 8
  skipped, 3 upstream/deprecation warnings, 0 failures (40.29 seconds).
- Database migrations: **In progress** — `3c74848` adds fresh-schema and
  upgrade-path assertions through migration `20260918_0009`; actual execution
  against a disposable PostgreSQL scratch database remains blocked until an
  `AGENTOS_TEST_POSTGRES_URL` is available.
- Frontend typecheck/lint/production build: **Verified Fact** — `934b731`
  passes all three, retains 2 Playwright mocked-API browser flows and an axe
  scan for preflight, and adds 2 seeded-sandbox backend-integrated paths
  (preflight and approval). Full critical-flow coverage and screen-reader
  testing remain **In
  progress**.
- Production dependency audit: **Verified Fact** — `627371a` ran `npm audit
  --omit=dev --json` with 0 vulnerabilities after the Next/PostCSS/Sharp
  security updates. Repeat this audit in CI/release environments.
- Full Phase 0 test matrix: **In progress** — no 100% claim is permitted.

## Phase 1 preparation boundary

The discovery materials already in `docs/product-discovery/` are preparation
only. Interview guide, scorecards, demo narrative, competitor hypotheses, and
consent/data boundaries may be refined locally. No customer contact, account
creation, sent-message claim, interview claim, pilot claim, or market-evidence
claim is authorized. Customer evidence remains **0**.

## Pending permissions / decisions

1. **Blocked — Tenant settings contract:** founder approval is required before
   adding persistent IdP, retention, credential, and break-glass configuration
   models and administrative APIs.
2. **Blocked — Phase 1 execution and later:** real interviews, founder wedge
   decision, signed pilot, production credentials/approvals, outreach, and
   deployment cannot be performed by this automated process.
3. **Merge gate:** `main` remains untouched until every Phase 0 item above is
   verified and the final merge checkpoint is explicitly reviewed.
