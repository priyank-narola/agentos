# Customer Credits & Refunds Pilot Spec V1

## Product definition

The first market product is an independent action-control layer for customer
credits and refunds proposed by an existing support workflow or AI agent.

It is **not** a helpdesk, chatbot, billing platform, general workflow builder,
or generic AI governance dashboard.

## Pilot user and moment

| Element | Pilot definition |
| --- | --- |
| Economic buyer | Head of Support, Support Operations, Customer Operations, or Billing Operations leader at a SaaS company |
| Daily user | Support operations lead or designated refund approver |
| Trigger | Existing support workflow proposes a customer credit or refund |
| Controlled consequence | A billing remedy changes money owed/returned to a customer |
| Success | The customer can prove what was proposed, why it was permitted, who approved it, what system executed it, and what happened if the provider response was uncertain |

## Exact pilot action contract

Required before an action can be submitted:

1. Support ticket/reference and customer billing account.
2. Billing payment/invoice/subscription reference.
3. Remedy type: refund or credit.
4. Display amount, currency, and provider-safe minor-unit amount (for example,
   USD 49.00 is `4900`).
5. Customer-facing/business reason.
6. Before state: refundable/creditable balance and prior remedies when available.
7. Proposed change.
8. Recovery class and honest recovery plan.
9. Idempotency key.

For a payment refund, recovery is normally `IRREVERSIBLE`: the product must not
claim that it can simply reverse a settled refund. A correction is an explicitly
documented follow-up business action, never a silent retry.

## Required control path

```text
Support AI / workflow
  → submits exact proposed refund or credit
  → deterministic policy and risk decision
  → independent approval when policy requires it
  → revalidate identity, delegation, policy, and payload
  → billing connector submits once with provider idempotency
  → provider receipt and webhook/readback update the case
  → unknown outcome enters reconciliation; no automatic retry
```

## First-pilot scope

- One helpdesk context source (start with Zendesk only if a design partner uses it).
- One billing provider (start with Stripe only if the same design partner uses it).
- Refunds and account credits only; no cancellations, plan changes, or goodwill
  discounts until the first remedy is reliable.
- Rules for automatic block, approval-required, and permitted paths.
- Case file, evidence export, audit sequence, and reconciliation queue.
- Sandbox/test-mode end-to-end rehearsal before any production credentials.

## Explicitly out of scope

- Building a new AI support agent or replying to customers.
- Reading whole ticket histories without a minimisation design.
- Automatically approving refunds in the first pilot.
- Live production payments, customer data, or connector credentials before a
  partner approves the scope and sandbox rehearsal succeeds.
- Multi-provider orchestration, usage billing, SSO/SCIM, and broad enterprise
  compliance promises.

## Differentiation test

Native platforms already provide pieces of this workflow. Zendesk documents
approval requests for refunds and action flows, and Stripe exposes refund
creation. The pilot earns its place only if a customer values the layer between
systems: exact-payload governance, cross-system evidence, independent approval,
revalidation, reconciliation, and a portable case file.

The pilot is rejected if the buyer says their helpdesk/billing platform already
provides adequate control and evidence for their actual refund workflow.

## Evidence gate before connector activation

The connector remains disabled until all are true:

1. Three or more relevant buyer interviews identify the same refund/credit
   control failure or audit burden.
2. At least one design partner confirms a sandbox/test-mode workflow.
3. The support ticket and billing identifiers can be minimised and mapped.
4. Policy thresholds, approver role, and refund recovery procedure are approved
   by the partner.
5. Webhook, idempotency, timeout, reconciliation, retention, and incident
   handling are tested against that provider's sandbox.

## Current implemented product slice

The sandbox demo provisions a support automation owner, independent support
operations lead, refund and account-credit actions, customer billing account,
active policy, and delegation. It binds the appropriate ticket/payment or
ticket/billing context and an honest recovery posture to the selected remedy,
then demonstrates policy, approval, revalidation, sandbox receipt, and audit
evidence. The refund path is irreversible; the account-credit path is
compensatable only through a separately governed correction. It does not
connect to Zendesk or Stripe by default.

The codebase also contains a disabled-by-default Stripe Refund API adapter. It
requires explicit server-side enablement, a server-only secret, a Stripe
PaymentIntent/Charge reference, a minor-unit amount, and provider idempotency.
It is not enabled until the evidence gate and a partner-approved test-mode
rehearsal are complete.

The Zendesk side is likewise disabled by default. Its read-only endpoint is
restricted to tenant `ADMIN`/`OPERATOR` roles and accepts only server-side OAuth
configuration. It retrieves minimised ticket metadata (status, type, priority,
requester/organisation IDs, tags, timestamps) and deliberately excludes subject,
description, comments, attachments, and customer message content.

## Sources

- [Zendesk approval requests](https://support.zendesk.com/hc/en-us/articles/8481179038490-Understanding-approvals-and-how-they-work) — supports refund approvals inside ticket workflows; accessed 15 September 2026.
- [Zendesk actions for AI-assisted workflows](https://support.zendesk.com/hc/en-us/articles/9174548349978-About-actions-for-auto-assist-and-action-flows) — documents support actions and cautions that write actions such as refunds should be agent-approved; accessed 15 September 2026.
- [Stripe Refund API](https://docs.stripe.com/api/refunds) — documents partial/full refunds and provider constraints; accessed 15 September 2026.
