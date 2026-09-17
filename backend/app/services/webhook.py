import hmac
import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import AuditEvent, ActorType, ExecutionState, FinancialExecution, WebhookEvent
from app.services.audit_sequence import next_action_event_sequence
from app.services.execution_lifecycle import ExecutionLifecycleError, validate_execution_transition


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

        # Validate state transition safety (handles out-of-order webhooks)
        try:
            validate_execution_transition(current_state, target_state)
        except ExecutionLifecycleError as exc:
            raise WebhookError(f"Out-of-order webhook ignored: {exc}") from exc

        return target_state


class WebhookDeliveryService:
    """Handles signed provider webhook delivery end-to-end.

    Flow: HMAC-SHA256 signature verification over the raw body
    -> timestamp skew check (replay protection)
    -> durable per-(tenant, event_id) deduplication
    -> tenant-safe resolution of the target FinancialExecution
    -> validated state transition (out-of-order events fail closed)
    -> WebhookEvent ledger row + audit event.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.handler = WebhookSecurityHandler(max_skew_seconds=settings.webhook_max_skew_seconds)
        self.secret = settings.webhook_secret

    def _record(self, tenant_id: UUID, payload: dict, outcome: str, event_type: str) -> None:
        existing = self.db.scalar(
            select(WebhookEvent).where(
                WebhookEvent.tenant_id == tenant_id,
                WebhookEvent.event_id == payload.get("event_id", ""),
            )
        )
        if existing is not None:
            return existing
        record = WebhookEvent(
            tenant_id=tenant_id,
            event_id=str(payload.get("event_id", uuid.uuid4())),
            event_type=event_type,
            source=str(payload.get("source", "provider")),
            outcome=outcome,
            payload=payload,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def deliver(self, raw_body: bytes, signature_header: str, payload: dict) -> dict[str, Any]:
        # 1. Signature verification (raw body bytes, constant-time compare).
        self.handler.verify_signature(raw_body, signature_header, self.secret)

        # 2. Timestamp / replay protection (t=<unix> included in signature header).
        ts = None
        if signature_header and "t=" in signature_header:
            try:
                ts = dict(part.split("=") for part in signature_header.split(",") if "=" in part).get("t")
            except ValueError:
                ts = None
        if ts is None:
            raise WebhookTimestampExpiredError("Webhook header must include a t=<unix timestamp> parameter")
        self.handler.validate_timestamp(ts)

        event_id = payload.get("event_id")
        action_request_id = payload.get("action_request_id")
        if not event_id or not action_request_id:
            raise WebhookError("Webhook payload must include event_id and action_request_id")

        # 3. Tenant-safe resolution of the target execution (never client-chosen tenant).
        try:
            request_uuid = UUID(str(action_request_id))
        except (ValueError, TypeError) as exc:
            raise WebhookError("action_request_id must be a valid UUID") from exc
        execution = self.db.scalar(
            select(FinancialExecution).where(FinancialExecution.action_request_id == request_uuid)
        )
        if execution is None:
            raise WebhookError("No FinancialExecution found for action_request_id")

        # 4. Durable deduplication (duplicate event_id for the same tenant).
        existing = self.db.scalar(
            select(WebhookEvent).where(
                WebhookEvent.tenant_id == execution.tenant_id,
                WebhookEvent.event_id == str(event_id),
            )
        )
        if existing is not None:
            return {"status": "duplicate", "event_id": str(event_id), "deduplicated": True}

        # 5. Tenant binding + state-transition validation (fails closed).
        target_state = self.handler.bind_and_process(payload, execution.tenant_id, execution.status)

        # 6. Apply transition to the execution ledger and record evidence.
        execution.status = target_state
        execution.error_message = payload.get("error_message")
        self._record(execution.tenant_id, payload, outcome="processed", event_type=str(payload.get("event_type", "provider_event")))
        self.db.add(AuditEvent(
            tenant_id=execution.tenant_id,
            event_type="WEBHOOK_EVENT_RECEIVED",
            actor_type=ActorType.SYSTEM,
            actor_id=uuid.UUID(int=0),
            action_request_id=request_uuid,
            event_sequence=next_action_event_sequence(self.db, request_uuid),
            event_data={"event_id": str(event_id), "status": target_state.value if hasattr(target_state, "value") else str(target_state), "deduplicated": False},
        ))
        self.db.commit()
        return {"status": "processed", "event_id": str(event_id), "execution_status": target_state.value if hasattr(target_state, "value") else str(target_state)}
