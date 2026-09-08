# AgentOS Phase 5C — Customer Discovery Execution Brief & Outreach Package

**Version**: Phase 5C Execution Protocol v1.0  
**Baseline**: Phase 5A & Phase 5B Discovery Documents  
**Core Thesis**: *"Your AI agents can act. AgentOS decides whether those actions are allowed."*  
**Critical Rule**: **Do NOT assume Finance/Treasury is the winning market wedge.** All 5 candidate market wedges (Finance, IT/SRE, Customer Operations, Security/IAM, Developer Automation) are treated as competing hypotheses until real customer evidence is collected.  

---

## Part 1: Personalized Discovery Outreach Packages (Targets 1–5)

---

### Target 1: Brex (Candidate Wedge A: Finance / Treasury)

#### 1. Relevant Buyer Persona
- **Primary Buyer**: Chief Information Security Officer (CISO) / Head of Security
- **Technical Champion**: Lead AI Platform Engineer / Head of Financial Engineering

#### 2. Exact Problem Hypothesis to Validate
> **Hypothesis A**: Brex restricts AI agents from autonomously initiating corporate payouts, ACH wires, or credit limit modifications >$5,000 because existing prompt filtering and LLM guardrails cannot guarantee payload digest integrity, separation of duties, or non-repudiable identity delegation.

#### 3. Personalized Outreach Message
```text
Subject: Research: How Brex security governs autonomous AI financial actions

Hi [First Name],

I’m conducting an industry research study on how security leaders at high-growth fintechs govern autonomous AI agents as they transition from read-only reporting to executing real-world financial write actions.

As teams integrate tools like Claude or custom financial LLM bots, security leaders face a core challenge: "Your AI agents can act — how does your team decide whether financial payouts or credit changes are allowed in real time?"

Specifically, I’m investigating how fintech CISOs prevent prompt injection exploits, payload tampering, and unauthorized payment initiation when agents call financial APIs.

Would you be open to a brief 20-minute research conversation next week? I’m happy to share our aggregated benchmark data on AI action control planes across 20 engineering teams in return for your perspective.

Purely research — no sales pitch.

Best regards,

Priyank Narola
AgentOS Security Research
priyank@agentos.dev
```

#### 4. Primary & Follow-Up Discovery Questions
- **5 Primary Questions**:
  1. What financial write or mutation actions are your AI models or automated bots permitted to execute in production today?
  2. What is the single highest-risk financial API call an AI agent could execute in your environment?
  3. How do you prevent an AI agent from being manipulated via prompt injection into altering payout amounts or beneficiary account numbers?
  4. What human approval steps are required before an AI-initiated payment over $10,000 settles?
  5. How do you map the identity of the human employee who prompted the agent to the resulting financial transaction?
- **5 Follow-Up Questions**:
  1. *"If an agent requested a $50,000 ACH payout, who approves it and via what interface?"*
  2. *"How do you verify that payment parameters weren't altered after human approval?"*
  3. *"Are your internal financial APIs exposed as MCP tools to AI models?"*
  4. *"What is your acceptable latency budget for real-time security policy evaluation on API tool calls?"*
  5. *"If a zero-trust financial action gateway existed, would Brex require single-tenant VPC deployment?"*

#### 5. Evidence Matrix: Strengthening vs. Invalidating
- **Evidence That Strengthens Hypothesis A**:
  - Customer states: *"We want agents to execute payments, but our security policy forbids it until we have server-side approval gates and payload hashing."*
  - Customer reports building custom Python `if/else` authorization code that is becoming unmaintainable.
- **Evidence That Invalidates Hypothesis A**:
  - Customer states: *"AI models will NEVER be allowed to execute payment initiation under any circumstances, even with human approvals."*
  - Customer states: *"Our existing API gateway already handles LLM identity delegation and payload hashing seamlessly."*

#### 6. Buying & Pilot Signals
- **Strong Signal**: CISO states active Q3 initiative to deploy AI financial agents; willing to test AgentOS sandbox gateway within 14 days; identified budget >$25k/yr.
- **Medium Signal**: Security team acknowledges problem; interested in reviewing benchmark report; open to follow-up technical review in Q4.
- **Weak Signal**: Casual curiosity; no active AI payment initiatives; unwilling to commit time for follow-up architecture review.

