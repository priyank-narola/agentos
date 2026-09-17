# Final Product UI/UX Specification V1

**Status:** Product-vision specification - not a declaration that every screen is already built.

**Purpose:** Define what the fully completed, launch-ready product should feel like for customers. This is intentionally independent of the current prototype's page list. It is a screen-by-screen blueprint for a focused AI-agent action-governance SaaS.

## 1. Product experience in one sentence

The product is a calm, evidence-first operating system that lets a company see, control, approve, execute, and prove consequential actions proposed by AI agents across its existing systems.

It is not a chatbot, agent builder, generic automation app, CRM, or payment system. It sits at the decision boundary before a consequential action occurs.

## 2. Experience principles

1. **Confidence before speed.** A user must understand what will happen, why it is allowed or blocked, who owns the decision, and what recovery is possible before acting.
2. **Exact action, not vague intent.** Every important view shows actor, action, target, parameters, policy, risk, evidence, and outcome together.
3. **Evidence is native.** Auditing is not a separate export after the fact. Every workflow creates readable, causal proof by default.
4. **Progressive disclosure.** Operators see a short explanation first, then can open policy logic, raw context, history, and provider receipts when needed.
5. **Never hide uncertainty.** A provider timeout or unknown outcome is a first-class operational state, never silently retried or described as successful.
6. **Guardrails look human.** Risk controls should explain the practical reason and the safe next action, not expose technical jargon by default.
7. **No final product name yet.** The information architecture uses neutral labels until the final wedge and brand are chosen.

## 3. Visual language and application shell

### Visual direction

- Desktop-first enterprise SaaS, responsive down to tablet and mobile approval tasks.
- Warm off-white canvas, midnight-navy navigation and type, cobalt blue primary actions, teal success, amber approval/attention, and restrained red block/danger states.
- Clean grid, generous whitespace, compact but readable data tables, 8px spacing rhythm, semantic icons, and accessible AA contrast.
- No flashy cyberpunk effects, no AI chat bubbles as the main interface, and no unexplained “AI score.”
- Every status uses both color and text/icon: `Allowed`, `Needs approval`, `Blocked`, `Executing`, `Succeeded`, `Failed`, `Unknown`, `Reconciled`.

### Persistent shell

**Left navigation** is grouped by the job the user is trying to do:

1. **Operate**: Control Center, Action Inbox, Approvals, Reconciliation.
2. **Govern**: Policies, Agents & Authority, Tools & Connectors.
3. **Prove**: Evidence, Observability, Intelligence.
4. **Administer**: People & Access, Organization Settings, Launch Readiness.

The bottom of the rail contains the active organization/tenant switcher, environment indicator (Sandbox, Test, Production), help, and user profile.

**Top bar** contains global search (“Search actions, agents, policies, or evidence”), time range, tenant/environment, alert bell, and profile menu. The environment must be visually unmistakable: sandbox/test uses a clearly labeled banner; production uses a neutral but explicit label.

**Shared behavior**:

- Every list view supports saved filters, URL-shareable filters, time range, export permissions, and row drill-down.
- Every critical page has loading, empty, error, permission-denied, and disconnected-provider states designed intentionally.
- Keyboard shortcuts: `/` search, `g` then page key for navigation, `a` action inbox, `p` approvals, `?` shortcut help.
- Destructive or irreversible action screens require clear confirmation, show recovery classification, and never use ambiguous buttons such as “OK.”

## 4. Complete screen map

| Area | Screens | Core outcome |
| --- | --- | --- |
| First use | Welcome, organization setup, identity connection, team/role setup, first governed action walkthrough | A secure tenant that understands the first value moment |
| Operate | Control Center, Action Inbox, Action Detail, Action Preflight, Approvals, Reconciliation | Run and supervise governed work |
| Govern | Policies, Policy Detail, Policy Builder, Policy Simulator, Agents, Agent Detail, Delegations, Tools, Connectors | Define who and what may act |
| Prove | Evidence Explorer, Evidence Export, Observability, Intelligence Review | Explain and prove every outcome |
| Administer | People & Access, Organization Settings, Data Controls, Notifications, API/MCP access, Launch Readiness | Configure and operate safely |
| Wedge module | Customer Remedy workspace, finance exception workspace, or another validated module | Solve one selected market workflow without bloating the core product |

