<!-- STATUS: STALE / HISTORICAL. This document predates the verified Chunks 1-3 state and may contradict current runtime behavior (e.g., sandbox execution, FinancialExecution ledger, tenant model, REST/MCP auth). Canonical sources: AGENTOS_OPERATING_PROMPT.md and AGENTOS_STATE.md. Do not use as source of truth. -->
# Demo Data

Run the idempotent seed after applying migrations and configuring `DATABASE_URL`:

```bash
cd backend
python -m app.seed
```

It creates:

- Principal: `Demo Admin` (`demo-admin`)
- Agents: `FinanceAgent`, `SalesAgent`, `ResearchAgent`
- Tools: `Payments`, `CRM`, `Email`, `Data`
- Actions: `bank_transfer`, `refund_payment`, `read_customer`, `update_customer`, `send_email`, `read_sensitive_payroll`
- Resources: `bank_account_001`, `crm_database`, `payroll_dataset`, `customer_record_001`
- Delegations: `finance.transfer`, `crm.read`, `research.read`

The seed checks stable identities before insertion. Running it multiple times does not create duplicates. It contains no credentials, API keys, real payment information, or sensitive business payloads.
