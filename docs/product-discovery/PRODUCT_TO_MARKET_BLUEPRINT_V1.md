# Product-to-Market Blueprint V1

## 1. Authority and outcome

This is the operating blueprint for taking the technical foundation to a launchable SaaS business. It supersedes feature-by-feature development as the primary work plan and is used alongside `PRODUCT_EXECUTION_MASTER_PLAN_V1.md`.

The outcome is not “a polished governance dashboard.” The outcome is:

> A company can safely let an existing AI agent perform one valuable, consequential business action that it previously kept manual, while the company can understand the exact change, enforce its own policy, approve it when needed, prove the result, and handle the declared recovery path.

The final product name remains undecided. The current repository name is an internal codename only.

## 2. Product thesis and non-negotiable positioning

### What we will sell

A focused **AI Action Control SaaS** for one selected operational workflow. The product becomes the independent decision and evidence layer between an existing AI agent and a selected business system.

### What we will not sell

- A general chatbot, helpdesk, agent builder, generic AI dashboard, or generic approval tool.
- A replacement for Intercom, Zendesk, Shopify, Stripe, GitHub, ServiceNow, an ERP, an identity provider, or a cloud platform.
- A broad “AI governance platform” claim.
- A production-ready or compliant product before the launch gates below are met.

### Why this direction can become SaaS

The buyer pays only if the product produces a clear outcome: more permitted automation, less human handling time, fewer costly mistakes, better evidence, or all four. The technology underneath—policy, approval binding, audit, and connector control—is not the headline; it is the reason the buyer can trust the outcome.

## 3. Market-selection rule

No vertical-specific SaaS is chosen by technical preference. The chosen workflow must satisfy all of these:

1. At least three independent teams describe the same blocked AI action.
2. The action has concrete cost, risk, delay, or customer impact and occurs at least monthly for two teams.
3. Current native tools or manual process have a specific limitation the buyer cares about.
4. A buyer can approve a bounded sandbox/staging pilot.
5. One connector can demonstrate policy, approval, provider receipt, and recovery posture.

Until this gate is passed, the only legitimate product work is reusable foundation, research, pilot feasibility, security, and launch readiness—not speculative vertical features.

## 4. Working customer and workflow hypothesis

This is the leading hypothesis, not a final choice.

| Item | Working hypothesis |
| --- | --- |
| Economic buyer | Head of Customer Operations, Support Operations, Revenue Operations, or AI Automation |
| Daily user | Operations reviewer/approver and automation owner |
| Existing stack | Support agent plus billing, order, CRM, or entitlement system |
| Proposed action | A high-consequence credit, exception, refund exception, subscription exception, or entitlement update |
| Current pain | AI can identify the correct action but cannot be trusted to perform it alone across existing systems |
| Product promise | Allow safe actions automatically, route exceptions to the right person, and provide proof/recovery context for every result |
| Initial deployment | Sandbox or staging connector with anonymised/approved data only |

The discovery programme may reject this hypothesis in favour of finance or IT/cloud operations. The product architecture deliberately supports that decision.

## 5. Complete product experience

### Core user journey

```text
Existing AI agent
  → submits one structured proposed action
  → user can preflight it without side effects
  → platform resolves identity, authority, policy, and risk
  → allow / block / approval-required decision
  → approver reviews the exact before/after payload and recovery posture
  → platform revalidates before connector execution
  → connector returns a provider result
  → action case file contains decision, receipt, audit sequence, and recovery status
```

### Primary screens at launch

| Surface | User value | Launch requirement |
| --- | --- | --- |
| Onboarding | Connect the selected system, create roles, policy, and sandbox test data | Guided setup must reach first safe action without engineering help |
| Action preflight | Preview policy/risk/approval route for an exact payload without executing | Must be clearly labelled non-persistent and non-authorizing |
| Action case file | See intent, before/after, policy, risk, approver, provider outcome, evidence, and recovery status in one place | Must be the source of truth for a pilot action |
| Approval inbox | Named reviewers approve/reject one bound payload with separation of duties | Must support expiry, clear reason, and revalidation result |
| Policy editor | Operations owner defines thresholds, roles, actions, exceptions, and required evidence | Must be constrained, explainable, versioned, and testable |
| Evidence export | Download a portable action record for review, incident handling, or internal audit | Must be tenant-scoped and redact secrets/internal fields |
| Connector settings | Configure the one selected connector, scopes, test mode, health, and action mapping | Secrets never appear in UI, logs, payloads, or exports |
| Operations health | See failed/unknown executions, pending approvals, connector health, and audit verification | Must help the operator act, not become a generic dashboard |