## 5. First-use and onboarding screens

### 5.1 Welcome / workspace creation

**Goal:** Start with the user’s high-consequence workflow, not with an empty dashboard.

**Layout:** Two-column page. Left side explains the product’s job in three short steps: connect an agent/workflow, define the action boundary, review governed outcomes. Right side is a compact form for organization name, region, intended environment, and team size.

**Key components:** security promise, data-boundary disclosure, “Start in sandbox” primary CTA, “Talk to implementation” secondary CTA, and progress indicator.

### 5.2 Identity and tenant setup

**Goal:** Make access control real before configuring actions.

**Layout:** Guided wizard with left-side checklist and a focused central card.

**Steps:** connect OIDC/SSO; define organization and tenant; invite administrators; assign roles; configure emergency access; verify test login; display an explicit completion receipt.

**Important states:** no identity provider configured, SSO test failed, user lacks admin rights, configuration awaiting security owner, production setup blocked because required security controls are incomplete.

### 5.3 First governed action walkthrough

**Goal:** Demonstrate value in under five minutes using synthetic data.

**Layout:** Stage tracker across the top: Propose -> Identify -> Evaluate -> Approve -> Revalidate -> Execute -> Prove.

**Content:** A compact action card explains a fictional high-risk action. The user sees risk and policy evaluate, sends it to a distinct approver, approves/rejects in sandbox, and ends in an evidence receipt.

**Success state:** “You have governed your first action” with links to Action Inbox, Policies, and Evidence. Never falsely imply that a real external action occurred.

## 6. Operate screens

### 6.1 Control Center

**Goal:** Give the accountable leader a truthful operating picture in one minute.

**Layout:**

- Header: “Control Center,” time range, environment, trust-health chip, and action search.
- KPI row: actions governed, approvals waiting, blocked risks, unresolved outcomes. Each card has a trend only when enough real history exists.
- Main panel: recent action table with agent, action, resource, risk, policy outcome, execution outcome, owner, and timestamp.
- Right rail: “Needs your attention” showing expiring approvals, unknown provider outcomes, policy coverage gaps, or connector health issues.
- Lower panels: causal audit trace for selected action, policy coverage chart, high-risk agents/actions, and latest security events.

**Interaction:** Clicking a KPI applies an Action Inbox filter. Clicking any row opens Action Detail in a full page or right-side inspector. No key decision is hidden inside a chart.

### 6.2 Action Inbox

**Goal:** Provide the operational queue for every proposed or completed action.

**Layout:** Table-first view with saved filters above it. Default tabs are `All`, `Needs review`, `Blocked`, `Executing`, `Unknown`, and `Completed`.

**Columns:** action ID, time, requester/agent, action type, target, risk tier, policy result, approval status, execution state, owner, and evidence health.

**Filters:** tenant, environment, agent, action type, connector, policy, status, risk, monetary range, time, requester/approver, tag, and unresolved-only.

**Bulk operations:** only safe operations: assign owner, export permitted evidence, apply tag, or acknowledge alert. Never bulk-approve consequential actions by default.

### 6.3 Action Preflight

**Goal:** Let a user or integrated workflow predict the governing decision before submitting an action.

**Layout:** Builder on the left, non-persistent “Expected control path” on the right.

**Left:** agent, action, resource, typed parameters, context references, requested time, and recovery classification.

**Right:** identity/delegation result, predicted risk, matched policy, approval requirement, payload-binding summary, planned connector route, missing requirements, and data minimization warning.

**Actions:** “Save draft,” “Submit for governance,” and “Copy API example.” Preflight never creates an execution record.

### 6.4 Action Detail

**Goal:** Be the single source of truth for one exact action.

**Layout:** Header card with current status and safe next action. Tabs:

