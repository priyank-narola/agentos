# AgentOS Phase 5 — Enterprise Customer Discovery Interview Script & Methodology

**Version**: Phase 5 Interview Protocol v1.0  
**Target Duration**: 30 Minutes  
**Golden Rule of Discovery**: **DO NOT PITCH AGENTOS.** Listen 80% of the time, speak 20% of the time. First understand the customer's problem before discussing solutions.

---

## 1. 30-Minute Interview Structure

| Time Block | Topic / Phase | Objective |
| :---: | :--- | :--- |
| **00:00 – 03:00** | Introduction & Context | Set non-pitch expectation, request permission to record/take notes. |
| **03:00 – 10:00** | Current AI Agent Landscape | Uncover current agent deployments, frameworks used, and active tools. |
| **10:00 – 18:00** | Risk & Authorization Deep-Dive | Explore highest-risk write actions, current security controls, and pain severity. |
| **18:00 – 24:00** | Human Approval, Identity & Audit | Investigate human-in-the-loop workflows, delegation mapping, and compliance logging. |
| **24:00 – 28:00** | Commercial & Deployment Constraints | Evaluate budget authority, latency tolerances, deployment preferences, and MCP adoption. |
| **28:00 – 30:00** | Wrap-Up & Next Steps | Gauge pilot interest, ask for referrals, and confirm follow-up. |

---

## 2. Opening Explanation (Non-Pitch Narrative)

> *"Thank you for taking the time to speak with us today. We are conducting research into how enterprise security and engineering teams govern autonomous AI agents as they transition from read-only search/Q&A to executing real-world write actions inside core enterprise systems.*
>
> *Our core research question is: **'Your AI agents can act — how does your organization decide whether those actions are allowed in real time?'**
>
> *We are not here to sell software today. We want to understand your current workflows, the security challenges you face, and where current tools fall short."*

---

## 3. 20 High-Quality Discovery Questions

### Current State & Agent Actions
1. **Current Deployments**: What specific AI agents or LLM-driven tools are currently running in your staging or production environments?
2. **Planned Capabilities**: What new capabilities or write actions are your teams planning to grant AI agents over the next 6 to 12 months?
3. **Highest-Risk Actions**: What is the single highest-risk action an AI agent could execute in your environment today that would cause severe financial, operational, or security damage if executed incorrectly?

### Security, Risk & Authorization Architecture
4. **Current Authorization**: How do you currently enforce authorization boundaries when an AI agent calls an internal API or tool (e.g. system prompts, hardcoded rules, API gateways)?
5. **Prompt Injection Resilience**: How do you prevent an AI agent from being tricked via prompt injection into executing an unauthorized write action?
6. **Risk Categorization**: How do you dynamically evaluate whether an agent's requested action is low-risk (auto-allowed) versus high-risk (requiring review)?

### Human Approval, Identity & Delegation
7. **Human Approval Workflow**: What does your human-in-the-loop approval process look like when an agent attempts a sensitive write action?
8. **Separation of Duties**: How do you ensure that the person approving an agent's requested action is independent from the employee who initiated the agent task?
9. **Identity Delegation**: How do your APIs determine which human employee authorized an AI agent to act, especially when agents execute tasks asynchronously?

### Audit, Compliance & Operations
10. **Audit Requirements**: What audit trail or compliance logging is required by your internal security auditors for AI agent actions?
11. **Security Incidents**: Have you experienced any incidents or near-misses where an AI model performed an unintended, hallucinated, or out-of-scope operation?
12. **Existing Tooling**: What existing security tools (LLM gateways, API firewalls, IAM solutions) have you deployed for AI safety, and where do they fail?

### Architecture, Latency & Standards
13. **MCP Adoption**: Are your engineering teams using or evaluating the Model Context Protocol (MCP) to standardize tool integration between AI clients and services?
14. **Latency Overhead**: What is your maximum acceptable latency overhead for a real-time security decision on an agent tool call (e.g., <5ms, <50ms, <200ms)?
15. **Deployment Preference**: Does your security policy permit using a multi-tenant SaaS control plane for AI authorization, or would you require single-tenant VPC / on-premise deployment?

