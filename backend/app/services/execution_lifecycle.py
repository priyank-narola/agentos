"""Safe persisted-execution lifecycle rules shared by webhooks and reconciliation.

An uncertain provider response is never converted into success by inference.
Only a later provider status check or verified webhook can move an execution to
a terminal result.
"""

from app.db.models import ExecutionState
from app.execution import ExecutionStatus


class ExecutionLifecycleError(ValueError):
    """Raised when an execution state change would violate the durable lifecycle."""


ALLOWED_EXECUTION_TRANSITIONS: dict[ExecutionState, set[ExecutionState]] = {
    ExecutionState.PENDING: {
        ExecutionState.SUBMITTED,
        ExecutionState.PROCESSING,
        ExecutionState.SUCCEEDED,
        ExecutionState.FAILED,
        ExecutionState.UNKNOWN,
        ExecutionState.CANCELLED,
    },
    ExecutionState.SUBMITTED: {
        ExecutionState.PROCESSING,
        ExecutionState.SUCCEEDED,
        ExecutionState.FAILED,
        ExecutionState.UNKNOWN,
        ExecutionState.CANCELLED,
        ExecutionState.RECONCILIATION_REQUIRED,
    },
    ExecutionState.PROCESSING: {
        ExecutionState.SUCCEEDED,
        ExecutionState.FAILED,
        ExecutionState.UNKNOWN,
        ExecutionState.CANCELLED,
        ExecutionState.RECONCILIATION_REQUIRED,
    },
    ExecutionState.UNKNOWN: {
        ExecutionState.SUCCEEDED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
        ExecutionState.RECONCILIATION_REQUIRED,
    },
    ExecutionState.RECONCILIATION_REQUIRED: {
        ExecutionState.SUCCEEDED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    },
    ExecutionState.SUCCEEDED: set(),
    ExecutionState.FAILED: set(),
    ExecutionState.CANCELLED: set(),
}


def validate_execution_transition(current: ExecutionState, target: ExecutionState) -> None:
    """Reject impossible or out-of-order execution outcomes."""
    if current == target:
        return
    if target not in ALLOWED_EXECUTION_TRANSITIONS.get(current, set()):
        raise ExecutionLifecycleError(
            f"Illegal execution state transition from {current.value} to {target.value}"
        )


def state_from_reconciliation_status(status: ExecutionStatus) -> ExecutionState:
    """Map provider readback to a safe persisted outcome.

    Ambiguous provider answers intentionally remain in the reconciliation path;
    the system must never retry a consequential write merely because a readback
    is inconclusive.
    """
    if status == ExecutionStatus.EXECUTION_SUCCEEDED:
        return ExecutionState.SUCCEEDED
    if status == ExecutionStatus.EXECUTION_FAILED:
        return ExecutionState.FAILED
    if status == ExecutionStatus.CANCELLED:
        return ExecutionState.CANCELLED
    return ExecutionState.RECONCILIATION_REQUIRED
