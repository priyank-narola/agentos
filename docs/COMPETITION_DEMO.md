<!-- STATUS: STALE / HISTORICAL. This document predates the verified Chunks 1-3 state and may contradict current runtime behavior (e.g., sandbox execution, FinancialExecution ledger, tenant model, REST/MCP auth). Canonical sources: AGENTOS_OPERATING_PROMPT.md and AGENTOS_STATE.md. Do not use as source of truth. -->
# AgentOS Competition Demo

## Product One-Liner

AgentOS is an AI Action Governance and Control Plane that evaluates agent actions against identity, delegated authority, risk, and policy before they reach the real world.

## Problem

Authentication proves which agent is connected. It does not prove that a specific action is authorized. AgentOS makes the action decision explicit, explainable, reviewable, and auditable.

## Solution

```text
Agent
  -> Action Request
  -> Risk Engine
  -> Policy Engine
  -> Human Approval when required
  -> Authorization
  -> External execution boundary
```

External execution is intentionally disabled for this competition MVP.

## Demo Data

Apply migrations, configure `DATABASE_URL`, then run:

```bash
cd backend
python -m app.seed
```

The seed is idempotent and creates the existing demo agents, tools, actions, resources, valid delegations, and three named policies:

- `Demo Safe CRM Read`
- `Demo Blocked Payroll`
- `Demo Approval Transfer`

## Three Scenarios

### Safe Action

- Agent: `SalesAgent`
- Action: `CRM / read_customer`
- Resource: `crm_record / customer_record_001`
- Result: `ALLOW` → `AUTHORIZED` → `NOT_EXECUTED`

### Blocked Action

- Agent: `ResearchAgent`
- Action: `Data / read_sensitive_payroll`
- Resource: `dataset / payroll_dataset`
- Result: high-risk evidence → explicit deny → `BLOCKED` → `NOT_EXECUTED`

### Human Approval

- Agent: `FinanceAgent`
- Action: `Payments / bank_transfer`
- Resource: `bank_account / bank_account_001`
- Parameters: `{ "amount": 18000, "currency": "USD" }`
- Result: high/critical risk → `REQUIRE_APPROVAL` → `PENDING_APPROVAL`
- Open `/approvals`, inspect the policy and risk evidence, then approve.
- Final result: `AUTHORIZED FOR EXECUTION` → `NOT EXECUTED`

Use the same approval flow with `REJECT` to demonstrate:

```text
PENDING_APPROVAL → REJECTED → BLOCKED → NOT EXECUTED
```

## Exact Three-Minute Click Path

1. Open `/` and point out the governance pipeline and `EXTERNAL EXECUTION DISABLED`.
2. Open `/gateway`, select `SalesAgent`, `read_customer`, `customer_record_001`, submit with context/payload configured for the safe policy, and show `AUTHORIZED`.
3. Return to `/gateway`, select `ResearchAgent`, `read_sensitive_payroll`, `payroll_dataset`, submit with the blocked context, and show risk plus `BLOCKED`.
4. Submit the FinanceAgent `$18,000` transfer, show `PENDING_APPROVAL`.
5. Open `/approvals`, open the pending request, show risk factors and policy reason, then approve.
6. Point to `AUTHORIZED FOR EXECUTION` and `NOT EXECUTED`.

## Architecture

- Next.js and TypeScript control center
- FastAPI service boundary
- PostgreSQL domain persistence
- Deterministic Risk Engine
- Deterministic Policy Evaluator
- Human Approval Workflow
- Append-oriented audit evidence

## Security Boundary

The frontend never decides authorization. The gateway resolves the tool from the action, evaluates risk and policy server-side, persists separate requests and decisions, and rejects caller-supplied decisions, risk, policy, or tool overrides.

## Intentionally Disabled

- External tool execution
- Banking APIs
- Email sending
- CRM writes
- MCP/A2A integrations
- Production authentication
- Multi-approver workflows

## Known Limitations

The demo approver is an authorization-domain principal rather than an authenticated production user. Dashboard metrics aggregate existing list APIs client-side for the competition MVP. The audit timeline uses available request, decision, risk, and approval evidence.
