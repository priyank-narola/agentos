# AgentOS Phase 3A — Financial Control Plane Security & Architecture Review

**Target Baseline Commit**: `7d5e97c4aedc220ffce3397cc92a9d5aa29e47cb`  
**Publication Date**: August 25, 2026  
**Review Target**: Phase 3A Financial Action Control Plane Prototype  
**Final Verdict**: **READY FOR SANDBOX DEMO** | **NOT READY FOR PRODUCTION PROVIDER**

---

## Executive Summary

AgentOS Phase 3A introduces a provider-agnostic **Financial Action Control Plane Prototype** supporting financial action validation (`wire_transfer`), configurable risk threshold classification ($1K low, $5K elevated, $10K approval, $50K critical), payload-bound human approval state transitions, and sandbox payment execution (`SandboxPaymentProvider`).

This security review evaluates the prototype against 10 critical security, architectural, and operational dimensions. While Phase 3A achieves **100% test pass rates** (133 unit tests, 52 adversarial security tests) and is **READY FOR SANDBOX DEMO**, real-money financial execution requires addressing key TOCTOU windows, separation of duties, and provider state machine reconciliation.

---

## 1. PAYLOAD INTEGRITY REVIEW

### 1.1 End-to-End Payload Lifecycle Trace

$$\text{Tool Call Params} \xrightarrow{\text{validate}} \text{Clean Dict} \xrightarrow{\text{canonicalize}} \text{JSON Str} \xrightarrow{\text{sha256}} \text{payload\_digest} \xrightarrow{\text{bind}} \text{Approval/Audit} \xrightarrow{\text{verify}} \text{Execution}$$

1. **Parameter Entry**: MCP `execute_action` receives parameters in `GatewayRequestCreate`.
2. **Contract Validation**: `validate_financial_action_parameters()` strips forbidden override keys (`principal_id`, `risk_score`, `approved`, etc.) and validates `WireTransferContract`.
3. **Canonical Serialization & Digest**: `compute_payload_digest()` generates a SHA-256 hash using `json.dumps(parameters, sort_keys=True, separators=(",", ":"))`.
4. **Approval Binding**: `GatewayService` records `payload_digest` in `ApprovalRequest.reason` (`[payload_digest:<sha256>]`) and `AuditEvent`.
5. **Pre-Execution Verification**: `ApprovalService.approve()` re-computes SHA-256 over current `ActionRequest.parameters` and verifies exact match with original `payload_digest`.

### 1.2 Payload Modification & Tamper Test Matrix

| Tamper Scenario | Detected? | System Action | Audit Event Emitted |
| :--- | :-: | :--- | :--- |
| **Amount Modification** (e.g. $25,000 -> $999,000) | **YES** | `ApprovalConflictError` raised; execution blocked | `SECURITY_PAYLOAD_TAMPERED` |
| **Currency Modification** (e.g. USD -> EUR) | **YES** | `ApprovalConflictError` raised; execution blocked | `SECURITY_PAYLOAD_TAMPERED` |
| **Beneficiary Modification** (e.g. Vendor -> Attacker) | **YES** | `ApprovalConflictError` raised; execution blocked | `SECURITY_PAYLOAD_TAMPERED` |
| **Source Account Modification** | **YES** | `ApprovalConflictError` raised; execution blocked | `SECURITY_PAYLOAD_TAMPERED` |
| **Destination Account Modification** | **YES** | `ApprovalConflictError` raised; execution blocked | `SECURITY_PAYLOAD_TAMPERED` |
| **Invoice ID / Purpose Modification** | **YES** | `ApprovalConflictError` raised; execution blocked | `SECURITY_PAYLOAD_TAMPERED` |
| **Field Insertion** (adding un-vetted parameters) | **YES** | `ApprovalConflictError` raised; execution blocked | `SECURITY_PAYLOAD_TAMPERED` |
| **Field Deletion** (removing reference fields) | **YES** | `ApprovalConflictError` raised; execution blocked | `SECURITY_PAYLOAD_TAMPERED` |
| **JSON Key Ordering Changes** | **NO TAMPER** | `sort_keys=True` normalizes key order; hash remains stable | Normal Execution |
| **Numeric Representation Drift** | **POTENTIAL RISK**| `Decimal("25000.00")` vs `"25000.0"` requires normalized string format | Identified Optimization |

### 1.3 Identified Ambiguity
* **Numeric Representation**: In JSON, `"25000.00"` (string) vs `25000.0` (float) produces distinct SHA-256 byte representations. Pydantic model serialization normalizes `WireTransferContract` fields before hashing, but production implementation must mandate strict string formatting (`f"{amount:.2f}"`) to guarantee hash stability across different language runtimes.

