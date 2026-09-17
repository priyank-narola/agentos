# Product Strategy and Market Research Master Plan

## Status and authority

This is the planning authority for the product-discovery stage starting 14 September 2026. It does not approve a product rebuild, a final market choice, a name, a brand, a public launch, or a production claim.

The project reports, codebase, and older phase documents remain useful evidence about what has been built. They are not a limitation on the future product. Where older market documents conflict with current market evidence, current evidence and direct customer interviews take priority.

## Founder objective

Turn the existing technical foundation into a real, useful, scalable business. The goal is not to preserve a college-project feature list. The goal is to identify a painful problem, prove that a reachable customer will pay to solve it, and build the smallest product that solves that problem better than the alternatives.

## Working rules

1. No major product rebuild before a validated market wedge is selected.
2. No final product name or brand decision before the customer, workflow, and positioning are clear.
3. No feature is justified because it is technically impressive. Every feature needs a customer problem, a buyer, and a measurable outcome.
4. Security and governance capabilities already built are assets, not the product definition.
5. Customer evidence outranks founder assumptions, old documents, and AI-generated market narratives.
6. A pilot is not success unless a customer uses the product for a real workflow and has a reason to continue paying.

## What the existing technology gives us

The current codebase already has useful primitives: agent and principal identity, delegated authority, deterministic policy evaluation, risk handling, approval separation, payload binding, revalidation, execution status, and audit evidence. These can become a strong product foundation if they solve one workflow that customers care about.

The current code does not prove that a customer wants a broad agent-governance platform. It also does not prove production readiness, commercial demand, or a winning market wedge.

## Current market facts

The market is real and moving quickly:

