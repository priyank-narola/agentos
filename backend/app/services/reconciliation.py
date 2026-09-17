"""Operator-driven reconciliation for uncertain provider outcomes.

This is deliberately a status-read workflow, not a retry mechanism. It is the
safe path after a timeout/unknown result: use the provider's durable reference
to learn what happened, record the result, and keep ambiguity visible if the
provider cannot confirm it.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    ActionRequest,
    ActorType,
    AuditEvent,
    ExecutionState,
    FinancialExecution,
    Principal,
    PrincipalStatus,
    PrincipalType,
    ReconciliationJob,
    ReconciliationJobStatus,
    TenantRole,
)
from app.schemas import ReconciliationCase, ReconciliationResult
from app.services.audit_sequence import next_action_event_sequence
from app.services.execution_lifecycle import (
    ExecutionLifecycleError,
    state_from_reconciliation_status,
    validate_execution_transition,
)
from app.services.execution_provider_registry import ExecutionProviderRegistry, build_execution_provider_registry
from app.services.authorization import RoleAuthorizationError, require_any_role


class ReconciliationError(ValueError):
    """Base reconciliation failure."""


class ReconciliationNotFoundError(ReconciliationError):
    """The requested execution is not visible in the trusted tenant scope."""


class ReconciliationConflictError(ReconciliationError):
    """The execution is terminal or cannot be safely reconciled."""


class ReconciliationForbiddenError(ReconciliationError):
    """The operator is not an independent active human in this tenant."""


_RECONCILABLE_STATES = {ExecutionState.UNKNOWN, ExecutionState.RECONCILIATION_REQUIRED}
_TERMINAL_STATES = {ExecutionState.SUCCEEDED, ExecutionState.FAILED, ExecutionState.CANCELLED}
_RETRY_DELAYS = (timedelta(minutes=5), timedelta(minutes=15), timedelta(hours=1))


class ReconciliationService:
    def __init__(self, db: Session, execution_providers: ExecutionProviderRegistry | None = None) -> None:
        self.db = db
        self.execution_providers = execution_providers or build_execution_provider_registry()

    def list(self, tenant_id: UUID) -> list[ReconciliationCase]:
        executions = list(
            self.db.scalars(
                select(FinancialExecution)
                .join(ActionRequest, FinancialExecution.action_request_id == ActionRequest.id)
                .where(
                    FinancialExecution.tenant_id == tenant_id,
                    ActionRequest.tenant_id == tenant_id,
                    FinancialExecution.status.in_(_RECONCILABLE_STATES),
                )
                .options(
                    joinedload(FinancialExecution.action_request).joinedload(ActionRequest.action),
                    joinedload(FinancialExecution.action_request).joinedload(ActionRequest.resource),
                )
                .order_by(FinancialExecution.updated_at.asc(), FinancialExecution.created_at.asc())
            ).unique().all()
        )
        return [self._case(execution) for execution in executions]

    def reconcile(
        self,
        action_request_id: UUID,
        actor_principal_id: UUID,
        tenant_id: UUID,
    ) -> ReconciliationResult:
        execution = self.db.scalar(
            select(FinancialExecution)
            .join(ActionRequest, FinancialExecution.action_request_id == ActionRequest.id)
            .where(
                FinancialExecution.action_request_id == action_request_id,
                FinancialExecution.tenant_id == tenant_id,
                ActionRequest.tenant_id == tenant_id,
            )
            .options(
                joinedload(FinancialExecution.action_request).joinedload(ActionRequest.action),
                joinedload(FinancialExecution.action_request).joinedload(ActionRequest.resource),
            )
            .with_for_update()
        )
        if execution is None:
            raise ReconciliationNotFoundError("Execution not found in tenant context")
        if execution.status not in _RECONCILABLE_STATES:
            raise ReconciliationConflictError(
                f"Execution is {execution.status.value} and does not require reconciliation"
            )

        request = execution.action_request
        actor = self.db.get(Principal, actor_principal_id)
        if (
            actor is None
            or actor.tenant_id != tenant_id
            or actor.status != PrincipalStatus.ACTIVE
            or actor.type != PrincipalType.HUMAN
        ):
            raise ReconciliationForbiddenError("An active human operator in this tenant is required")
        if actor.id == request.principal_id:
            raise ReconciliationForbiddenError("Requester cannot reconcile their own uncertain action")
        try:
            require_any_role(
                self.db,
                tenant_id=tenant_id,
                principal_id=actor.id,
                roles={TenantRole.ADMIN, TenantRole.OPERATOR},
            )
        except RoleAuthorizationError as exc:
            raise ReconciliationForbiddenError(str(exc)) from exc

        provider = self.execution_providers.resolve(request.action.name)
        previous_state = execution.status
        observed_status = provider.get_status(
            execution.provider_request_id,
            execution.provider_transaction_id,
        )
        target_state = state_from_reconciliation_status(observed_status)
        try:
            validate_execution_transition(previous_state, target_state)
        except ExecutionLifecycleError as exc:
            raise ReconciliationConflictError(str(exc)) from exc

        execution.status = target_state
        if target_state == ExecutionState.RECONCILIATION_REQUIRED:
            execution.error_message = "Provider outcome remains unconfirmed after reconciliation check"
        else:
            execution.error_message = None if target_state == ExecutionState.SUCCEEDED else execution.error_message

        now = datetime.now(timezone.utc)
        self.db.add(
            AuditEvent(
                tenant_id=tenant_id,
                event_type="EXECUTION_RECONCILIATION_CHECKED",
                actor_type=ActorType.PRINCIPAL,
                actor_id=actor.id,
                agent_id=request.agent_id,
                action_request_id=request.id,
                event_sequence=next_action_event_sequence(self.db, request.id),
                event_data={
                    "provider": execution.provider_name,
                    "provider_request_id": execution.provider_request_id,
                    "previous_state": previous_state.value,
                    "observed_provider_status": observed_status.value,
                    "resulting_state": target_state.value,
                    "checked_at": now.isoformat(),
                },
            )
        )
        if target_state == ExecutionState.RECONCILIATION_REQUIRED:
            self.db.add(
                AuditEvent(
                    tenant_id=tenant_id,
                    event_type="EXECUTION_RECONCILIATION_REQUIRED",
                    actor_type=ActorType.PRINCIPAL,
                    actor_id=actor.id,
                    agent_id=request.agent_id,
                    action_request_id=request.id,
                    event_sequence=next_action_event_sequence(self.db, request.id),
                    event_data={
                        "provider": execution.provider_name,
                        "reason": "Provider readback did not confirm a terminal outcome",
                    },
                )
            )
        self._sync_job(execution, now=now, terminal=target_state in _TERMINAL_STATES)
        self.db.commit()
        self.db.refresh(execution)
        return ReconciliationResult(
            **self._case(execution).model_dump(),
            previous_state=previous_state,
            observed_provider_status=observed_status.value,
            reconciled_at=now,
        )

    def run_due_checks(self, *, limit: int = 25, now: datetime | None = None) -> dict[str, int]:
        """Process due status-readback jobs without ever calling provider.execute.

        A scheduled worker can invoke this method. It only calls ``get_status``
        using durable ledger references. After bounded ambiguous readbacks, the
        job escalates and stays visible to an operator; it never retries a
        consequential write.
        """
        current_time = now or datetime.now(timezone.utc)
        jobs = list(
            self.db.scalars(
                select(ReconciliationJob)
                .where(
                    ReconciliationJob.status == ReconciliationJobStatus.PENDING.value,
                    ReconciliationJob.next_check_at <= current_time,
                )
                .order_by(ReconciliationJob.next_check_at, ReconciliationJob.created_at)
                .limit(limit)
                .with_for_update()
            ).all()
        )
        completed = 0
        rescheduled = 0
        escalated = 0
        for job in jobs:
            execution = self.db.scalar(
                select(FinancialExecution)
                .where(
                    FinancialExecution.action_request_id == job.action_request_id,
                    FinancialExecution.tenant_id == job.tenant_id,
                )
                .options(joinedload(FinancialExecution.action_request).joinedload(ActionRequest.action))
            )
            if execution is None or execution.status in _TERMINAL_STATES:
                job.status = ReconciliationJobStatus.COMPLETED.value
                job.last_checked_at = current_time
                completed += 1
                continue
            request = execution.action_request
            provider = self.execution_providers.resolve(request.action.name)
            previous_state = execution.status
            try:
                observed_status = provider.get_status(execution.provider_request_id, execution.provider_transaction_id)
                target_state = state_from_reconciliation_status(observed_status)
                validate_execution_transition(previous_state, target_state)
            except Exception as error:
                observed_status = None
                target_state = ExecutionState.RECONCILIATION_REQUIRED
                job.last_error = "Provider status readback failed; action was not retried"
                # Do not surface provider exception details in durable job data.
                _ = error

            execution.status = target_state
            job.attempt_count += 1
            job.last_checked_at = current_time
            self._append_system_audit(
                execution,
                previous_state=previous_state,
                observed_status=observed_status.value if observed_status is not None else "READBACK_ERROR",
                target_state=target_state,
                checked_at=current_time,
            )
            if target_state in _TERMINAL_STATES:
                job.status = ReconciliationJobStatus.COMPLETED.value
                job.last_error = None
                completed += 1
            elif job.attempt_count >= len(_RETRY_DELAYS):
                job.status = ReconciliationJobStatus.ESCALATED.value
                job.last_error = job.last_error or "Provider outcome remains unconfirmed after bounded status checks"
                execution.error_message = job.last_error
                self._append_escalation_audit(execution, current_time)
                escalated += 1
            else:
                job.status = ReconciliationJobStatus.PENDING.value
                job.next_check_at = current_time + _RETRY_DELAYS[job.attempt_count - 1]
                execution.error_message = "Provider outcome remains unconfirmed; a status-only follow-up is scheduled"
                rescheduled += 1
        self.db.commit()
        return {"claimed": len(jobs), "completed": completed, "rescheduled": rescheduled, "escalated": escalated}

    @staticmethod
    def _case(execution: FinancialExecution) -> ReconciliationCase:
        request = execution.action_request
        return ReconciliationCase(
            action_request_id=request.id,
            requester_principal_id=request.principal_id,
            action_name=request.action.name,
            resource_key=request.resource.resource_key,
            execution_state=execution.status,
            provider_name=execution.provider_name,
            provider_reference=execution.provider_transaction_id,
            provider_request_id=execution.provider_request_id,
            error_code=execution.error_code,
            error_message=execution.error_message,
            requested_at=request.requested_at,
            updated_at=execution.updated_at,
        )

    def _sync_job(self, execution: FinancialExecution, *, now: datetime, terminal: bool) -> None:
        job = self.db.scalar(select(ReconciliationJob).where(ReconciliationJob.action_request_id == execution.action_request_id))
        if job is None:
            if terminal:
                return
            job = ReconciliationJob(
                tenant_id=execution.tenant_id,
                action_request_id=execution.action_request_id,
                status=ReconciliationJobStatus.PENDING.value,
                next_check_at=now + _RETRY_DELAYS[0],
            )
            self.db.add(job)
            return
        job.last_checked_at = now
        if terminal:
            job.status = ReconciliationJobStatus.COMPLETED.value
            job.last_error = None
        elif job.status != ReconciliationJobStatus.ESCALATED.value:
            job.status = ReconciliationJobStatus.PENDING.value
            job.next_check_at = now + _RETRY_DELAYS[min(job.attempt_count, len(_RETRY_DELAYS) - 1)]

    def _append_system_audit(
        self,
        execution: FinancialExecution,
        *,
        previous_state: ExecutionState,
        observed_status: str,
        target_state: ExecutionState,
        checked_at: datetime,
    ) -> None:
        request = execution.action_request
        self.db.add(AuditEvent(
            tenant_id=execution.tenant_id,
            event_type="EXECUTION_RECONCILIATION_WORKER_CHECKED",
            actor_type=ActorType.SYSTEM,
            actor_id=None,
            agent_id=request.agent_id,
            action_request_id=request.id,
            event_sequence=next_action_event_sequence(self.db, request.id),
            event_data={
                "provider": execution.provider_name,
                "provider_request_id": execution.provider_request_id,
                "previous_state": previous_state.value,
                "observed_provider_status": observed_status,
                "resulting_state": target_state.value,
                "checked_at": checked_at.isoformat(),
                "operation": "status_readback_only",
            },
        ))

    def _append_escalation_audit(self, execution: FinancialExecution, checked_at: datetime) -> None:
        request = execution.action_request
        self.db.add(AuditEvent(
            tenant_id=execution.tenant_id,
            event_type="EXECUTION_RECONCILIATION_ESCALATED",
            actor_type=ActorType.SYSTEM,
            actor_id=None,
            agent_id=request.agent_id,
            action_request_id=request.id,
            event_sequence=next_action_event_sequence(self.db, request.id),
            event_data={"reason": "bounded_status_readbacks_exhausted", "checked_at": checked_at.isoformat()},
        ))
