# Build Execution Record V1

**Status:** Reference record. `AGENTOS_STATE.md` is the canonical current
state lock. The product/market direction below is a hypothesis, not an approved
launch decision; the review branch remains unmerged.

## Purpose

This is the running engineering and product record for the current build. It
prevents repeated analysis, distinguishes implemented work from planned work,
and records the small number of permissions that must be obtained before a
live pilot or public launch.

## Product direction

The current **provisional** first-pilot hypothesis is governed customer credits
and refunds. The product would sit between an existing support AI/workflow and
the connected business systems. It would govern the precise proposed action;
it would not replace the support agent, helpdesk, billing platform, or payment
provider.

The pilot is still subject to discovery evidence and design-partner validation.
It may be changed if customer evidence shows that native support/billing tools
already solve the buyer's actual problem.

## Completed milestones (review-branch artifacts)

These are implemented artifacts on `codex/unverified-working-tree-20260917`.
They are not a customer-validated product milestone or authorization to merge.

| Milestone | Outcome | Verification |
| --- | --- | --- |
| Action-control foundation | Typed action context, policy/risk evaluation, approval binding, revalidation, execution receipt, causal audit sequence, and portable evidence export | Backend automated suite |
| Remedy pilot sandbox | Guided synthetic customer-refund and account-credit flows, policy/approval path, sandbox receipt, and case evidence | Demo and backend integration tests |
| Connector boundary | Disabled-by-default Stripe refund adapter and read-only, minimised Zendesk context adapter | Connector-specific tests; no live credentials used |
| Failure recovery | Durable reconciliation jobs for uncertain execution outcomes; status readback never re-submits a consequential action | Execution-ledger and reconciliation tests |
| Tenant roles | Database-backed `ADMIN`, `POLICY_AUTHOR`, `APPROVER`, `OPERATOR`, and `AUDITOR` enforcement on sensitive control-plane and read surfaces | Authorization and REST security tests |
| Agent lifecycle | Explicit activate, suspend, and irreversible retire operations; generic record edits cannot change status; UI case file supports the lifecycle | Backend registry/authorization tests; frontend typecheck and lint |
| Hosted configuration hardening | Staging and production reject unsafe startup configuration rather than accepting placeholder database, identity, browser-origin, webhook, rate-limit, or log settings | Commit `58bcaf6`; configuration and full backend test suites |
| Structured log minimisation | JSON logs emit only approved operational fields, cannot copy arbitrary token/action-context/provider-payload extras, and record only exception type rather than raw message/stack | Commits `aea82b0`, `573bd44`; regression and full backend test suites |

## Current milestone

**Frozen-scope review-branch verification and discovery preparation.** Until
the founder Next Decision in `AGENTOS_STATE.md` is approved, work is limited to
verified bug/security fixes, test coverage, documentation reconciliation,
accessibility/reliability work, and locally testable launch-readiness. No new
pilot feature, production exposure, external outreach, or merge to `main` is
authorized by this record.

## Verified checks

Latest full backend run on `codex/unverified-working-tree-20260917`:
**399 passed, 8 skipped, 1 upstream warning**. Frontend typecheck, lint, and
the 21-route production build pass. These are branch verification facts only;
they do not validate demand, certify production readiness, or authorize a
merge/deployment. Docker and a real PostgreSQL deployment rehearsal have not
been run in this environment.

## Known launch gaps

1. Discovery interviews and a design partner have not validated the pilot
   problem or connector choice.
2. A real Stripe test-mode rehearsal and partner-approved Zendesk OAuth flow
   have not been performed.
3. Hosted PostgreSQL migration/restore rehearsal, shared rate limiting,
   production monitoring/alerting, and a production identity-provider test are
   still required.
4. Privacy notice, DPA/subprocessor review, retention policy, terms, support
   runbook, and qualified legal/security review remain external launch work.
5. No production deployment, customer processing, billing, or commercial
   launch has occurred.

## Decisions and rationale

| Decision | Rationale |
| --- | --- |
| Do not build a generic AI-agent builder | Established platforms already own broad agent creation and workflow automation. The defensible product is the independent control/evidence layer for consequential actions. |
| Keep agents as registered, governed identities | An agent may propose work, but it cannot grant itself authority or bypass policy, approval, evidence, and recovery controls. |
| Sandbox first | It supports a credible buyer demo while preventing accidental real payment or customer-data processing before the evidence and security gates are met. |
| Lifecycle retirement is irreversible | A retired agent should not silently regain authority. Historical evidence must remain auditable. |

## Pending permissions list

| Permission / decision | Why it is needed | What it blocks |
| --- | --- | --- |
| Founder approval to send customer-discovery outreach | Customer evidence is zero; any outreach is external communication in Priyank's name. | Real buyer/problem validation and design-partner discovery. |
| Founder approval for external/customer-hosted exposure | Requires a selected pilot environment, scoped credentials, identity/tenant design, and external operational ownership. | Hosted validation, test-mode connector rehearsal, and real customer data access. |
| Founder approval to merge a reviewed change set to `main` | The review branch contains an unmerged snapshot and subsequent verification/hardening commits. | A release candidate or any claim that the branch is the accepted baseline. |

When discovery identifies a willing design partner, expand the second entry
with the provider, environment, minimum OAuth/API scopes, data fields, owner,
purpose, test plan, and expiry/rotation plan. Production deployment, customer
communication, legal terms, paid services, and live credentials require
explicit, scoped approval and are not inferred from this record.
