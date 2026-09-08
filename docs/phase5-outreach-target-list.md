# AgentOS Phase 5A — Outreach Target List (20 Potential Enterprise Candidates)

**Status**: DISCOVERY OUTREACH TARGET LIST  
**Baseline**: Phase 5 Customer Discovery Plan  
**Directive**: All target entries rely on publicly verifiable evidence and explicit hypotheses. **No internal architecture, customer quotes, or AI maturity details are invented.**  

---

## Candidate Wedge A: Finance / Treasury

### Target 1: Brex
- **Company**: Brex
- **Industry**: Corporate Cards, Spend Management & Business Banking (Fintech)
- **Approximate Size**: ~1,200 employees
- **Likely AI-Agent Maturity**: High (Publicly blogged about internal LLM agents for receipt matching, expense categorization, and spend insights).
- **Likely High-Risk Agent Actions**: Automated payment disbursement, credit limit adjustments, vendor bill payments, ACH transfer initiation.
- **Relevant Persona to Contact**: Head of Security / CISO, VP Engineering, Lead AI Engineer.
- **Likely Buyer**: CISO / VP Engineering.
- **Why Relevant**: High-volume financial transactions driven by AI automation; high blast radius if an agent misallocates corporate funds.
- **Candidate Wedge**: Finance / Treasury
- **Publicly Verifiable Evidence**: Brex Tech Blog posts on building internal LLM agents for financial workflows (2024–2025).
- **Outreach Priority**: **P1**

### Target 2: Ramp
- **Company**: Ramp
- **Industry**: Financial Operations & Expense Management (Fintech)
- **Approximate Size**: ~1,000 employees
- **Likely AI-Agent Maturity**: High (Publicly announced AI-powered vendor management, invoice parsing, and procurement workflows).
- **Likely High-Risk Agent Actions**: Purchase order approval, invoice payout execution, card limit modifications.
- **Relevant Persona to Contact**: Head of Information Security, VP Product Engineering, Lead AI Engineer.
- **Likely Buyer**: CISO / VP Engineering.
- **Why Relevant**: Ramp automates accounts payable and procurement; AI agents acting on invoices need strict payload & approval guardrails.
- **Candidate Wedge**: Finance / Treasury
- **Publicly Verifiable Evidence**: Ramp Product Releases & Engineering publications detailing AI-assisted procurement and AP automation.
- **Outreach Priority**: **P1**

### Target 3: Mercury
- **Company**: Mercury
- **Industry**: Banking for Startups & Enterprise Treasury (Fintech)
- **Approximate Size**: ~700 employees
- **Likely AI-Agent Maturity**: Moderate-High (Exploring AI automation for treasury management, wire transfer workflows, and customer verification).
- **Likely High-Risk Agent Actions**: Synthetic wire transfer initiation, internal account transfers, beneficiary management.
- **Relevant Persona to Contact**: Chief Information Security Officer, Head of Risk & Compliance, VP Engineering.
- **Likely Buyer**: CISO / Head of Treasury Tech.
- **Why Relevant**: Handles high-value corporate treasury wires where unauthorized AI wire execution represents catastrophic loss.
- **Candidate Wedge**: Finance / Treasury
- **Publicly Verifiable Evidence**: Mercury Engineering & Security public presentations on automated banking rails.
- **Outreach Priority**: **P1**

### Target 4: Invoice2go (a Bill.com company)
- **Company**: Bill.com / Invoice2go
- **Industry**: Accounts Payable & Receivable Automation
- **Approximate Size**: ~2,500 employees (Bill.com total)
- **Likely AI-Agent Maturity**: Moderate (Integrating generative AI for automated invoice extraction and payment scheduling).
- **Likely High-Risk Agent Actions**: ACH payment execution, vendor account detail updates, payment hold releases.
- **Relevant Persona to Contact**: Director of Security Engineering, VP Product Architecture.
- **Likely Buyer**: CISO / VP Engineering.
- **Why Relevant**: AP automation involves high-frequency payment scheduling where prompt injection could lead to fraudulent payout routing.
- **Candidate Wedge**: Finance / Treasury
- **Publicly Verifiable Evidence**: Bill.com Investor Presentations highlighting AI/ML automation in payment processing.
- **Outreach Priority**: **P2**

---

## Candidate Wedge B: IT / SRE Operations

### Target 5: Datadog
- **Company**: Datadog
- **Industry**: Cloud Monitoring & Observability SaaS
- **Approximate Size**: ~5,500 employees
- **Likely AI-Agent Maturity**: High (Publicly launched Bits AI assistant for automated incident investigation and remediation).
- **Likely High-Risk Agent Actions**: Triggering automated incident remediation scripts, restarting production services, modifying alert routing rules.
- **Relevant Persona to Contact**: VP Security / CISO, Head of Reliability Engineering (SRE), AI Product Lead.
- **Likely Buyer**: CISO / VP Infrastructure.
- **Why Relevant**: SRE AI agents with remediation capabilities can inadvertently degrade or shut down infrastructure if actions are unchecked.
- **Candidate Wedge**: IT / SRE Operations
- **Publicly Verifiable Evidence**: Datadog Bits AI announcement & technical documentation (2024–2025).
- **Outreach Priority**: **P1**