### UX principles

1. Start from the business action, not technical objects.
2. Show a reviewer the exact consequence, not an opaque JSON blob.
3. Make “what happens next?” obvious: blocked, approval required, executing, executed, failed, or reconciling.
4. Never make a preview look like an authorization.
5. Never make a receipt look like a success if the provider outcome is unknown.
6. Put recovery posture beside the proposed change before execution.
7. Keep policy language plain enough for the accountable operations owner.

## 6. Feature blueprint

### Selected first pilot

The founder selected **customer credits and refunds for SaaS support teams** on
15 September 2026. The immediate product is the independent control layer for a
proposed remedy, not a competing support AI or billing product. The detailed
scope and evidence gate are in [Customer Credits & Refunds Pilot Spec V1](CUSTOMER_REMEDIATION_PILOT_SPEC_V1.md).

### P0 — launch-blocking capabilities

| Capability | Required behaviour | Status at blueprint creation |
| --- | --- | --- |
| Tenant isolation and auth | Every read/write uses server-derived tenant and authenticated principal | Tenant role foundation implemented for reconciliation; production identity integration and full RBAC coverage required |
| Action contract | Typed proposed action, before/after state, business intent, recovery class, idempotency key | Foundation implemented; selected vertical schema pending |
| Deterministic authorization | Policy evaluates exact action, actor, resource, context, and risk | Draft-only authoring, immutable live versions, rule editing, simulation entry point, atomic publish/supersede, audit events, and staging/production policy-author gates implemented. Customer-specific templates and approval workflow validation remain. |
| Bound human approval | Approval is attached to one immutable digest and is revalidated before execution | Foundation implemented; staging/production role enforcement added; notification/assignment experience needs pilot design |
| One production-quality connector | Least-privilege connection, idempotency, webhook verification/reconciliation, receipts | Not implemented; selected after discovery |
| Execution evidence | Provider result, status, reference, safe error and recovery posture | Foundation implemented; staging/production evidence-reader gate added; real-provider reconciliation pending |
| Audit integrity | Causally ordered action audit events and export | Foundation implemented; PostgreSQL migration validation pending |
| Secure configuration | Secret manager integration, environment separation, encryption/TLS, key rotation process | Not launch-ready |
| Operational resilience | Timeouts, retries, unknown state, dead-letter/reconciliation queue, support runbook | Unknown-state reconciliation inbox implemented; durable queue, scheduling, and real connector work still required |
| Data controls | Data inventory, retention/deletion policy, minimisation, access logging, DPA/subprocessor process | Not launch-ready |

### P1 — first paid-customer capabilities

- Role-based access for policy authors, approvers, operators, and auditors.
- Slack/email/in-product approval notification after an actual workflow requirement is known.
- Policy simulation against saved examples. The current UI supports manual representative-request testing; saved regression suites are a remaining release requirement.
- Connector health checks and actionable failure diagnosis.
- Search/filter/export of action cases.
- Configurable retention and case archival.
- Usage metering based on governed actions, not generic users alone.
- Customer-specific branding only when it improves approval adoption.

### P2 — expansion only after repeatable pilot usage

- Second action within the same customer workflow.
- Second connector in the same selected ecosystem.
- SSO/SAML, SCIM, custom roles, and enterprise deployment options where deals require them.
- SDK/MCP packaging for additional agent frameworks.
- Signed evidence exports and customer-managed storage options.
- Recovery workflow orchestration where the provider supports a safe correction action.

## 7. Architecture blueprint

### Logical architecture

```text
Agent / workflow platform
  → authenticated ingress API or MCP adapter
  → action-contract validator
  → policy + risk + preflight engine
  → action case and approval service
  → connector orchestration service
  → selected provider API / webhook

Action case, receipt, audit evidence, and observability remain in the control plane.
```

### Service boundaries