#### 7. Structured Evidence Capture Log (Brex)
- **OBSERVED FACT**: `UNKNOWN / NOT YET VALIDATED`
- **CUSTOMER QUOTE**: `UNKNOWN / NOT YET VALIDATED`
- **CUSTOMER OPINION**: `UNKNOWN / NOT YET VALIDATED`
- **OUR INFERENCE**: `UNKNOWN / NOT YET VALIDATED`
- **OUR ASSUMPTION**: `Hypothesis A: Brex limits autonomous AI payments due to payload tamper risks.`

---

### Target 2: Datadog (Candidate Wedge B: IT / SRE Operations)

#### 1. Relevant Buyer Persona
- **Primary Buyer**: Vice President of Security / Chief Information Security Officer (CISO)
- **Technical Champion**: Head of Site Reliability Engineering (SRE) / Bits AI Product Lead

#### 2. Exact Problem Hypothesis to Validate
> **Hypothesis B**: Datadog SRE teams require real-time policy evaluation and human approval gates before Bits AI or incident bots can execute destructive remediation runbooks (service restarts, cloud config modifications, node rebalancing) to prevent false-positive production outages.

#### 3. Personalized Outreach Message
```text
Subject: Research: Guardrails & blast-radius control for SRE AI remediation bots

Hi [First Name],

I’m reaching out because of Datadog’s leadership in AI-driven observability and incident response.

We are running a research project studying how SRE and infrastructure leaders manage blast-radius controls when deploying AI agents (like Bits AI) for incident triage, automated runbook execution, and cloud remediation.

While AI agents accelerate incident response, granting them permission to restart production services or modify cloud security groups introduces significant operational risk if an agent acts on hallucinated parameters or false-positive alerts.

I’d love to get 20 minutes of your feedback on how your team bounds the execution permissions of automated remediation tools today.

In exchange, I’m happy to share our performance metrics on real-time policy evaluation (<1ms latency) for infrastructure action gateways.

Best regards,

Priyank Narola
AgentOS Systems Security Research
priyank@agentos.dev
```

#### 4. Primary & Follow-Up Discovery Questions
- **5 Primary Questions**:
  1. What write or remediation capabilities does Bits AI or internal SRE bots currently have in production cloud environments?
  2. What is the highest-risk action an SRE AI agent could perform during a P1 incident?
  3. How do you prevent an AI agent from executing an out-of-scope remediation runbook that causes a cascading outage?
  4. What authorization mechanisms ensure an AI agent cannot escalate its own AWS/GCP IAM permissions?
  5. How are human SRE approvals integrated into automated incident remediation loops?
- **5 Follow-Up Questions**:
  1. *"If Bits AI recommends restarting a core database cluster, can it execute automatically or does an engineer approve?"*
  2. *"How do you enforce separation of duties during emergency incident response?"*
  3. *"Is real-time policy evaluation latency (<1ms) a critical blocker for SRE workflows?"*
  4. *"Do your engineering teams use MCP to expose observability tools to AI agents?"*
  5. *"Would Datadog require an on-premise / single-tenant gateway for infrastructure actions?"*

#### 5. Evidence Matrix: Strengthening vs. Invalidating
- **Evidence That Strengthens Hypothesis B**:
  - Customer states: *"Our SREs waste time manually verifying AI remediation recommendations because we don't have policy gates to safely auto-execute low-risk fixes."*
  - Customer reports a near-miss outage caused by an automated script acting on bad parameters.
- **Evidence That Invalidates Hypothesis B**:
  - Customer states: *"Bits AI is strictly an advisory chat assistant; we have zero interest in ever letting AI execute remediation commands."*
  - Customer states: *"Our SRE runbooks are fully static scripts triggered by Webhooks; LLM reasoning plays no role in execution."*

#### 6. Buying & Pilot Signals
- **Strong Signal**: Head of SRE states AI remediation is blocked by CISO due to blast-radius fears; requests immediate staging pilot of sub-millisecond policy engine.
- **Medium Signal**: SRE team interested in policy evaluation benchmark; agrees to share internal runbook authorization requirements.
- **Weak Signal**: Content with existing static PagerDuty runbooks; no plans for AI-driven infrastructure automation.

