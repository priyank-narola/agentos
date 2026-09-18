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
| Preflight | `db6d379` uses `/action-preflight` only | Verified Fact | Browser/E2E coverage remains required. |
| Approval workbench | `46f3925`, `11c93dd` persist a required decision reason | Verified Fact | Add acceptance/E2E/accessibility coverage; cancellation/expiry semantics must remain clear. |
| Policies | Existing list, draft editor, lifecycle controls | In progress | Current policy evaluation covers active policy state; no server contract simulates an unpublished draft. Do not label draft simulation complete. |
| Agents and tools | Existing `/agents`, `/tools`, agent lifecycle routes | In progress | Validate registry/lifecycle journeys and accessible keyboard paths. |
| Delegations | Existing `/delegations` data view | In progress | Current UI has no issue/revoke control exposed by a confirmed backend contract. |
| Evidence / audit explorer | `c9843a6` uses action, approval, timeline, and evidence APIs | Verified Fact | Add browser/E2E/accessibility coverage. |
| Observability | Existing `/observability` metrics/runtime/timeline | In progress | Existing API provides process-local request latency and timeout counts, not durable decision-latency or provider unknown-outcome rates. |
| Reconciliation | `08e602d` uses reconciliation checks and correction-action handoff | Verified Fact | A correction action is deliberately a separate governed action; browser/E2E coverage remains required. |
| Tenant settings | `/access` provides real role assignment | Blocked | No current API/model covers IdP configuration, retention, API/MCP credential lifecycle, or emergency break-glass. These must not be rendered as fake working controls. |

## Test matrix status

- Backend unit/API/service/security: **Verified Fact** — `46f3925` ran 401
  passing tests, 8 skipped, with 3 upstream/deprecation warnings.
- Database migrations: **In progress** — migration `20260918_0009` exists;
  fresh and upgrade-path verification must be added before Phase 0 closure.
- Frontend typecheck/lint/production build: **Verified Fact** — completed for
  `11c93dd`; browser E2E and accessibility suites do not yet exist in the
  repository and are not claimed complete.
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
2. **Blocked — Policy draft simulation:** founder approval is required before
   expanding deterministic policy evaluation to accept unpublished draft
   versions safely.
3. **Blocked — Delegation issue/revoke controls:** founder approval is required
   before adding delegation mutation APIs.
4. **Blocked — Phase 1 execution and later:** real interviews, founder wedge
   decision, signed pilot, production credentials/approvals, outreach, and
   deployment cannot be performed by this automated process.
5. **Merge gate:** `main` remains untouched until every Phase 0 item above is
   verified and the final merge checkpoint is explicitly reviewed.
