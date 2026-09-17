# Product Execution Master Plan V1

## Decision

We are no longer working as a sequence of disconnected technical features. We are building toward one commercial proof:

> A reachable company uses this product to safely automate one AI-agent action it previously kept manual or refused to permit, and can explain why it will continue paying for it.

The current repository name is an internal codename. No final name, brand, public launch, or market wedge has been selected.

## What already exists

The technology base is valuable, but it is not yet the product. It already supports identity and delegated authority, deterministic policy, explainable risk, exact-payload approval binding, revalidation, execution receipts, recovery posture, causal audit order, portable evidence export, connector routing, and non-persistent action preflight.

These capabilities are the control layer beneath the future pilot. They do **not** prove customer demand, production readiness, or differentiation.

## The working product thesis

The thesis to test is not “AI governance for every company.” It is:

> When an existing AI agent proposes a consequential business action across an existing system, a company needs an independent way to decide whether the exact change is allowed, show accountable people its impact, bind approval to it, prove the actual result, and recover when possible.

The first candidate remains customer/business operations where an AI agent proposes a sensitive credit, refund exception, subscription exception, entitlement update, or similar cross-system change. This is a **hypothesis**, not a decision. Existing support platforms already automate many actions, so the first product cannot be a generic AI support agent.

## Product operating model

There are four programmes. Work inside a programme may contain many small tasks, but progress is reported only when the programme deliverable is complete.

| Programme | Outcome | Current state | Gate to continue |
| --- | --- | --- | --- |
| 1. Evidence | Prove one repeated, costly, reachable customer problem | Active | Same blocked action reported by at least 3 independent teams |
| 2. Definition | Specify one buyer, workflow, promise, pilot scope, and commercial test | Waiting on evidence | One buyer and one connector path are credible |
| 3. Pilot product | Deliver the complete end-to-end experience for that workflow | Foundation complete; vertical build paused | A design partner agrees to a bounded pilot |
| 4. Commercial proof | Demonstrate adoption, renewal intent, and a scalable path | Not started | A pilot shows measurable value and willingness to continue |

## Programme 1 — Evidence: choose the problem before the vertical build

### Objective

Identify one high-consequence agent action that customers genuinely hold back today and for which native tools are insufficient.

### Evidence standard

Do not select a wedge until all five conditions hold:

1. Three independent teams describe a comparable blocked action.
2. Two teams say it happens at least monthly.
3. A buyer can quantify money loss, delay, customer harm, compliance risk, or operational cost.
4. Existing tools or internal workflow have a named limitation that matters to the buyer.
5. At least one team will review or test a narrow pilot on sandbox, staging, or anonymised data.

### Research lanes

| Lane | Candidate buyer | Candidate action | Why investigate | Rejection condition |
| --- | --- | --- | --- | --- |
| Customer/business operations | Support Ops, CX Ops, RevOps, AI automation lead | Credit exception, subscription exception, refund exception, entitlement update | Frequent actions; clear customer impact; likely cross-system workflow | Native support/billing controls already solve authority, evidence, and recovery needs |
| Finance operations | Controller, treasury, AP/AR lead | Payment exception, vendor change, payout exception | Strong financial risk and willingness to pay | Pilot cannot be isolated from heavy banking, compliance, or procurement work |
| IT/cloud operations | Platform engineering, SRE, DevOps | Runtime infrastructure, access, or incident action | Strong fit to action control and developer-led pilots | Pull requests, CI/CD, and existing change controls already solve the exact need |

### Required deliverables

- A 15-interview evidence ledger with real workflows, not opinions.
- A current competitor/alternative map for the repeated action(s).
- A scored wedge decision record using the existing evidence scorecard.
- A one-page problem brief for the selected workflow.

### Founder-required action

No one can manufacture market truth from code. The founder must send the approved research invitation, participate in or listen to interviews, and record evidence. External outreach is intentionally not sent automatically.

## Programme 2 — Definition: make the product narrow and sellable

This begins only after Programme 1 selects a workflow.

### Required decisions

| Decision | Required answer |
| --- | --- |
| Ideal customer | Company type, size, existing systems, buyer, and daily user |
| First action | One precise write action; no action family or broad category |
| Product promise | A measurable statement of what becomes safer, faster, or easier |
| System boundary | Which existing agent sends the proposal, which system is changed, and what remains outside the product |
| Connector | Exactly one first provider/API and its sandbox/staging option |
| Policy model | The customer’s real thresholds, roles, exceptions, and required evidence |
| Recovery model | Reversible, compensatable, or irreversible; who owns the recovery decision |
| Pilot economics | Pilot duration, success measure, buyer commitment, and continuation price hypothesis |

