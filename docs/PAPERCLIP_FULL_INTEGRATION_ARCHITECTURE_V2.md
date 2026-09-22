# Paperclip full-source integration architecture

## Decision

AgentOS will retain its current governance product, routes, FastAPI service,
SQLAlchemy database, and evidence model. Paperclip will be included as a
pinned, upstream MIT source module and operated as a separately runnable
workforce-control-plane sidecar. It is not a replacement for AgentOS and it
does not share AgentOS's database.

This is the closest technically sound route to the original Paperclip product
experience: the upstream React/Vite UI, Express server, database schema,
workflows, interactions, animations, and agent runtime remain together rather
than being reimplemented piecemeal in an incompatible framework.

## Audited upstream baseline

- Repository: `https://github.com/paperclipai/paperclip.git`
- Pinned source revision: `8326e33adad63e26c918edf6adf6db114997eced`
- Upstream license: MIT, Copyright (c) 2025 Paperclip AI
- Verified local source date: 22 September 2026
- Runtime requirements: Node.js 24.11 or newer and pnpm 9.15.4

The integration pin is deliberately independent from an AgentOS release. An
upstream update must be reviewed, tested, recorded, and committed before the
pin moves.

## What the upstream source supplies

Paperclip supplies a complete workforce operating experience, including:

- company/workspace identity and memberships;
- agents, reporting lines, roles, permissions, and budgets;
- goals, projects, issues, comments, attachments, work products, and boards;
- heartbeat schedules, routines, run state, activity, cost tracking, and
  runtime/workspace management;
- approvals, audit/activity history, secrets, skills, plugins, integrations,
  and organization import/export;
- a React 19/Vite UI using React Router, TanStack Query, Motion, DnD Kit,
  Lexical, xterm, and other upstream packages; and
- an Express/Drizzle/PostgreSQL server with its own authentication and agent
  adapter ecosystem.

These are upstream capabilities, not a claim that AgentOS has already enabled
each one. Their availability in AgentOS depends on the integration stages
below and each stage needs its own committed verification record.

## Runtime topology

```text
Browser
  |\
  | \-- AgentOS (Next.js + FastAPI) -------------------------------+
  |      governance, policy, approvals, execution ledger, evidence  |
  |                                                                  |
  \---- Workforce Studio (upstream Paperclip sidecar) --------------+
          React/Vite UI + Express + Paperclip PostgreSQL
          goals, org, tasks, routines, workspaces, agents

Paperclip intent requiring an external/protected action
  -> AgentOS bridge contract
  -> AgentOS preflight/policy/approval/evidence boundary
  -> separately governed execution or a recorded denial
```

## Boundaries that protect both products

1. **Separate storage.** Paperclip owns its PostgreSQL schema and local data
   directory. AgentOS data remains in the AgentOS database. No table is shared
   and no migration crosses the boundary.
2. **AgentOS remains the protected-action authority.** A Paperclip task can
   create an intent for preflight, but it cannot self-approve, bypass policy,
   directly invoke an AgentOS connector, or fabricate evidence.
3. **Identity is mapped, not copied.** Initial local sandbox operation keeps
   Paperclip's local identity isolated. A future authenticated SSO and tenant
   identity mapping requires separate security review and founder approval.
4. **No live integrations by default.** The local sidecar is sandbox-first;
   no provider credential, customer data, payment, external account, outreach,
   or background agent execution is configured by this integration.
5. **No branding confusion.** The upstream code and license notice are
   retained. AgentOS presents the capability as **Workforce Studio** and does
   not represent itself as Paperclip or affiliated with Paperclip AI.

## Delivery sequence

| Stage | Deliverable | Completion evidence |
| --- | --- | --- |
| P0 | Pin complete upstream source as a Git submodule; retain MIT notice | submodule SHA + commit |
| P1 | Local sidecar launch configuration at a non-conflicting port, isolated data directory and authenticated/private configuration | reproducible local smoke check |
| P2 | AgentOS navigation/launcher and a same-origin-safe routing strategy, without changing existing AgentOS surfaces | UI/browser check |
| P3 | Read-only bridge: Paperclip task/agent/project summaries can be viewed from AgentOS; no side effects | API + UI tests |
| P4 | Governed intent bridge: Paperclip can submit an action intent only through AgentOS preflight and approval | contract + policy/evidence tests |
| P5 | Optional identity mapping, production deployment posture, and selected provider adapters | explicit founder/security approval |

P0 is source integration. P1-P4 are the work required for a genuinely working
combined product. P5 is blocked by the state-lock decisions on external
exposure and production identity.

## Local implementation rules

- Do not run Paperclip's installer script from the network.
- Do not run its agents, configure any API key, or enable a live connector.
- Use a dedicated local data directory outside AgentOS databases.
- Require `PAPERCLIP_PORT=3100` (or another configured non-conflicting port);
  AgentOS development remains on its existing port.
- Start Paperclip in its documented authenticated/private deployment mode for
  anything beyond a local smoke test.
- Any upstream code modified locally must keep the MIT copyright and license
  notice and be recorded in `THIRD_PARTY_NOTICES.md`.

## Current status

The P0 source pin is included in the same review-branch baseline as this
document. It does not mark the sidecar as installed, started, proxied,
authenticated, or integrated with AgentOS actions. Those states must be backed
by later commits and verification.
