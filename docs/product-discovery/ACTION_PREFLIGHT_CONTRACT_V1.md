# Action Preflight Contract V1

## Purpose

Action preflight lets a team inspect the real control path for a proposed agent action before anything is persisted or sent to a connector. It is designed for policy design, operational rehearsal, and a design-partner pilot—not as a second authorization mechanism.

## API and product surface

- `POST /api/v1/action-preflight` evaluates a principal, agent, action, resource, executable parameters, and optional typed action context.
- The **Action preflight** screen exposes that safely in the product UI. It accepts executable parameters as JSON and can include the same typed business intent, before-state, proposed change, recovery class, and recovery plan used by the gateway.
- The response includes the deterministic decision, reason, matched policies, explainable risk, planned connector class, payload digest, and next control.

## Non-persistence invariant

A preflight never creates or changes:

- Action requests or decisions.
- Approval records.
- Audit events or evidence exports.
- Execution receipts, provider calls, or external system state.

The server computes a digest for visibility only. That digest is not an authorization token and cannot be replayed to bypass the normal gateway path.

## Decision meaning

| Preview result | Meaning at preview time | What a real submission still does |
| --- | --- | --- |
| `BLOCKED` | The current policy/identity/risk state does not permit the action. | Evaluates again and remains fail-closed if controls are still unmet. |
| `HUMAN_APPROVAL_AND_REVALIDATION_REQUIRED` | Policy permits the action only after a human decision. | Creates a payload-bound approval and revalidates immediately before execution. |
| `READY_TO_SUBMIT` | Current controls would permit submission. | Evaluates again; only the gateway can persist evidence or call a configured provider. |

## Product boundary

Preflight derives the connector route from the same server-controlled registry used by the gateway and approval service. Today that route is sandbox-only. A result showing a connector class means “this is the configured route if submitted,” not that an external connection exists or that an action will execute.

This gives pilot teams a way to test a proposed governance policy before they expose a production workflow. The first live connector and vertical workflow still require discovery evidence and explicit founder approval.