| Component | Responsibility | Must never do |
| --- | --- | --- |
| Ingress | Authenticate caller, validate schema, rate-limit, attach request metadata | Trust caller-supplied tenant, risk, policy decision, or approver |
| Action service | Persist proposed action, bind context/digest, generate case state | Execute raw connector call before authorization gate |
| Policy/risk service | Produce deterministic decision and explainable factors | Let LLM advice override deterministic rules |
| Approval service | Assign, expire, bind, enforce separation of duties, revalidate | Approve a changed payload or let requester approve themselves |
| Connector service | Map only executable parameters, invoke provider, reconcile outcomes | Receive secrets from action payloads or invent a provider result |
| Receipt/audit service | Persist evidence and causal event sequence | Claim a result without provider evidence |
| Admin/config service | Tenant policy/roles/connector setup | Expose credentials or cross-tenant data |

### Data model required for launch

- Tenant, principal, role, agent identity, delegation, tool/action, resource, policy and policy version.
- Action request/case with immutable submitted payload digest, action context, status, and idempotency key.
- Approval request/decision with assigned role/principal, expiry, actor, digest, and reason.
- Connector configuration reference (never plaintext secret), connector action mapping, health state, and webhook registration state.
- Execution receipt with provider ID/reference, outcome, error class, timestamps, evidence digest, reconciliation status, and recovery posture.
- Append-only audit events with per-action causal sequence.
- Support/operational records: incident, retry/reconciliation attempt, and customer-visible status history.

### API contract requirements

- Versioned REST API; MCP only when the selected agent ecosystem needs it.
- Idempotency required for every state-changing action.
- Tenant/principal derived from verified authentication, never accepted as a trusted body field.
- Pagination, filtering, stable error taxonomy, request IDs, and OpenAPI documentation.
- Webhook signatures, replay protection, event deduplication, and explicit unknown-state handling.
- Backward-compatible schema evolution with migration and contract tests.

## 8. Integration strategy

### Selection order

1. Customer evidence selects the action.
2. The action selects the business system.
3. The system selects the first connector design.
4. Existing ingress API/MCP capability is adapted to the customer’s agent.

### Connector acceptance checklist

- Sandbox, test mode, or partner-approved staging environment.
- OAuth/service-account scope can be least privilege.
- Stable provider action, read-after-write verification, and durable reference ID.
- Documented rate limit, timeout, retry, and webhook behaviour.
- Recovery action or declared irreversible outcome.
- No customer secrets in logs, evidence, code repository, or action parameters.
- Threat model and test plan complete before partner installation.

### Current feasibility posture

Shopify development-store refunds/cancellations are a conditional technical rehearsal candidate; GitHub deployment gating is intentionally not the first SaaS target because native controls already exist. See `PILOT_CONNECTOR_FEASIBILITY_V1.md`.

## 9. Security, privacy, and compliance programme

This is a product engineering plan, not legal advice. Jurisdiction, customer data, deployment model, and workflow can change requirements; obtain qualified legal/security review before contracting or production processing.

### Security baseline before a pilot with customer data

- Threat model for agent input, prompt injection, malicious tool output, confused deputy, privilege escalation, IDOR/tenant escape, webhook forgery, credential theft, replay, and audit tampering.
- External authentication with verified issuer/audience, short-lived tokens, least privilege, and tenant/principal mapping.
- Secrets manager; no committed secrets; rotation/revocation runbook; separate development/staging/production credentials.
- TLS in transit, encryption at rest, secure backups, access logging, dependency scanning, SAST, secret scanning, and vulnerability response process.
- Rate limits, abuse controls, input validation, output encoding, secure headers, and dependency lockfiles.
- Independent security review/penetration-test scope before broad launch, proportional to risk and customer segment.

### AI-specific control baseline

- Treat model output as untrusted input; no LLM may grant authority or directly choose a connector side effect.
- Maintain a test corpus for prompt injection, ambiguous instructions, malicious tool output, payload mutation, and unsafe recovery claims.
- Human override, kill switch/connector disablement, and incident review path.
- Document intended use, excluded uses, known limitations, and human oversight model.

NIST's AI RMF and Generative AI Profile provide a useful risk-management structure; OWASP's current AI/agent security guidance informs threat coverage. These are inputs to the engineering programme, not compliance certificates.

### Privacy/data baseline

- Data map: what enters from each connector, why it is needed, where it is stored, who can access it, and when it is deleted.
- Minimise customer/PII in action context, logs, prompts, support exports, and analytics.
- Tenant isolation tests; access/audit logs; retention and deletion jobs; backup/restore process.
- Privacy notice, data-processing agreement, subprocessor list, security contact, and incident-notification process before paid customer processing.
- DPIA/privacy impact review whenever risk, jurisdiction, or personal-data processing warrants it.

