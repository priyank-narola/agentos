import hmac
import hashlib
import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.db.models import ExecutionState
from app.execution import ExecutionStateMachine, InvalidExecutionStateTransitionError


class WebhookError(ValueError):
    """Base exception for webhook security and processing errors."""
    pass


class WebhookSignatureVerificationError(WebhookError):
    """Raised when HMAC signature verification fails."""
    pass


class WebhookTimestampExpiredError(WebhookError):
    """Raised when webhook timestamp exceeds allowable time skew."""
    pass


class WebhookDuplicateEventError(WebhookError):
    """Raised when duplicate webhook event ID is received."""
    pass


class WebhookTenantBindingError(WebhookError):
    """Raised when webhook payload tenant ID does not match trusted transaction tenant ID."""
    pass


class WebhookSecurityHandler:
    """
    Production Webhook Security & Verification Architecture.
    Provides HMAC-SHA256 signature verification, timestamp skew validation,
    event ID deduplication, tenant & transaction binding, and state transition safety.
    """

    def __init__(self, max_skew_seconds: int = 300) -> None:
        self.max_skew_seconds = max_skew_seconds
        self._processed_events: set[tuple[UUID, str]] = set()

    def verify_signature(self, raw_body: bytes, signature_header: str, secret: str, timestamp_header: str | None = None) -> bool:
        """
        Verify HMAC-SHA256 signature over webhook payload bytes using secret.
        Supports timestamp-prefixed signature format (e.g. t=12345,v1=sha256_hash).
        """
        if not signature_header or not secret:
            raise WebhookSignatureVerificationError("Webhook signature header and secret are required")

        # Parse signature header format
        extracted_sig = signature_header.strip()
        ts_prefix = ""
        if "v1=" in extracted_sig:
            parts = dict(item.split("=") for item in extracted_sig.split(",") if "=" in item)
            extracted_sig = parts.get("v1", "")
            ts_prefix = parts.get("t", "")

        signed_payload = f"{ts_prefix}.".encode("utf-8") + raw_body if ts_prefix else raw_body
        expected_sig = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()

        # Secure constant-time comparison
        if not hmac.compare_digest(extracted_sig.lower(), expected_sig.lower()):
            raise WebhookSignatureVerificationError("Invalid HMAC-SHA256 webhook signature")

        return True

    def validate_timestamp(self, timestamp: int | float | str) -> bool:
        """Verify timestamp is within allowable skew window (prevents replay attacks)."""
        now = time.time()
        try:
            ts_val = float(timestamp)
        except (ValueError, TypeError) as e:
            raise WebhookTimestampExpiredError(f"Invalid timestamp format: {timestamp}") from e

        if abs(now - ts_val) > self.max_skew_seconds:
            raise WebhookTimestampExpiredError(
                f"Webhook timestamp skew ({abs(now - ts_val):.1f}s) exceeds maximum allowed ({self.max_skew_seconds}s)"
            )
        return True

    def deduplicate_event(self, event_id: str, tenant_id: UUID) -> bool:
        """Verify webhook event ID has not been processed previously for this tenant."""
        key = (tenant_id, event_id)
        if key in self._processed_events:
            raise WebhookDuplicateEventError(f"Duplicate webhook event ID '{event_id}' for tenant '{tenant_id}'")
        self._processed_events.add(key)
        return True

    def bind_and_process(
        self,
        event_payload: dict[str, Any],
        trusted_tenant_id: UUID,
        current_state: ExecutionState
    ) -> ExecutionState:
        """
        Validates tenant binding, transaction reference, and state transition safety.
        Returns target ExecutionState if valid.
        """
        payload_tenant_str = event_payload.get("tenant_id")
        if payload_tenant_str:
            try:
                payload_tenant_id = UUID(str(payload_tenant_str))
                if payload_tenant_id != trusted_tenant_id:
                    raise WebhookTenantBindingError(
                        f"Cross-tenant webhook mismatch: payload tenant '{payload_tenant_id}' != trusted '{trusted_tenant_id}'"
                    )
            except ValueError as e:
                raise WebhookTenantBindingError(f"Invalid tenant_id in webhook payload: {payload_tenant_str}") from e

        target_status_str = event_payload.get("status", "").upper()
        try:
            target_state = ExecutionState(target_status_str)
        except ValueError:
            target_state = ExecutionState.UNKNOWN

        # Validate state machine transition safety (handles out-of-order webhooks)
        try:
            ExecutionStateMachine.validate_transition(current_state, target_state)
        except InvalidExecutionStateTransitionError as e:
            # Out-of-order webhook trying to mutate terminal state -> safe ignore / fail closed
            raise WebhookError(f"Out-of-order webhook ignored: {e}") from e

        return target_state
