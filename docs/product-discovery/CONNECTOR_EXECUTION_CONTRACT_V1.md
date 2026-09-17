# Connector Execution Contract V1

## Purpose

The control plane can now route a governed action to a connector selected by action name. This is an implementation seam for a future verified pilot connector; it is not a claim that the product is integrated with a live customer system.

## Execution boundary

Before a connector is called, the product must already have:

- Resolved the principal, agent, action, resource, and tenant on the server.
- Evaluated deterministic policy and risk.
- Collected a typed action context when supplied, and bound it into the payload digest.
- Obtained and revalidated an approval when policy requires one.

The connector receives only executable parameters, an action-request identifier, a tenant identifier, and an idempotency key. It never receives the internal action-context envelope as if that were a provider-native field.

## Provider contract

Every connector implements `ActionExecutionProvider`:

- `execute` returns a provider name, execution identifier, authoritative reference, status, completion time, and safe evidence payload.
- `get_status`, `verify_result`, and `cancel` make later reconciliation and recovery possible.
- The provider must honor the supplied idempotency key within the tenant scope.
- Credentials and provider secrets are configuration concerns; they must never be submitted as action parameters or added to audit evidence.

`PaymentExecutionProvider` remains as a compatible specialization for existing financial code. The current `SandboxPaymentProvider` remains the default and makes no external calls or real transactions.

## Routing rules

`ExecutionProviderRegistry` chooses a provider by normalized action name and falls back to the explicit safe default. A single server-controlled factory composes the default routing rules for both gateway and approval services. A future selected connector can therefore be added through that composition point and tested without changing policy or approval logic.

No action name should be mapped to a production connector until all of these are true:

1. A design partner has confirmed the exact high-risk action and source/target systems.
2. The connector's least-privilege access, tenant isolation, idempotency, failure states, verification method, and recovery limits have been reviewed.
3. A non-production end-to-end test produces a receipt and evidence export that the partner can inspect.
4. The founder explicitly approves the pilot scope.

## Current limitation

There is no live connector, credential store, customer data connection, or real transaction in this repository. The first connector remains intentionally undecided until customer discovery identifies a narrowly valuable workflow.