### Target 6: PagerDuty
- **Company**: PagerDuty
- **Industry**: Digital Operations & Incident Response Management
- **Approximate Size**: ~1,100 employees
- **Likely AI-Agent Maturity**: High (Publicly announced PagerDuty Advance AI for automated incident triage and remediation runbooks).
- **Likely High-Risk Agent Actions**: Executing automated runbooks, granting emergency access during incidents, modifying escalation policies.
- **Relevant Persona to Contact**: CISO, Chief Technology Officer, VP Infrastructure & Operations.
- **Likely Buyer**: CISO / VP Operations.
- **Why Relevant**: Incident automation agents possess elevated access to execute remediation runbooks on production clusters.
- **Candidate Wedge**: IT / SRE Operations
- **Publicly Verifiable Evidence**: PagerDuty Advance AI product overview & technical press releases.
- **Outreach Priority**: **P1**

### Target 7: HashiCorp (IBM)
- **Company**: HashiCorp
- **Industry**: Infrastructure-as-Code & Cloud Security (Terraform, Vault)
- **Approximate Size**: ~2,500 employees
- **Likely AI-Agent Maturity**: High (AI generation of Terraform HCL configurations, cloud infrastructure provisioning bots).
- **Likely High-Risk Agent Actions**: Executing `terraform apply`, modifying Vault secret access policies, altering cloud security groups.
- **Relevant Persona to Contact**: VP Security Engineering, Head of Developer Platform, Lead SRE Architect.
- **Likely Buyer**: CISO / VP Platform Engineering.
- **Why Relevant**: Automated `terraform apply` by AI agents can modify production cloud architecture or expose storage buckets.
- **Candidate Wedge**: IT / SRE Operations
- **Publicly Verifiable Evidence**: HashiCorp Developer documentation on AI-assisted IaC tools and Terraform integrations.
- **Outreach Priority**: **P1**

### Target 8: Dynatrace
- **Company**: Dynatrace
- **Industry**: Enterprise Cloud Observability & Security
- **Approximate Size**: ~4,200 employees
- **Likely AI-Agent Maturity**: High (Davis AI copilot executing automated causal analysis and remediation workflow triggers).
- **Likely High-Risk Agent Actions**: Auto-rebalancing cloud nodes, invoking serverless functions, triggering auto-rollback deployments.
- **Relevant Persona to Contact**: Chief Security Officer, VP Engineering Infrastructure.
- **Likely Buyer**: CSO / VP SRE.
- **Why Relevant**: Autonomous cloud infrastructure remediation requires server-side policy controls to bound execution scope.
- **Candidate Wedge**: IT / SRE Operations
- **Publicly Verifiable Evidence**: Dynatrace Davis AI documentation and technical whitepapers.
- **Outreach Priority**: **P2**

---

## Candidate Wedge C: Customer Operations / CRM

### Target 9: Zendesk
- **Company**: Zendesk
- **Industry**: Customer Service & CRM Software
- **Approximate Size**: ~6,000 employees
- **Likely AI-Agent Maturity**: High (Publicly launched Zendesk AI agents for automated customer resolution, refunds, and ticket actions).
- **Likely High-Risk Agent Actions**: Issuing billing credits/refunds, modifying customer account subscriptions, executing account cancellations.
- **Relevant Persona to Contact**: Chief Information Security Officer, VP AI Engineering, Head of Product Security.
- **Likely Buyer**: CISO / VP Product Engineering.
- **Why Relevant**: Millions of customer support tickets handled by AI agents; financial & privacy risks if support bots are prompt-injected into granting unauthorized refunds.
- **Candidate Wedge**: Customer Operations / CRM
- **Publicly Verifiable Evidence**: Zendesk AI product suite announcements & enterprise security documentation.
- **Outreach Priority**: **P1**

### Target 10: Intercom
- **Company**: Intercom
- **Industry**: AI Customer Service Platform
- **Approximate Size**: ~1,000 employees
- **Likely AI-Agent Maturity**: High (Fin AI Agent handling autonomous customer support resolutions via internal API actions).
- **Likely High-Risk Agent Actions**: Executing API webhooks, updating customer subscription tiers, modifying CRM data fields.
- **Relevant Persona to Contact**: Chief Security Officer, VP Engineering, Lead Fin AI Architect.
- **Likely Buyer**: CSO / VP Engineering.
- **Why Relevant**: Fin AI agent interacts directly with third-party customer APIs; policy governance is critical to prevent malicious prompt manipulation.
- **Candidate Wedge**: Customer Operations / CRM
- **Publicly Verifiable Evidence**: Intercom Fin AI product documentation and technical API integration guides.
- **Outreach Priority**: **P1**

