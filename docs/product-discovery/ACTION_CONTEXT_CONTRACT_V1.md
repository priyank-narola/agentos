# Action Context Contract V1

## Status

Implemented in the prototype on 14 September 2026. This is a reusable product foundation, not proof of customer demand or a final vertical choice.

## Why it exists

A governed action must explain the business intent, the state that will change, and the available recovery path. An amount or API payload alone is not enough for a human reviewer to make a safe decision.

## Contract

An agent may include an optional `action_context` when it submits an action request:

```json
{
  "summary": "Apply a goodwill account credit after a delayed shipment",
  "target_system": "support-platform",
  "before": {"account_credit": "0.00"},
  "proposed_change": {"account_credit": "25.00"},
  "recovery_class": "COMPENSATABLE",
  "recovery_plan": "Record an offsetting debit with the original case reference."
}
```

`recovery_class` is one of:

- `REVERSIBLE` — the target system can restore the previous state.
- `COMPENSATABLE` — the original action cannot simply be undone, but a documented correcting action exists.
- `IRREVERSIBLE` — there is no reliable reversal; the approval experience must make this explicit.

## Security behaviour

- The context is captured only through the typed gateway field; callers cannot insert it into raw provider parameters.
- It is merged into the stored action payload and included in the SHA-256 digest used for approval binding and tamper detection.
- It is retained in the case file and returned to an approval reviewer.
- It is not passed to the execution provider as a provider-native parameter.
- Changing the context after an approval request is created blocks approval execution.
- Every action response now includes an execution receipt: provider evidence,
  provider reference, exact digest, outcome, and the declared recovery posture.

## Product impact

This works for a future support credit, refund, subscription change, customer-record update, finance approval, or operational change. It lets the existing authorization engine remain reusable while we validate the first market wedge through customer discovery.

The runtime gateway now exposes this contract in the operator interface. A user can attach the plain-language intent, target system, before state, proposed change, recovery class, and recovery plan before the agent action enters governance. The UI validates JSON state objects locally; the server remains the authority for typed validation, payload binding, policy, and approval.

## Remaining work

- Select the first real system and action from interview evidence.
- Implement a production connector and authoritative provider receipt for that action.
- Add a tested recovery or compensation workflow for the selected connector.
- Require `action_context` for that product action once the pilot contract is selected.
