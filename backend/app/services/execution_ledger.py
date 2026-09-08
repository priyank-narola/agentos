"""Persistence of sandbox execution truth into the financial_executions ledger.

The ledger is written ONLY after the sandbox provider returns a definitive
outcome for an action request. No row is created merely because an action
request exists, and no row is created for NOT_EXECUTED or DUPLICATE outcomes
(the provider reports those only when no new execution occurred).

tenant_id is always derived from the trusted server-side execution context
(action request / approval tenant), never from client-supplied values.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ExecutionState, FinancialExecution
from app.execution import ExecutionResult, ExecutionStatus
from app.financial import compute_payload_digest


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
    return record