1. **Overview** - exact proposal, actor, target, parameters, owner, impact, and recovery classification.
2. **Decision** - matched policy/version, deterministic risk signals, advisory intelligence explanation, and block/allow/approval reason.
3. **Approval** - approver identity, separation-of-duties check, expiry, decision reason, and revalidation result.
4. **Execution** - connector/provider route, provider receipt, idempotency key, attempts, timing, and terminal outcome.
5. **Evidence** - causal timeline, attached references, hashes, export action, and activity log.

**Status behavior:** `Unknown` shows a high-visibility warning and a “Open reconciliation case” action. `Blocked` explains how to amend/re-submit without letting the user bypass policy.

### 6.5 Approvals

**Goal:** Let a distinct authorized human decide safely and quickly.

**Layout:** Queue on left, review surface on right. Mobile uses a focused, single-action page.

**Review surface:** action summary, value/impact, requester and agent, target, policy clause, risk factors, evidence references, historical similar actions, recovery warning, expiry countdown, and revalidation notice.

**Actions:** `Approve`, `Reject`, `Request changes`, `Delegate review` only if policy permits. Approval requires a reason when risk is high or action is irreversible. The product warns and prevents self-approval or expired/changed action approval.

### 6.6 Reconciliation

**Goal:** Safely resolve provider failures, timeouts, and uncertain outcomes.

**Layout:** Priority queue with clear uncertainty language: `Provider timeout`, `Receipt missing`, `Webhook delayed`, `Execution unknown`, `Manual verification required`.

**Case detail:** action facts, provider query history, received webhook events, last known state, recommended safe investigation steps, owner, SLA, notes, and evidence export.

**Actions:** query provider again where safe, attach verified receipt, mark confirmed succeeded/failed, create a correction action, or escalate. There is never an automatic consequential retry.

## 7. Govern screens

### 7.1 Policies

**Goal:** Make authority boundaries understandable, testable, versioned, and reviewable.

**Layout:** Policy library with status, scope, owner, last changed, coverage, and recent outcomes. Categories include financial limits, customer changes, data access, infrastructure actions, and custom validated workflows.

**Policy Detail:** human-readable rule summary first; tabs for scope, logic, versions, simulation, coverage, change history, and affected actions.

### 7.2 Policy Builder

**Goal:** Enable safe policy creation without hiding the underlying logic.

**Layout:** Three columns: conditions/logic on left, readable policy statement in center, impact preview on right.

**Core controls:** action and resource scope, delegated authority, thresholds, risk conditions, approval role, time/window, data classification, connector/environment, exception path, and recovery requirements.

**Guardrails:** changes are drafts; policy diff and impacted action count are mandatory; high-impact activation requires a second reviewer when organization policy requires it; rollback is explicit and audited.

### 7.3 Policy Simulator

**Goal:** Test policy changes against synthetic and historical-permitted action patterns before publishing.

**Layout:** scenario input, selected policy version, outcome comparison, coverage impact, false-block/false-allow review, and safe export.

**Result:** No action is executed. The simulator clearly labels whether an outcome is deterministic or advisory.

### 7.4 Agents & Authority

**Goal:** Answer “which AI system may do what, for whom, and until when?”

**Agents list:** name, owner, status, risk level, allowed tools/actions, last activity, blocked rate, and credential health.

**Agent Detail:** overview, identity/owner, lifecycle controls, authority summary, action history, risk profile, policy coverage, linked tools/connectors, and audit history.

**Lifecycle:** activate, suspend, retire. Retire is clearly irreversible; suspension immediately blocks new work while preserving evidence.

### 7.5 Delegations

**Goal:** Make temporary and scoped authority visible.

**Layout:** list of principal-to-agent authority grants with scope, limits, environment, issue/expiry date, issuer, and status.

**Actions:** issue, amend through a new version, revoke, and inspect all affected actions. The UI makes expired/revoked authority a clear reason when an action is blocked.

### 7.6 Tools & Connectors

**Goal:** Define the systems agents can call and the exact action contracts they expose.

