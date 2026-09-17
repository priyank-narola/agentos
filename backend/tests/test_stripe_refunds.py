"""Offline contract tests for the disabled-by-default Stripe refund adapter."""

from uuid import uuid4

import pytest

from app.execution import ExecutionStatus
from app.config import Settings
import app.services.execution_provider_registry as registry_module
from app.execution import SandboxPaymentProvider
from app.services.execution_provider_registry import build_execution_provider_registry
from app.services.stripe_refunds import StripeHttpResponse, StripeRefundProvider
from app.financial import FinancialValidationError, validate_financial_action_parameters


class FakeStripeTransport:
    def __init__(self, response: StripeHttpResponse | None = None, timeout: bool = False) -> None:
        self.response = response or StripeHttpResponse(200, {"id": "re_demo_123", "status": "succeeded", "payment_intent": "pi_demo_123"})
        self.timeout = timeout
        self.calls: list[tuple[str, dict[str, str], dict[str, str]]] = []

    def post(self, path: str, form: dict[str, str], headers: dict[str, str]) -> StripeHttpResponse:
        self.calls.append((path, form, headers))
        if self.timeout:
            raise TimeoutError("simulated timeout")
        return self.response

    def get(self, path: str, headers: dict[str, str]) -> StripeHttpResponse:
        return self.response


def test_stripe_refund_uses_provider_idempotency_and_minor_amounts():
    transport = FakeStripeTransport()
    provider = StripeRefundProvider("sk_test_not_real", transport)
    result = provider.execute(
        uuid4(),
        {"payment_reference": "pi_demo_123", "amount_minor": 4900, "reason": "requested_by_customer"},
        "agentos-case-42",
    )
    assert result.status == ExecutionStatus.EXECUTION_SUCCEEDED
    assert result.transaction_reference == "re_demo_123"
    path, form, headers = transport.calls[0]
    assert path == "/v1/refunds"
    assert form["payment_intent"] == "pi_demo_123"
    assert form["amount"] == "4900"
    assert headers["Idempotency-Key"] == "agentos-case-42"
    assert "sk_test_not_real" not in result.raw_response.values()


def test_stripe_refund_fails_closed_for_ambiguous_amount_or_payment_reference():
    provider = StripeRefundProvider("sk_test_not_real", FakeStripeTransport())
    invalid_reference = provider.execute(uuid4(), {"payment_reference": "not-a-provider-id", "amount_minor": 4900}, "case-1")
    invalid_amount = provider.execute(uuid4(), {"payment_reference": "pi_demo_123", "amount_minor": "49.00"}, "case-2")
    assert invalid_reference.status == ExecutionStatus.EXECUTION_FAILED
    assert invalid_amount.status == ExecutionStatus.EXECUTION_FAILED


def test_stripe_refund_timeout_is_never_reported_as_success():
    provider = StripeRefundProvider("sk_test_not_real", FakeStripeTransport(timeout=True))
    result = provider.execute(uuid4(), {"payment_reference": "ch_demo_123", "amount_minor": 4900}, "case-timeout")
    assert result.status == ExecutionStatus.TIMEOUT
    assert "unknown" in (result.error_message or "").lower()


def test_stripe_connector_routing_is_explicit_opt_in(monkeypatch):
    monkeypatch.setattr(
        registry_module,
        "settings",
        Settings(stripe_refund_connector_enabled=True, stripe_secret_key="sk_test_not_real", stripe_api_base="https://api.stripe.com"),
    )
    registry = build_execution_provider_registry()
    assert isinstance(registry.resolve("issue_refund"), StripeRefundProvider)
    assert isinstance(registry.resolve("unrelated_action"), SandboxPaymentProvider)


def test_refund_contract_rejects_missing_provider_fields_before_approval():
    with pytest.raises(FinancialValidationError, match="Invalid issue_refund parameters"):
        validate_financial_action_parameters("issue_refund", {"ticket_id": "ZD-1", "amount": "49.00"})


def test_account_credit_contract_rejects_refund_fields_before_approval():
    with pytest.raises(FinancialValidationError, match="Invalid issue_account_credit parameters"):
        validate_financial_action_parameters("issue_account_credit", {"ticket_id": "ZD-1", "payment_reference": "pi_demo", "amount": "49.00"})
