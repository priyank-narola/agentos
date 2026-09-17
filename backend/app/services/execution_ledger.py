"""Persistence of sandbox execution truth into the financial_executions ledger.

The ledger is written ONLY after the sandbox provider returns a definitive
outcome for an action request. No row is created merely because an action
request exists, and no row is created for NOT_EXECUTED or DUPLICATE outcomes
(the provider reports those only when no new execution occurred).

tenant_id is always derived from the trusted server-side execution context
(action request / approval tenant), never from client-supplied values.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ExecutionState, FinancialExecution, ReconciliationJob, ReconciliationJobStatus
from app.execution import ExecutionResult, ExecutionStatus
from app.financial import compute_payload_digest


# Canonical product-facing execution status vocabulary. Distinct from the raw
# provider/domain ExecutionState: it answers "what actually happened" in the
# four UI terms the product uses (NOT_EXECUTED / PENDING / EXECUTED / FAILED).
# The authoritative source remains the financial_executions ledger row.
_STATE_TO_CANONICAL_EXECUTION_STATUS: dict[ExecutionState, str] = {
    ExecutionState.SUCCEEDED: "EXECUTED",
    ExecutionState.FAILED: "FAILED",
    ExecutionState.PENDING: "PENDING",
    ExecutionState.SUBMITTED: "PENDING",
    ExecutionState.PROCESSING: "PENDING",
    ExecutionState.CANCELLED: "NOT_EXECUTED",
    ExecutionState.UNKNOWN: "PENDING",  # outcome not confirmed -> awaiting a definitive result
    ExecutionState.RECONCILIATION_REQUIRED: "PENDING",
}


def canonical_execution_status(state: ExecutionState | None) -> str:
    """Map a persisted ExecutionState to the canonical product status.

    Absence of a ledger row means no execution was authoritatively recorded,
    which the product presents as NOT_EXECUTED.
    """
    if state is None:
        return "NOT_EXECUTED"
    return _STATE_TO_CANONICAL_EXECUTION_STATUS.get(state, "NOT_EXECUTED")


def fetch_execution_status(db: Session, action_request_id: UUID) -> str:
    """Read the authoritative execution status for one action request.

    The ledger is tenant-scoped by construction (rows are persisted only from
    trusted server-side tenant context); the action_request_id lookup already
    implies the owning tenant boundary.
    """
    record = db.scalar(
        select(FinancialExecution)
        .where(FinancialExecution.action_request_id == action_request_id)
        .order_by(FinancialExecution.id)
        .limit(1)
    )
    return canonical_execution_status(record.status if record is not None else None)


_EXECUTION_STATUS_TO_STATE: dict[ExecutionStatus, ExecutionState] = {
    ExecutionStatus.EXECUTION_SUCCEEDED: ExecutionState.SUCCEEDED,
    ExecutionStatus.EXECUTION_FAILED: ExecutionState.FAILED,
    ExecutionStatus.TIMEOUT: ExecutionState.UNKNOWN,
    ExecutionStatus.CANCELLED: ExecutionState.CANCELLED,
    ExecutionStatus.UNKNOWN: ExecutionState.UNKNOWN,
}


def execution_state_for(status: ExecutionStatus) -> ExecutionState | None:
    """Map a provider ExecutionStatus to the persisted ExecutionState domain enum.

    NOT_EXECUTED and DUPLICATE represent the absence of a new execution and
    therefore map to None (no ledger row).
    """
    return _EXECUTION_STATUS_TO_STATE.get(status)


def persist_execution_result(
    db: Session,
    *,
    action_request_id: UUID,
    tenant_id: UUID,
    result: ExecutionResult,
    parameters: dict,
) -> FinancialExecution | None:
    """Persist one FinancialExecution ledger row for a definitive provider result.

    Idempotent per action request: if a ledger row already exists for the
    request, it is returned unchanged and no duplicate row is inserted.
    """
    existing = db.scalar(select(FinancialExecution).where(FinancialExecution.action_request_id == action_request_id))
    if existing is not None:
        return existing

    state = execution_state_for(result.status)
    if state is None:
        return None

    record = FinancialExecution(
        tenant_id=tenant_id,
        action_request_id=action_request_id,
        provider_name=result.provider_name,
        provider_transaction_id=result.transaction_reference,
        provider_request_id=result.execution_id,
        status=state,
        payload_digest=compute_payload_digest(parameters or {}),
        error_code=(result.raw_response or {}).get("code"),
        error_message=result.error_message,
    )
    db.add(record)
    db.flush()
    if state == ExecutionState.UNKNOWN:
        # This durable job contains only provider references held in the ledger;
        # it never receives action parameters and cannot resubmit the action.
        db.add(
            ReconciliationJob(
                tenant_id=tenant_id,
                action_request_id=action_request_id,
                status=ReconciliationJobStatus.PENDING.value,
                next_check_at=datetime.now(timezone.utc),
            )
        )
    return record
