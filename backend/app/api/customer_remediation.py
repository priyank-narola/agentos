"""Narrow endpoints for the selected Zendesk + Stripe customer-remediation pilot."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.authorization import require_tenant_roles
from app.api.ratelimit import check_rate_limit
from app.config import settings
from app.db.models import TenantRole
from app.services.zendesk_context import ZendeskContextError, ZendeskTicketContextProvider, UrllibZendeskTransport


router = APIRouter(prefix="/api/v1/customer-remediation", tags=["customer-remediation"])
operator_required = require_tenant_roles({TenantRole.ADMIN, TenantRole.OPERATOR})


@router.get("/readiness", dependencies=[Depends(operator_required)])
def connector_readiness() -> dict:
    """Expose safe connector posture without revealing account identifiers or secrets."""
    zendesk_configured = (
        settings.zendesk_context_connector_enabled
        and bool(settings.zendesk_subdomain.strip())
        and bool(settings.zendesk_oauth_access_token.strip())
    )
    stripe_configured = (
        settings.stripe_refund_connector_enabled
        and bool(settings.stripe_secret_key.strip())
        and settings.stripe_api_base.startswith("https://")
    )
    return {
        "zendesk_ticket_context": {
            "enabled": settings.zendesk_context_connector_enabled,
            "configured": zendesk_configured,
            "mode": "read_only_minimised_context",
            "required_scope": "tickets:read",
        },
        "stripe_refund_execution": {
            "enabled": settings.stripe_refund_connector_enabled,
            "configured": stripe_configured,
            "mode": "idempotent_refund_execution",
            "requires_test_mode_rehearsal": True,
        },
        "sandbox_demo_available": True,
    }


@router.get("/zendesk/tickets/{ticket_id}", dependencies=[Depends(check_rate_limit), Depends(operator_required)])
def zendesk_ticket_context(ticket_id: int) -> dict:
    """Retrieve minimised ticket metadata for a proposed remedy, if explicitly enabled."""
    if not settings.zendesk_context_connector_enabled:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Zendesk ticket context connector is not enabled")
    try:
        context = ZendeskTicketContextProvider(
            settings.zendesk_oauth_access_token,
            UrllibZendeskTransport(settings.zendesk_subdomain),
        ).fetch(ticket_id)
    except (ValueError, ZendeskContextError) as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    return {
        "ticket_id": context.ticket_id,
        "status": context.status,
        "type": context.type,
        "priority": context.priority,
        "requester_id": context.requester_id,
        "organization_id": context.organization_id,
        "tags": context.tags,
        "created_at": context.created_at,
        "updated_at": context.updated_at,
    }
