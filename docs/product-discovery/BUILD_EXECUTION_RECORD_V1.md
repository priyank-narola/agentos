# Build Execution Record V1

## Purpose

This is the running engineering and product record for the current build. It
prevents repeated analysis, distinguishes implemented work from planned work,
and records the small number of permissions that must be obtained before a
live pilot or public launch.

## Product direction

The current **provisional** first pilot is governed customer credits and
refunds. The product sits between an existing support AI/workflow and the
connected business systems. It governs the precise proposed action; it does
not replace the support agent, helpdesk, billing platform, or payment provider.

The pilot is still subject to discovery evidence and design-partner validation.
It may be changed if customer evidence shows that native support/billing tools
already solve the buyer's actual problem.

## Completed milestones

| Milestone | Outcome | Verification |
| --- | --- | --- |
| Action-control foundation | Typed action context, policy/risk evaluation, approval binding, revalidation, execution receipt, causal audit sequence, and portable evidence export | Backend automated suite |
| Remedy pilot sandbox | Guided synthetic customer-refund and account-credit flows, policy/approval path, sandbox receipt, and case evidence | Demo and backend integration tests |
| Connector boundary | Disabled-by-default Stripe refund adapter and read-only, minimised Zendesk context adapter | Connector-specific tests; no live credentials used |
| Failure recovery | Durable reconciliation jobs for uncertain execution outcomes; status readback never re-submits a consequential action | Execution-ledger and reconciliation tests |
| Tenant roles | Database-backed `ADMIN`, `POLICY_AUTHOR`, `APPROVER`, `OPERATOR`, and `AUDITOR` enforcement on sensitive control-plane and read surfaces | Authorization and REST security tests |
| Agent lifecycle | Explicit activate, suspend, and irreversible retire operations; generic record edits cannot change status; UI case file supports the lifecycle | Backend registry/authorization tests; frontend typecheck and lint |

## Current milestone

**Pilot workflow completeness and launch-hardening.** The next implementation
work must make the first pilot easier for a buyer/operator to set up, inspect,
and safely rehearse without expanding into a generic agent platform.

## Verified checks

Latest full backend run: **381 passed, 8 skipped**. Latest targeted agent
lifecycle run: **10 passed**. Frontend typecheck and lint pass. Docker and a
real PostgreSQL deployment rehearsal have not been run in this environment.

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

No immediate permission blocks safe local development.

When discovery identifies a willing design partner, add a scoped entry before
any real integration: provider, environment, minimum OAuth/API scopes, data
fields, owner, purpose, test plan, and expiry/rotation plan. Production
deployment, customer communication, legal terms, paid services, and live
credentials require explicit, scoped approval and are not inferred from this
record.
