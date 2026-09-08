# Opportunity Research — AI Manufacturing Operating System (Hypothesis B)

**Status:** RESEARCH HYPOTHESIS — not customer-validated. Labeled hypothesis only.
**Canonical context:** `AGENTOS_OPERATING_PROMPT.md` §21; `AGENTOS_STATE.md` §2.
**Date:** 8 September 2026

## Framing
Explore whether "an operating/control layer for AI-driven manufacturing operations" is a stronger wedge than generic agent action governance. Keep entirely separate from AgentOS hypothesis A until interviews decide.

## Structure
- Problem: manufacturing operations increasingly pilot AI for scheduling, quality, yield, maintenance, and supplier coordination; production decisions are consequential (line stops, rework, scrap, safety).
- Customer: plant/operations managers, VP manufacturing, quality leaders at discrete or process manufacturers.
- User: operators, process engineers, quality engineers, AI/automation leads.
- Workflow: change/action requests on production systems (setpoint changes, recipe edits, dispatch decisions, quality dispositions) that need governed, auditable, human-approved execution.
- Current alternatives: MES/ERP change control, paper/email approvals, spreadsheet logs, IT change management, point solutions.
- Pain hypotheses: uncontrolled AI changes to production parameters; audit/compliance gaps; human-in-loop approval without governance trail.
- Frequency/severity: to be validated in interviews (expect high severity for quality/safety, low-moderate frequency).
- Economic value: avoided scrap/rework/line-down events; auditability for certifications (IATF/ISO).
- Data requirements: production system context, equipment state, recipe/quality data; likely on-prem/edge constraints.
- AI advantage: real-time risk contextualization of agent actions.
- Moat: integration depth + workflow lock-in + compliance evidence.
- Distribution: plant-floor vendors, systems integrators, MES partners.
- Competitive landscape: MES vendors extending AI, industrial automation majors, quality platforms.
- Validation questions: who owns AI changes today? What breaks without a governance trail? Which change is most expensive to get wrong? Would you pilot a governed-action layer on one line?

## Evidence standard
No customer evidence exists yet. Do not treat interest as validation.
