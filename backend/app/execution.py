from __future__ import annotations

import abc
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID


class ExecutionStatus(str, Enum):
    NOT_EXECUTED = "NOT_EXECUTED"
    EXECUTION_SUCCEEDED = "EXECUTION_SUCCEEDED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    TIMEOUT = "TIMEOUT"
    DUPLICATE = "DUPLICATE"
    UNKNOWN = "UNKNOWN"
    CANCELLED = "CANCELLED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


class InvalidExecutionStateTransitionError(ValueError):
    """Raised when an invalid state transition is attempted in the Execution State Machine."""
    pass


class ExecutionStateMachine:
    """
    Formal Financial Execution State Machine enforcing valid state transitions.
    States: PENDING -> SUBMITTED -> PROCESSING -> SUCCEEDED | FAILED | UNKNOWN | RECONCILIATION_REQUIRED
    Terminal states: SUCCEEDED, FAILED, CANCELLED
    """

    ALLOWED_TRANSITIONS: dict[ExecutionStatus, set[ExecutionStatus]] = {
        ExecutionStatus.NOT_EXECUTED: {
            ExecutionStatus.EXECUTION_SUCCEEDED,
            ExecutionStatus.EXECUTION_FAILED,
            ExecutionStatus.TIMEOUT,
            ExecutionStatus.UNKNOWN,
            ExecutionStatus.CANCELLED,
        },
        ExecutionStatus.UNKNOWN: {
            ExecutionStatus.EXECUTION_SUCCEEDED,
            ExecutionStatus.EXECUTION_FAILED,
            ExecutionStatus.RECONCILIATION_REQUIRED,
            ExecutionStatus.CANCELLED,
        },
        ExecutionStatus.RECONCILIATION_REQUIRED: {
            ExecutionStatus.EXECUTION_SUCCEEDED,
            ExecutionStatus.EXECUTION_FAILED,
            ExecutionStatus.CANCELLED,
        },
        # Terminal states have NO outgoing transitions to PENDING/SUBMITTED/EXECUTION_SUCCEEDED
        ExecutionStatus.EXECUTION_SUCCEEDED: set(),
        ExecutionStatus.EXECUTION_FAILED: set(),
        ExecutionStatus.CANCELLED: set(),
        ExecutionStatus.DUPLICATE: set(),
    }

    @classmethod
    def validate_transition(cls, current: ExecutionStatus, target: ExecutionStatus) -> None:
        if current == target:
            return
        allowed = cls.ALLOWED_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidExecutionStateTransitionError(
                f"Illegal execution state transition from {current.value} to {target.value}"
            )


@dataclass(frozen=True)
class ExecutionResult:
    execution_id: str
    status: ExecutionStatus
    provider_name: str
    transaction_reference: str
    completed_at: datetime
    error_message: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


class ActionExecutionProvider(abc.ABC):
    """Provider contract for a governed action execution.

    The contract deliberately carries only the executable action parameters.
    Policy evaluation, approval, action context, evidence binding, and audit
    sequencing remain the control plane's responsibility, rather than being
    delegated to a connector implementation.
    """

    @abc.abstractmethod
    def execute(self, request_id: UUID, parameters: dict[str, Any], idempotency_key: str, tenant_id: UUID | None = None) -> ExecutionResult:
        """Execute a governed action via the provider."""
        pass

    @abc.abstractmethod
    def get_status(self, execution_id: str, provider_transaction_id: str | None = None) -> ExecutionStatus:
        """Retrieve execution status for a given execution ID."""
        pass

    @abc.abstractmethod
    def verify_result(self, execution_id: str, provider_transaction_id: str | None = None, expected_digest: str | None = None) -> bool:
        """Verify whether an execution completed successfully and matches expected payload digest."""
        pass

    @abc.abstractmethod
    def cancel(self, execution_id: str, provider_transaction_id: str | None = None) -> ExecutionResult:
        """Attempt cancellation of a pending or submitted action execution."""
        pass


class PaymentExecutionProvider(ActionExecutionProvider):
    """Backward-compatible name for the original financial provider contract.

    Existing payment connectors can keep inheriting from this class while new
    non-financial connectors use :class:`ActionExecutionProvider` directly.
    """


