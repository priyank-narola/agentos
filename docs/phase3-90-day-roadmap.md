# AgentOS Phase 3 — 90-Day Implementation Roadmap

**Baseline Commit**: `7d5e97c4aedc220ffce3397cc92a9d5aa29e47cb`  
**Publication Date**: August 25, 2026  
**Strategic Focus**: Enterprise Financial & Treasury Action Control Plane

---

## Roadmap Structure

The 90-day execution plan is divided into three 30-day iterations. Tasks are explicitly categorized as:
* **MUST BUILD**: Essential path for core value delivery and technical foundation.
* **SHOULD BUILD**: High-value enhancements that strengthen differentiation.
* **EXPERIMENT**: Low-cost spikes to evaluate future capability.
* **DO NOT BUILD YET**: Features deferred to preserve focus.

---

## Phase 3A: Days 1–30 — Protocol Modernization & Execution Engine

### MUST BUILD
1. **Streamable HTTP MCP Transport Migration**:
   - Implement POST-only Streamable HTTP transport per 2026 MCP spec.
   - Enforce required headers: `MCP-Protocol-Version`, `Mcp-Method`, `Mcp-Name`.
   - Remove legacy GET `/sse` endpoint dependency for remote transport.
2. **Dynamic Real-Time Action Execution Engine**:
   - Replace mock `execution_status = NOT_EXECUTED` with a pluggable downstream HTTP webhook / gRPC dispatch system.
   - Update `GatewayService` to return real-time execution results upon policy & approval authorization.
3. **Tenant Context & Multi-Tenant Schema Support**:
   - Add `tenant_id: Mapped[UUID]` to `Principal`, `Agent`, `Delegation`, `ActionRequest`, `Decision`, `ApprovalRequest`, and `AuditEvent` models with database indexes.

### SHOULD BUILD
- **Client Metadata Documents (OAuth 2.1)**: Replace static environment secrets with dynamic URL-backed Client Metadata Documents for OAuth client resolution.

### EXPERIMENT
- **Wasm Action Runner Sandbox**: Prototype WebAssembly container sandbox for isolated tool execution.

### DO NOT BUILD YET
- Custom LLM Gateway Proxy, Prompt Moderation Guardrail, Vector DB RAG Integration.

---

## Phase 3B: Days 31–60 — Workload Identity & Financial Compliance Pack

### MUST BUILD
1. **SPIFFE / Workload Identity Integration**:
   - Support SPIFFE Verifiable Identity Documents (SVIDs) for machine-level agent authentication.
   - Implement `SpiffeTokenValidator` verifying SPIFFE X.509 SVIDs alongside OAuth JWTs.
2. **DPoP Token Binding (RFC 9449)**:
   - Enforce `DPoP` HTTP header verification, binding access tokens to client public keys (`cnf` claim).
3. **Financial & Treasury Compliance Policy Pack**:
   - Pre-built policy rules for high-value financial actions (`wire_transfer`, `invoice_payout`, `card_limit_increase`).
   - Hard threshold rules (e.g., transactions >$10,000 automatically set `decision = REQUIRE_APPROVAL`).

### SHOULD BUILD
- **Slack / Email Approval Notifications**: Asynchronous webhook dispatch to Slack/Email when `ApprovalRequest` is created.

### EXPERIMENT
- **Multi-Hop Agent Delegation Passport**: Cryptographic signature chain carrying principal intent across sub-agent calls.

### DO NOT BUILD YET
- Multi-cloud UI dashboard, fine-tuning observability.

---

## Phase 3C: Days 61–90 — Multi-Agent Provenance & Launch Readiness

### MUST BUILD
1. **Cryptographic Audit Ledger & Provenance Engine**:
   - SHA-256 hash chaining across `AuditEvent` records to guarantee tamper-proof audit trails.
   - Export endpoints for SOX and EU AI Act compliance auditors (`GET /api/v1/audit/export`).
2. **Enterprise Admin Console (Minimal Web UI)**:
   - Next.js dashboard for CISOs to inspect agent active delegations, pending approvals, and action audit logs.
3. **End-to-End Treasury Agent Integration Demo**:
   - Complete working demonstration of an AI Finance Agent executing accounts payable via AgentOS Control Plane.

### SHOULD BUILD
- **OpenTelemetry Agent Trait Spans**: Export OTel spans for gateway action execution pipelines.

### EXPERIMENT
- **Behavioral Anomaly Risk Scoring**: Machine learning classifier detecting unusual tool calling frequencies.

### DO NOT BUILD YET
- Self-hosted enterprise deployment Helm charts, dynamic LLM prompt routing.

---

## Summary Summary Table

| Iteration | Focus Area | Core Deliverable | Target Outcome |
| :--- | :--- | :--- | :--- |
| **Days 1–30** | Protocol & Execution | Streamable HTTP + Action Dispatch | Spec-compliant 2026 MCP server with live webhook execution |
| **Days 31–60** | Identity & Finance Pack | SPIFFE + DPoP + Treasury Policy | Enterprise financial agent control plane prototype |
| **Days 61–90** | Provenance & Launch | Cryptographic Ledger + CISO UI | Production-ready AgentOS Financial Control Plane v1.0 |
