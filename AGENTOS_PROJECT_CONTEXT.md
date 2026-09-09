<!--
STATUS: HISTORICAL / LEGACY — 8 September 2026
This document records the ORIGINAL Prompt2Product Challenge 2026 competition context.
It is retained for history and MUST NOT be used as the source of truth for current or
future work. Its statements predate the verified governance pipeline, the financial
control-plane direction, and the REST authentication gap.
Canonical references: AGENTOS_OPERATING_PROMPT.md (operating constitution) and
AGENTOS_STATE.md (current state lock). Verified Git checkpoint: a8d6ddf.
-->

# AgentOS --- Project Context [LEGACY / HISTORICAL]

## Prompt2Product Challenge 2026

### 1. Competition Mission

We are participating individually in the Prompt2Product Challenge 2026
by Parul University's Centre for Distance and Online Education.

Official challenge: - 36-hour non-stop AI-assisted product development
challenge. - Development window: 22 August 2026, 12:00 PM to 23 August
2026, 11:59 PM. - Final submission deadline: 23 August 2026, 11:59 PM. -
The official challenge asks participants to conceptualize, design,
develop and present a real working AI-powered software solution. -
AI-assisted development, prompt engineering, real-world problem solving,
and an industry-ready project are explicit objectives. - AI tools,
open-source libraries and public APIs are allowed. - Work must be
original; plagiarism leads to disqualification. - Participation is
individual.

### 2. Official Evaluation --- 100 Marks

Our product must be designed around these criteria: - Innovation &
Creativity: 20 - Problem Identification & Design: 20 - Technical
Implementation: 20 - Functionality & Completeness: 15 - Effective Use of
AI & Prompting: 15 - UI & UX: 10

Target strategy: optimize every engineering and product decision against
these six dimensions.

### 3. Required Submission

Official PPT specifies: - Full name, enrollment number, programme and
semester - Project title and problem statement - Project description:
150--300 words - Live project link - Demo video: maximum 5 minutes - AI
tools used + prompt engineering summary - Originality declaration

The mentor's separate instructions also mention preparing GitHub, AI
prompt history/journey, LinkedIn URL and other evidence. Keep all of
these ready.

### 4. Current Product Thesis

Working product name: AgentOS

Working category: Runtime Trust Infrastructure for Autonomous AI Agents

Core thesis: As AI agents become capable of accessing enterprise data,
calling tools, modifying systems, spending money and delegating tasks,
organizations need a vendor-neutral layer that can verify agent identity
and delegated authority, evaluate an exact action against policy and
contextual risk, allow/block/escalate the action, and maintain an
auditable record.

### 5. Hackathon MVP

Do NOT attempt to build a complete enterprise AgentOS in 36 hours.

Build: AgentOS --- Autonomous Action Firewall

Core flow: AI Agent → Action Request → AgentOS → Identity Check →
Delegated Authority Check → Policy Check → Risk Assessment → ALLOW /
BLOCK / HUMAN APPROVAL → Execute → Audit Trail

### 6. Killer Demonstration

Use a small simulated environment: Agents: - SalesAgent - FinanceAgent -
ResearchAgent

Tools/actions: - CRM read/update - Email send - Invoice read/create -
Refund - Bank transfer - Sensitive database read - Delete record

Primary demo: FinanceAgent requests an \$18,000 bank transfer. Policy
allows autonomous transfers only up to \$5,000. AgentOS evaluates
identity, authority, policy and risk. Decision: BLOCK or HUMAN APPROVAL.
After one-time approval, execute and record the complete audit trail.

Secondary demos: - SalesAgent reading CRM → ALLOW - SalesAgent
attempting bank transfer → BLOCK - ResearchAgent requesting payroll data
→ BLOCK - Malicious/untrusted content attempting to cause customer-data
export → resulting action independently evaluated and blocked

### 7. Product Principles

-   Security decisions must not live only in the UI.
-   Never trust model output as authorization.
-   Enforce authorization server-side.
-   Least privilege by default.
-   Preserve human identity, agent identity and delegated authority
    separately.
-   Every high-impact action must be explainable.
-   Prefer secure defaults.
-   Never hardcode secrets.
-   Never bypass authorization to make a demo work.
-   Do not silently invent major product behavior.
-   Keep the MVP small enough to finish and polish.

### 8. Long-Term Startup Vision

The hackathon objective is to win the competition with a strong MVP. The
later business objective is to evolve the product toward global
infrastructure for autonomous software.

Possible evolution: Action Firewall → Runtime Authorization → Agent
Identity → Delegated Authority Engine → Agent Identity Graph → Agent
Trust Fabric

Do NOT implement the long-term platform now unless it directly
strengthens the MVP.

### 9. AI Development Workflow

Primary coding agent: Claude Code with Claude Opus 4.8.

ChatGPT role: - product strategy - research - architecture review -
prompt design - QA - security test design - debugging guidance -
documentation - competition strategy

Optional: - Cursor for IDE-based review/UI iteration - v0 for UI
exploration only

Every important AI iteration must be preserved for the prompt journey.

### 10. Prompt Journey

Maintain: P001 Master/architecture P002 Database P003 Agent Registry
P004 Tool Registry P005 Permissions P006 Policy Engine P007 Runtime
Gateway P008 Risk Engine P009 Human Approval P010 Audit P011 Dashboard
P012 Agent Simulator P013 Security Tests P014 UX Polish P015 Deployment
P016 Final QA

Each record should include: - Prompt ID - Objective - AI tool/model -
Prompt - Output - Problem discovered - Iteration - Final result

### 11. Suggested Architecture

Frontend: - Next.js - TypeScript - Tailwind - shadcn/ui

Backend: - FastAPI - Python

Database: - PostgreSQL

Initial policy implementation: - Explicit Python/JSON rules - Keep a
future path to OPA/Rego-style policy-as-code

Interfaces: - REST - MCP-oriented integration where useful

Deployment target: - Vercel frontend - Render backend - PostgreSQL

### 12. Engineering Priority

P0: - Core action decision pipeline - Policy enforcement - Working
demo - Audit trail - Stable UI

P1: - Agent registry - Tool registry - Risk scoring - Human approval

P2: - Extra polish and supporting views

Do not sacrifice P0 for P2.

### 13. Competition Positioning

Do not claim that no one is solving agent security/governance. The
market already contains serious work in agent control planes, identity,
runtime authorization, AI gateways and network security.

Our differentiation hypothesis: A vendor-neutral, action-centric runtime
trust/delegated-authority layer across heterogeneous agents and tools.

This hypothesis must be tested against competitors before final
positioning.

### 14. Claude's Role

Act as: - Senior Staff Engineer - Security Architect - Full-Stack
Engineer - Test Engineer

But do not act as the final product owner. Product scope and strategic
decisions remain controlled by the user + ChatGPT.

### 15. Definition of Done

The MVP is done when: - A user can register/view agents - Tools/actions
can be represented - Policies can be represented - An agent action can
be intercepted - The system makes an explicit allow/block/approval
decision - The decision is enforced server-side - Human approval works
for the main scenario - Audit evidence is visible - Security test cases
pass - The main demo is stable - The application is deployable - Prompt
journey evidence is preserved