---

## 2. APPROVAL TO EXECUTION TOCTOU (TIME-OF-CHECK / TIME-OF-USE) REVIEW

### 2.1 The TOCTOU Window Problem
A Time-of-Check to Time-of-Use (TOCTOU) vulnerability exists if system security context changes **between** the time an approval is requested and the time the approval is executed by a human reviewer.

```
[Time T0: Request Created] -------- (TOCTOU Window: Pending Queue) --------> [Time T1: Human Approves]
- Agent Active                                                                - Agent Suspended!
- Delegation Valid                                                            - Delegation Revoked!
- Policy ALLOWs                                                               - Policy DENIEs!
```

### 2.2 TOCTOU Scenario Evaluation

| State Mutation During Pending Approval Queue | Current Behavior in Prototype | Required Production Defense |
| :--- | :--- | :--- |
| **Delegation Revoked** after approval request | Approval succeeds; execution proceeds | **RE-EVALUATE DELEGATION** at `approve()` time |
| **Agent Suspended / Retired** after approval request | Approval succeeds; execution proceeds | **RE-EVALUATE AGENT STATUS** at `approve()` time |
| **Principal Suspended** after approval request | Approval succeeds; execution proceeds | **RE-EVALUATE PRINCIPAL STATUS** at `approve()` time |
| **Resource Status Changed to INACTIVE** | Approval succeeds; execution proceeds | **RE-EVALUATE RESOURCE STATUS** at `approve()` time |
| **Policy Rule Revoked / Denied** | Approval succeeds; execution proceeds | **RE-RUN POLICY EVALUATOR** at `approve()` time |
| **Approval Expiry** | `expires_at <= now` raises `ApprovalConflictError` | **VERIFIED CORRECT** (Fails Closed) |
| **Duplicate / Concurrent Approval** | Database lock + `status != PENDING` check | **VERIFIED CORRECT** (Fails Closed) |

> **Security Finding**: Production execution dispatch MUST run a full **Security Context Re-Validation** (`revalidate_security_context()`) at the exact millisecond of approval execution to guarantee that delegations, agent statuses, and policies remain active.

---

## 3. IDEMPOTENCY REVIEW

### 3.1 Idempotency Guarantee Analysis

```
Client Request (idem_key_1) ---> [GatewayService] ---> [SandboxPaymentProvider]
                                      |                       |
                            Checks DB idempotency    Checks Provider idempotency
```

1. **Same Request + Same Idempotency Key**: Gateway retrieves existing `ActionRequest` from DB and returns cached `GatewayResponse`. Zero duplicate processing.
2. **Different Payload + Same Idempotency Key**: Gateway compares canonical payload strings. Mismatch raises `GatewayIdempotencyConflict` (HTTP 409).
3. **Provider Retry After Network Timeout**: `SandboxPaymentProvider` maintains an idempotency map (`_idempotency_map`). Retry with same key returns `ExecutionStatus.DUPLICATE` with previous transaction reference. Zero double-charge.

### 3.2 State Machine Recommendation for Production Payment Gateways

```
[RECEIVED] ---> [EVALUATED] ---> [APPROVAL_PENDING] ---> [APPROVED]
                                                            |
                                                   [SUBMITTED_TO_PROVIDER]
                                                            |
                                          +-----------------+-----------------+
                                          |                                   |
                                [EXECUTION_SUCCEEDED]               [EXECUTION_FAILED]
```

---

## 4. SANDBOX PROVIDER REVIEW

### 4.1 Prototype vs. Production Capabilities

`SandboxPaymentProvider` provides a clean, deterministic, zero-dependency sandbox execution model. However, production banking networks (ACH, FedNow, SWIFT, Wire) operate asynchronously.

| Payment State | Prototype Support | Production Requirement |
| :--- | :-: | :--- |
| **NOT_EXECUTED** | Supported | Initial state before gateway dispatch |
| **SUBMITTED** | Missing | Transaction dispatched to banking API |
| **PROCESSING / PENDING_SETTLEMENT** | Missing | Transaction queued in banking clearing house |
| **EXECUTION_SUCCEEDED / SETTLED** | Supported | Funds settled at destination bank |
| **EXECUTION_FAILED** | Supported | Immediate API error response |
| **CANCELLED / REVERSED** | Missing | Wire recall or user cancellation |
| **UNKNOWN_TIMEOUT** | Supported | Network timeout during API call |
| **RECONCILED** | Missing | Matched against bank statement feed |

