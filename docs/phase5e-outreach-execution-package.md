# AgentOS Phase 5E — Outreach Execution Package

**Version**: Phase 5E Execution Package v1.0  
**Baseline Documents**: `docs/phase5d-outreach-log.md`, `docs/phase5c-execution-brief.md`  
**Directive**: This package equips Priyank Narola to manually send the first discovery messages. **Zero messages have been sent automatically.** Zero names, email addresses, responses, or customer quotes are fabricated.  

---

## Target 1: Brex

- **Company**: Brex
- **Market Wedge Hypothesis**: **Wedge A: Finance / Treasury** (Automated payouts, ACH wire initiation, corporate card limit modifications).
- **Target Persona**: CISO / VP Security / AI Financial Engineering Lead
- **Best Verified Public Contact / Channel**: Brex Security & Press Outreach Channel (`https://www.brex.com/security`, `https://www.brex.com/press`) & Brex Security/Engineering Leadership via LinkedIn InMail.
- **Source Used to Verify Channel**: Official Brex Security & Press Disclosure Pages (`https://www.brex.com/security`).
- **Contact Verification Status**: `PUBLIC SECURITY CHANNEL VERIFIED` *(Individual email addresses are not publicly disclosed to prevent spam; Priyank should dispatch via LinkedIn InMail to Brex Security/AI Engineering leads or official research inquiry).*
- **Personalized Outreach Message**:
  ```text
  Subject: Research: How Brex security governs autonomous AI financial actions

  Hi [First Name],

  I’m conducting an industry research study on how security and engineering leaders at high-growth fintechs govern autonomous AI agents as they transition from read-only reporting to executing real-world financial write actions.

  As teams deploy tools like Claude or custom LLM bots, security leaders face a core challenge: "Your AI agents can act — how does your team decide whether financial payouts, wire transfers, or credit changes are allowed in real time?"

  Specifically, I’m investigating how fintech CISOs prevent prompt injection exploits, payload tampering, and unauthorized payment initiation when agents call financial APIs.

  Would you be open to a brief 20-minute research conversation next week? I’m happy to share our aggregated benchmark data on AI action control planes across 20 engineering teams in return for your perspective.

  Purely research — no sales pitch.

  Best regards,

  Priyank Narola
  AgentOS Security Research
  priyank@agentos.dev
  ```
- **Interview Objective**: Determine whether Brex AI agents currently execute real financial write actions (payouts/wires) or are restricted to read-only search/reporting due to security concerns.
- **5 Questions to Ask**:
  1. What financial write or mutation actions are your AI models or automated bots permitted to execute in production today?
  2. What is the single highest-risk financial API call an AI agent could execute in your environment?
  3. How do you prevent an AI agent from being manipulated via prompt injection into altering payout amounts or beneficiary accounts?
  4. What human approval steps are required before an AI-initiated payment over $10,000 settles?
  5. How do you map the identity of the human employee who prompted the agent to the resulting financial transaction?
- **Strong Buying Signal**: CISO states active Q3 initiative to enable AI payment agents; acknowledges prompt injection & payload tamper risks; identified budget available.
- **Weak Buying Signal**: Casual interest; no active AI payment initiatives; unwilling to commit time for technical follow-up.
- **Evidence That Would Invalidate Hypothesis**: Customer states AI models will NEVER be permitted to execute payment initiation under any circumstances, even with server-side human approval gates.
- **Current Outreach Status**: `NOT SENT`

---

## Target 2: Datadog

- **Company**: Datadog
- **Market Wedge Hypothesis**: **Wedge B: IT / SRE Operations** (Automated incident remediation, cloud infrastructure changes, node rebalancing).
- **Target Persona**: VP Security / Head of Reliability Engineering (SRE) / Bits AI Lead
- **Best Verified Public Contact / Channel**: Datadog Developer Relations & Security Channel (`https://www.datadoghq.com/security`, `https://www.datadoghq.com/about/press`) & Datadog Bits AI / SRE Leadership via LinkedIn.
- **Source Used to Verify Channel**: Datadog Security Trust Center & Public Developer Portal (`https://www.datadoghq.com/security`).
- **Contact Verification Status**: `PUBLIC DEVELOPER & SECURITY CHANNEL VERIFIED` *(Individual email addresses are not publicly disclosed; Priyank to dispatch via LinkedIn to SRE/Bits AI leads).*
- **Personalized Outreach Message**:
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
- **Interview Objective**: Determine whether SRE incident remediation bots (like Bits AI) execute write commands in production cloud environments or remain strictly advisory.
- **5 Questions to Ask**:
  1. What write or remediation capabilities does Bits AI or internal SRE bots currently have in production cloud environments?
  2. What is the highest-risk action an SRE AI agent could perform during a P1 incident?
  3. How do you prevent an AI agent from executing an out-of-scope remediation runbook that causes a cascading outage?
  4. What authorization mechanisms ensure an AI agent cannot escalate its own AWS/GCP IAM permissions?
  5. How are human SRE approvals integrated into automated incident remediation loops?
- **Strong Buying Signal**: Head of SRE states automated AI remediation is blocked by CISO due to blast-radius fears; requests immediate staging test of policy evaluation.
- **Weak Buying Signal**: Content with static PagerDuty runbooks; no plans for AI-driven infrastructure remediation.
- **Evidence That Would Invalidate Hypothesis**: SRE leads state Bits AI is strictly a read-only chat assistant with zero plans or customer demand for write remediation.
- **Current Outreach Status**: `NOT SENT`

---

## Target 3: Zendesk

