# AgentOS Phase 3 — Technology Radar (2026)

**Baseline Commit**: `7d5e97c4aedc220ffce3397cc92a9d5aa29e47cb`  
**Publication Date**: August 25, 2026  
**Strategic Mission**: *"Build the world's most trusted control plane for AI agents performing real-world enterprise actions."*

---

## Radar Overview

The 2026 Technology Radar categorizes emerging standards, protocols, security mechanisms, and developer platforms across 21 technology areas into four strategic rings:

```
+-----------------------------------------------------------------------+
|  ADOPT NOW    : Standardized, critical for core mission              |
|  EXPERIMENT   : Promising technology, prototype integration           |
|  WATCH        : Evolving standard, track industry adoption            |
|  IGNORE       : Non-core distraction, out of scope for control plane  |
+-----------------------------------------------------------------------+
```

---

## 1. ADOPT NOW

Technologies that must be incorporated into AgentOS core architecture immediately:

| Technology Area | Technology / Standard | Business & Technical Rationale |
| :--- | :--- | :--- |
| **MCP Transport** | **Streamable HTTP MCP Transport** | The 2026 MCP specification standardizes POST-only Streamable HTTP as the official remote transport model (removing legacy GET `/sse` session negotiation). Requires `MCP-Protocol-Version`, `Mcp-Method`, and `Mcp-Name` HTTP headers. |
| **OAuth Metadata** | **Client Metadata Documents** | Replaces deprecated Dynamic Client Registration (RFC 7591) with URL-backed Client Metadata Documents for OAuth 2.1 identity discovery. |
| **Token Protection** | **DPoP (Demonstrating Proof-of-Possession)** (RFC 9449) | Cryptographically binds Bearer JWT access tokens to the client agent's public key pair, eliminating token replay attacks from intercepted networks. |
| **Workload Identity** | **SPIFFE / SPIRE (SVIDs)** | CNCF standard for issuing short-lived, cryptographically verifiable machine identities for AI agents running in containerized/k8s environments. |
| **Agent Identity Standard**| **AIMS (Agent Identity Management System)** | IETF draft standardizing agent identity federation, delegating token issuance, and multi-hop credential chains. |
| **Policy Engines** | **OPA (Open Policy Agent) / Rego / Cedar** | Industry-standard policy-as-code engines for complex enterprise ABAC/ReBAC rule compilation. |

---

## 2. EXPERIMENT

Technologies to prototype in research branches to validate technical feasibility and customer value:

| Technology Area | Technology / Standard | Evaluation Objective |
| :--- | :--- | :--- |
| **Agent-to-Agent Protocols** | **Multi-Hop Agent Delegation Passports** | Cryptographic token chains carrying user intent and scope across multi-agent chains (Agent A → Agent B → Agent C). |
| **Sandboxing** | **MicroVM / Wasm Sandbox Action Runner** | Isolated WebAssembly or Firecracker microVM execution environments for running un-trusted agent tool calls safely. |
| **Cryptographic Signing** | **Sigstore / COSE Action Signatures** | Cryptographic signing of `ActionRequest` and `Decision` records to guarantee non-repudiation in audit ledgers. |
| **Agent Observability** | **OpenTelemetry Agent Trait Extensions** | Instrumenting agent decision trajectories with OTel tracing spans linked to Gateway Action Requests. |
| **Prompt Injection Defense**| **Structural Parameter Sanitizers** | Heuristic classifiers detecting adversarial prompt injection patterns nested within JSON parameter values. |

---

## 3. WATCH

Technologies to monitor for industry convergence before allocating engineering resources:

| Technology Area | Technology / Standard | Trigger for Action |
| :--- | :--- | :--- |
| **Confidential Computing**| **AMD SEV-SNP / Intel SGX Enclaves** | Enterprise requirement for zero-trust enclave execution of sensitive financial tool credentials. |
| **Provenance Standards** | **C2PA / Supply Chain Provenance** | Industry standardization of provenance metadata for agent-generated dataset mutations. |
| **AI Security Standards** | **OWASP Top 10 for Agentic Applications (2026)** | Formal inclusion in enterprise compliance checklists (SOX, SOC2, HIPAA). |
| **Model Routing** | **Semantic Model Gateways** | If enterprise customers request dynamic model failover integrated directly with action policy rules. |
| **Computer Use Agents** | **GUI / OS Action Interceptors** | Evolution of OS-level virtual desktop agents mutating enterprise desktop software. |

---

## 4. IGNORE

Technologies that are non-core distractions to the AgentOS Control Plane mission:

| Technology Area | Technology / Framework | Reason to Ignore |
| :--- | :--- | :--- |
| **LLM Proxies / Caching** | **LiteLLM / Portkey Proxy** | AgentOS is an *Action Control Plane*, not an LLM API cost manager or prompt caching proxy. |
| **Agent Frameworks** | **LangChain / AutoGen / CrewAI** | AgentOS must remain framework-agnostic, governing tool execution regardless of how agents are built. |
| **Agent Memory / RAG** | **Vector DBs / Pinecone / Chroma** | Data retrieval is an input; AgentOS governs *out-of-band enterprise actions and state mutations*. |
| **Model Fine-Tuning** | **LoRA / PEFT Pipelines** | Model training is orthogonal to runtime action authorization. |
