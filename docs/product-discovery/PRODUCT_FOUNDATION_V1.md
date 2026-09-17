# Product Foundation V1

## Status

Working product hypothesis. This document defines the next product direction; it is not a brand decision or a claim that the product is market-validated.

## Product purpose

Enable companies to let AI agents take valuable customer and business actions without giving up human control, accountability, or the ability to recover from mistakes.

## First customer hypothesis

Operations leaders at B2B SaaS, e-commerce, marketplace, or fintech companies with roughly 50 to 500 employees. These teams are introducing AI support or operations agents but still require people to approve sensitive actions.

## First problem to validate

An AI agent can understand a customer issue, but a company may not trust it to issue a refund, apply account credit, change a subscription, cancel an order, or update a customer record. Existing support platforms focus on answering customers or automating a whole workflow. The company still needs a reliable way to decide whether this exact action is allowed, who must approve it, and what actually happened afterward.

## Product hypothesis

The product receives a proposed action from an AI agent before that action reaches a business system. It evaluates the action against a company policy and returns one of four outcomes:

- Allow automatically.
- Hold for a named human approver.
- Block with a clear reason.
- Require a safer alternative or narrower action.

If an approver authorizes an action, the product binds the approval to the exact payload, rechecks relevant state before execution, stores the actual execution result, and exposes a recovery or compensation path when the connected system supports one.

## Initial action scope

Start with one action family, not a generic agent platform:

| Action | Example policy | Recovery model |
| --- | --- | --- |
| Refund | Auto-allow under a low amount and low fraud risk; require approval above the threshold | Void, refund reversal, or documented irreversible outcome depending on payment provider state |
| Account credit | Auto-allow within a customer-specific limit; otherwise approval | Apply an offsetting debit or record a compensation action |
| Subscription change | Allow a supported downgrade; require approval for exceptional pricing or cancellation | Restore prior plan when provider supports it |
| Customer record update | Allow low-risk fields; hold sensitive identity or entitlement changes | Restore the before value from a captured version |

The first customer interview cycle will determine the single action to build first.

## Core user journey

1. A customer asks for help through an existing AI support agent.
2. The agent proposes a structured business action with the customer, reason, amount or field change, and target system.
3. The product shows the business impact in plain language and evaluates the company policy.
4. The action is allowed, blocked, or sent to the right approver.
5. Before execution, the product confirms that the approved payload, authority, policy, and relevant customer state have not changed.
6. The connected system executes the action and returns a real result.
7. The company can view an evidence record and, where available, start a recovery or compensation workflow.

## Minimum viable product

The first pilot needs only the following capabilities:

- One agent integration API or MCP gateway.
- One connector to a real business system.
- One action schema with clear before and after values.
- Company policies for amount, role, action type, and customer context.
- A concise approver screen or Slack-style approval flow.
- Exact-payload approval binding and revalidation before execution.
- An execution receipt showing the real provider response.
- One tested recovery or compensation path.

## Explicit non-goals for the first pilot

- A final company name, logo, or broad brand system.
- A proprietary model, model fine-tuning, general RAG, or a large knowledge corpus.
- A general-purpose AI agent builder.
- Every SaaS connector.
- A large security dashboard or a claim to replace an identity provider.
- Enterprise production claims before real external validation.

## Technology direction

Retain the existing deterministic governance foundation: identities, delegated authority, policies, risk handling, approvals, payload integrity, revalidation, execution state, and audit records.

Add or reshape product-facing layers around a focused action contract:

- `ProposedAction`: agent request, target system, business reason, before/after values, recovery class, and idempotency key.
- `PolicyDecision`: automatic allow, human approval, block, or safer alternative required.
- `ExecutionReceipt`: provider result, authoritative state, evidence chain, and recovery availability.
- `RecoveryPlan`: reversible, compensatable, or irreversible classification with a defined user experience for each.

The product must treat AI analysis as advisory. The deterministic policy and approval path remains the final action authority.

## What success looks like

The first pilot is successful only if a company uses the product to automate an action it previously kept manual or refused to allow an AI agent to perform.

Useful measurements:

- Number and value of actions proposed, automatically allowed, approved, blocked, and recovered.
- Manual approval time.
- Percentage of actions completed without human handling while staying within policy.
- Policy violations or prevented mistakes.
- Customer willingness to continue after the pilot and pay for the product.

## Validation plan

### Week 1

Interview ten people responsible for customer operations, support, finance operations, or AI adoption. Ask for real examples of actions their AI agent cannot safely perform today.

### Week 2

Choose one repeated action only if at least three interviewees describe a comparable problem with a real business consequence.

### Weeks 3 and 4

Build a narrow interactive prototype or working integration around that exact action. Ask for two design partners to test it using a real or safely anonymized workflow.

## Decision gates

Do not expand the product until the answer to each question is yes:

1. Does a reachable buyer have this problem repeatedly?
2. Is the action important enough that they will pay to automate it safely?
3. Can the action be integrated and evaluated using an explicit policy?
4. Can the product prove execution and explain what happens when the action fails?
5. Will at least one company run a time-boxed pilot?

## Naming

The repository's current name is an internal codename only. Naming, SEO research, domain selection, and visual identity happen after the product has a validated customer, workflow, and market position.
