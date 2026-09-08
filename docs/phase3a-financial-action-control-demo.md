# AgentOS Phase 3A — Financial Action Control Plane Demonstration

**Baseline Commit**: `7d5e97c4aedc220ffce3397cc92a9d5aa29e47cb`  
**Publication Date**: August 25, 2026  
**Status**: Verified Prototype (133 Unit Tests + 52 Adversarial Security Tests Passing)

---

## Overview

This demonstration illustrates how AgentOS acts as an out-of-band **Financial Action Control Plane** for AI agents performing real-world corporate financial transactions.

In this scenario:
An AI agent (`TreasuryBot-v1`) attempts to execute a **$25,000 wire transfer** to settle an enterprise vendor invoice.

AgentOS intercepts the request and enforces the complete governance lifecycle:

$$\text{Bearer JWT} \rightarrow \text{Identity & Delegation} \rightarrow \text{Contract Validation} \rightarrow \text{Policy & Financial Risk} \rightarrow \text{Human Approval (Payload-Bound)} \rightarrow \text{Sandbox Payment Execution} \rightarrow \text{Audit Ledger}$$

---

## Step-by-Step Scenario Execution

### 1. Agent Tool Call Request
`TreasuryBot-v1` initiates a tool call via the Model Context Protocol (MCP) `execute_action` tool interface with HTTP Authorization:

```http
POST /mcp/sse HTTP/1.1
Host: agentos-api.internal
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImFnZW50b3Mta2V5LTEiLCJ0eXAiOiJKV1QifQ...
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": "mcp-req-001",
  "method": "tools/call",
  "params": {
    "name": "execute_action",
    "arguments": {
      "action_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3d0001",
      "resource_id": "7a0deb4d-1a2b-3c4d-5e6f-7a8b9c0d1e2f",
      "idempotency_key": "tx-idem-vendor-invoice-88912",
      "parameters": {
        "amount": "25000.00",
        "currency": "USD",
        "beneficiary_id": "BENEFICIARY-ACME-CORP",
        "source_account_id": "ACC-CORP-TREASURY-001",
        "destination_account_id": "ACC-VENDOR-ACME-999",
        "transaction_reference": "INV-2026-08-88912",
        "purpose": "ACME Corp Invoice Q3 Settlement"
      }
    }
  }
}
```

---

### 2. Transport Authentication & Identity Resolution
* `MCPTransportContextMiddleware` extracts Bearer JWT exclusively from HTTP headers.
* `TokenValidator` cryptographically verifies signature, expiration (`exp`), issuer (`iss`), and audience (`aud`).
* `AgentIdentityResolver` translates token claims into trusted domain entities:
  - `Principal`: Alice Treasury Manager (`id: c3968fd5-2948-4dcd-9e41-828b24aa5db1`)
  - `Agent`: TreasuryBot-v1 (`id: 747b3e01-3933-4ebf-a62a-229e9d389770`)
  - `Delegation`: Active delegation scope `*` binding Alice to TreasuryBot-v1.

---

### 3. Financial Action Contract Validation
`validate_financial_action_parameters()` validates parameters against `WireTransferContract`:
- `amount`: `25000.00` (> 0) — **VALID**
- `currency`: `USD` (supported ISO code) — **VALID**
- `beneficiary_id`, `source_account_id`, `destination_account_id`, `transaction_reference`: Non-empty strings — **VALID**
- Rejection of client-injected override keys (`principal_id`, `risk_score`, `approved`, `decision`): None detected — **VALID**
- Generates canonical SHA-256 **`payload_digest`**:  
  `payload_digest = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"`

---

### 4. Financial Risk & Policy Engine Evaluation
* `RiskEngine.evaluate()` evaluates transaction magnitude against `FinancialRiskConfig`:
  - Registered Action Risk: `HIGH` (+30 pts)
  - Registered Agent Risk: `LOW` (+0 pts)
  - Resource Sensitivity: `HIGH` (+25 pts)
  - Transaction Amount: `$25,000.00` >= `$10,000.00` Approval Threshold (`FINANCIAL_HIGH_TRANSACTION`, +25 pts)
  - **Total Financial Risk Score**: `80 / 100` (`HIGH` Risk Classification)