#### 7. Structured Evidence Capture Log (Datadog)
- **OBSERVED FACT**: `UNKNOWN / NOT YET VALIDATED`
- **CUSTOMER QUOTE**: `UNKNOWN / NOT YET VALIDATED`
- **CUSTOMER OPINION**: `UNKNOWN / NOT YET VALIDATED`
- **OUR INFERENCE**: `UNKNOWN / NOT YET VALIDATED`
- **OUR ASSUMPTION**: `Hypothesis B: SRE AI remediation is blocked by blast-radius concerns.`

---

### Target 3: Zendesk (Candidate Wedge C: Customer Operations / CRM)

#### 1. Relevant Buyer Persona
- **Primary Buyer**: CISO / Head of Product Security
- **Technical Champion**: VP of AI Engineering / Lead Customer Support Architect

#### 2. Exact Problem Hypothesis to Validate
> **Hypothesis C**: Customer support AI agents executing refunds, billing credits, or account modifications are vulnerable to prompt injection attacks, creating financial loss risks that require dollar-bounded policy rules and manager approval gates.

#### 3. Personalized Outreach Message
```text
Subject: Research: How support leaders govern AI agents executing refunds & billing credits

Hi [First Name],

I’m conducting an industry research study on how customer operations and security leaders govern AI support agents as they transition from answering FAQs to executing customer account write actions.

When an AI support agent is granted API access to issue refunds, apply subscription credits, or update CRM records, security teams face a critical challenge: "How do you prevent prompt injection attacks from manipulating AI support bots into granting unauthorized refunds?"

I’m interviewing AI engineering and security leads to understand how enterprise teams enforce dollar-bounded policy rules and manager approval gates on support bot tool calls.

Would you be open to a 20-minute research conversation next week? I’d be glad to share our draft findings on AI customer support security patterns across 20 enterprise teams.

Purely research — no sales pitch.

Best regards,

Priyank Narola
AgentOS Security Research
priyank@agentos.dev
```

#### 4. Primary & Follow-Up Discovery Questions
- **5 Primary Questions**:
  1. What billing or account mutation actions can Zendesk AI agents execute autonomously today?
  2. What is the hard dollar threshold for automated refunds before a human manager must approve?
  3. How do you protect customer support AI agents against prompt injection attacks attempting unauthorized billing credits?
  4. How do you audit state changes made by AI agents inside customer CRM databases?
  5. How do you map an AI agent's support action back to the underlying customer session and authorization scope?
- **5 Follow-Up Questions**:
  1. *"Have you observed instances where support bots were manipulated into granting out-of-scope discounts?"*
  2. *"How do you enforce separation of duties between the support bot and the approving manager?"*
  3. *"Is Zendesk evaluating MCP for standardizing AI agent tool access to customer backends?"*
  4. *"What audit trail format is required by your enterprise compliance auditors?"*
  5. *"Would a lightweight API authorization gateway fit into your support microservices architecture?"*

#### 5. Evidence Matrix: Strengthening vs. Invalidating
- **Evidence That Strengthens Hypothesis C**:
  - Customer states: *"We limit AI agent refunds to under $25 because we've seen users trick LLMs into issuing maximum account credits."*
  - Customer expresses urgent need for central audit logging of all AI-initiated CRM state changes.
- **Evidence That Invalidates Hypothesis C**:
  - Customer states: *"All refunds are processed by human agents; AI bots only draft suggested responses."*
  - Customer states: *"Our backend payment gateway handles refund rate limiting seamlessly, so bot security is a non-issue."*

#### 6. Buying & Pilot Signals
- **Strong Signal**: VP AI Engineering reports active prompt injection vulnerabilities on refund bots; requests pilot of AgentOS policy gateway to enforce $100 manager approval rules.
- **Medium Signal**: Team acknowledges refund fraud risk; requests copy of prompt injection resilience benchmarks.
- **Weak Signal**: Support bots handle static FAQ queries only; no API write access planned.

#### 7. Structured Evidence Capture Log (Zendesk)
- **OBSERVED FACT**: `UNKNOWN / NOT YET VALIDATED`
- **CUSTOMER QUOTE**: `UNKNOWN / NOT YET VALIDATED`
- **CUSTOMER OPINION**: `UNKNOWN / NOT YET VALIDATED`
- **OUR INFERENCE**: `UNKNOWN / NOT YET VALIDATED`
- **OUR ASSUMPTION**: `Hypothesis C: Support bot prompt injection refund fraud is an active pain point.`

