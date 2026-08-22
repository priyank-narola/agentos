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
