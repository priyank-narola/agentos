# AgentOS Phase 5B — First 5 Customer Interview Customized Briefs

**Version**: Phase 5B Interview Briefs v1.0  
**Directive**: These briefs prepare Priyank Narola to conduct the first 5 customer discovery interviews. **Zero customer data, quotes, or pilot commitments are fabricated.** Unverified items are marked `UNKNOWN / NOT YET VALIDATED`.  

---

## Target 1: Brex (Candidate Wedge A: Finance / Treasury)

### Metadata & Context
- **Company**: Brex
- **Target Persona**: CISO / Head of Security / Lead AI Engineer
- **Candidate Wedge**: Finance / Treasury (Automated payments, card limits, ACH wires)
- **Why Strategically Valuable**: High-volume financial automation platform. Validates whether financial wire/payout execution is the highest-urgency wedge.
- **What We Need to Learn**: Do financial AI agents currently initiate real payouts or wire transfers, or are they restricted to read-only reporting due to security concerns?

### Customized Interview Brief
- **30-Minute Interview Structure**:
  - `00:00–03:00`: Research intro (Non-pitch: *"How does Brex govern autonomous AI actions?"*).
  - `03:00–10:00`: Current AI agent tools & financial payment workflows.
  - `10:00–18:00`: High-risk payment initiation, prompt injection fears, and authorization logic.
  - `18:00–25:00`: Separation of duties, human approvals, and payload digest verification.
  - `25:00–30:00`: Latency requirements (<2ms), deployment preferences (SaaS vs VPC), and pilot criteria.
- **5 Priority Questions**:
  1. What financial write/mutation actions are your AI models or internal bots permitted to execute today?
  2. What is the single highest-risk financial tool call an agent could make in your stack?
  3. How do you prevent an AI agent from being manipulated via prompt injection into altering payout amounts or beneficiary accounts?
  4. What human approval steps are required before an AI-initiated payout over $10,000 settles?
  5. How do you map the identity of the human employee who prompted the agent to the resulting financial transaction?
- **5 Follow-Up Questions**:
  1. *"If an agent requested a $50,000 ACH payout, who approves it and via what interface?"*
  2. *"How do you verify that the payment parameters weren't altered after human approval?"*
  3. *"Are your financial APIs exposed as MCP tools to internal AI models?"*
  4. *"What is your acceptable latency budget for real-time security evaluation on API tool calls?"*
  5. *"If a zero-trust financial action gateway existed, would you require single-tenant VPC deployment?"*
- **Specific Workflow to Investigate**: AI-driven accounts payable invoice processing and automated ACH/wire disbursement.
- **Security/Control-Plane Hypothesis**: Brex restricts AI agents from executing payouts >$5,000 without out-of-band human approval and payload digest validation.
- **Buying Signal to Look for**: Expressing active anxiety about AI agent financial fraud + having allocated security/innovation budget.
- **Pilot Signal to Look for**: Willingness to connect `SandboxPaymentProvider` in a Brex staging environment within 30 days.
- **Red Flags**: Customer states that AI models will never be allowed to execute financial actions under any circumstances.
- **Evidence We Must NOT Assume**: *Do NOT assume Brex currently uses MCP or allows autonomous AI wire transfers in production.*

---

## Target 2: Datadog (Candidate Wedge B: IT / SRE Operations)

### Metadata & Context
- **Company**: Datadog
- **Target Persona**: VP Security / Head of Reliability Engineering (SRE) / Bits AI Product Lead
- **Candidate Wedge**: IT / SRE Operations (Automated incident remediation, cloud infrastructure changes)
- **Why Strategically Valuable**: Leaders in AI-assisted observability (Bits AI). Validates whether SRE incident remediation is a stronger wedge than Finance.
- **What We Need to Learn**: Does Bits AI execute write remediation actions (service restarts, cloud config changes), or is it strictly advisory?

### Customized Interview Brief
- **30-Minute Interview Structure**:
  - `00:00–03:00`: Research intro (*"How does Datadog bound the execution permissions of Bits AI?"*).
  - `03:00–10:00`: SRE incident remediation workflows and automation tools.
  - `10:00–18:00`: Blast-radius controls, automated runbook risk scoring, and authorization boundaries.
  - `18:00–25:00`: Human-in-the-loop approvals for production infrastructure changes.
  - `25:00–30:00`: Performance requirements (<1ms latency), SaaS vs VPC preferences, and pilot interest.
- **5 Priority Questions**:
  1. What write/mutation capabilities does Bits AI or your internal SRE bots currently have in cloud environments?
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
- **Specific Workflow to Investigate**: Automated P1 incident triage and infrastructure remediation runbook execution.
- **Security/Control-Plane Hypothesis**: Datadog requires real-time policy gates and human SRE approval before any AI agent can modify production cloud state.
- **Buying Signal to Look for**: SRE leadership expressing concern over AI agents causing unintended production outages during incident response.
- **Pilot Signal to Look for**: Requesting an immediate staging test of AgentOS policy evaluation on Terraform or Kubernetes API tool calls.
- **Red Flags**: Customer states Bits AI is exclusively a read-only chat assistant with zero write execution plans.
- **Evidence We Must NOT Assume**: *Do NOT assume Datadog permits autonomous AI cloud infrastructure modifications without human oversight.*

---

## Target 3: Zendesk (Candidate Wedge C: Customer Operations / CRM)