---

### Target 4: Wiz (Candidate Wedge D: Security / IAM Operations)

#### 1. Relevant Buyer Persona
- **Primary Buyer**: Chief Technology Officer (CTO) / Chief Information Security Officer (CISO)
- **Technical Champion**: VP Security Engineering / Head of Cloud Security Architecture

#### 2. Exact Problem Hypothesis to Validate
> **Hypothesis D**: Automated cloud security containment bots (isolating compromised VMs, revoking IAM credentials, altering security groups) cause high false-positive disruption risks, requiring cryptographic attestation and human SOC analyst approval gates.

#### 3. Personalized Outreach Message
```text
Subject: Research: Blast-radius controls for automated security containment bots

Hi [First Name],

I’m reaching out because of Wiz’s leadership in cloud security and automated threat remediation.

We are conducting a research study on how enterprise security teams manage blast-radius controls when deploying AI agents or automated bots for threat containment and cloud vulnerability remediation.

While automated containment accelerates incident response, granting security bots permission to isolate workloads or revoke IAM permissions introduces severe operational disruption risks if false positives occur.

I’d love to get 20 minutes of your feedback on how your team bounds the execution scope of security remediation bots and enforces analyst approval gates.

In exchange, I’m happy to share our performance benchmarks on zero-trust policy engines and immutable audit logging.

Best regards,

Priyank Narola
AgentOS Security Research
priyank@agentos.dev
```

#### 4. Primary & Follow-Up Discovery Questions
- **5 Primary Questions**:
  1. What automated remediation actions can AI security tools execute in customer cloud environments today?
  2. What is the highest-risk action a security bot could perform (e.g. isolating a production database host)?
  3. How do you prevent an AI security agent from accidentally revoking critical IAM roles during automated containment?
  4. What approval workflows exist when a security bot proposes isolating a high-sensitivity cloud resource?
  5. How do you cryptographically attest the identity and codebase of automated security bots?
- **5 Follow-Up Questions**:
  1. *"How do SOC teams handle false-positive alerts that trigger automated containment runbooks?"*
  2. *"How do you enforce that the SOC analyst approving containment is not the author of the security rule?"*
  3. *"Are you evaluating MCP as a standardized protocol for cloud security tool execution?"*
  4. *"Would Wiz enterprise customers require an on-premise / single-tenant control plane for security actions?"*
  5. *"What latency budget is allowed for security policy evaluation during active threat containment?"*

#### 5. Evidence Matrix: Strengthening vs. Invalidating
- **Evidence That Strengthens Hypothesis D**:
  - Customer states: *"Customers disable our automated remediation features because they fear false-positive isolation of production infrastructure."*
  - Customer demands dual-key approval mechanisms before any bot can alter IAM permissions.
- **Evidence That Invalidates Hypothesis D**:
  - Customer states: *"Security automation is fully deterministic (lambda scripts); AI reasoning plays zero role."*
  - Customer states: *"Cloud security tools should only report vulnerabilities, never execute write remediation."*

#### 6. Buying & Pilot Signals
- **Strong Signal**: CTO states enterprise sales are blocked because customers lack confidence in security bot containment boundaries; proposes pilot integration.
- **Medium Signal**: Security team requests technical architecture review of AgentOS TOCTOU revalidation.
- **Weak Signal**: Prefers manual SOC analyst remediation exclusively; no interest in automated containment.

#### 7. Structured Evidence Capture Log (Wiz)
- **OBSERVED FACT**: `UNKNOWN / NOT YET VALIDATED`
- **CUSTOMER QUOTE**: `UNKNOWN / NOT YET VALIDATED`
- **CUSTOMER OPINION**: `UNKNOWN / NOT YET VALIDATED`
- **OUR INFERENCE**: `UNKNOWN / NOT YET VALIDATED`
- **OUR ASSUMPTION**: `Hypothesis D: Security containment bots are restricted due to false-positive fears.`

---

### Target 5: Anysphere / Cursor (Candidate Wedge E: Developer Automation)

#### 1. Relevant Buyer Persona
- **Primary Buyer**: Founder / Chief Technology Officer (CTO)
- **Technical Champion**: Lead Security Engineer / MCP Integration Architect