### Target 11: Freshworks
- **Company**: Freshworks
- **Industry**: Business Software & Customer Engagement
- **Approximate Size**: ~5,000 employees
- **Likely AI-Agent Maturity**: Moderate-High (Freddy AI agents executing customer service and IT service desk ticket workflows).
- **Likely High-Risk Agent Actions**: Initiating return labels, applying promotional discount codes, modifying user contact data.
- **Relevant Persona to Contact**: Chief Information Security Officer, Head of Platform Security, VP AI.
- **Likely Buyer**: CISO / Head of AI Platform.
- **Why Relevant**: Broad customer base using AI agents to update CRM records; policy boundaries prevent unauthorized state mutations.
- **Candidate Wedge**: Customer Operations / CRM
- **Publicly Verifiable Evidence**: Freshworks Freddy AI product announcements and developer documentation.
- **Outreach Priority**: **P2**

### Target 12: Gorgias
- **Company**: Gorgias
- **Industry**: E-Commerce Customer Support Automation
- **Approximate Size**: ~300 employees
- **Likely AI-Agent Maturity**: High (Deep Shopify integration allowing AI agents to issue refunds, edit orders, and cancel shipments).
- **Likely High-Risk Agent Actions**: Issuing Shopify order refunds, editing shipping addresses, canceling pending orders.
- **Relevant Persona to Contact**: Head of Security, Chief Technology Officer, Lead Product Manager.
- **Likely Buyer**: CTO / Head of Security.
- **Why Relevant**: AI agents have direct access to write actions in Shopify stores; unauthorized refunds cause immediate financial loss.
- **Candidate Wedge**: Customer Operations / CRM
- **Publicly Verifiable Evidence**: Gorgias AI Agent features for Shopify order management.
- **Outreach Priority**: **P2**

---

## Candidate Wedge D: Security / IAM Operations

### Target 13: Okta
- **Company**: Okta
- **Industry**: Enterprise Identity & Access Management (IAM)
- **Approximate Size**: ~6,000 employees
- **Likely AI-Agent Maturity**: High (Publicly developing AI assistants for identity administration, access reviews, and policy recommendations).
- **Likely High-Risk Agent Actions**: Provisioning user access, revoking MFA tokens, granting administrative role privileges.
- **Relevant Persona to Contact**: Chief Information Security Officer, VP Identity Architecture, Head of Product Security.
- **Likely Buyer**: CISO / VP Identity.
- **Why Relevant**: Identity systems are the highest-risk enterprise control point; AI agents modifying IAM roles require strict separation of duties.
- **Candidate Wedge**: Security / IAM Operations
- **Publicly Verifiable Evidence**: Okta Identity Threat Protection and AI strategy technical keynotes.
- **Outreach Priority**: **P1**

### Target 14: Wiz
- **Company**: Wiz
- **Industry**: Cloud Security Posture Management & SOC Automation
- **Approximate Size**: ~1,500 employees
- **Likely AI-Agent Maturity**: High (AI-driven cloud threat detection and automated remediation suggestions).
- **Likely High-Risk Agent Actions**: Modifying cloud security group rules, isolating virtual machines, revoking IAM credentials.
- **Relevant Persona to Contact**: Chief Technology Officer, VP Security Engineering, Head of Cloud Security.
- **Likely Buyer**: CISO / VP Security Engineering.
- **Why Relevant**: Automated cloud security remediation agents can cause unintended downtime if false positives trigger resource isolation.
- **Candidate Wedge**: Security / IAM Operations
- **Publicly Verifiable Evidence**: Wiz Cloud Security documentation and AI-assisted remediation features.
- **Outreach Priority**: **P1**

### Target 15: CrowdStrike
- **Company**: CrowdStrike
- **Industry**: Cybersecurity & Endpoint Detection and Response (EDR)
- **Approximate Size**: ~8,000 employees
- **Likely AI-Agent Maturity**: High (Charlotte AI security assistant executing threat hunting, containment, and incident response).
- **Likely High-Risk Agent Actions**: Network isolation of critical domain controllers, terminating system processes, revoking API keys.
- **Relevant Persona to Contact**: Chief Security Officer, VP Product Architecture, Charlotte AI Engineering Lead.
- **Likely Buyer**: CSO / VP Product Security.
- **Why Relevant**: Charlotte AI executes security containment actions; controlling blast radius and human approvals is essential.
- **Candidate Wedge**: Security / IAM Operations
- **Publicly Verifiable Evidence**: CrowdStrike Charlotte AI documentation and technical threat hunting demonstrations.
- **Outreach Priority**: **P1**