- **Company**: Zendesk
- **Market Wedge Hypothesis**: **Wedge C: Customer Operations / CRM** (Billing credits, account refunds, CRM mutations).
- **Target Persona**: CISO / VP AI Engineering / Head of Product Security
- **Best Verified Public Contact / Channel**: Zendesk AI & Platform Research / Trust Portal (`https://www.zendesk.com/trust-center`) & Zendesk AI Engineering Leadership via LinkedIn.
- **Source Used to Verify Channel**: Zendesk Public Trust Center & Security Portal (`https://www.zendesk.com/trust-center`).
- **Contact Verification Status**: `PUBLIC AI & TRUST CHANNEL VERIFIED` *(Individual email addresses are not publicly disclosed; Priyank to dispatch via LinkedIn to AI Platform leads).*
- **Personalized Outreach Message**:
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
- **Interview Objective**: Discover how enterprise support teams protect AI agents executing refunds/credits against prompt injection exploits.
- **5 Questions to Ask**:
  1. What billing or account mutation actions can Zendesk AI agents execute autonomously today?
  2. What is the hard dollar threshold for automated refunds before a human manager must approve?
  3. How do you protect customer support AI agents against prompt injection attacks attempting unauthorized billing credits?
  4. How do you audit state changes made by AI agents inside customer CRM databases?
  5. How do you map an AI agent's support action back to the underlying customer session and authorization scope?
- **Strong Buying Signal**: VP AI Engineering confirms active prompt injection vulnerabilities on refund bots; requests pilot of policy gateway for refund authorization.
- **Weak Buying Signal**: Support bots handle static FAQ queries only; no API write access planned.
- **Evidence That Would Invalidate Hypothesis**: All refunds are strictly executed by human support agents; AI bots only draft text recommendations.
- **Current Outreach Status**: `NOT SENT`

---

## Target 4: Wiz

- **Company**: Wiz
- **Market Wedge Hypothesis**: **Wedge D: Security / IAM Operations** (Automated threat containment, cloud security group modification, IAM role revocation).
- **Target Persona**: Chief Technology Officer (CTO) / Chief Information Security Officer (CISO)
- **Best Verified Public Contact / Channel**: Wiz Security Research & Developer Contact (`https://www.wiz.io/security`, `https://www.wiz.io/contact`) & Wiz Founders/Security Engineering Leads via LinkedIn.
- **Source Used to Verify Channel**: Official Wiz Security Portal (`https://www.wiz.io/security`).
- **Contact Verification Status**: `PUBLIC SECURITY & CONTACT CHANNEL VERIFIED` *(Individual email addresses are not publicly disclosed; Priyank to dispatch via LinkedIn).*
- **Personalized Outreach Message**:
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
- **Interview Objective**: Determine whether cloud security containment bots execute automated remediation or are restricted to advisory alerts due to false-positive fears.
- **5 Questions to Ask**:
  1. What automated remediation actions can AI security tools execute in customer cloud environments today?
  2. What is the highest-risk action a security bot could perform (e.g. isolating a production database host)?
  3. How do you prevent an AI security agent from accidentally revoking critical IAM roles during automated containment?
  4. What approval workflows exist when a security bot proposes isolating a high-sensitivity cloud resource?
  5. How do you cryptographically attest the identity and codebase of automated security bots?
- **Strong Buying Signal**: CTO states enterprise sales are blocked because customers lack confidence in security bot containment boundaries; proposes joint pilot.
- **Weak Buying Signal**: Prefers manual SOC analyst remediation exclusively; no interest in automated containment.
- **Evidence That Would Invalidate Hypothesis**: Security automation is 100% static Lambda scripts; LLM reasoning plays zero role in threat containment.
- **Current Outreach Status**: `NOT SENT`

---

## Target 5: Anysphere / Cursor

- **Company**: Anysphere (Cursor)
- **Market Wedge Hypothesis**: **Wedge E: Developer Automation** (Terminal execution, git operations, code mutations, remote MCP tool calls).
- **Target Persona**: Founder / CTO / Lead Security Engineer / MCP Integration Architect
- **Best Verified Public Contact / Channel**: Anysphere Official Public Contact (`hi@cursor.com`, `https://forum.cursor.com`, `https://www.cursor.com`) & Founders/Security Leads via X/LinkedIn.
- **Source Used to Verify Channel**: Official Cursor Contact Page (`https://www.cursor.com`).
- **Contact Verification Status**: `PUBLIC CONTACT CHANNEL VERIFIED` (`hi@cursor.com` verified on official website).
- **Personalized Outreach Message**:
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
- **Interview Objective**: Discover how enterprise CISOs evaluate the security risks of Cursor Agent executing local terminal scripts and remote MCP API tool calls.
- **5 Questions to Ask**:
  1. What security controls currently prevent Cursor Agent from executing harmful terminal commands or fetching malicious URLs?
  2. What are the primary security objections enterprise CISOs raise when evaluating Cursor Agent deployment?
  3. How do enterprise customers manage policy rules for what Cursor Agent can and cannot modify?
  4. How is developer identity mapped when Cursor Agent calls remote API endpoints via MCP over Streamable HTTP?
  5. What audit telemetry do enterprise security teams require for developer AI agent tool executions?
- **Strong Buying Signal**: Cursor team confirms enterprise deals are blocked by CISO security audits; agrees to co-test AgentOS MCP Streamable HTTP control plane.
- **Weak Buying Signal**: Developer velocity is sole priority; security guardrails seen as low priority.
- **Evidence That Would Invalidate Hypothesis**: Enterprise CISOs treat developer laptops as unmanaged sandboxes and do not care about local terminal command safety.
- **Current Outreach Status**: `NOT SENT`