### Metadata & Context
- **Company**: Zendesk
- **Target Persona**: CISO / VP AI Engineering / Head of Product Security
- **Candidate Wedge**: Customer Operations / CRM (Billing credits, account refunds, CRM mutations)
- **Why Strategically Valuable**: High-volume customer support platform. Validates whether support bot refund fraud is a high-urgency wedge.
- **What We Need to Learn**: How do enterprise customers prevent Zendesk AI agents from being prompt-injected into issuing unauthorized refunds or billing credits?

### Customized Interview Brief
- **30-Minute Interview Structure**:
  - `00:00–03:00`: Research intro (*"How do you govern AI support agents executing billing actions?"*).
  - `03:00–10:00`: Zendesk AI agent capabilities and customer service ticket automation.
  - `10:00–18:00`: Billing credit limits, prompt injection risks, and refund fraud prevention.
  - `18:00–25:00`: Delegation mapping (customer vs agent vs manager) and audit requirements.
  - `25:00–30:00`: Latency budgets, multi-tenant SaaS acceptability, and pilot readiness.
- **5 Priority Questions**:
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
- **Specific Workflow to Investigate**: Automated customer refund processing, subscription upgrades, and credit disbursements.
- **Security/Control-Plane Hypothesis**: Customer support AI agents require dollar-bounded policy rules and human manager approvals for refunds exceeding $100.
- **Buying Signal to Look for**: Customer reporting active financial losses or security concerns due to support bot prompt injection.
- **Pilot Signal to Look for**: Willingness to test AgentOS refund authorization policies against Zendesk API webhooks.
- **Red Flags**: Support agents only answer static FAQs and have zero API integration into billing/CRM systems.
- **Evidence We Must NOT Assume**: *Do NOT assume Zendesk AI agents currently possess unrestricted refund capabilities.*

---

## Target 4: Wiz (Candidate Wedge D: Security / IAM Operations)

### Metadata & Context
- **Company**: Wiz
- **Target Persona**: Chief Technology Officer / VP Security Engineering / Head of Cloud Security
- **Candidate Wedge**: Security / IAM Operations (Automated threat containment, cloud security group modification, IAM role revocation)
- **Why Strategically Valuable**: Leading cloud security platform. Validates whether automated security containment is the top wedge.
- **What We Need to Learn**: When security AI bots detect cloud misconfigurations, do they automatically execute remediation actions or generate recommendations?

### Customized Interview Brief
- **30-Minute Interview Structure**:
  - `00:00–03:00`: Research intro (*"How do you govern automated AI security containment actions?"*).
  - `03:00–10:00`: Cloud security posture automation and AI remediation workflows.
  - `10:00–18:00`: Blast-radius management, false-positive containment risk, and privilege escalation prevention.
  - `18:00–25:00`: Separation of duties for security bots and SOC analyst approval gates.
  - `25:00–30:00`: On-premise/VPC requirements, real-time evaluation latencies, and pilot interest.
- **5 Priority Questions**:
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
- **Specific Workflow to Investigate**: Automated cloud vulnerability remediation, IAM privilege revocation, and security group isolation.
- **Security/Control-Plane Hypothesis**: Automated security bots require server-side policy guardrails to prevent false-positive service disruptions.
- **Buying Signal to Look for**: Security leaders identifying automated remediation false-positives as a primary operational barrier.
- **Pilot Signal to Look for**: Interest in co-testing AgentOS authorization controls on AWS IAM and security group modification actions.
- **Red Flags**: Wiz customers only accept advisory alerts and forbid any automated remediation execution.
- **Evidence We Must NOT Assume**: *Do NOT assume cloud security bots are granted unmonitored administrative permissions in production.*

---

## Target 5: Anysphere / Cursor (Candidate Wedge E: Developer / Engineering Automation)

### Metadata & Context
- **Company**: Anysphere (Cursor)
- **Target Persona**: Founder / CTO / Lead Security Engineer / MCP Integration Architect
- **Candidate Wedge**: Developer / Engineering Automation (Terminal execution, git commits, code mutations, local MCP tool calls)
- **Why Strategically Valuable**: Cursor pioneered agentic code editing and MCP execution. Validates whether developer tool authorization is the top wedge.
- **What We Need to Learn**: How do enterprise security teams evaluate the security risk of Cursor Agent executing local terminal scripts and external API calls?

### Customized Interview Brief
- **30-Minute Interview Structure**:
  - `00:00–03:00`: Research intro (*"How can enterprise security teams safely govern Cursor Agent tool calls?"*).
  - `03:00–10:00`: Cursor Agent capabilities, local terminal execution, and MCP tool integrations.
  - `10:00–18:00`: Enterprise security concerns (unauthorized network calls, malicious scripts, code leakage).
  - `18:00–25:00`: Developer identity mapping, local vs server policy enforcement, and audit trail requirements.
  - `25:00–30:00`: Enterprise feature requests, latency budgets (<5ms), and joint pilot feasibility.
- **5 Priority Questions**:
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
- **Specific Workflow to Investigate**: Cursor Agent executing local shell commands, git operations, and remote MCP tool calls.
- **Security/Control-Plane Hypothesis**: Enterprise CISOs block Cursor Agent adoption unless tool calls can be authorized and audited by a central control plane.
- **Buying Signal to Look for**: Cursor leadership stating enterprise sales are blocked by CISO concerns over unchecked agent execution.
- **Pilot Signal to Look for**: Agreement to test AgentOS MCP Streamable HTTP Gateway as a security extension for Cursor enterprise customers.
- **Red Flags**: Enterprise security teams do not care about local terminal execution safety and treat developers' machines as unmanaged sandboxes.
- **Evidence We Must NOT Assume**: *Do NOT assume enterprise CISOs currently allow unrestricted Cursor Agent execution on production codebases.*
