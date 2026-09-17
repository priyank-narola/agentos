# Competitor Comparison V1

## Purpose

Map the current market before choosing what to build. This document does not claim that any vendor lacks a capability unless a direct source or customer evidence supports that conclusion. Vendor positioning may change quickly; validate key claims again before public marketing or a product launch.

## Strategic rule

Do not compete by building a general AI agent, a generic chatbot, an all-purpose AI security platform, or a replacement identity provider. Those categories already have established vendors, distribution, or platform ownership.

## Cross-market agent governance vendors

| Company or platform | Market position | Relevant capability | Strategic implication |
| --- | --- | --- | --- |
| Microsoft Entra Agent ID | Enterprise identity platform | Agent identity, lifecycle, governance, and enterprise access management | Integrate where possible; do not try to replace enterprise identity infrastructure |
| Okta for AI Agents | Identity security | Agent identity governance, discovery, and ecosystem integration | Identity alone is not a product wedge for us |
| Zenity | AI-agent security and governance | Discovery, posture, runtime defence, policy, identity, and threat response | Avoid a broad AI-security-platform battle |
| Palo Alto Networks Prisma AIRS | Enterprise AI security | AI gateway, runtime protection, agent security, and observability | Avoid general gateway and prompt-security positioning |
| CyberArk Secure AI Agents | Privileged identity and MCP controls | Identity broker, agent discovery, control, governance, and audit | Avoid leading with credential or privileged-access management |
| Kynara | Agent permission control plane | Runtime authorization, approval, MCP tool control, and tamper-evident audit | “Allow, deny, approve, audit” is not sufficient differentiation |
| Helixar | AI control plane | Runtime policy enforcement, delegated authorization, approvals, and signed evidence | Signed evidence alone is not a unique product |
| Caracal and Delego | Open-source action authorization | Delegated authority, policy, audit, MCP, and in some cases hosted-control-plane plans | An SDK or open-source policy engine alone is not enough differentiation |

Reference sources: [Microsoft](https://learn.microsoft.com/en-us/entra/agent-id/), [Okta](https://www.okta.com/newsroom/articles/okta-expands-ai-agent-security-to-any-idp/), [Zenity](https://zenity.io/), [Palo Alto Networks](https://www.paloaltonetworks.com/resources/whitepapers/secure-the-ai-enterprise), [CyberArk](https://www.cyberark.com/resources/best-practices/extend-agentic-identity-security-to-any-mcp-server), [Kynara](https://kynaraai.com/), [Helixar](https://helixar.ai/platform/), [Caracal](https://github.com/Garudex-Labs/caracal), and [Delego](https://delegohq.com/).

## Customer operations competitors

| Company or platform | What it already covers | What we must test before entering |
| --- | --- | --- |
| Intercom Fin | Support-agent procedures, connected-system actions, refunds, cancellations, subscriptions, credits, and escalation | Whether companies need independent action authority and recovery outside Intercom's own workflow |
| Zendesk AI Agents | Automated customer issue resolution and escalation in support channels | Whether support teams see a material gap in approval, evidence, or connected business actions |
| Salesforce Agentforce | Actions, flows, customer verification, return and refund workflows, and platform-native approval extensions | Whether customers operating across Salesforce and other systems need consistent control outside the platform |
| Shopify and Stripe ecosystems | E-commerce and payment actions through support-platform integrations | Whether a focused product can add value without becoming another connector layer |

Reference sources: [Intercom actions](https://www.intercom.com/learning-center/ai-agents-that-take-action), [Zendesk](https://support.zendesk.com/hc/en-us/articles/10488757995034-Creating-an-AI-agent-to-automatically-resolve-customer-issues), and [Salesforce](https://trailhead.salesforce.com/content/learn/projects/deploy-agent-authentication/learn-about-authentication-for-topics-and-actions).

### Customer operations entry condition

Only enter this market if interviews show that native support-platform controls fail at a specific, expensive action boundary. A possible gap could be cross-system authority and execution proof across a support agent, payment provider, subscription system, and customer-record system. This is an unvalidated hypothesis.

## Finance operations competitors

| Company or platform | What it already covers | What we must test before entering |
| --- | --- | --- |
| Flowwiz | Finance data, approvals, payments, vendor and customer workflows, and finance agents | Whether an independent action-authority layer is needed across multiple finance systems |
| Flowie | Procure-to-pay, approval routing, invoice processing, vendor checks, and payment workflows | Whether a customer needs control outside a full finance-orchestration platform |
| Otera | Governed procure-to-pay workflow and payment holds | Whether a narrow payment-release or exception workflow remains underserved |
| Loopfour | Finance automation with approval and audit controls | Whether proof, action binding, or recovery is a priority beyond existing controls |
| ERP and spend-management platforms | Existing workflow, approval, reconciliation, and audit capabilities | Whether buyers will place an independent service in a financial execution path |

Reference sources: [Flowwiz](https://flowwiz.io/platform), [Flowie](https://get-flowie.com/), [Otera](https://www.otera.ai/solutions/gbs-procure-to-pay), and [Loopfour](https://www.loopfour.com/).

### Finance operations entry condition

Only enter this market if a finance buyer identifies a specific action that existing finance workflow software cannot safely delegate to AI and agrees that a sandboxed, limited pilot can test the gap. High willingness to pay is irrelevant if a design partner is unreachable.

## IT and cloud operations competitors

| Company or platform | What it already covers | What we must test before entering |
| --- | --- | --- |
| ServiceNow AI Control Tower | AI asset discovery, governance, impact analysis, change review, approval, and workflow management | Whether teams without ServiceNow need a lighter runtime control layer for autonomous writes |
| Cloud providers | Native identity, policies, logs, and deployment controls | Whether cross-cloud or runtime agent actions fall outside existing cloud-native controls |
| Source control and CI/CD platforms | Pull requests, review, deployment approvals, audit history, and rollback workflows | Whether autonomous runtime actions create a problem not solved by normal code-review gates |
| DevOps and security products | Policy-as-code, infrastructure scanning, incident automation, and change management | Whether a buyer needs an agent-specific action contract and approval flow |

Reference sources: [ServiceNow AI Control Tower](https://newsroom.servicenow.com/press-releases/details/2026/ServiceNow-expands-AI-Control-Tower-to-discover-observe-govern-secure-and-measure-AI-deployed-across-any-system-in-the-enterprise/), [ServiceNow impact analysis](https://www.servicenow.com/docs/r/servicenow-platform/now-assist-for-configuration-management-database-cmdb/na-cmdb-awf-impact-analysis-use.html), and [ServiceNow approval flow](https://www.servicenow.com/docs/r/zurich/intelligent-experiences/ac-review-change-request.html).

### IT and cloud operations entry condition

Only enter this market if teams describe an autonomous runtime action that bypasses or outgrows pull-request, CI/CD, cloud-policy, and conventional change-management controls. A developer SDK or gateway should be considered only after that exact integration point is proven.

## Current conclusion

No market has earned a build decision. The most promising opportunity is not a platform category but a narrow action boundary where a buyer cannot safely rely on existing controls. The next step is to collect evidence, then compare observed demand with this competitor map.