**Tools page:** capabilities, actions, resources, connector status, data classification, policy coverage, and owner.

**Connector Detail:** authentication health without exposing secrets, environment, approved routes, permission scope, webhook health, provider rate limit, test status, recent receipts, kill switch, and connection audit log.

**Connector onboarding:** guided, test-first flow: choose provider, define minimal scope, configure secret through managed secret storage, run safe connection test, map typed action contract, verify webhook, set rollback/recovery plan, submit for security review.

## 8. Prove screens

### 8.1 Evidence Explorer

**Goal:** Let auditors and operators prove what happened without reading raw logs.

**Layout:** global evidence search with facets. Results group action, decision, approval, execution, connector receipt, actor, policy version, and audit integrity status.

**Evidence Detail:** a human-readable narrative at the top (“Finance Agent proposed X; policy Y required independent approval; Z approved; connector returned receipt; outcome succeeded”), followed by a causal timeline and raw/exportable facts.

### 8.2 Evidence Export

**Goal:** Create portable, minimally scoped proof for an audit, incident, or customer review.

**Layout:** choose action/case/time range, select evidence fields, see PII/data-boundary preview, select format, and generate export. Exports include scope, generation time, actor, integrity information, and access record.

### 8.3 Observability

**Goal:** Find system, security, and workflow health issues before customers do.

**Panels:** action volume/outcome, latency/error, approval aging, policy blocks, connector/webhook health, authentication failures, tenant-boundary denials, rate-limit events, audit integrity checks, and reconciliation backlog.

**Interaction:** every chart filters through to real actions. Alerts become assigned operational items, not anonymous red numbers.

### 8.4 Intelligence Review

**Goal:** Review advisory AI findings without giving them decision power.

**Layout:** findings list with confidence, signal provenance, human outcome, false-positive feedback, and link to underlying action/policy. A visible badge says `Advisory - cannot approve or execute actions`.

**Admin content:** model/provider health, evaluation scorecard, drift alerts, latency/cost, fallback status, and model change history.

## 9. Administration screens

### 9.1 People & Access

Users, service accounts, roles, team membership, access reviews, pending invitations, and emergency access records. Sensitive actions always show affected tenant and require a confirmation appropriate to risk.

### 9.2 Organization Settings

Tenant profile, regions, environments, SSO, allowed domains, data classifications, retention/deletion policy, notification rules, API/MCP endpoint settings, feature flags, and audit settings.

### 9.3 Data Controls

PII inventory, action-context minimization settings, retention schedule, export/delete requests, subprocessor list, and data-access log. Never display payment-card data or connector secrets.

### 9.4 Notifications

Channels, severity routing, approval reminders, escalation timings, unknown-outcome alert, policy change notice, security event notice, and digest preferences. External channels are enabled only once customer evidence and security review justify them.

### 9.5 Launch Readiness

An internal founder/operator checklist, not a false “100% meter.” It shows gate status for customer validation, security, infrastructure, privacy/legal, integration, support, and go-to-market. Each incomplete gate shows owner, evidence required, and next decision.

## 10. Validated wedge modules

The core product remains the same. The first commercial module is selected only after discovery. The UI must avoid pretending every industry workflow has been built.

### Customer Remedy workspace (only if selected)

For support operations handling customer credits/refund exceptions. Includes: case context reference, customer/account reference, exact requested remedy, amount/currency/reason, refund vs credit classification, policy threshold, human approval, provider receipt, recovery classification, and correction workflow. It must not ingest full conversations or payment-card data by default.

### Finance exception workspace (only if selected)

For treasury/AP workflows. Includes: payee/vendor, amount, budget context, invoice/evidence reference, approval chain, sanctions/vendor verification boundary where explicitly integrated, execution receipt, and exception/remediation path.

### Other validated workspace

An IT, cloud, data, or entitlement-action workspace may be added only if discovery proves a repeated, owned, painful action-control gap. It uses the same action-detail, policy, approval, evidence, and reconciliation patterns.

