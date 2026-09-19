# Workforce OS integration assessment — Paperclip reference

**Status:** VERIFIED RESEARCH / IMPLEMENTATION PLAN  
**Date:** 19 September 2026  
**Reference reviewed:** PaperclipAI/paperclip at `6d03428682d9c0bc75f620e74c7075b6d9d0d12e` (18 September 2026)

## Decision

AgentOS should not be replaced by Paperclip or presented as Paperclip. The
product will add a first-class **Workforce** module: an AI-workforce operating
layer that plans, assigns, schedules, and measures agent work. AgentOS remains
the independent, authoritative action-governance layer. Any Workforce task
that attempts a protected external action must enter the existing AgentOS
gateway; it cannot authorize, approve, execute, or self-approve that action.

This gives the integrated product a clear value proposition:

```
mission → goal → project → work item → agent run → protected action request
                                                  ↓
                              AgentOS policy / risk / SoD / approval / evidence
```

## Upstream findings

Paperclip is an open-source “company OS” for teams of agents. Its primary
domains are multi-company isolation, memberships/identity, organization chart
and agents, goals, projects, work items, routines/heartbeats, cost budgets,
approvals, workspaces, skills, integrations, audit/activity, and instance
administration. It uses a TypeScript pnpm monorepo with a Node/Express server,
React/Vite UI, Drizzle/PostgreSQL data layer, adapter packages, and Playwright
plus Vitest tests. Its root workspace contains `server`, `ui`, `cli`, and
`packages/*`; its current source has a large, actively evolving schema and
more than 4,000 commits.

The relevant authenticated experience consists of onboarding, dashboard,
organizations, agents and their runs, projects/workspaces, task/issue lists
and detail conversations, goals, routines, approvals, budgets/costs/activity,
artifacts, inbox/decision queues, skills, apps/connectors, company settings,
members/secrets, and instance administration.

## License and reuse boundary

The upstream **code repository** is MIT licensed. MIT permits use,
modification, distribution, sublicensing, and commercial use, provided the
copyright and permission notice are retained in copies or substantial portions
of reused code. This repository may reuse narrowly selected upstream code only
with an attribution/notice file, a pinned upstream source reference, dependency
security review, and tests.

This does *not* authorize using the Paperclip name, logo, visual identity,
marketing copy, hosted account, credentials, or a representation that AgentOS
is Paperclip. The separate Paperclip documentation repository is CC BY-NC-N
4.0; its prose and documentation assets are not a commercial-copy source.

**Initial implementation choice:** do not vendor or embed the full upstream
application. It is a separate runtime, authentication model, PostgreSQL schema,
and large adapter ecosystem. A wholesale embed would duplicate identity and
authorization, weaken AgentOS's security boundary, and create a difficult
upgrade/fork burden. Rebuild the product concepts in AgentOS's existing
Next.js/FastAPI/SQLAlchemy architecture, borrowing only isolated MIT source
where later justified and recorded in `THIRD_PARTY_NOTICES.md`.

## Product surface to build

### Public and identity experience

1. Marketing home, product explanation, security/governance, workforce,
   integrations, pricing/contact placeholders, documentation, and legal pages.
2. Sign-up/sign-in, invitation acceptance, organization creation, and guided
   onboarding. Production identity-provider selection and email delivery remain
   a separate permission/deployment decision; no real account/email action is
   permitted by this assessment.

### Authenticated Workforce experience

1. **Workforce dashboard:** mission health, active work, workforce capacity,
   budget posture, approvals, governed-action posture, and attention queue.
2. **Organization:** company profile, org chart, positions, agent directory,
   reporting lines, lifecycle, permitted work, and escalation boundaries.
3. **Goals:** mission, nested goals, owners, progress, related projects and
   work items.
4. **Projects and work:** projects, work-item board/list, detail timeline,
   comments, dependencies, assignments, artifacts, and completion evidence.
5. **Runs and routines:** agent run timeline, heartbeat schedules, trigger
   history, safe pause/resume, and failure/unknown-outcome handling.
6. **Budgets:** scoped model/token/cost budgets, threshold warnings, hard stop
   posture, and cost-event attribution. Live provider billing remains disabled
   until an explicit connector approval.
7. **Governance bridge:** explicit links from work items/runs to existing
   action requests, policy results, approvals, reconciliation, and evidence.
8. **Administration:** organization members/roles, integrations/adapters,
   secrets references (not secret values), retention, export, audit, and
   instance administration.

## Delivery order and acceptance gates

| Increment | Scope | Acceptance evidence |
| --- | --- | --- |
| W0 | research, attribution boundary, domain map | this document + state lock, committed |
| W1 | persisted organizations, workforce agents, goals, projects, work items; seed data; REST API | migration + unit/API/database tests |
| W2 | Workforce dashboard, organization, goals, projects/work pages wired to W1 APIs | frontend typecheck/lint/build + browser journey |
| W3 | assignment lifecycle, comments/artifacts, governed-action links, audit events | SoD/tenant/isolation tests |
| W4 | routines/runs and budget ledger with sandbox-only execution | queue/idempotency/failure tests |
| W5 | identity/onboarding/admin and public pages | threat model, accessibility, authenticated E2E |
| W6 | adapters, credentials, production deployment and customer validation | blocked pending explicit production and founder approvals |

Every increment stays on `codex/unverified-working-tree-20260917`, is committed
and pushed for review, and is not merged to `main` without a separate founder
decision.

## Non-negotiable integration invariants

- All new entities are tenant-scoped; every lookup is tenant-filtered.
- A requester or assigned agent cannot approve its own governed action.
- Workforce work cannot bypass `GatewayService` for protected actions.
- Connector state is visibly `sandbox`, `configured`, or `live`; AgentOS
  currently supports sandbox/test connectors only.
- Schedules create durable work/run records; they do not make unbounded,
  unobserved agent loops.
- “Correction action” remains the only remediation language for irreversible
  actions.
- Public/production identity, outbound messaging, cloud accounts, live billing,
  live money movement, and customer data remain out of scope until separately
  approved.

## Sources

- Paperclip code and product overview: <https://github.com/PaperclipAI/paperclip>
- MIT license: <https://github.com/PaperclipAI/paperclip/blob/master/LICENSE>
- Product explanation: <https://docs.paperclip.ing/guides/welcome/what-is-paperclip/>
- Installation and self-hosting: <https://docs.paperclip.ing/guides/getting-started/installation/>
- Documentation repository license: <https://github.com/paperclipai/paperclip-docs>