### Definition deliverable

The result is a **Pilot Product Requirements Document**. It contains user journey, action contract, screens, API boundaries, integration design, non-goals, threat model, data handling, success metrics, and acceptance tests. It replaces generic feature requests for the pilot period.

## Programme 3 — Pilot product: build a complete workflow, not a platform collection

### Pilot workflow

```text
Existing AI agent
  → Proposed action with before/after state and recovery posture
  → Policy + risk + preflight
  → Allow / named approver / block
  → Exact-payload revalidation
  → One selected connector in sandbox or staging
  → Provider receipt + recovery status
  → Case file + portable evidence
```

### Scope

The pilot must contain only what is needed for one action:

- One agent ingress method (API or MCP).
- One structured action schema.
- One selected connector.
- One real policy set from a design partner.
- One human approval experience.
- One observable execution outcome.
- One tested recovery or compensation flow, or an explicit irreversible-action stop condition.
- One onboarding/demo path that a buyer can operate without engineering assistance.

### Explicit non-goals

- No generic agent builder, helpdesk, finance suite, or cloud-management platform.
- No second vertical, second connector, final brand, public launch, or broad compliance claim.
- No production customer data or live authority until the design partner and security conditions approve it.
- No feature added merely because it is technically interesting.

### Build gate

A new feature enters the pilot only if it supports the selected user journey, removes a pilot risk, or is demanded by validated partner evidence. Otherwise it goes into a parked backlog.

## Programme 4 — Commercial proof: decide whether to grow, change, or stop

### Pilot scorecard

| Metric | Evidence of success |
| --- | --- |
| Adoption | A real team submits or reviews real/safely anonymised workflow actions repeatedly |
| Time saved | Approval or handling time is lower than the old manual flow |
| Safety | Policy blocks, approval binding, revalidation, and provider receipts catch or explain meaningful cases |
| Reliability | Execution outcome and recovery posture are visible for every pilot action |
| Value | Buyer can explain why the workflow is worth retaining or paying for |
| Expansion | Buyer identifies adjacent actions or systems after the first workflow works |

### Decision after pilot

- **Grow:** repeatable usage, buyer value, feasible connector, and continuation intent.
- **Refine:** the action is valuable but the workflow, policy, or experience needs focused change.
- **Change wedge:** pain exists but the buyer, action, or integration path is wrong.
- **Stop:** no repeated urgent problem or no credible pilot commitment after disciplined discovery.

Stopping a weak wedge is a good decision; building a broad product without evidence is not.

## Twelve-week execution sequence

| Weeks | Major milestone | Deliverable | Decision gate |
| --- | --- | --- | --- |
| 1–2 | Evidence preparation and first discovery cycle | Candidate ledger, interview records, competitor/alternative notes | Continue only with real workflow evidence |
| 3–4 | Wedge selection | Completed scorecard and signed problem brief | Select one workflow or repeat discovery in another lane |
| 5 | Pilot definition | Pilot PRD, one connector decision, partner success metrics | Partner agrees scope is useful and safe enough to test |
| 6–8 | Vertical pilot build | End-to-end workflow in sandbox/staging with acceptance tests | Demo works against the selected action contract |
| 9–10 | Partner validation | Pilot feedback, workflow observations, bugs, value metrics | Buyer requests continued use or clearly identifies required change |
| 11–12 | Commercial decision | Pricing hypothesis, launch-readiness decision, next-quarter plan | Grow, refine, change wedge, or stop |

The dates are planning targets, not a claim that a customer will be available on schedule.

## Immediate execution order

1. Complete a founder-ready candidate and interview evidence system; no messages are sent automatically.
2. Conduct the first five interviews across the three lanes.
3. Review whether one action repeats before doing more vertical code.
4. Complete all fifteen interviews if the first five do not provide a clear repeated action.
5. Select the wedge using evidence, then create the Pilot PRD and build only that product.

## Work already completed and protected

The following foundation work is complete and should be reused rather than rebuilt: action context, payload-bound approval, execution receipt, evidence export, causal audit order, connector contract, and action preflight. It is intentionally generic until a selected workflow tells us how to shape it.

## Reporting rule

From now on, updates are by major deliverable:

1. Evidence system ready.
2. First-five interview synthesis.
3. Wedge selection decision.
4. Pilot PRD complete.
5. End-to-end pilot workflow complete.
6. Pilot outcome and commercial decision.

Internal coding, research, testing, and documentation tasks will continue without interrupting the founder for small approvals. I will stop only for a true external commitment, a final wedge choice where evidence is ambiguous, live customer/system access, spend, legal/privacy scope, or production deployment.
