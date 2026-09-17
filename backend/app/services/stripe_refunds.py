"""Narrow Stripe refund connector for the selected customer-remediation pilot.

This module is disabled unless server-side configuration explicitly enables it.
It never receives policy context or approval state: the control plane binds and
authorizes the action before this provider sees only provider-facing fields.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import UUID

from app.execution import ActionExecutionProvider, ExecutionResult, ExecutionStatus


@dataclass(frozen=True)
class StripeHttpResponse:
    status_code: int
    body: dict[str, Any]


class StripeTransport(Protocol):
    def post(self, path: str, form: dict[str, str], headers: dict[str, str]) -> StripeHttpResponse: ...
    def get(self, path: str, headers: dict[str, str]) -> StripeHttpResponse: ...


class UrllibStripeTransport:
    """Small standard-library transport so the adapter has no hidden SDK magic."""

    def __init__(self, api_base: str, timeout_seconds: float = 15) -> None:
        self.api_base = api_base.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def post(self, path: str, form: dict[str, str], headers: dict[str, str]) -> StripeHttpResponse:
        request = Request(
            f"{self.api_base}{path}",
            data=urlencode(form).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded", **headers},
            method="POST",
        )
        return self._send(request)

    def get(self, path: str, headers: dict[str, str]) -> StripeHttpResponse:
        return self._send(Request(f"{self.api_base}{path}", headers=headers, method="GET"))

    def _send(self, request: Request) -> StripeHttpResponse:
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - fixed configured provider base
                return StripeHttpResponse(response.status, json.loads(response.read().decode("utf-8")))
        except HTTPError as error:
            payload = error.read().decode("utf-8")
            try:
                body = json.loads(payload)
            except json.JSONDecodeError:
                body = {"error": {"message": "Stripe returned an unreadable error"}}
            return StripeHttpResponse(error.code, body)
        except (TimeoutError, URLError) as error:
            raise TimeoutError("Stripe request did not complete") from error


class StripeRefundProvider(ActionExecutionProvider):
    """Execute exactly one idempotent refund against Stripe's Refund API."""

    provider_name = "StripeRefundProvider"

    def __init__(self, secret_key: str, transport: StripeTransport) -> None:
        if not secret_key.strip():
            raise ValueError("Stripe secret key is required")
        self._secret_key = secret_key
        self._transport = transport

    def execute(self, request_id: UUID, parameters: dict[str, Any], idempotency_key: str, tenant_id: UUID | None = None) -> ExecutionResult:
        now = datetime.now(timezone.utc)
        try:
            form = self._refund_form(request_id, parameters)
        except ValueError as error:
            return self._failed(request_id, now, str(error), "invalid_refund_request")
        try:
            response = self._transport.post("/v1/refunds", form, self._headers(idempotency_key))
        except TimeoutError:
            return ExecutionResult(
                execution_id=f"stripe-pending-{request_id}", status=ExecutionStatus.TIMEOUT, provider_name=self.provider_name,
                transaction_reference=str(parameters.get("payment_reference", "unknown")), completed_at=now,
                error_message="Stripe refund outcome is unknown after transport timeout; reconcile using the provider reference.", raw_response={"code": "stripe_timeout"},
            )
        if not 200 <= response.status_code < 300:
            return self._failed(request_id, now, self._error_message(response.body), "stripe_api_error", response.body)
        return self._result_from_refund(request_id, response.body, now)

    def get_status(self, execution_id: str, provider_transaction_id: str | None = None) -> ExecutionStatus:
        reference = provider_transaction_id or execution_id
        if not reference.startswith("re_"):
            return ExecutionStatus.NOT_EXECUTED
        try:
            response = self._transport.get(f"/v1/refunds/{reference}", self._headers())
        except TimeoutError:
            return ExecutionStatus.UNKNOWN
        if not 200 <= response.status_code < 300:
            return ExecutionStatus.UNKNOWN
        return self._stripe_status(str(response.body.get("status", "")))

    def verify_result(self, execution_id: str, provider_transaction_id: str | None = None, expected_digest: str | None = None) -> bool:
        return self.get_status(execution_id, provider_transaction_id) == ExecutionStatus.EXECUTION_SUCCEEDED

    def cancel(self, execution_id: str, provider_transaction_id: str | None = None) -> ExecutionResult:
        return ExecutionResult(
            execution_id=execution_id,
            status=ExecutionStatus.NOT_EXECUTED,
            provider_name=self.provider_name,
            transaction_reference=provider_transaction_id or execution_id,
            completed_at=datetime.now(timezone.utc),
            error_message="Stripe refunds are not cancelled by this connector after submission; use reconciliation and a documented corrective action.",
        )

    def _headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self._secret_key}"}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    @staticmethod
    def _refund_form(request_id: UUID, parameters: dict[str, Any]) -> dict[str, str]:
        reference = str(parameters.get("payment_reference", "")).strip()
        amount_minor = parameters.get("amount_minor")
        if not reference or not (reference.startswith("pi_") or reference.startswith("ch_")):
            raise ValueError("payment_reference must be a Stripe PaymentIntent (pi_) or Charge (ch_) identifier")
        if isinstance(amount_minor, bool) or not str(amount_minor).isdigit() or int(amount_minor) <= 0:
            raise ValueError("amount_minor must be a positive integer in the payment currency's smallest unit")
        form = {
            "amount": str(amount_minor),
            "metadata[action_request_id]": str(request_id),
        }
        form["payment_intent" if reference.startswith("pi_") else "charge"] = reference
        reason = str(parameters.get("reason", ""))
        if reason in {"duplicate", "fraudulent", "requested_by_customer"}:
            form["reason"] = reason
        return form

    def _result_from_refund(self, request_id: UUID, refund: dict[str, Any], now: datetime) -> ExecutionResult:
        reference = str(refund.get("id") or f"stripe-refund-{request_id}")
        status = self._stripe_status(str(refund.get("status", "")))
        error = None if status == ExecutionStatus.EXECUTION_SUCCEEDED else self._error_message(refund)
        return ExecutionResult(
            execution_id=reference, status=status, provider_name=self.provider_name, transaction_reference=reference,
            completed_at=now, error_message=error, raw_response={"id": reference, "status": refund.get("status"), "payment_intent": refund.get("payment_intent"), "charge": refund.get("charge")},
        )

    @staticmethod
    def _stripe_status(status: str) -> ExecutionStatus:
        if status == "succeeded":
            return ExecutionStatus.EXECUTION_SUCCEEDED
        if status in {"pending", "requires_action"}:
            return ExecutionStatus.UNKNOWN
        return ExecutionStatus.EXECUTION_FAILED

    def _failed(self, request_id: UUID, now: datetime, message: str, code: str, body: dict[str, Any] | None = None) -> ExecutionResult:
        return ExecutionResult(
            execution_id=f"stripe-failed-{request_id}", status=ExecutionStatus.EXECUTION_FAILED, provider_name=self.provider_name,
            transaction_reference="unsubmitted", completed_at=now, error_message=message, raw_response={"code": code, "provider": body or {}},
        )

    @staticmethod
    def _error_message(body: dict[str, Any]) -> str:
        error = body.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return error["message"]
        return "Stripe did not confirm the refund outcome"
