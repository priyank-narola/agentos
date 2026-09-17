# Tenant Roles Foundation V1

## Outcome

The product now separates external identity from tenant authority. A verified user identity answers “who is this?”; a persisted tenant role answers “what may they do in this workspace?”

## Implemented roles

| Role | Intended authority now | Future extension |
| --- | --- | --- |
| `ADMIN` | Manage tenant role grants/revocations; may reconcile uncertain executions | Tenant setup, billing, connector administration |
| `POLICY_AUTHOR` | Create drafts, change draft rules, create versions, publish, and retire policy versions | Customer-specific approval workflow for changes |
| `APPROVER` | Approve/reject/cancel eligible governed actions | Action-family/threshold-specific approval routing |
| `OPERATOR` | Reconcile an uncertain execution when independent from requester | Connector health and incident operations |
| `AUDITOR` | Read governed-action evidence exports | Read-only export/audit access |

## Current enforcement

- Role grants are tenant-scoped and unique per principal/role.
- Only an existing `ADMIN` can grant or revoke a role through the controlled role-management service.
- The last `ADMIN` role in a tenant cannot be revoked, preventing accidental loss of tenant administration.
- Role grants and revocations emit tenant-scoped audit events; an idempotent repeat grant does not create a misleading second grant event.
- The first production `ADMIN` is intentionally **not** self-service. It must be created by secure tenant-provisioning automation after identity, tenancy, and contractual setup are complete.
- The Access control screen is the product UI for reviewing role assignments and making controlled changes. In production, the authenticated identity is bound server-side and cannot name a different acting administrator.
- Reconciliation requires an active human with `ADMIN` or `OPERATOR`, in the same tenant, who is not the original action requester.
- The reconciliation UI only offers active principals who hold an eligible role.
- In staging/production, approval, rejection, and cancellation require `APPROVER` or `ADMIN`; a valid login alone is insufficient.
- In staging/production, drafting, changing draft rules, versioning, publishing, or retiring a policy requires `POLICY_AUTHOR` or `ADMIN`.
- In staging/production, action-evidence exports require `AUDITOR`, `OPERATOR`, or `ADMIN`.
- In staging/production, the agent registry, tool/action catalogue, resources,
  and delegations are control-plane surfaces: `ADMIN` or `OPERATOR` may change
  them, while `ADMIN`, `OPERATOR`, or `AUDITOR` may review them. Agent owners
  and human identity records have the narrower `ADMIN`/`AUDITOR` read path,
  and only `ADMIN` can create a principal.
- Agent lifecycle is explicit: an `ACTIVE` agent may be suspended or retired;
  a `SUSPENDED` agent may be reactivated or retired; and a `RETIRED` agent is
  irreversible. Status cannot be changed through a generic record edit.
  The case-file UI explains these effects and uses the same server-side
  `ADMIN`/`OPERATOR` gate as every other registry mutation.

## Read-surface protection

Outside local development, sensitive tenant-wide read surfaces are role-gated
as well as write operations. Action case lists/details/evidence and
observability views require `ADMIN`, `AUDITOR`, or `OPERATOR`; approval queues
also allow `APPROVER`; and role administration requires `ADMIN`. This prevents
an ordinary authenticated tenant member from browsing execution references,
audit history, approver eligibility, or role assignments by default.

The development demo remains intentionally open to synthetic data so the local
workflow is usable. Production and staging use the database-backed grants.

## Deliberate next work

Roles now protect recovery, approval decisions, policy lifecycle, evidence,
agent lifecycle/control-plane records, and sensitive tenant-wide read
surfaces. Before customer launch, extend authorization to connector setup,
support operations, billing, and SSO/SCIM provisioning. Do not claim full RBAC
coverage yet.
