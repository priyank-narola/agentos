# AgentOS Phase 3F — Enterprise Control Plane Demonstration Guide

**Target Audience**: CISO, Head of AI Engineering, CTO, CFO & Treasury Leadership  
**Core Narrative**: *"AI agents can request powerful actions, but AgentOS independently controls whether those actions are allowed to happen."*  
**System Version**: AgentOS Control Plane & Observability Suite v1.0  
**Execution Environment**: Safe Provider-Agnostic Sandbox (`SandboxPaymentProvider`)  
**Real-Money Execution**: Absolutely Zero Real Money Movement  

---

## Executive Overview

As enterprises deploy autonomous AI agents to interact with core financial systems, ERPs, and banking APIs, leadership faces a critical governance challenge:
> *"How do we unlock the productivity of AI agents without exposing our organization to unmonitored financial transfers, prompt injection attacks, self-approval vulnerabilities, or cross-tenant data leakage?"*

AgentOS provides an enterprise-grade control plane that decouples AI agent execution from financial authorization. Agents interact exclusively over the Model Context Protocol (MCP), while AgentOS independently evaluates identity, delegation, risk, policy, separation of duties, cryptographic payload integrity, and execution state.

---

## Stakeholder Demonstration Scenarios

### 1. Executive Presentation for the CISO & Security Leadership
**Key Focus**: Zero-Trust Authentication, Multi-Tenant Isolation, and TOCTOU Defense.

- **Demonstration Flow (Scenario F & E)**:
  - Show an agent in **Tenant A** attempting to execute a wire transfer against a resource in **Tenant B**. AgentOS immediately fails closed with `Tenant mismatch: cross-tenant reference detected`.
  - Show a high-value request entering `PENDING_APPROVAL`. While pending, administrator revokes the agent's delegation. Approver attempts to approve. AgentOS performs pre-execution TOCTOU re-validation, detects the revoked delegation, and cancels the execution (`TOCTOU_REVALIDATION_FAILED`).

---

### 2. Executive Presentation for the Head of AI Engineering & CTO
**Key Focus**: Provider-Agnostic MCP Integration, Idempotency, and Failure Safety.

- **Demonstration Flow (Scenario A, G, & H)**:
  - **Scenario A**: AI agent requests a $500 vendor payout. Evaluates low risk, matches `ALLOW` policy rule, executes automatically via `SandboxPaymentProvider` in <50ms.
  - **Scenario G**: Simulated payment provider timeout. State machine cleanly transitions to `TIMEOUT` / `RECONCILIATION_REQUIRED` without hanging event loops or corrupting DB state.
  - **Scenario H**: Duplicate submission of identical idempotency key returns cached `DUPLICATE` execution status without re-triggering execution.

---

### 3. Executive Presentation for the CFO & Treasury Leadership
**Key Focus**: Financial Risk Governance, Separation of Duties (SoD), and Cryptographic Tamper Defense.

- **Demonstration Flow (Scenario B, C, & D)**:
  - **Scenario B ($250,000 Wire Transfer)**: Risk engine scores transaction at 75 (`HIGH`). Policy rule permits the transfer subject to mandatory human approval. The requesting human/agent is **blocked** from self-approving (`approver != requester`). VP of Finance Bob Jones approves; execution succeeds.
  - **Scenario C (Unauthorized Jurisdiction Transfer)**: Agent requests $1,000,000 to an unapproved beneficiary. Policy Engine evaluates `DENY`. Gateway returns status `BLOCKED`, zero money moves.
  - **Scenario D (Post-Approval Payload Tampering)**: Request approved for $50,000. Attacker tampers parameters to $500,000 before approval processing. SHA-256 payload digest re-verifier flags mismatch (`SECURITY_PAYLOAD_TAMPERED`), transaction is aborted.

---

## Live API Scenario Runner Reference

Every scenario can be triggered deterministically via REST API without supplying external parameters:

```bash
# List available demonstration scenarios
GET /api/v1/demo/scenarios

# Execute Scenario B (High-Risk Approved Transaction)
POST /api/v1/demo/scenarios/SCENARIO_B/run

# Fetch complete 12-step audit chain trace
GET /api/v1/demo/audit-chain/{action_request_id}

# Fetch control plane summary metrics
GET /api/v1/demo/summary
```
