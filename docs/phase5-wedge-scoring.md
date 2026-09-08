# AgentOS Phase 5 — Product Wedge Scoring Model & Feature Deferral Register

**Version**: Phase 5 Wedge Scoring System v1.0  
**Baseline**: 5 Candidate Market Wedges Evaluated Over 10 Standardized Evaluation Dimensions  

---

## 1. 10-Factor Product Wedge Scoring Model

Each candidate market wedge is evaluated across 10 distinct, weighted criteria. Each factor is scored on a **1 to 10 scale** (where 1 = minimal/poor, 10 = extreme/ideal), yielding a maximum total score of **100 points**:

| # | Evaluation Dimension | Description | Weight / Max Points |
| :-: | :--- | :--- | :-: |
| **1** | **Pain Severity** | How critical and painful is an unauthorized or incorrect agent action in this workflow? | 10 |
| **2** | **Frequency** | How frequently do agents attempt write/mutation actions in this workflow daily? | 10 |
| **3** | **Urgency** | Is the customer actively seeking a solution right now (Q3 budget / active initiative)? | 10 |
| **4** | **Agent Adoption** | How mature and prevalent is AI agent adoption in this specific operational area today? | 10 |
| **5** | **Security Risk** | What is the blast radius (financial loss, data exposure, system outage) of failure? | 10 |
| **6** | **Compliance Pressure** | Are there mandatory regulatory mandates (SOC2, HIPAA, PCI-DSS, GDPR, SOX) driving control? | 10 |
| **7** | **Budget Availability** | Does the target buyer persona (CISO, CTO, VP Treasury) control active software budget? | 10 |
| **8** | **Willingness To Pay** | Will the customer pay recurring software fees for an external control plane? | 10 |
| **9** | **Competitive Differentiation** | How unique is AgentOS's payload-bound authorization vs existing prompt/API firewalls? | 10 |
| **10** | **Implementation Feasibility** | How fast can we integrate our existing Phase 4B gateway into their technical stack (<1 week)? | 10 |

---

## 2. Candidate Market Wedge Definitions & Pre-Interview Baseline Analysis

```
Candidate Wedge A: Finance / Treasury (Payments, wire transfers, refunds, invoice approvals)
Candidate Wedge B: IT / SRE Operations (AWS/GCP changes, K8s deployments, IAM grants, remediation)
Candidate Wedge C: Customer Operations / CRM (Billing credits, order modifications, refunds, CRM state)
Candidate Wedge D: Security / IAM Operations (Privilege escalation, SOC threat response, key rotation)
Candidate Wedge E: Developer / Engineering Automation (CI/CD pipelines, DB migrations, IaC apply)
```

> [!NOTE]
> Final wedge scores will be computed strictly from real customer evidence collected during Phase 5 interviews. Pre-interview estimates serve as hypotheses to be validated or invalidated.

---

## 3. Structured "Do Not Build Yet" Feature Register

To prevent engineering waste, all prospective features are categorized into a strict deferral framework. **No feature in the DEFERRED status will be implemented until customer discovery evidence justifies it.**

| Feature Name | Primary Target Persona | Current Classification | Classification Rationale | Discovery Metric Required to Unblock |
| :--- | :--- | :---: | :--- | :--- |
| **SPIFFE/SPIRE Workload Identity** | Security Architect | **ENGINEERING-DRIVEN / DEFERRED** | Sophisticated mTLS workload attestation. Unneeded for initial customer pilots using OAuth JWTs. | ≥3 of 5 CISOs explicitly require SPIFFE SVID attestation for POC. |
| **OAuth DPoP (RFC 9449)** | Security Architect | **ENGINEERING-DRIVEN / DEFERRED** | Cryptographic token binding. High implementation complexity; non-critical for pilot phase. | ≥2 enterprise security audits mandate DPoP proof-of-possession. |
| **Production Banking Connectors** | CFO / Treasury | **UNVALIDATED / DEFERRED** | Real ACH/Wire rails (Stripe, Plaid, JPM). High risk & legal overhead before market wedge validation. | Confirmation that Finance/Treasury is the winning market wedge after 5 interviews. |
| **Real-Time Slack/Teams Approvals** | All Personas | **CUSTOMER-REQUESTED / DEFERRED** | Interactive messaging approval bots. High customer interest expected, but sandbox UI suffices for initial discovery. | ≥4 of 5 customers state Slack/Teams is a mandatory pilot blocker. |
| **Okta / SCIM Identity Provisioning** | IT Administrator | **UNVALIDATED / DEFERRED** | Automated user/agent directory sync. Manual REST seeding works for sandbox pilots. | Enterprise IT buyer requires SCIM 2.0 sync for staging pilot. |
| **Additional MCP Transports (e.g. gRPC)** | AI Engineer | **ENGINEERING-DRIVEN / DEFERRED** | Streamable HTTP POST /mcp implemented in Phase 4A covers 95%+ of MCP clients (Claude, Cursor). | Customer AI team uses gRPC or WebSockets exclusively for MCP. |
| **LLM Gateway / Prompt Guardrails** | Head of AI | **UNVALIDATED / DEFERRED** | Text-based prompt safety filtering. Out of scope for AgentOS's action authorization core thesis. | Customer evidence proves action gateway alone is insufficient. |
| **Vector DB / RAG Access Security** | Data Architect | **UNVALIDATED / DEFERRED** | Embedding & vector database filtering. Unrelated to action execution governance. | Customer identifies RAG retrieval as their highest-risk vulnerability. |
| **Visual Drag-and-Drop Policy Builder** | Compliance Lead | **CUSTOMER-REQUESTED / DEFERRED** | Graphical policy editing interface. REST API / JSON policies are sufficient for early technical pilots. | Non-technical compliance officer is designated primary policy administrator. |
| **Multi-Region DB Active-Active** | SRE Lead | **ENGINEERING-DRIVEN / DEFERRED** | Global database replication. Single-region PostgreSQL/SQLite handles early pilot traffic. | Customer SLA requires multi-region high-availability failover. |
