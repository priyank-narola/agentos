# Operations and Data Controls V1

## Purpose and status

This is the internal operating baseline for the customer-remediation pilot. It
is a product and engineering control document, **not legal advice**, a privacy
notice, a data-processing agreement, or a promise to customers. It turns the
product's data-minimisation design into concrete release and support gates.

No live customer connector may be enabled until the relevant sections are
reviewed against the pilot customer's jurisdiction, contract, systems, and
chosen hosting provider.

## 1. Data inventory and minimisation boundary

| Data class | Current purpose | Stored in product | Explicitly excluded from connector context |
| --- | --- | --- | --- |
| Tenant and principal identifiers | Tenant isolation, authorization, approvals, audit attribution | Yes | — |
| Action contract and policy result | Determine whether a proposed action may proceed | Yes | Raw model prompts, unbounded agent memory, and unrelated tool data |
| Refund case references | Bind the approved case to a ticket and payment | Yes: ticket reference, payment reference, account reference, amount/currency/reason | Payment-card data, full customer profile, support conversation text |
| Zendesk context | Verify stable case metadata before a remedy | Transient response used by the operator; current adapter returns only metadata | Subject, description, comments, attachments, email addresses, custom fields |
| Stripe provider evidence | Confirm result/reconcile an uncertain outcome | Refund/provider IDs, state, controlled error code/message | Stripe secret, full charge/payment method payload, card data |
| Audit and evidence records | Explain who requested, approved, executed, or recovered an action | Yes, tenant-scoped | Authentication tokens, secrets, unredacted connector payloads |

The integration boundary must remain narrow. Adding a new field to a connector
response requires an explicit purpose, sensitivity assessment, retention
classification, policy review, and test proving the field is not exported or
logged unintentionally.

## 2. Default retention posture

These are proposed defaults for the pilot, pending legal and customer review:

| Record | Proposed default | Reason |
| --- | --- | --- |
| In-flight connector context | Do not persist beyond the action request | Reduce exposure; use references rather than ticket bodies |
| Action, approval, execution, and audit evidence | 12 months | Supports customer dispute review and pilot evidence analysis |
| Reconciliation cases | 12 months after final resolution | Supports recovery and incident review |
| Structured application logs | 30 days in the selected log platform | Operational troubleshooting; logs must not contain bodies/tokens |
| Backups | 35 days, encrypted and access-restricted | Recovery window only; expire automatically |

These defaults are not activated by source code alone. The selected database,
backup, and logging providers must enforce them, and the customer contract may
require different settings. A deletion or legal-hold requirement always takes
precedence over a scheduled purge.

## 3. Deletion and export procedure

1. Receive a tenant-authorized request through the designated support channel.
2. Verify requester identity and tenant authority; open a support case without
   copying sensitive connector content into the ticket.
3. Determine the requested scope: user identity, action evidence, connector
   references, or entire tenant. Identify legal hold, security investigation,
   billing, or contractual obligations before deletion.
4. Export the tenant-scoped evidence record when requested and authorized. The
   existing evidence export must be reviewed for sensitive fields before it is
   sent outside the tenant.
5. Delete or anonymise eligible application records, revoke connector access,
   and schedule backup-expiry handling. Do not alter an audit trail silently:
   record the authorized deletion request and outcome using a non-sensitive
   deletion marker.
6. Confirm completion, scope, exclusions, and backup-expiry date to the
   authorized tenant contact. Retain the support case according to the support
   system's approved policy.

Automated deletion jobs are a future implementation requirement. They must be
tenant-scoped, idempotent, observable, dry-run capable, and reviewed against
foreign-key/audit-evidence requirements before activation.

## 4. Connector and secret operations

- Use a separate least-privilege Zendesk OAuth app and Stripe test-mode key for
  every non-production environment. Never copy live keys into a demo.
- Store connector credentials only in the chosen platform's secret manager;
  never in source control, browser code, exports, or logs.
- Enable a connector only after its safe configuration check passes, its
  required scope is reviewed, and a sandbox rehearsal is documented.
- Rotate a suspected credential immediately, disable the connector, inspect
  action/audit evidence, and record the incident timeline.
- A connector timeout or uncertain provider result is not a success. It must
  remain in reconciliation until independent provider evidence resolves it.

## 5. Incident response baseline

### Trigger conditions

Open an incident for unauthorized action attempt, suspected credential exposure,
cross-tenant data access, unexpected live execution, persistent provider
timeout, evidence-integrity failure, or service outage affecting action control.

### First 30 minutes

1. Assign an incident owner and record the timestamp, scope, and systems.
2. Disable affected connector(s) and prevent new consequential actions if
   integrity is uncertain. Preserve evidence; do not modify or erase it.
3. Identify affected tenants/actions from structured logs and tenant-scoped
   audit evidence. Treat all provider outcomes as unknown until verified.
4. Rotate exposed credentials and engage the hosting/identity/connector
   provider according to their emergency procedures.
5. Notify the authorized customer contact according to the executed contract
   and applicable legal obligations. Do not make speculative statements.

### Recovery and follow-up

1. Reconcile each affected action with independent provider evidence.
2. Restore service only after root cause, compensating controls, and owner
   approval are recorded.
3. Produce a factual post-incident record: timeline, impact, decisions,
   remediation, customer communication, and follow-up owner/date.
4. Convert preventive engineering work into tracked release gates and add a
   regression test where practical.

## 6. Pre-pilot acceptance checklist

- [ ] Pilot scope and data map agreed with the design partner.
- [ ] Required Zendesk OAuth and Stripe scopes/permissions reviewed.
- [ ] Test-mode rehearsal covers success, decline/error, timeout, duplicate,
  approval rejection, and reconciliation.
- [ ] Hosting, database, backups, logs, and secrets have named owners.
- [ ] Retention/deletion terms, DPA/subprocessor requirements, privacy notice,
  support contact, and incident-notification path receive founder/legal review.
- [ ] The launch-readiness dashboard has no remaining `BLOCKED` or `PENDING`
  checks relevant to the pilot.

## 7. Ownership boundaries

Engineering can build and test the controls in this repository. The founder,
legal counsel, hosting provider, connector account owners, and design partner
must approve the actual data-processing, contractual, and live-environment
commitments. Those decisions must not be guessed or represented as complete by
the product.