#### 2. Exact Problem Hypothesis to Validate
> **Hypothesis E**: Enterprise CISOs block enterprise-wide adoption of Cursor Agent because local terminal script execution and remote API tool calls lack central policy authorization, identity delegation, and compliance audit logging.

#### 3. Personalized Outreach Message
```text
Subject: Research: Enterprise security policy controls for Cursor Agent & MCP tools

Hi [First Name],

I’m reaching out because of Cursor’s pioneering work in agentic code editing and MCP execution.

We are running a research project investigating how enterprise CISOs evaluate the security risks of AI coding agents executing local shell commands, git operations, and remote MCP tool calls.

While Cursor Agent massively accelerates developer velocity, enterprise security teams often hesitate to grant AI agents local terminal and API write access without central policy controls, identity attribution, and audit logging.

I’d love to get 20 minutes of your perspective on what security features enterprise CISOs require before deploying Cursor Agent across 1,000+ developer seats.

If open next week, I’d be glad to share our open-source benchmarks on Streamable HTTP MCP gateway security.

Best regards,

Priyank Narola
AgentOS Developer Security Research
priyank@agentos.dev
```

#### 4. Primary & Follow-Up Discovery Questions
- **5 Primary Questions**:
  1. What security controls currently prevent Cursor Agent from executing harmful terminal commands or fetching malicious URLs?
  2. What are the primary security objections enterprise CISOs raise when evaluating Cursor Agent deployment?
  3. How do enterprise customers manage policy rules for what Cursor Agent can and cannot modify?
  4. How is developer identity mapped when Cursor Agent calls remote API endpoints via MCP over Streamable HTTP?
  5. What audit telemetry do enterprise security teams require for developer AI agent tool executions?
- **5 Follow-Up Questions**:
  1. *"Would enterprise customers benefit from an unbypassable policy control plane between Cursor and remote MCP servers?"*
  2. *"How do you handle prompt injection attacks originating from untrusted third-party code repositories?"*
  3. *"What performance latency (<2ms vs <10ms) is required to ensure developer workflow velocity remains high?"*
  4. *"Is there a demand for server-side human approval gates when Cursor Agent initiates production deployments?"*
  5. *"Would Cursor be interested in validating Streamable HTTP MCP security standards jointly?"*

#### 5. Evidence Matrix: Strengthening vs. Invalidating
- **Evidence That Strengthens Hypothesis E**:
  - Customer states: *"Fortune 500 CISOs block Cursor sales because they cannot audit or restrict what terminal commands the agent runs."*
  - Customer requests a central enterprise administrative console to set agent tool execution rules.
- **Evidence That Invalidates Hypothesis E**:
  - Customer states: *"Developers run Cursor on local machines; enterprise CISOs treat developer laptops as untrusted sandboxes anyway."*
  - Customer states: *"Cursor Agent will remain strictly a local code editor with no remote enterprise API capabilities."*

#### 6. Buying & Pilot Signals
- **Strong Signal**: Cursor team confirms enterprise deals are blocked by CISO security audits; agrees to co-test AgentOS MCP Streamable HTTP control plane.
- **Medium Signal**: Team interested in MCP security standards discussion; requests copy of latency benchmark report.
- **Weak Signal**: Developer velocity is sole priority; security guardrails seen as low priority.

#### 7. Structured Evidence Capture Log (Cursor)
- **OBSERVED FACT**: `UNKNOWN / NOT YET VALIDATED`
- **CUSTOMER QUOTE**: `UNKNOWN / NOT YET VALIDATED`
- **CUSTOMER OPINION**: `UNKNOWN / NOT YET VALIDATED`
- **OUR INFERENCE**: `UNKNOWN / NOT YET VALIDATED`
- **OUR ASSUMPTION**: `Hypothesis E: Enterprise CISO blocks on Cursor are driven by unmonitored terminal/MCP execution.`

---

## Part 2: Phase 5C Execution Brief & Protocol

### 1. Outreach Sequence & Timeline
1. **Day 1**: Send initial personalized outreach emails to Brex, Datadog, Zendesk, Wiz, and Cursor.
2. **Day 3**: Send follow-up note #1 emphasizing open-source MCP benchmark sharing.
3. **Day 7**: Send final follow-up note #2 with summary of early research findings.
4. **Days 8–15**: Conduct 30-minute discovery interviews as responses are confirmed.

