# Audit Sequence Reliability V1

## Status

Implemented on 14 September 2026. This is a product-reliability improvement to the action-governance foundation.

## Problem solved

Database timestamps are not a causal ordering mechanism. Multiple audit events can be created during the same database clock instant, making a timestamp-only export unable to prove which event occurred first.

## Implementation

- Each action-scoped audit event now receives a durable positive `event_sequence`.
- Sequence allocation locks the owning action request, serializing gateway, approval, and webhook writers for that action.
- A database uniqueness constraint on `(action_request_id, event_sequence)` prevents duplicate positions.
- The additive migration backfills existing action-scoped audit events deterministically.
- Evidence exports and case-file timelines display events in sequence order.

Events that are not attached to an action request remain intentionally unsequenced.

## Migration repair

The repository had a broken Alembic reference: migration `0005` referenced a non-existent `0004` revision. Its parent is now correctly set to `20260908_0004`, restoring a single valid migration chain before adding revision `20260914_0006`.

## Verification target

Run `alembic upgrade head` against a dedicated PostgreSQL scratch database, followed by the PostgreSQL migration tests, before any hosted pilot. Local automated tests verify the application behavior but do not replace that database-specific validation.