### Compliance positioning

Do not claim GDPR, SOC 2, ISO 27001, HIPAA, PCI DSS, or AI Act compliance unless an appropriate scoped assessment and legal review support the claim. For EU-facing AI features, transparency and risk classification must be checked against the current official AI Act guidance. The product should be built with traceability, human oversight, robustness, and documentation because these are useful product controls regardless of legal category.

## 10. Quality and test strategy

### Automated test layers

| Layer | Purpose | Launch bar |
| --- | --- | --- |
| Unit tests | Policy logic, digest binding, state transitions, error mapping | High coverage on safety-critical rules |
| API/contract tests | Auth, tenant isolation, schemas, idempotency, pagination, error taxonomy | Every public state-changing endpoint covered |
| Integration tests | Real selected-connector sandbox and webhook signature/replay flow | Required for the chosen action path |
| Migration tests | Clean install, upgrade from prior version, rollback/recovery plan | PostgreSQL scratch DB required |
| End-to-end tests | Agent proposal to approval to provider receipt to evidence export | One deterministic happy path and critical failure paths |
| Security tests | Cross-tenant, self-approval, payload tampering, revoked authority, replay, secret exposure | Must fail closed |
| Load/reliability tests | Approval bursts, provider timeout, retry, queue/reconciliation recovery | Target based on pilot volume and SLO |
| UX/accessibility tests | Reviewer comprehension, keyboard flow, error state, mobile approval | Pilot users can complete critical task without guidance |

### Release quality gates

- No unreviewed critical/high security finding.
- All required tests green against production-like configuration.
- Database migration rehearsal passes on a dedicated PostgreSQL scratch database.
- Backup/restore and incident drill pass.
- Selected connector test mode handles success, decline/failure, timeout/unknown, duplicate, webhook replay, and reconciliation.
- A pilot user verifies the approval and case-file flow against a real/safely anonymised example.

## 11. Deployment and operations architecture

### Environments

| Environment | Data | Purpose |
| --- | --- | --- |
| Local development | Synthetic only | Fast implementation and unit tests |
| Shared test | Synthetic only | API, UI, connector mocks, and integration contracts |
| Staging | Provider sandbox/anonymised data only | End-to-end rehearsal, migration, reliability, and acceptance testing |
| Production | Approved customer data only | Paid/approved pilot and launch workloads |

### Production components

- Containerised API service with a pinned runtime and health/readiness probes.
- Managed PostgreSQL with encrypted backups, point-in-time recovery, migration job, and restricted network access.
- Managed secret store and environment-specific configuration.
- Durable job/queue mechanism for webhook processing, retries, and reconciliation; do not rely on in-process retry state.
- Object storage only if evidence exports or attachments require it; encryption and retention rules required.
- Reverse proxy/WAF, TLS, domain, DNS, rate limiting, and audit logs.
- Central structured logging, metrics, traces, error monitoring, uptime checks, and alert routing.
- Infrastructure as code and a repeatable staging-to-production deployment pipeline.

### Reliability targets for first pilot

- Define an availability and response target only after expected volume is known; do not invent enterprise SLO claims.
- Any uncertain provider outcome becomes `UNKNOWN`/reconciliation-required, never automatic success or retry without idempotency evidence.
- Connector disable switch must be available to an authorised operator.
- Every production incident has an owner, timeline, customer communication rule, and post-incident record.

## 12. Business model and commercial design

### Initial packaging hypothesis

| Package element | Initial hypothesis to validate |
| --- | --- |
| Buyer | Operations/automation leader with accountable write-action risk |
| Value metric | Governed action volume, protected action family, or connector/workspace—not generic seat count alone |
| Pilot | Time-boxed paid or clearly scoped design-partner pilot with success metrics and data boundary |
| Standard plan | One workflow, one connector, policy/approval/evidence controls, support tier |
| Expansion | Additional actions, connectors, higher-volume processing, SSO, custom retention, private deployment |

### Commercial proof required

- Customer can describe the manual baseline and expected/observed improvement.
- Buyer confirms the product is differentiated from their existing native tools.
- At least one design partner expresses continuation or paid expansion intent.
- Pricing discussion is tied to verified workflow value, not an arbitrary dashboard price.

## 13. Go-to-market and launch requirements

### Before announcing publicly