* `DeterministicPolicyEvaluator.evaluate()` checks active policies:
  - Match: Treasury Payout Policy (Rule 10: `ALLOW wire_transfer`)
  - Policy Condition: High-risk action requires human approval.
  - **Gateway Decision**: `REQUIRE_APPROVAL` (`gateway_status = PENDING_APPROVAL`)

```json
{
  "action_request_id": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
  "gateway_status": "PENDING_APPROVAL",
  "decision": "REQUIRE_APPROVAL",
  "reason_code": "APPROVAL_REQUIRED",
  "reason": "Action wire_transfer requires human approval due to high risk classification (Score: 80)",
  "risk_level": "HIGH",
  "risk_score": 80,
  "risk_classification": "HIGH",
  "approval_required": true,
  "execution_status": "NOT_EXECUTED"
}
```

---

### 5. Human-in-the-Loop Approval & Payload Binding
An `ApprovalRequest` is generated and assigned to Alice Treasury Manager.

> [!IMPORTANT]
> **Payload-Bound Security Invariant**:  
> The `ApprovalRequest` is cryptographically bound to `payload_digest`. If an attacker attempts to alter the beneficiary (`ACC-EVIL-666`) or amount (`$999,000.00`) after approval creation, `ApprovalService.approve()` detects digest mismatch, sets approval status to `REJECTED`, halts execution, and logs `SECURITY_PAYLOAD_TAMPERED`.

Alice reviews the transaction details and approves:

```python
approval_service.approve(
    approval_id=UUID("e2b0c442-98fc-1c14-9afb-f4c8996fb924"),
    payload=ApprovalActionRequest(approver_principal_id=Alice.id)
)
```

---

### 6. Sandbox Payment Provider Execution
Upon valid approval confirmation and payload digest verification:
1. `ApprovalService` transitions status to `APPROVED`.
2. Emits `EXECUTION_STARTED` audit event.
3. Dispatches execution payload to `SandboxPaymentProvider`:
   - Generates stable, deterministic transaction ID: `tx-sandbox-E3B0C44298FC`
   - Simulates zero-latency, zero-risk ledger settlement (no real money moved).
   - Execution status set to `EXECUTION_SUCCEEDED`.
4. Emits `EXECUTION_SUCCEEDED` audit event.

---

### 7. Audit Trail Reconstruction
The complete transaction produces an un-alterable sequence of `AuditEvent` records:

| Event Index | Event Type | Actor / Agent | Key Metadata |
| :-: | :--- | :--- | :--- |
| **1** | `ACTION_REQUEST_RECEIVED` | Alice / TreasuryBot-v1 | `action_id: wire_transfer`, `payload_digest: e3b0c4...` |
| **2** | `RISK_EVALUATED` | Alice / TreasuryBot-v1 | `score: 80`, `classification: HIGH`, `factors: [FINANCIAL_HIGH_TRANSACTION]` |
| **3** | `POLICY_EVALUATED` | Alice / TreasuryBot-v1 | `decision: REQUIRE_APPROVAL`, `reason_code: APPROVAL_REQUIRED` |
| **4** | `APPROVAL_REQUESTED` | Alice / TreasuryBot-v1 | `approval_id: e2b0c4...`, `expires_at: +15m` |
| **5** | `APPROVAL_APPROVED` | Alice / TreasuryBot-v1 | `approver_id: Alice.id`, `status: APPROVED` |
| **6** | `EXECUTION_STARTED` | Alice / TreasuryBot-v1 | `provider: SandboxPaymentProvider` |
| **7** | `EXECUTION_SUCCEEDED` | Alice / TreasuryBot-v1 | `execution_id: exec-sb-e3b0c4...`, `tx_ref: INV-2026-08-88912` |

---

## Verification Summary

* **Unit Tests**: 133 / 133 Passed (`pytest backend/tests/`)
* **Adversarial Security**: 52 / 52 Passed (`run_phase2d_adversarial.py`)
* **Execution Safety**: 100% Mock/Sandbox execution — zero real money movement or external banking API dependencies.
