# Market Wedge Briefs V1

## Purpose

This document compares three candidate markets before choosing the product to build. It is desk research, not a final market decision. Vendor pages describe vendor claims; customer interviews must confirm whether the claimed gaps matter to buyers.

## Decision status

**Founder-selected pilot wedge (15 September 2026): customer credits and refunds for SaaS support teams.**

This is a product-direction decision, not proof of product-market fit. The first
pilot must validate that a support/billing team needs an independent control
record across its support and billing systems, rather than only native workflow
features inside one platform.

## Shared market observation

AI agents are increasingly being given the ability to take actions in business systems. The market need is real, but each candidate market already has strong platforms. The opportunity is therefore not “build AI agents” or “add a generic approval button.” It is to solve one specific action-control problem that current systems leave unsolved for a reachable customer.

## Candidate A Customer operations

### Customer and workflow

Target buyers are heads of customer support, customer operations, or support automation at e-commerce, marketplace, or B2B SaaS companies. Candidate actions include refunds, account credits, subscription changes, returns, order changes, and customer-record updates.

### Current market evidence

- Intercom says its Fin agent can process refunds, cancellations, subscription changes, and account updates through connected systems such as Stripe, Shopify, and custom APIs. [Intercom](https://www.intercom.com/learning-center/ai-agents-that-take-action)
- Intercom also documents routing refund requests to a human through its guidance and escalation controls. [Intercom Help](https://www.intercom.com/help/en/articles/11829564-prevent-emails-from-being-closed-using-fin-guidance)
- Salesforce documents Agentforce actions for returns and refunds and requires customer verification before sensitive actions in its example service flow. [Salesforce action example](https://trailhead.salesforce.com/content/learn/projects/quick-start-einstein-copilot/connect-your-flows-to-einstein-copilot) and [Salesforce authentication example](https://trailhead.salesforce.com/content/learn/projects/deploy-agent-authentication/learn-about-authentication-for-topics-and-actions)
- Zendesk supports AI agents that resolve customer issues without human intervention. [Zendesk](https://support.zendesk.com/hc/en-us/articles/10488757995034-Creating-an-AI-agent-to-automatically-resolve-customer-issues)

### Competitive implication

This is not a good market for a generic support AI agent. Established platforms already provide the agent, workflows, connectors, escalation, and in some cases action authentication.

The research question is whether a company using several support and business systems needs an independent record of action authority, exact-payload approval, execution evidence, and recovery across those systems. If customers are satisfied with native platform controls, this wedge should be rejected.

### Questions to validate

1. Which customer-facing action is currently forced to a human, and why?
2. Do existing Intercom, Zendesk, Salesforce, or internal controls already solve the approval and evidence need?
3. Does the company use more than one AI support platform or more than one system of record?
4. What is the cost of a wrong refund, credit, cancellation, or account change?
5. Would an external control layer be accepted in the action path, or would the buyer require native integration?

### Initial assessment

Customer access and action frequency may be strong. Differentiation is unproven, because support vendors already control much of the workflow. This wedge advances only if interviews reveal a meaningful cross-platform or high-risk-action gap.

### Selected pilot thesis

The product will not compete to answer tickets or become a generic support AI.
It will sit at the consequence boundary when an existing support AI, agent, or
workflow proposes a customer credit or refund. Its job is to bind the exact
ticket, payment, customer, amount, reason, policy decision, independent
approval, execution receipt, and recovery posture into one case file.

The first technical path is **support context → governed refund/credit → billing
execution receipt**. Zendesk and similar platforms may provide native approvals
and actions; a customer must confirm whether an independent, cross-system,
tamper-evident control record is valuable enough to adopt.

## Candidate B Finance operations

### Customer and workflow

Target buyers are finance operations leaders, controllers, treasury teams, accounts payable teams, and finance-automation providers. Candidate actions include payment initiation, invoice approval, vendor changes, payout changes, payment-release exceptions, and high-value refund approval.

### Current market evidence

- Avalara reported in 2026 that finance leaders feel pressure to deploy AI agents while governance, accountability, and internal controls struggle to keep pace. Its survey covered more than 1,500 CFOs and senior finance leaders, but it is still vendor-sponsored evidence. [Avalara](https://www.avalara.com/blog/en/north-america/2026/08/agentic-ai-finance-governance-survey.html)
- Finance platforms such as Flowwiz, Flowie, Otera, Blackbee AI, Loopfour, and ProvenanceCode already combine AI agents, workflow automation, approvals, payment or finance operations, and audit-oriented controls. [Flowwiz](https://flowwiz.io/platform), [Flowie](https://get-flowie.com/), [Otera](https://www.otera.ai/solutions/gbs-procure-to-pay), and [Loopfour](https://www.loopfour.com/)
- The IMF describes boundaries, approval thresholds, human oversight, and the ability to suspend or override agents as important controls for agentic AI in public financial management. [IMF](https://www.imf.org/-/media/files/publications/tnm/2026/english/tnmea2026006-s001.pdf)

### Competitive implication

The money and urgency are attractive, but companies already buy full finance-automation platforms. A new product should not attempt to rebuild procure-to-pay or accounting automation.

The testable gap is whether companies need a system-independent authority and evidence layer for AI actions that move, approve, or alter money. That may matter most where agents, payment tools, and enterprise resource planning systems come from different vendors.

### Questions to validate

1. Which finance action is still prohibited for an AI agent, despite existing workflow software?
2. Who owns the risk: controller, treasury lead, CFO, security team, or operations leader?
3. What controls are mandatory before money is released?
4. Is the buyer willing to place an independent service in the payment or approval path?
5. Can a safe pilot use a sandbox or low-value workflow without legal or banking integration delays?

### Initial assessment

This wedge may have the highest willingness to pay and strongest risk narrative. It also has the longest trust, compliance, integration, and sales path. It advances only if we can reach a design partner with a bounded sandbox workflow.

## Candidate C IT and cloud operations

### Customer and workflow

Target buyers are engineering leaders, platform engineers, DevOps leaders, SRE leaders, and security engineering teams. Candidate actions include production deployments, infrastructure changes, IAM changes, incident remediation, configuration changes, database migrations, and rollback operations.

### Current market evidence

- ServiceNow's AI Control Tower already covers discovery, governance, approval, and management for AI systems and workflows. [ServiceNow](https://newsroom.servicenow.com/press-releases/details/2026/ServiceNow-expands-AI-Control-Tower-to-discover-observe-govern-secure-and-measure-AI-deployed-across-any-system-in-the-enterprise/)
- ServiceNow documents agentic impact analysis for proposed changes and an approval workflow that can apply a reviewed change. [Impact analysis](https://www.servicenow.com/docs/r/servicenow-platform/now-assist-for-configuration-management-database-cmdb/na-cmdb-awf-impact-analysis-use.html) and [change approval](https://www.servicenow.com/docs/r/zurich/intelligent-experiences/ac-review-change-request.html)
- Engineering teams are increasingly discussing the need for human review, narrow permissions, clear diffs, and rollback when AI assists with production infrastructure changes. This is a useful hypothesis, but community discussion is not customer evidence.

### Competitive implication

This market is served by ServiceNow, cloud providers, DevOps products, source-control platforms, and security vendors. A broad “AI change-management platform” would be hard to differentiate.

The testable gap is a lightweight, vendor-neutral action contract for teams that do not use a full ServiceNow change-management deployment but still need to govern AI-triggered production writes. It could be developer-led and easier to pilot than finance, but the buyer may prefer pull requests, existing CI/CD controls, or cloud-native policy tooling.

### Questions to validate

1. Which production action do teams refuse to let a coding or operations agent execute?
2. Do pull requests, CI/CD approvals, infrastructure-as-code reviews, and cloud-native policies already solve the problem?
3. What action needs faster approval than a conventional change-management process provides?
4. Is the desired product a developer SDK, a gateway, a CI/CD integration, or an operational user interface?
5. Can the team identify a rollback or compensation action for every pilot workflow?

### Initial assessment

The technical fit with the existing codebase is strong and developer-led pilots may be more accessible. The competitive and integration risk is also high. It advances only if interviews show that existing pull-request and change-management controls fail for autonomous, runtime agent actions.

## Comparison before interviews

| Criterion | Customer operations | Finance operations | IT and cloud operations |
| --- | --- | --- | --- |
| Customer action frequency | Likely high | Medium to high | Medium to high |
| Potential willingness to pay | Medium | High | Medium to high |
| Time to an early pilot | Medium | Low | Medium to high |
| Existing platform competition | High | High | Very high |
| Fit with current governance foundation | High | Very high | Very high |
| Differentiation evidence today | Unproven | Unproven | Unproven |

## Research conclusion

Desk research does not justify choosing a final market. Finance has the strongest economic risk, customer operations has the most frequent business actions, and IT/cloud may provide the fastest technical learning. None is automatically the right company to build.

The next decision depends on direct evidence from potential buyers. The winning wedge must show the same painful action across several interviews, a clear reason existing tools are insufficient, a reachable buyer, and a safe pilot path.