## 11. End-to-end journeys

### Journey A: routine low-risk action

1. Agent/workflow calls Action Preflight or submits a typed action.
2. Product resolves identity, tenant, delegation, tool, resource, and policy.
3. Action is allowed because all bounds are met.
4. Approved connector executes in the selected safe environment.
5. Provider receipt, audit event sequence, and evidence narrative are created.
6. User can find the result from the Control Center, Action Inbox, agent, policy, or Evidence Explorer.

### Journey B: high-risk action requiring approval

1. Agent proposes exact action with data-minimized context.
2. Policy/risk identifies high impact and routes to an independent approver.
3. Approver sees exact request, evidence, policy, risk, history, expiry, and recovery path.
4. Approver approves/rejects/requests changes. Product enforces separation of duties.
5. Before execution, the product revalidates identity, delegation, policy, and payload digest.
6. Execution is recorded as succeeded, failed, or unknown; every state is visible and exportable.

### Journey C: provider uncertainty

1. Provider timeout means no success claim is made.
2. A reconciliation case is created and assigned with the original action immutable.
3. Operator verifies provider state using a safe route and attached evidence.
4. The case ends with a confirmed state or correction action; no destructive retry is automated.

### Journey D: policy author changes a threshold

1. Author drafts change in Policy Builder.
2. Policy Simulator shows historical/synthetic impact and all affected action types.
3. Required reviewer approves the policy change.
4. New version activates; the version/diff/approvers are recorded.
5. Observability tracks blocks, approvals, exceptions, and potential policy gaps.

## 12. Final UI/UX acceptance criteria

The final product experience is complete for the selected wedge only when:

- A new authorized administrator can onboard a test tenant without engineering help.
- A requester can understand why an action is allowed, blocked, or waiting.
- An approver can make a safe decision from the UI without hidden context.
- An operator can resolve uncertain execution without unsafe retry.
- An auditor can reconstruct a full action story and export minimum necessary evidence.
- A policy author can safely simulate, review, version, and roll back a policy.
- Critical paths work by keyboard, have clear errors, and pass browser E2E/accessibility testing.
- Every screen truthfully distinguishes sandbox/test/production and known/unknown outcomes.
- The selected customer workflow is validated by real users; unused generic modules are not presented as finished product scope.

## 13. Copy/paste build prompt

Use this prompt to design or implement the final product UI:

> Design a production-quality, desktop-first enterprise SaaS called **[final brand name later]**. It is an AI-agent action-governance control plane, not a chatbot or generic automation tool. The user must be able to see, control, approve, execute, reconcile, and prove consequential actions proposed by AI agents across existing systems. Use a calm, evidence-first visual style: warm off-white content canvas, midnight navy navigation, cobalt-blue primary actions, teal success, amber approval states, restrained red blocked states; clean data-grid layout, generous whitespace, AA contrast, keyboard-accessible controls, no cyberpunk or neon style. Build an app shell with grouped navigation: Operate (Control Center, Action Inbox, Approvals, Reconciliation), Govern (Policies, Agents & Authority, Tools & Connectors), Prove (Evidence, Observability, Intelligence), and Administer (People & Access, Organization Settings, Launch Readiness). The Control Center must show transparent KPIs, an action table, attention queue, causal audit trace, and policy coverage. Action Detail must show Overview, Decision, Approval, Execution, and Evidence tabs. Approval workflow must surface exact action parameters, requester/agent, policy rule, risk, evidence, expiry, recovery classification, and clear Approve/Reject actions while preventing self-approval. Policies must be human-readable, versioned, simulatable, reviewable, and reversible. Reconciliation must treat provider uncertainty as a first-class case and never silently retry consequential actions. Evidence Explorer must turn an event trail into a readable action narrative with a causal timeline and controlled export. Include all loading, empty, error, permission-denied, disconnected-provider, sandbox, test, production, success, blocked, failed, and unknown states. Use realistic synthetic data only. Do not use a final product name, logos, customer PII, payment-card data, real connectors, or claims that a live transaction occurred.