class SandboxPaymentProvider(PaymentExecutionProvider):
    """
    Safe, provider-agnostic mock/sandbox payment execution engine.
    Supports deterministic transaction IDs, idempotency deduplication,
    simulated success, failure, timeout, and duplicate request handling.
    Zero real money movement or external API calls.
    """

    def __init__(self) -> None:
        self._history: dict[str, ExecutionResult] = {}
        self._idempotency_map: dict[str, ExecutionResult] = {}

    def execute(self, request_id: UUID, parameters: dict[str, Any], idempotency_key: str, tenant_id: UUID | None = None) -> ExecutionResult:
        now = datetime.now(timezone.utc)
        idem_scope = f"{tenant_id}:{idempotency_key}" if tenant_id else idempotency_key

        # 1. Idempotency Check
        if idem_scope in self._idempotency_map:
            previous = self._idempotency_map[idem_scope]
            return ExecutionResult(
                execution_id=previous.execution_id,
                status=ExecutionStatus.DUPLICATE,
                provider_name="SandboxPaymentProvider",
                transaction_reference=previous.transaction_reference,
                completed_at=now,
                error_message="Duplicate execution request ignored by provider idempotency check",
                raw_response=previous.raw_response,
            )

        # 2. Generate Deterministic Transaction Reference
        raw_sig = f"sandbox:{tenant_id}:{request_id}:{idempotency_key}:{json.dumps(parameters, sort_keys=True)}"
        tx_hash = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()[:16]
        tx_ref = parameters.get("transaction_reference", f"TX-SB-{tx_hash.upper()}")
        execution_id = f"exec-sb-{tx_hash}"

        # 3. Simulated Error/Timeout Parameter Hooks for Testing
        if parameters.get("force_timeout") is True:
            result = ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.TIMEOUT,
                provider_name="SandboxPaymentProvider",
                transaction_reference=tx_ref,
                completed_at=now,
                error_message="Simulated provider timeout during transaction processing",
                raw_response={"code": "ERR_SANDBOX_TIMEOUT"},
            )
        elif parameters.get("force_failure") is True:
            result = ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.EXECUTION_FAILED,
                provider_name="SandboxPaymentProvider",
                transaction_reference=tx_ref,
                completed_at=now,
                error_message="Simulated provider failure: Insufficient sandbox ledger balance",
                raw_response={"code": "ERR_INSUFFICIENT_FUNDS"},
            )
        else:
            # 4. Successful Execution
            result = ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.EXECUTION_SUCCEEDED,
                provider_name="SandboxPaymentProvider",
                transaction_reference=tx_ref,
                completed_at=now,
                error_message=None,
                raw_response={
                    "status": "SETTLED",
                    "cleared_amount": str(parameters.get("amount", "0.00")),
                    "currency": parameters.get("currency", "USD"),
                    "beneficiary_id": parameters.get("beneficiary_id"),
                    "settlement_time": now.isoformat(),
                },
            )

        # Store in provider history
        self._history[execution_id] = result
        self._idempotency_map[idem_scope] = result
        return result

    def get_status(self, execution_id: str, provider_transaction_id: str | None = None) -> ExecutionStatus:
        result = self._history.get(execution_id)
        return result.status if result else ExecutionStatus.NOT_EXECUTED

    def verify_result(self, execution_id: str, provider_transaction_id: str | None = None, expected_digest: str | None = None) -> bool:
        result = self._history.get(execution_id)
        return result is not None and result.status == ExecutionStatus.EXECUTION_SUCCEEDED

    def cancel(self, execution_id: str, provider_transaction_id: str | None = None) -> ExecutionResult:
        result = self._history.get(execution_id)
        now = datetime.now(timezone.utc)
        if not result or result.status == ExecutionStatus.EXECUTION_SUCCEEDED:
            return ExecutionResult(
                execution_id=execution_id,
                status=result.status if result else ExecutionStatus.NOT_EXECUTED,
                provider_name="SandboxPaymentProvider",
                transaction_reference=result.transaction_reference if result else "N/A",
                completed_at=now,
                error_message="Cannot cancel settled transaction",
            )
        cancelled = ExecutionResult(
            execution_id=execution_id,
            status=ExecutionStatus.CANCELLED,
            provider_name="SandboxPaymentProvider",
            transaction_reference=result.transaction_reference,
            completed_at=now,
            error_message="Transaction cancelled in sandbox",
        )
        self._history[execution_id] = cancelled
        return cancelled