- Gartner reported in April 2026 that only 13 percent of organisations believe they have the right AI-agent governance in place, while warning about agent sprawl. [Gartner](https://www.gartner.com/en/newsroom/press-releases/2026-04-28-gartner-identifies-six-steps-to-manage-artificial-intelligence-agent-sprawl)
- The Cloud Security Alliance reported widespread use of multiple agent platforms and gaps in real-time inventory, runtime authorization, and traceability. Its survey was vendor-commissioned, so its statistics are directional evidence rather than neutral market measurement. [Cloud Security Alliance](https://cloudsecurityalliance.org/artifacts/enterprise-ai-security-starts-with-ai-agents)
- NIST has identified agent identity, authorization, delegation, auditing, non-repudiation, and prompt-injection mitigation as implementation questions still requiring practical solutions. [NIST](https://www.nccoe.nist.gov/publications/other/accelerating-adoption-software-and-ai-agent-identity-and-authorization-concept)
- The World Economic Forum published an Agent Capability and Authorization Profile framework in 2026, which shows that trusted deployment and enforceable delegation are becoming recognised needs. [World Economic Forum](https://www.weforum.org/publications/ai-agents-in-action-a-playbook-for-trusted-adoption-authorization-and-scaling/)

This means the category is valuable, but not empty. Microsoft, Okta, CyberArk, Palo Alto Networks, Zenity, Kynara, Helixar, Caracal, govern.sh, and Delego cover different parts of identity, discovery, runtime security, action authorization, approvals, or audit. We must not compete with all of them at once.

## Product opportunity to investigate

The core opportunity is not generic “AI governance.” It is the moment an AI agent wants to change something that matters in a real business system.

The product hypothesis to test is:

> A company needs an independent way to decide whether an AI agent may perform this exact business action now, to show a human the consequence, to prove what happened, and to recover when the connected system permits it.

This is a hypothesis, not our final positioning. Customer interviews decide whether it is painful enough and which action matters first.

## Candidate market wedges

| Candidate | Buyer and workflow | Why it is promising | Main risk |
| --- | --- | --- | --- |
| Customer operations | Support or operations leaders governing refunds, credits, subscription changes, order changes, and customer-record updates | Frequent actions, visible financial and customer-experience impact, measurable ROI | Support platforms may build parts of this themselves; connector quality is critical |
| Finance operations | Finance or treasury leaders governing payments, invoices, payout changes, and high-value approvals | High willingness to pay and clear approval/audit requirements | Slow sales, high trust bar, legal and integration complexity |
| IT and cloud operations | Engineering and SRE leaders governing deployments, infrastructure changes, access changes, and incident remediation | Developer-led integration and actions often have clear before/after state | Heavy competition from security, cloud, and DevOps vendors |
| Security and identity operations | Security teams governing temporary access, IAM changes, and containment actions | Strong risk and compliance narrative | Major identity and security incumbents dominate buyer relationships |
| Broad enterprise agent control | CISO or Head of AI governing many agent systems | Large future market | Too broad for an early product and directly competitive with funded platforms |

## Initial research position

Customer operations, finance operations, and IT/cloud operations deserve equal investigation. We will not choose one based on old documents or technical convenience. The likely first product should have all of these properties:

- A frequent, specific action with material cost if it goes wrong.
- A buyer who can describe the current manual approval or restriction.
- A system with an accessible API and a clear execution result.
- A policy that a customer can explain in plain language.
- A realistic recovery or compensation model.
- A reachable design partner who can test without a twelve-month procurement process.

## Research questions

For each candidate market, we must answer:

1. What exact action do teams refuse to let an AI agent execute today?
2. What is the current workaround, cost, approval chain, and failure consequence?
3. Which person owns the budget and which person feels the pain?
4. Which products, internal tools, or manual processes are used today?
5. Why are those alternatives insufficient?
6. What would a safe pilot need to prove within 30 days?
7. What would make the customer pay after the pilot?
8. Can the action be reversed, compensated, or only prevented before execution?

## Discovery workstreams

### Workstream 1 Market map

Create a current market map for each candidate wedge. It must separate direct competitors, adjacent products, customer-built solutions, and non-consumption. For every competitor, record target buyer, integration approach, pricing signal, claimed capabilities, and an evidence-backed gap. Do not claim differentiation unless a customer confirms it matters.

### Workstream 2 Customer discovery

Conduct at least 15 interviews across the three leading wedges before a final market decision. Interviews are for learning, not pitching. Capture exact quotes, real actions, current workflow, systems involved, approval rule, consequence of error, existing alternative, and willingness to pilot.

### Workstream 3 Product and workflow design

For the three most repeated actions, create a one-page workflow: action input, policy, risk, approval, execution result, recovery path, user experience, and success metric. Avoid implementation detail until the buyer problem is understood.

### Workstream 4 Technical feasibility

Only after a workflow passes the first customer test, map it to the existing codebase. Identify reusable components, missing connectors, data model changes, security requirements, and a safe sandbox plan. Technical work should reduce pilot risk, not expand the platform.

### Workstream 5 Business model

Test whether the buyer expects a SaaS control plane, a self-hosted deployment, an SDK, a managed integration, or an open-core product. Test a willingness-to-pay range before creating a detailed pricing page.

## Six stage decision process

| Stage | Output | Gate to advance |
| --- | --- | --- |
| 0 Planning | This master plan, source inventory, research template | Founder agrees that code changes are paused for market discovery |
| 1 Market research | Current competitor map and three wedge briefs | Each wedge has a stated buyer, action, alternatives, and unanswered questions |
| 2 Interviews | 15 structured interview records | At least one repeated high-cost action appears in three or more interviews |
| 3 Wedge selection | Evidence-based scoring and one market choice | A reachable buyer, urgent problem, feasible integration, and pilot path are all present |
| 4 Pilot specification | One workflow, product requirements, technical scope, and success measures | One or more design partners agree to review or test the pilot |
| 5 Build and learn | Narrow working pilot | Real usage evidence supports expanding, changing, or stopping the direction |

## Wedge scoring model

Score every candidate from 1 to 5 after interviews. Do not score based only on assumptions.

| Criterion | Evidence to collect |
| --- | --- |
| Pain severity | Cost, risk, delay, or customer impact of the current problem |
| Frequency | How often the action occurs or is blocked |
| Urgency | Active deployment or current decision timeline |
| Buyer access | Ability to reach and learn from the buyer |
| Willingness to pay | Budget, paid alternative, or commitment to a pilot |
| Integration feasibility | API, sandbox, action clarity, and customer technical capacity |
| Differentiation | A gap that a customer identifies as important |
| Recovery viability | Whether the action can be reversed, compensated, or reliably prevented |
| Expansion potential | Related actions and systems after the first workflow works |
| Founder advantage | Existing technical assets, learning speed, and credible distribution path |

## Product principles to preserve

- Authorize an exact action, not a vague agent identity or a broad credential.
- Explain the action in language an accountable human can understand.
- Keep deterministic policy and approval as the final execution authority.
- Bind approvals to the exact payload and revalidate before execution.
- Record the real provider result as evidence.
- Distinguish reversible, compensatable, and irreversible actions.
- Integrate with existing agent and business systems rather than trying to replace them.

## What is paused

Until Stage 3 is complete, do not start a broad frontend redesign, a final rebrand, a proprietary model, RAG work, new intelligence features, multiple connectors, broad compliance packs, or production deployment work intended for an unknown buyer.

Small research prototypes are allowed only when they help answer a customer-discovery question.

## First immediate tasks

1. Produce the three wedge briefs: customer operations, finance operations, and IT/cloud operations.
2. Produce a current competitor map for each wedge.
3. Create an interview guide and evidence-capture format.
4. Build a first outreach list of people who match the three target buyer profiles.
5. Review the evidence after the first five interviews before committing to a product direction.

## Naming decision

The repository name is an internal codename. The final product name will be chosen only after Stage 4, when the actual customer, workflow, positioning, product benefit, and category language are known.
