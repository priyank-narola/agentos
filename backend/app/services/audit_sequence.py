"""Causal ordering for audit events belonging to a governed action."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import ActionRequest, AuditEvent


def next_action_event_sequence(db: Session, action_request_id: UUID | None) -> int | None:
    """Allocate the next durable sequence for one action's audit timeline.

    Row-locking the action request serializes writers from the gateway,
    approvals, and webhooks. A database uniqueness constraint is the final
    protection against duplicate sequence allocation.
    """
    if action_request_id is None:
        return None
    cache_key = str(action_request_id)
    sequence_cache: dict[str, int] = db.info.setdefault("agentos_action_event_sequences", {})
    if cache_key in sequence_cache:
        sequence_cache[cache_key] += 1
        return sequence_cache[cache_key]

    locked_request = db.scalar(
        select(ActionRequest.id)
        .where(ActionRequest.id == action_request_id)
        .with_for_update()
    )
    if locked_request is None:
        raise ValueError("Cannot create an audit sequence for a missing action request")
    previous = db.scalar(
        select(func.max(AuditEvent.event_sequence))
        .where(AuditEvent.action_request_id == action_request_id)
    )
    sequence_cache[cache_key] = int(previous or 0) + 1
    return sequence_cache[cache_key]
