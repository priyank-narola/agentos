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
}


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


def compute_payload_digest(parameters: dict[str, Any]) -> str:
    """
    Compute a deterministic SHA-256 digest over canonical JSON parameter payload.
    Used for binding approved payloads to execution requests.
    """
    canonical_json = json.dumps(parameters, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def validate_financial_action_parameters(action_name: str, parameters: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """
    Validates parameters for known financial action contracts (e.g. 'wire_transfer').
    Strips forbidden override keys and returns (clean_parameters, payload_digest).
    """
    # 1. Reject forbidden override keys
    found_forbidden = [k for k in parameters if k in FORBIDDEN_FINANCIAL_KEYS]
    if found_forbidden:
        raise FinancialValidationError(f"Forbidden authorization/identity override keys in parameters: {found_forbidden}")

    # 2. Validate action contract if wire_transfer
    if action_name == "wire_transfer":
        try:
            validated_model = WireTransferContract(**parameters)
            # Dump to JSON-serializable dict with Decimal as string/float
            clean_dict = json.loads(validated_model.model_dump_json(exclude_none=True))
            digest = compute_payload_digest(clean_dict)
            return clean_dict, digest
        except Exception as e:
            raise FinancialValidationError(f"Invalid wire_transfer parameters: {str(e)}") from e

    # Fallback for generic actions
    clean_dict = {k: v for k, v in parameters.items() if k not in FORBIDDEN_FINANCIAL_KEYS}
    digest = compute_payload_digest(clean_dict)
    return clean_dict, digest