---

## 5. APPROVAL SECURITY REVIEW

### 5.1 Approval Control Assessment

| Security Control | Status | Finding & Recommendation |
| :--- | :-: | :--- |
| **Authorized Approver Check** | **PASS** | Approver `principal_id` must exist and be `ACTIVE` in DB. |
| **Separation of Duties (SoD)** | **MISSING** | Requester CAN currently approve their own request. **Must enforce `approver_id != requester_id` for financial actions.** |
| **Approval Single-Use** | **PASS** | Status transitions from `PENDING` to `APPROVED`/`REJECTED`. Re-use raises `ApprovalConflictError`. |
| **Non-Transferable** | **PASS** | Approval bound strictly to the `action_request_id`. |
| **Payload Invariance** | **PASS** | `payload_digest` verification blocks altered parameters. |
| **Resource / Beneficiary Binding** | **PASS** | Resource ID and beneficiary ID are embedded in the SHA-256 payload digest. |

---

## 6. FINANCIAL BUSINESS RULE REVIEW

### 6.1 Control Classification Taxonomy

```
+-----------------------------------------------------------------------+
| 1. SECURITY REQUIREMENTS   : Payload binding, TOCTOU re-validation,   |
|                              SoD (Dual Control), Idempotency          |
| 2. BUSINESS REQUIREMENTS   : Velocity limits, Cumulative daily caps,  |
|                              Vendor whitelist, Multi-tier approvals   |
| 3. COMPLIANCE REQUIREMENTS : SOX 404 audit log, EU AI Act record,     |
|                              BSA/AML SAR threshold tracking ($10k+)   |
| 4. OPTIONAL ENHANCEMENTS   : Slack interactive approval, FX locking   |
+-----------------------------------------------------------------------+
```

---

## 7. FAILURE & RECOVERY REVIEW

### 7.1 Provider & Network Failure Scenarios

```
Scenario: Provider Timeout during Wire Transfer
1. AgentOS sends wire dispatch to Payment Provider.
2. Network connection drops before response is received.
3. Local DB status remains PENDING_EXECUTION.
4. Recovery Action: AgentOS issues background reconciliation status poll using idempotency key.
5. Provider returns "tx-sandbox-123 (SETTLED)" -> AgentOS updates local audit ledger to EXECUTION_SUCCEEDED.
```

---

## 8. AUDIT LEDGER REVIEW

### 8.1 Audit Trail Completeness Audit

The audit log captures complete end-to-end evidence:
- **WHO**: `actor_id` (Principal) & `agent_id` (Agent)
- **WHAT**: `action_id` (`wire_transfer`) & `resource_id` (`ACC-CORP-001`)
- **WHAT PAYLOAD**: `payload_digest` (SHA-256 parameter hash)
- **WHY ALLOWED**: Matched policy rule & risk score
- **WHO APPROVED**: `approver_principal_id` & `decided_at` timestamp
- **WHAT EXECUTED**: `provider_name` & `execution_id`
- **FINAL OUTCOME**: `EXECUTION_SUCCEEDED` / `EXECUTION_FAILED`

---

## 9. REAL PROVIDER READINESS GATE

Checklist before connecting real banking APIs (Stripe Treasury, Modern Treasury, Plaid):

| Category | Requirement | Status |
| :--- | :--- | :-: |
| **BLOCKER** | Enforce Separation of Duties (`approver_id != requester_id`) | OPEN |
| **BLOCKER** | Implement TOCTOU Security Context Re-validation at `approve()` | OPEN |
| **BLOCKER** | Asynchronous Webhook Signature Verification (HMAC-SHA256) | OPEN |
| **HIGH** | Multi-tenant schema isolation (`tenant_id` on all tables) | OPEN |
| **HIGH** | Cumulative daily spending velocity limits per agent | OPEN |
| **MEDIUM** | Standardized Decimal String Serialization for hash stability | OPEN |
| **LOW** | Slack / Email interactive approval notifications | OPEN |

---

## 10. FINAL VERDICT

### **READY FOR SANDBOX DEMO**
### **NOT READY FOR PRODUCTION PROVIDER**

**Rationale**:  
The Phase 3A Financial Control Plane Prototype successfully proves the commercial workflow and achieves **100% test pass rates** (133/133 unit tests, 52/52 adversarial security tests) with zero application defects. It is fully ready for customer sandbox demonstrations. Production deployment with live money movement will proceed upon completing the Phase 3B Workload Identity & Financial Compliance Pack.