### 2. Interview Objectives & Discovery Golden Rules
- **Objective**: Identify which candidate wedge exhibits the highest pain severity, urgency, and willingness to pay.
- **Golden Rule 1**: **DO NOT PITCH AGENTOS.** Spend 80% of the interview listening and 20% asking open-ended questions.
- **Golden Rule 2**: **NEVER LEAD THE CUSTOMER.** Do not suggest that Finance or SRE is the "correct" area for agent security. Let the customer describe their primary pain point independently.
- **Golden Rule 3**: **NO FABRICATED DATA.** If an interview question is skipped or unvalidated, log it strictly as `UNKNOWN / NOT YET VALIDATED`.

### 3. Strict 5-Bucket Data Classification Rules
Every observation in raw interview notes must be parsed into:
1. `OBSERVED FACT`: Empirical truth (e.g. *"We run 50 microservices on AWS EKS"*).
2. `CUSTOMER QUOTE`: Direct verbatim quote (e.g. *"'Our CISO will not allow AI agents near production'"*).
3. `CUSTOMER OPINION`: Subjective belief or projection (e.g. *"I think we might pay $1,000/mo for this"*).
4. `OUR INFERENCE`: Logical deduction by AgentOS team (e.g. *Inference: Their custom auth code is unmaintainable*).
5. `OUR ASSUMPTION`: Unverified hypothesis requiring testing (e.g. *Assumption: SREs care more about latency than CISOs*).

---

## Part 3: Wedge Validation & Pivot Strategy

### 1. 10-Factor Wedge Scoring System (100 Points Max)
Post-interview, each candidate wedge (A–E) will be scored on a 1–10 scale across 10 dimensions:
1. Pain Severity (10 pts)
2. Frequency of Actions (10 pts)
3. Urgency / Q3 Initiative (10 pts)
4. AI Agent Adoption Level (10 pts)
5. Security Risk / Blast Radius (10 pts)
6. Compliance Mandate Pressure (10 pts)
7. Budget Availability (10 pts)
8. Willingness to Pay (10 pts)
9. Competitive Differentiation (10 pts)
10. Implementation Feasibility (10 pts)

### 2. Pivot Conditions ("What Evidence Would Cause Us to Pivot AgentOS?")
We will **PIVOT** away from the financial wire transfer wedge if:
1. $\ge 3$ of 5 enterprise customers report that financial AI agents are strictly forbidden by corporate governance under all circumstances.
2. SRE or Developer Automation scores $\ge 20\%$ higher than Finance on the 100-point Wedge Scoring Model.
3. Customers state that LLM gateways or API firewalls adequately solve financial prompt risks, but fail completely on infrastructure/IAM actions.

### 3. Continuation Conditions ("What Evidence Would Justify Continuing the Current Strategy?")
We will **CONTINUE** with the Finance/Treasury wedge if:
1. $\ge 3$ of 5 customers report active financial AI payment initiatives blocked by CISO security concerns.
2. Customers express clear willingness to pay ($\ge \$25,000/yr$) for a server-side financial action gateway with payload hashing and separation of duties.
3. Finance/Treasury scores highest among all candidate wedges on the 100-point scoring model.

---

## Part 4: Exact Information Priyank Must Bring Back After Each Interview

After completing each customer interview, Priyank Narola must log the following 10 core facts into `docs/phase5-interview-evidence-template.md`:

1. **Exact Write Actions**: What specific API endpoints or tools do their agents execute?
2. **Highest-Risk Operation**: What single action keeps the CISO/CTO awake at night?
3. **Current Control**: How do they authorize tool calls today (prompts vs gateway vs hardcoded code)?
4. **Failure Impact**: What happens if an agent executes an action with tampered parameters?
5. **Human Approval Gate**: How are human approvals requested and verified?
6. **Identity Attribution**: How is human employee identity linked to agent tool calls?
7. **Latency Tolerance**: What is their hard latency limit (<2ms, <10ms, <50ms)?
8. **Deployment Requirement**: Multi-tenant SaaS vs single-tenant VPC requirement?
9. **Commercial Commitment**: Willingness to run a 30-day sandbox pilot and estimated budget?
10. **Evidence Classification**: All 19 parameters logged into the 5-bucket schema without unverified assumptions.
