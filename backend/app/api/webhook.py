"""Sandbox payment-provider webhook endpoint.

Signature scheme mirrors common provider webhooks:
    X-AgentOS-Signature: t=<unix>,v1=<hmac-sha256 hex>
where the HMAC is computed over the byte string ``f"{t}." + raw_body`` using the
configured WEBHOOK_SECRET. No real payment provider is connected; this endpoint
exists to prove the webhook security contract (signature, timestamp/replay,
durable dedup, tenant binding, state-transition safety).
"""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.webhook import (
    WebhookDeliveryService,
    WebhookDuplicateEventError,
    WebhookError,
    WebhookSignatureVerificationError,
    WebhookTenantBindingError,
    WebhookTimestampExpiredError,
)
from app.api.ratelimit import check_rate_limit

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/payment", dependencies=[Depends(check_rate_limit)])
async def receive_payment_webhook(request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Receive, verify, deduplicate and apply a signed sandbox provider event."""
    signature_header = request.headers.get("X-AgentOS-Signature", "")
    try:
        raw_body = await request.body()
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to read request body") from exc

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed JSON payload") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload must be a JSON object")

    service = WebhookDeliveryService(db)
    try:
        return service.deliver(raw_body, signature_header, payload)
    except WebhookSignatureVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except WebhookTimestampExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except WebhookTenantBindingError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except WebhookDuplicateEventError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except WebhookError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
