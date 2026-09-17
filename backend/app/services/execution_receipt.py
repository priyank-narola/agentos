"""Product-facing execution evidence for a governed action.

The current persistence table is named ``financial_executions`` because the
prototype started with a treasury workflow. This adapter deliberately exposes a
provider-neutral receipt so the action-control product can support a future
support, CRM, or operations connector without leaking that implementation
detail into its public contract.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import FinancialExecution
from app.schemas import ActionContext, ExecutionReceipt
from app.services.execution_ledger import canonical_execution_status


def build_execution_receipt(
    db: Session,
    action_request_id: UUID,
    action_context: ActionContext | None = None,
) -> ExecutionReceipt:
    """Return the authoritative provider outcome and recovery posture.

    A recovery posture is descriptive only. It never asserts that a reversal or
    compensation action has been performed; that requires a future connector
    workflow and its own governed action.
    """
    record = db.scalar(
        select(FinancialExecution)
        .where(FinancialExecution.action_request_id == action_request_id)
        .order_by(FinancialExecution.id)
        .limit(1)
    )
    status = canonical_execution_status(record.status if record is not None else None)
    recovery_status = _recovery_status(status, action_context)
    return ExecutionReceipt(
        status=status,
        evidence_status="RECORDED" if record is not None else "NOT_RECORDED",
        provider_name=record.provider_name if record is not None else None,
        provider_reference=record.provider_transaction_id if record is not None else None,
        provider_request_id=record.provider_request_id if record is not None else None,
        payload_digest=record.payload_digest if record is not None else None,
        error_code=record.error_code if record is not None else None,
        error_message=record.error_message if record is not None else None,
        recorded_at=record.created_at if record is not None else None,
        recovery_status=recovery_status,
        recovery_plan=action_context.recovery_plan if action_context is not None else None,
    )


def _recovery_status(status: str, context: ActionContext | None) -> str:
    if status == "NOT_EXECUTED":
        return "NOT_STARTED"
    if status == "PENDING":
        return "AWAITING_OUTCOME"
    if status == "FAILED":
        return "NOT_REQUIRED"
    if context is None:
        return "NOT_DECLARED"
    if context.recovery_class.value == "IRREVERSIBLE":
        return "NOT_AVAILABLE"
    return "AVAILABLE"
