# Pilot Connector Feasibility V1

## Purpose

This document answers a narrow technical question for Programme 1: if customer evidence selects a workflow, can we prove policy, approval, execution receipt, and recovery posture in a safe sandbox or staging environment?

It does **not** select the market wedge. A technically easy connector without a painful buyer problem is not a SaaS business.

## Evaluation criteria

| Criterion | What good looks like |
| --- | --- |
| Safe test environment | Development, sandbox, test mode, or fully anonymised staging path |
| Exact action result | Provider returns a durable identifier and definitive success/failure state |
| Before/after state | Product can show the state used for human decision and later reconciliation |
| Recovery posture | Action is reversible, compensatable, or explicitly irreversible |
| Least privilege | Connector can be limited to the smallest required scope |
| Pilot complexity | One integration can demonstrate the full story in a short pilot |
| Market validity | Buyer evidence says this action/control boundary is actually unsolved |

## Candidate paths

| Candidate | Technical feasibility | Product value condition | Current decision |
| --- | --- | --- | --- |
| Shopify order refund/cancellation in a development store | Strong technical candidate: documented refund/cancel APIs and example provider transaction outcomes using a test/bogus gateway | Only proceed if customer/business-operations interviews show an independent cross-system control/evidence gap beyond native Shopify/support-platform controls | Conditional sandbox candidate; do not build yet |
| Account credit or subscription exception in a selected billing platform | Potentially attractive because the before/after and compensation action can be explicit | Requires a buyer to name the billing system and explain why its native workflow is insufficient | Unknown until interviews identify the actual system |
| GitHub deployment protection rule | Technically possible through a GitHub App, webhook, and approve/reject callback | Weak initial SaaS thesis because GitHub already supports required reviewers and custom third-party deployment gates | Do not choose as first pilot without strong runtime-action evidence outside CI/CD |
| Payment/payout exception | Potentially high economic value but higher trust/compliance risk | Must have a bounded sandbox, clear buyer, and no need for live banking access | Research-only; not a first technical build target |

## Conditional Shopify pilot shape

This is a **technical rehearsal**, not a chosen product direction.

```text
Existing support/operations agent
  → proposes a specific refund or cancellation with order context
  → control layer evaluates policy and before/after state
  → named approver reviews exact payload when required
  → Shopify development store API executes only after revalidation
  → provider transaction ID/status becomes an execution receipt
  → case file records whether the action is irreversible or has a permitted correction path
```

### Why this is useful for a later pilot

- Shopify documents refund and order-cancel interfaces for development stores.
- Its refund examples include a transaction status and test marker, which can exercise the execution-receipt model without live commerce activity.
- A refund/cancellation has concrete amount, order, and before/after state—better for testing an action contract than a vague generic tool call.

### Why this may still be the wrong business

- Shopify and support platforms may already provide sufficient native approval, refund, and audit workflows.
- A company may reject an independent service in a customer/payment action path.
- Refunds can be irreversible in practice; a “recovery plan” must not claim the payment can always be reversed.

## Security conditions before any real connector implementation

1. The wedge and exact action pass the customer-evidence gate.
2. A design partner approves sandbox, staging, or fully anonymised test data.
3. Credentials are stored outside action payloads and use the least available privilege.
4. Webhook authenticity, provider idempotency, timeout/unknown state, reconciliation, and data retention are specified.
5. PostgreSQL migrations pass against a dedicated scratch database.
6. The founder explicitly approves the connector scope. No production system, spend, or customer data is used by default.

## Decision rule

The first connector is chosen by this order:

1. Repeated customer action and buyer pain.
2. Existing-tool gap confirmed by interviews.
3. Safe partner-approved test environment.
4. Clear provider result and recovery posture.
5. Lowest integration scope that proves the product promise.

Never choose a connector because it is easy to demo.

## Sources

- [Shopify refund API](https://shopify.dev/docs/api/admin-rest/latest/resources/refund) — accessed 15 September 2026.
- [Shopify cancel order API](https://shopify.dev/docs/api/admin-rest/2026-10/resources/order) — accessed 15 September 2026.
- [Shopify GraphQL refund query](https://shopify.dev/docs/api/admin-graphql/latest/queries/refund) — accessed 15 September 2026.
- [GitHub custom deployment protection rules](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/create-custom-protection-rules) — accessed 15 September 2026.
- [GitHub deployment environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments) — accessed 15 September 2026.
