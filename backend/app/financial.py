from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP", "CAD", "AUD", "JPY"}

FORBIDDEN_FINANCIAL_KEYS = {
    "principal_id",
    "agent_id",
    "delegation_id",
    "policy_id",
    "policy_effect",
    "policy_decision",
    "decision",
    "risk_level",
    "risk_score",
    "risk_classification",
    "approval_status",
    "approved",
    "override",
    "authorization",
    "authorization_override",
    "execution_status",
    "decided_by",
    "_action_context",
}

# Reserved server-side envelope key. It carries the human-readable business
# context that was approved alongside an action's executable parameters. A
# caller must use the typed `action_context` field on GatewayRequestCreate;
# allowing this key directly inside parameters would bypass that validation.
ACTION_CONTEXT_PARAMETER_KEY = "_action_context"


class FinancialValidationError(ValueError):
    """Raised when financial action parameter validation fails."""
    pass


class FinancialRiskConfig(BaseModel):
    """Configurable server-side financial risk thresholds."""
    low_threshold: Decimal = Field(default=Decimal("1000.00"))
    elevated_threshold: Decimal = Field(default=Decimal("5000.00"))
    approval_threshold: Decimal = Field(default=Decimal("10000.00"))
    critical_threshold: Decimal = Field(default=Decimal("50000.00"))


class WireTransferContract(BaseModel):
    """
    Typed, strictly-validated contract for financial wire transfer action.
    Enforces server-side field constraints and rejects unauthorized key overrides.
    """
    model_config = ConfigDict(extra="forbid")

    amount: Decimal = Field(..., gt=0, description="Transfer amount must be strictly greater than 0")
    currency: str = Field(..., min_length=3, max_length=3, description="3-letter ISO currency code")
    beneficiary_id: str = Field(..., min_length=1, max_length=200, description="Unique beneficiary identifier")
    source_account_id: str = Field(..., min_length=1, max_length=200, description="Source account identifier")
    destination_account_id: str = Field(..., min_length=1, max_length=200, description="Destination account identifier")
    transaction_reference: str = Field(..., min_length=1, max_length=200, description="Unique transaction reference string")
    
    invoice_id: str | None = Field(default=None, max_length=200)
    purpose: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] | None = Field(default=None)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        curr = v.strip().upper()
        if curr not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency '{v}'. Supported: {sorted(SUPPORTED_CURRENCIES)}")
        return curr

    @field_validator("beneficiary_id", "source_account_id", "destination_account_id", "transaction_reference")
    @classmethod
    def validate_non_empty_str(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or whitespace only")
        return cleaned


class CustomerRefundContract(BaseModel):
    """Minimum provider-facing fields for the selected refund pilot action."""

    model_config = ConfigDict(extra="forbid")

    ticket_id: str = Field(min_length=1, max_length=200)
    payment_reference: str = Field(min_length=1, max_length=200)
    customer_account_id: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=0)
    amount_minor: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    remedy: str = Field(default="refund", pattern="^refund$")
    reason: str = Field(min_length=1, max_length=500)
    transaction_reference: str = Field(min_length=1, max_length=200)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        currency = value.strip().upper()
        if currency not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency '{value}'. Supported: {sorted(SUPPORTED_CURRENCIES)}")
        return currency

    @field_validator("ticket_id", "payment_reference", "customer_account_id", "reason", "transaction_reference")
    @classmethod
    def validate_non_empty_str(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or whitespace only")
        return cleaned


class CustomerAccountCreditContract(BaseModel):
    """Minimum provider-facing fields for a sandbox account-credit remedy.

    A credit is deliberately a separate action contract from a refund. A
    payment reference is not silently repurposed as an account balance change,
    and a future billing connector must opt in to this action explicitly.
    """

    model_config = ConfigDict(extra="forbid")

    ticket_id: str = Field(min_length=1, max_length=200)
    billing_reference: str = Field(min_length=1, max_length=200)
    customer_account_id: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=0)
    amount_minor: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    remedy: str = Field(default="account_credit", pattern="^account_credit$")
    reason: str = Field(min_length=1, max_length=500)
    transaction_reference: str = Field(min_length=1, max_length=200)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        currency = value.strip().upper()
        if currency not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency '{value}'. Supported: {sorted(SUPPORTED_CURRENCIES)}")
        return currency

    @field_validator("ticket_id", "billing_reference", "customer_account_id", "reason", "transaction_reference")
    @classmethod
    def validate_non_empty_str(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or whitespace only")
        return cleaned


def compute_payload_digest(parameters: dict[str, Any]) -> str:
    """
    Compute a deterministic SHA-256 digest over canonical JSON parameter payload.
    Used for binding approved payloads to execution requests.
    """
    canonical_json = json.dumps(parameters, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def executable_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
    """Return only the provider-facing portion of a governed action payload.

    The action context is intentionally included in the digest and audit record,
    but is not sent to a provider as if it were a provider-native field.
    """
    return {key: value for key, value in parameters.items() if key != ACTION_CONTEXT_PARAMETER_KEY}


def validate_financial_action_parameters(action_name: str, parameters: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """
    Validates parameters for known financial action contracts (e.g. 'wire_transfer').
    Strips forbidden override keys and returns (clean_parameters, payload_digest).
    """
    # 1. Reject forbidden override keys
    found_forbidden = [k for k in parameters if k in FORBIDDEN_FINANCIAL_KEYS]
    if found_forbidden:
        raise FinancialValidationError(f"Forbidden authorization/identity override keys in parameters: {found_forbidden}")

    # 2. Validate strict known action contracts before any policy evaluation or
    # approval request is created. This prevents reviewers seeing malformed
    # provider work that would only fail after approval.
    contracts = {
        "wire_transfer": WireTransferContract,
        "issue_refund": CustomerRefundContract,
        "issue_account_credit": CustomerAccountCreditContract,
    }
    contract = contracts.get(action_name)
    if contract is not None:
        try:
            validated_model = contract(**parameters)
            # Dump to JSON-serializable dict with Decimal as string/float
            clean_dict = json.loads(validated_model.model_dump_json(exclude_none=True))
            digest = compute_payload_digest(clean_dict)
            return clean_dict, digest
        except Exception as e:
            raise FinancialValidationError(f"Invalid {action_name} parameters: {str(e)}") from e

    # Fallback for generic actions
    clean_dict = {k: v for k, v in parameters.items() if k not in FORBIDDEN_FINANCIAL_KEYS}
    digest = compute_payload_digest(clean_dict)
    return clean_dict, digest