### Commercial, Urgency & Decision Making
16. **Biggest Blocker**: What is the single biggest blocker currently preventing your leadership from giving AI agents full autonomy to execute write operations?
17. **Urgency & Timeline**: How urgent is solving AI agent action authorization for your team (e.g. active Q3 priority vs exploratory research for next year)?
18. **Alternatives Evaluated**: Have you considered building an in-house authorization gateway for AI agents, and what was the estimated engineering effort?
19. **Buying Authority & Budget**: Who inside your organization holds final purchasing authority for AI governance tools, and is there designated budget?
20. **Willingness to Pilot**: If a lightweight sandbox control plane existed that could enforce policies and human approvals without changing your existing code, would you be open to running a 30-day pilot?

---

## 4. Probing & Follow-Up Questions by Candidate Wedge

### Probe A: Finance / Treasury
- *"When an agent initiates a refund or payout, what is the hard dollar threshold that triggers human review?"*
- *"How do you handle payload tampering if a payment parameter changes between approval and execution?"*

### Probe B: IT / SRE Operations
- *"If an SRE agent suggests modifying Terraform or restarting a production cluster, who verifies the blast radius?"*
- *"How do you prevent an AI agent from granting itself elevated AWS IAM roles during incident remediation?"*

### Probe C: Customer Operations / CRM
- *"What prevents a support bot from issuing maximum account credits to a malicious user?"*
- *"How do you audit state changes made by customer service bots inside Salesforce or Zendesk?"*

### Probe D: Security / IAM Operations
- *"When a security bot isolates an endpoint or revokes access, how do you prevent false-positive lockouts?"*

### Probe E: Developer / Engineering Automation
- *"What permissions do coding assistants (Cursor, Claude Desktop) have on your developers' local machines and repositories?"*

---

## 5. Objection Handling Guide

| Customer Objection | Root Cause | Discovery Response |
| :--- | :--- | :--- |
| *"We rely on system prompts and output parser validation."* | Early AI maturity; relying on probabilistic safety. | *"How do you handle prompt injection or hallucinated parameters when system prompts fail?"* |
| *"We built custom if/else checks in our backend code."* | In-house custom code; maintenance burden. | *"How do you manage policy updates, risk scoring, and audit logging as the number of agent tools scales?"* |
| *"We use an LLM gateway (e.g. Portkey, LiteLLM) for guardrails."* | Confusing prompt filtering with action authorization. | *"LLM gateways inspect prompt text — how do they validate payment parameters, tenant isolation, and payload digest integrity at execution time?"* |
| *"We can't add latency to our real-time agent loops."* | Performance sensitivity. | *"If security policy evaluation took under 2 milliseconds, would that fit within your performance envelope?"* |
| *"We can't send our data to a third-party SaaS."* | Enterprise security policy. | *"If the control plane ran inside your own AWS VPC via Docker/Kubernetes, would that satisfy compliance?"* |

---

## 6. Rigorous 5-Category Evidence Classification Methodology

To prevent bias and self-deception, every piece of information collected during customer interviews must be categorized into one of five mutually exclusive data buckets:

1. **OBSERVED FACT**: Verifiable, empirical truth stated by the customer (e.g., *"We run 14 Claude agents in production using AWS Bedrock."*).
2. **CUSTOMER QUOTE**: Direct, verbatim statements captured during the interview (e.g., *"'Our CISO will not allow agents to touch production databases without a human approval step.'"*).
3. **CUSTOMER OPINION**: Subjective beliefs or projections stated by the customer (e.g., *"I think our management might be willing to pay $2,000/month for this."*).
4. **OUR INFERENCE**: Deductions drawn by the AgentOS team based on customer evidence (e.g., *Inference: Their current custom Python auth checks are becoming unmaintainable as they add new tools.*).
5. **OUR ASSUMPTION**: Unverified hypotheses held by the AgentOS team that still require empirical validation (e.g., *Assumption: Finance teams are more risk-averse than DevOps teams.*).

> [!CRITICAL]
> **Never mix or substitute assumptions for observed facts or quotes.**
