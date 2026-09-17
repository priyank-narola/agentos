# Action-Control Gap Research V1

## Status

Current desk-research baseline for Programme 1. It narrows interview questions; it does not select a wedge or prove a market gap. Vendor documentation describes product capabilities, not customer satisfaction or willingness to pay.

## Research question

Where, if anywhere, is there a valuable gap between existing AI/support/change-management platforms and an independent, exact-action control layer?

## What established platforms already cover

| Platform category | Source-backed capability | Why this matters to our strategy |
| --- | --- | --- |
| Zendesk support actions | Zendesk documents Shopify actions that look up an order, cancel/refund an entire order, or refund selected items. Its guidance recommends approval for write actions such as refunds rather than marking them pre-approved. | We must not build a generic “AI support agent can issue refunds” product. Native action and approval workflows already exist. |
| Zendesk approval workflow | Zendesk documents approval requests that can be created, shared, withdrawn, and then approved or denied; a changed request must be withdrawn and recreated rather than edited. | Exact request immutability is not enough differentiation by itself. Interviews must test whether the buyer needs cross-system payload binding, evidence, or recovery beyond the native approval object. |
| ServiceNow AI Control Tower | ServiceNow documents steward approval for AI assets, models, MCP servers, and AI lifecycle/change requests; it can trigger governance playbooks and route work to an Activity Center. | We must not position as broad AI-asset inventory, lifecycle governance, MCP approval, or enterprise governance workspace. |
| ServiceNow controlled AI changes | ServiceNow's change flow can require a steward to review and approve a structured change request before it changes a managed AI asset. | Approval + lifecycle management are already established categories. The testable question is runtime business/system actions proposed by agents, not governance of the agent asset itself. |

## Candidate boundary worth testing

The only current hypothesis worth testing in customer/business operations is:

> A company runs an existing support or operations agent across multiple systems, but does not have one independent control boundary that can evaluate a specific cross-system write, show its before/after impact and recovery posture, bind a human decision to the exact payload, retain provider outcome evidence, and support correction when the connected system allows it.

This statement is **not** a market claim. A customer may say that their support platform, billing system, internal workflow, or manual process already solves it. If so, the candidate wedge is rejected.

## Interview tests by action

| Candidate action | Native capability that may already solve it | Specific gap test | Rejection signal |
| --- | --- | --- | --- |
| Refund or order cancellation | Support platform can trigger/refund orders and request human approval | Does the team need consistent controls across support, payment, order, and CRM systems, including provider receipt and compensation evidence? | Team trusts native platform workflow and does not need independent evidence or multi-system policy |
| Account credit | Often implemented through billing/support workflow or internal tool | Is the credit policy spread across systems, manual approvals, and reconciliation? Can a wrong credit be corrected? | One native platform has clear policy, approvals, audit, and correction already adopted |
| Subscription exception | Billing platform owns plan/price changes | Is the risky part an exception that cannot be governed by the billing platform's normal workflow? | Billing owner has a satisfactory native approval/evidence model |
| Entitlement/customer-record update | CRM/support/internal systems can update fields and maintain history | Does the action cross system-of-record boundaries and need identity/policy/recovery proof? | Existing CRM workflow provides adequate controls and audit evidence |

## Questions that distinguish a real gap from a feature request

1. Show the last real write action that required human approval. Which systems were touched, in order?
2. Could the support/billing/CRM platform already perform the entire action? If not, what exact boundary failed?
3. Was approval attached to the exact before/after payload, or was it a general ticket/comment/Slack decision?
4. After execution, can a reviewer prove the provider accepted the action and see whether it can be reversed or compensated?
5. If the same agent action originates in a different channel or system, does the policy remain consistent?
6. Would placing an independent service in this path add enough safety or speed to justify the integration? Why or why not?

## Research conclusions so far

- **Rejected positioning:** generic AI support agent, generic refund automation, generic approval workflow, generic AI governance dashboard, AI asset lifecycle management, and MCP-server approval.
- **Open hypothesis:** independent control and evidence for a narrowly defined, high-consequence cross-system write action.
- **Required proof:** at least three independent teams must describe the same unsolved action boundary and at least one must accept a bounded pilot discussion.

## IT/cloud operations baseline

GitHub already provides a mature control path around code and deployments: coding agents can create pull requests for review; protected deployments can require a reviewer other than the initiator; and GitHub environments can use custom third-party protection rules. GitHub also documents agent-authored commit/session traceability and branch-protection controls.

### Implication

Do **not** enter IT/cloud operations with “AI coding agent approval,” “AI pull-request review,” or “deployment approval workflow.” Those are native product capabilities and can be extended through custom protection rules.

The only IT/cloud hypothesis worth interviewing is narrower: an autonomous runtime action that occurs outside the normal pull-request/deployment path, crosses systems, and cannot be safely governed with existing environment rules, CI/CD controls, or an existing ITSM deployment gate. An example could be an agent-initiated incident action whose desired change, live state, guardrails, and recovery evidence must be evaluated at runtime.

### IT/cloud rejection test

Reject this lane if platform/SRE teams say an environment protection rule, branch policy, pull request, existing change-management system, or custom GitHub deployment rule covers the proposed action adequately. Do not compete with a customer’s working developer workflow.

## Finance operations baseline

Desk research confirms that payment and finance systems already expose action APIs and approval-oriented workflows, but it does not yet identify a defensible independent-control gap. The relevant research is therefore not “can a payment system issue a refund?” It is whether a controller or finance-operations buyer has a specific AI-proposed exception action that existing ERP, spend, payment, and approval systems cannot safely govern across their actual system boundary.

Finance should advance only if interviews reveal a bounded, sandboxable action such as a defined payment exception, vendor-change exception, or payout-release exception with a named accountable buyer. It should be rejected if the first usable pilot requires live banking access, lengthy compliance review, or a replacement finance workflow.

## Sources

- [Zendesk: actions for auto assist and action flows](https://support.zendesk.com/hc/en-us/articles/9174548349978-About-actions-for-auto-assist-and-action-flows) — accessed 15 September 2026.
- [Zendesk: approval requests](https://support.zendesk.com/hc/en-us/articles/9483757385114-Accessing-sharing-and-withdrawing-approval-requests) — accessed 15 September 2026.
- [ServiceNow: AI Control Tower approvals](https://www.servicenow.com/docs/r/intelligent-experiences/ai-control-tower/explore-approvals.html) — accessed 15 September 2026.
- [ServiceNow: AI asset change requests](https://www.servicenow.com/docs/r/intelligent-experiences/ai-control-tower/create-ai-asset-change-request.html) — accessed 15 September 2026.
- [ServiceNow: AI Control Tower work and approvals](https://www.servicenow.com/docs/r/intelligent-experiences/aict-managing-tasks-and-approvals.html) — accessed 15 September 2026.
- [GitHub: deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments) — accessed 15 September 2026.
- [GitHub: third-party coding agents](https://docs.github.com/en/copilot/concepts/agents/about-third-party-coding-agents) — accessed 15 September 2026.
- [GitHub: Copilot cloud-agent risks and mitigations](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/risks-and-mitigations) — accessed 15 September 2026.

## Next research action

Use these questions in the first customer/business-operations interviews. If the native platforms satisfy the need, do not attempt to compete there; move remaining interviews toward finance and IT/cloud operations and apply the same action-boundary test.
