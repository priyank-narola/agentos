# AgentOS MCP Tool Contract

This document defines the interface schemas, parameters, execution constraints, and authorization requirements for all tools exposed by the AgentOS MCP Server.

---

## 1. Tool Categories

To enforce strict separation of concerns, tools are classified into four distinct operational boundaries:

### A. READ Tools
*   **Purpose**: Allows the AI Agent to inspect active policies, registries, audit events, and approval status.
*   **Security Principle**: Read-only tools have no side effects, cannot modify databases, and are used solely for context gathering.

### B. REQUEST-ACTION Tools
*   **Purpose**: Allows the AI Agent to request execution of domain capabilities (e.g. `bank_transfer`).
*   **Security Principle**: These tools *never* execute actions directly. They only register a stateful `ActionRequest` inside the AgentOS Action Gateway and return the evaluation state.

### C. APPROVAL Tools
*   **Purpose**: Exposes endpoints to review, approve, reject, or cancel pending requests.
*   **Security Principle**: Exposing these to AI Agents is strictly limited to cases where the principal is an authorized human administrator. The calling principal's identity must match the authorized role.

### D. ADMINISTRATIVE Tools
*   **Purpose**: Registers new agents, tools, actions, resources, and policies.
*   **Security Principle**: Highly restricted. Exposed only to authorized orchestrators.

---

## 2. Core Tool Contract Inventory

### Tool 1: `read_principals` (READ)
*   **Purpose**: Retrieve principal registries.
*   **Input Schema**: Empty payload or optional `limit`/`offset` parameters.
*   **Output Schema**: `list[PrincipalSchema]`
*   **Required Identity**: Active Principal
*   **Policy/Risk Point**: Bypass (Read-only query boundary)
*   **Approval Behavior**: Immediate execution.
*   **Audit Events**: None.
*   **Failure Behavior**: Returns JSON-RPC standard error on database connection failure.

### Tool 2: `request_action` (REQUEST-ACTION)
*   **Purpose**: Submit a runtime task request.
*   **Input Schema**:
    ```json
    {
      "action_id": "UUID",
      "resource_id": "UUID",
      "parameters": "object"
    }
    ```
*   **Output Schema**: `GatewayResponse`
*   **Required Identity**: Principal + Agent Identity
*   **Required AgentOS Action**: Target Action ID
*   **Required Resource**: Target Resource ID
*   **Policy Evaluation Point**: Action Gateway Policy Engine (matches active rules)
*   **Risk Evaluation Point**: Risk Engine score evaluation
*   **Approval Behavior**: If policy Allow rule triggers `RiskClassification.HIGH`, transitions to `PENDING_APPROVAL`. Otherwise, executes immediately on `ALLOW` or gets blocked on `DENY`.
*   **Audit Events**: `ACTION_REQUEST_RECEIVED`, `RISK_EVALUATED`, `POLICY_EVALUATED`, `APPROVAL_REQUESTED` (if high risk), `ACTION_AUTHORIZED` (if allow).
*   **Failure Behavior**: Invalid IDs return `400 Bad Request`. Duplicate idempotency keys return `409 Conflict`.

### Tool 3: `review_approval` (APPROVAL)
*   **Purpose**: Review and approve a pending action request.
*   **Input Schema**:
    ```json
    {
      "approval_id": "UUID"
    }
    ```
*   **Output Schema**: `ApprovalDetailSchema`
*   **Required Identity**: Reviewer Principal (must be authorized)
*   **Required AgentOS Action**: `POST /approvals/{approval_id}/approve`
*   **Policy Evaluation Point**: Validation of the `approver_principal_id` matching an active human administrator.
*   **Approval Behavior**: Updates approval request status to `APPROVED`, resolves associated `ActionRequest` status to `COMPLETED`, and decisions to `ALLOW`.
*   **Audit Events**: `APPROVAL_APPROVED`
*   **Failure Behavior**: Expired requests or unauthorized reviewer actions return `409 Conflict`.

---

## 3. Boundary Exposure Decisions & Justifications

### A. Registry Operations (Expose: YES)
*   **Justification**: The AI Agent must be able to discover registered agents, tools, actions, and resources to understand what operations can be requested. This enables active tool routing.

### B. Policy Evaluations (Expose: NO)
*   **Justification**: Direct policy evaluation queries could allow agents to probe authorization rules for boundary exploits. Policy evaluation must only be triggered implicitly during `request_action` tool execution.

### C. Action Request Creation (Expose: YES)
*   **Justification**: This is the primary runtime entry point for an agent. Without this tool, the agent cannot orchestrate any stateful actions.

### D. Approval Status (Expose: YES)
*   **Justification**: Exposing approval status allows the agent to inform the user about pending approval requests and halt execution gracefully until the request is approved.

### E. Audit Information (Expose: NO)
*   **Justification**: Audit logs contain sensitive system-level state information. Exposing them to untrusted client agents introduces information-leakage risks.