- Product name, domain, trademark/brand review, positioning, and landing page only after the workflow is validated.
- Clear ideal-customer profile, buyer pain, one-sentence promise, and proof-oriented demo.
- Customer story/case study only with written permission; no invented logos, testimonials, metrics, or compliance claims.
- Pricing/packaging page, product documentation, integration documentation, security page, privacy notice, terms, DPA path, and support contact.
- Sales/demo environment using synthetic data and a reliable guided workflow.
- Customer onboarding, incident/support process, feedback loop, roadmap method, and cancellation/data-deletion process.

### Launch sequence

1. Internal alpha on synthetic data.
2. Design-partner sandbox/staging pilot.
3. Limited private beta with explicit operating boundaries.
4. Paid early-access launch after reliability, support, legal/privacy, and evidence gates pass.
5. Broader public launch only after repeatable onboarding and a defensible customer story.

## 14. Milestone roadmap and gates

| Milestone | Outcome | Deliverables | Gate |
| --- | --- | --- | --- |
| M0: Evidence | Select one real customer action | 15 interviews, scorecard, repeated-action matrix, alternative map | One workflow meets market-selection rule |
| M1: Pilot definition | Decide exactly what to build | Pilot PRD, UX flow, data map, threat model, connector design, success metrics | Design partner reviews/accepts scope |
| M2: Production foundation | Make the platform safe to host | Auth/secrets/config, PostgreSQL migration rehearsal, observability, CI/CD, runbooks | Staging passes security/reliability gates |
| M3: Vertical pilot | Complete one end-to-end workflow | Connector, policy pack, approver UX, receipt/reconciliation, onboarding | E2E sandbox/staging acceptance tests pass |
| M4: Partner validation | Prove real usage/value | Pilot feedback, action metrics, incidents, usability findings | Buyer asks to continue or provides clear paid-path evidence |
| M5: Launch readiness | Make the SaaS sellable and supportable | Pricing hypothesis, legal/privacy artefacts, docs, website, support/SLO process | Founder launch decision with evidence |
| M6: Market launch | Acquire and retain early customers | Private beta or public launch, feedback/metrics cadence | Repeatable value and retention signal |

## 15. Current status

### Built foundation

- Typed action context with before/after state and recovery posture.
- Deterministic policy/risk path, exact-payload digest binding, separation of duties, and approval revalidation.
- Execution receipt abstraction, evidence export, causal audit sequence, connector registry seam, and action preflight.
- Backend automated test suite and frontend static checks currently pass in the local environment.

### Known gaps that block production launch

- No chosen market wedge, design partner, or validated customer workflow.
- No real selected connector, secure credential lifecycle, or real-provider reconciliation implementation.
- PostgreSQL migration has not yet been rehearsed because no dedicated local PostgreSQL scratch environment is available.
- No production identity provider/SSO design, secret manager, queue, managed database, infrastructure-as-code, monitoring/alerting, backup drill, or incident process.
- No privacy/legal/commercial artefacts, pricing evidence, onboarding, support process, or public launch materials.

## 16. Execution rules from this point

1. Work is reported by completed milestones, not micro-tasks.
2. We build the reusable production foundation in parallel with discovery only when it is useful for every likely wedge.
3. We do not build vertical-specific features, connect live customer systems, process customer data, spend money, send external messages, or deploy production without the relevant gate and explicit founder approval.
4. Customer evidence beats desk research; current official sources beat stale assumptions.
5. A feature without a selected workflow, user, buyer, metric, and acceptance test stays out of the launch scope.

## 17. Immediate autonomous work order

1. Maintain and execute the discovery evidence programme until a wedge is selected or rejected.
2. Audit the current repository against M2 production-foundation requirements and produce a concrete remediation backlog.
3. Implement safe, cross-vertical foundation gaps from that backlog, with tests.
4. After wedge selection, create the Pilot PRD and build the selected connector/workflow end to end.
5. Before any launch, execute M2–M5 gates in order and present only true founder decisions or external commitments for approval.

## Official reference inputs

- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) and [NIST Generative AI Profile](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf).
- [OWASP GenAI Security Project](https://genai.owasp.org/2026/09/01/owasp-genai-security-project-unveils-2026-top-10-for-llm-applications-new-agent-control-standard-and-sponsors-as-community-tops-30000-members/).
- [UK ICO AI and data-protection guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/about-this-guidance/).
- [European Commission AI Act information](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai). Check the latest jurisdiction-specific requirements with qualified counsel before launch.
