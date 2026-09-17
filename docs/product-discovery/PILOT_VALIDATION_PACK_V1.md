# Pilot Validation Pack V1

## Status

Active validation plan. This is the next business milestone after the reusable product foundation. It does not select the final market, product name, or launch plan.

## Critical market correction

Do **not** build a generic “AI support agent that can issue refunds.” Intercom, Zendesk, and other support platforms already promote agents that can issue refunds, credits, cancellations, subscription changes, and account updates through connected systems. The buyer problem we must test is narrower:

> When an AI agent wants to make a sensitive customer or business change across existing systems, can the company apply an independent policy, show a human the exact before/after impact, bind approval to that payload, prove the provider outcome, and handle recovery without rebuilding every workflow in the support platform?

This is a testable hypothesis—not a market claim.

## First pilot hypothesis

**Buyer:** Head of Customer Operations, Support Operations, Revenue Operations, or AI/Automation at an organisation with an existing support agent and at least two connected systems (for example support + billing, or support + orders).

**Trigger:** Their agent can read customer context but is limited, manually reviewed, or distrusted for customer-affecting write actions.

**First action candidate:** A policy-bound account credit, subscription exception, refund exception, or customer entitlement update that crosses systems and needs evidence plus a correction path.

**Product to test:** The existing action-control prototype with business context, exact-payload approval, provider receipt, recovery posture, causal audit timeline, and JSON evidence export.

## What we are explicitly not testing

- Whether a chatbot can answer support questions.
- Whether a company needs a new helpdesk or a general agent builder.
- Whether companies want generic AI “governance dashboards.”
- Whether the product should replace Intercom, Zendesk, ServiceNow, Stripe, Chargebee, or an identity provider.

## Interview target queue — 15 evidence slots

No external messages have been sent. Fill the organisation and contact only after founder review of the outreach list.

| Slot | Buyer role | Organisation profile | Screening signal | Interview objective |
| --- | --- | --- | --- | --- |
| 1–3 | Head/Director of Support Operations | B2B SaaS, 50–500 people, uses a support platform and billing system | AI answers tickets but people still approve refunds, credits, or exceptions | Identify the most repeated blocked write action |
| 4–5 | Customer Experience / Operations Lead | E-commerce, marketplace, travel, or subscription business | High volume of refunds, cancellations, delivery claims, or credits | Measure error cost, policy complexity, and recovery needs |
| 6–8 | Revenue Operations / Billing Operations Lead | Subscription or usage-based SaaS | Manual exceptions, credits, plan changes, or invoice disputes | Test whether billing write actions have enough urgency and willingness to pay |
| 9–10 | Product Operations / Trust & Safety Lead | Marketplace, fintech-adjacent, or identity-sensitive service | Sensitive account, entitlement, or customer-record changes | Test before/after proof and audit requirements |
| 11–13 | AI Automation / Platform Engineering Lead | Company with internally built agents or custom tools | Agent tools touch multiple systems and need approval/review | Test integration fit and independent-control need |
| 14–15 | Founder / COO | Early growth B2B SaaS with lean operations | Decisions bottleneck on a small number of people | Test pilot speed, budget owner, and design-partner commitment |

## Screening questions before booking

Only interview people who answer yes to at least two:

1. Does an AI agent or automation already read customer, order, subscription, or account data?
2. Is there a customer-affecting write action that still needs a person to approve or perform manually?
3. Does the action touch more than one system or require a policy threshold?
4. Would a mistaken action create money loss, customer harm, compliance risk, or a difficult correction?
5. Could the team run a small pilot on anonymised or sandbox data within 30 days?

## Interview evidence we need

For every interview, record a real past incident or repeated workflow—not an opinion:

- The exact action, systems involved, and who owns it.
- How often it happens each month.
- Why the current agent or automation cannot execute it safely.
- The current approval path and time cost.
- The cost of a mistaken action and whether it can be reversed or compensated.
- The current tools used and what they fail to prove.
- Whether the buyer would trial a narrow integration, who signs off, and what result would make them continue.

## Decision rule after 15 interviews

Choose a first wedge only if one action family has all of the following:

1. At least **three** independent teams describe the same action problem.
2. At least **two** say the problem occurs monthly or more often.
3. At least **two** agree to review a working pilot or become a design partner.
4. A single real connector can demonstrate policy, approval, execution receipt, and recovery for the action.
5. The product is independent of the support platform rather than a duplicate of its built-in automation.

If no action meets this threshold, we do **not** force a product direction. We revisit finance operations and IT/cloud operations with the same evidence standard.

## Founder-ready research invitation

> I’m researching a narrow problem: when an AI agent wants to make a sensitive customer or business change, how does your team decide what is allowed, who approves it, and how do you prove or correct the outcome? I’m not selling anything. Could I ask about one real workflow in a 25-minute research conversation?

## Sources used to sharpen the hypothesis

- Intercom documents AI actions including refunds, cancellations, credits, and account changes: <https://www.intercom.com/learning-center/ai-agents-that-take-action>
- Zendesk documents AI agents resolving customer requests and taking actions across connected systems: <https://www.zendesk.com/service/ai/ai-agents/>
- Zendesk’s current agentic-AI guidance describes policy-bounded refunds, payment-plan updates, and human escalation: <https://www.zendesk.com/blog/ai/agentic-ai/agentic-ai-with-customer-service-platforms/>
- Chargebee documents the operational surface of subscriptions, credits, payments, and cancellations: <https://www.chargebee.com/billing/manage-subscriptions/>
- ServiceNow’s AI Control Tower documentation shows that agent approvals and governance are also an active enterprise category: <https://www.servicenow.com/docs/r/intelligent-experiences/ai-control-tower/explore-approvals.html>

## Immediate internal work

1. Prepare a founder-reviewed list of real interview candidates, grouped by the 15 slots above.
2. Make the product demo support one selected action contract only after the first repeated evidence appears.
3. Perform PostgreSQL migration validation on a dedicated scratch database before any hosted pilot.