### Target 16: Ping Identity
- **Company**: Ping Identity
- **Industry**: Enterprise Identity Security & Access Governance
- **Approximate Size**: ~1,500 employees
- **Likely AI-Agent Maturity**: Moderate (AI-assisted access governance and identity orchestration workflows).
- **Likely High-Risk Agent Actions**: Modifying OAuth scope grants, updating SSO routing rules, resetting privileged accounts.
- **Relevant Persona to Contact**: CISO, Chief Architect, VP Identity Governance.
- **Likely Buyer**: CISO / VP Identity.
- **Why Relevant**: Managing access grants for both human employees and AI agents requires delegated authorization frameworks.
- **Candidate Wedge**: Security / IAM Operations
- **Publicly Verifiable Evidence**: Ping Identity Orchestration documentation.
- **Outreach Priority**: **P3**

---

## Candidate Wedge E: Developer / Engineering Automation

### Target 17: Anysphere (Cursor)
- **Company**: Anysphere (Cursor)
- **Industry**: AI-First Code Editor & Developer Automation
- **Approximate Size**: ~50 employees
- **Likely AI-Agent Maturity**: Very High (Cursor Agent executes local shell commands, git operations, and code mutations).
- **Likely High-Risk Agent Actions**: Executing terminal scripts (`rm -rf`, network fetches), committing code, running local build binaries.
- **Relevant Persona to Contact**: Founder / CTO, Lead Security Engineer, MCP Integration Lead.
- **Likely Buyer**: CTO / Head of Engineering.
- **Why Relevant**: Cursor is an primary pioneer of MCP tool execution; securing local terminal and API tool calls is a core enterprise requirement.
- **Candidate Wedge**: Developer / Engineering Automation
- **Publicly Verifiable Evidence**: Cursor product release notes and MCP implementation documentation.
- **Outreach Priority**: **P1**

### Target 18: GitHub (Microsoft)
- **Company**: GitHub
- **Industry**: Developer Platform & AI Coding (Copilot Workspace)
- **Approximate Size**: ~3,000 employees
- **Likely AI-Agent Maturity**: Very High (GitHub Copilot Workspace & Copilot Extensions executing code modifications and PR creation).
- **Likely High-Risk Agent Actions**: Merging pull requests, modifying CI/CD secret variables, deploying release tags.
- **Relevant Persona to Contact**: VP Security Engineering, Lead Copilot Architect, Head of Product Security.
- **Likely Buyer**: CISO / VP Developer Experience.
- **Why Relevant**: Autonomous coding agents creating and merging pull requests require pre-execution policy gates and payload checks.
- **Candidate Wedge**: Developer / Engineering Automation
- **Publicly Verifiable Evidence**: GitHub Copilot Workspace technical previews and Copilot Extensions documentation.
- **Outreach Priority**: **P1**

### Target 19: GitLab
- **Company**: GitLab
- **Industry**: DevOps & DevSecOps Enterprise Platform
- **Approximate Size**: ~2,200 employees
- **Likely AI-Agent Maturity**: High (GitLab Duo AI agents executing pipeline troubleshooting, code generation, and vulnerability resolution).
- **Likely High-Risk Agent Actions**: Auto-applying vulnerability patches, triggering production deployment pipelines, altering repository access settings.
- **Relevant Persona to Contact**: VP Security, Head of AI Engineering, Chief Product Officer.
- **Likely Buyer**: CISO / VP DevOps.
- **Why Relevant**: DevSecOps platform integrating AI agents across the software delivery lifecycle; action policy controls prevent pipeline tampering.
- **Candidate Wedge**: Developer / Engineering Automation
- **Publicly Verifiable Evidence**: GitLab Duo documentation and DevSecOps AI roadmap.
- **Outreach Priority**: **P2**

### Target 20: Replit
- **Company**: Replit
- **Industry**: Cloud Development Environment & AI Coding Agent
- **Approximate Size**: ~150 employees
- **Likely AI-Agent Maturity**: Very High (Replit Agent building, testing, and deploying full-stack web applications autonomously).
- **Likely High-Risk Agent Actions**: Provisioning cloud databases, deploying public domain endpoints, managing environment variables.
- **Relevant Persona to Contact**: Head of Security, Chief Technology Officer, Lead Agent Architect.
- **Likely Buyer**: CTO / Head of Security.
- **Why Relevant**: Replit Agent autonomously provisions cloud resources and deploys code; securing execution boundaries is a foundational requirement.
- **Candidate Wedge**: Developer / Engineering Automation
- **Publicly Verifiable Evidence**: Replit Agent product launch and technical documentation.
- **Outreach Priority**: **P2**
