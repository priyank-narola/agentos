"""Safe, secret-free launch readiness posture for tenant administrators."""

from fastapi import APIRouter, Depends

from app.api.authorization import require_tenant_roles
from app.config import settings
from app.db.models import TenantRole

router = APIRouter(prefix="/api/v1/launch-readiness", tags=["launch-readiness"])
admin_required = require_tenant_roles({TenantRole.ADMIN})


@router.get("", dependencies=[Depends(admin_required)])
def launch_readiness() -> dict:
    production = settings.app_env == "production"
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
    checks = [
        {"id": "environment", "label": "Production environment", "status": "READY" if production else "BLOCKED", "detail": "Production environment configured." if production else "Local/sandbox environment only."},
        {"id": "database", "label": "PostgreSQL database", "status": "READY" if settings.database_url.startswith("postgresql+") else "BLOCKED", "detail": "PostgreSQL configured." if settings.database_url.startswith("postgresql+") else "A production PostgreSQL rehearsal is required."},
        {"id": "identity", "label": "Production identity", "status": "READY" if production and bool(settings.mcp_auth_public_key or settings.mcp_auth_jwks_url or settings.mcp_auth_secret_key) else "BLOCKED", "detail": "Production token verification configured." if production and bool(settings.mcp_auth_public_key or settings.mcp_auth_jwks_url or settings.mcp_auth_secret_key) else "Configure a real identity provider and tenant provisioning."},
        {"id": "zendesk", "label": "Zendesk test-mode context", "status": "READY" if zendesk_configured else "BLOCKED" if settings.zendesk_context_connector_enabled else "PENDING", "detail": "Read-only Zendesk context is configured." if zendesk_configured else "Connector is enabled but its required OAuth configuration is incomplete." if settings.zendesk_context_connector_enabled else "Requires a partner-approved OAuth tickets:read test integration."},
        {"id": "stripe", "label": "Stripe test-mode refund", "status": "READY" if stripe_configured else "BLOCKED" if settings.stripe_refund_connector_enabled else "PENDING", "detail": "Stripe refund connector is configured for a controlled rehearsal." if stripe_configured else "Connector is enabled but its test-mode credential or HTTPS provider endpoint is incomplete." if settings.stripe_refund_connector_enabled else "Requires a partner-approved Stripe test-mode rehearsal."},
        {"id": "pilot", "label": "Design-partner validation", "status": "PENDING", "detail": "Complete customer interviews and one sandbox pilot before enabling live payments."},
        {"id": "data_controls", "label": "Privacy, retention, and incident controls", "status": "PENDING", "detail": "Complete legal review, retention policy, DPA/subprocessor review, and support runbook."},
    ]
    blockers = sum(item["status"] == "BLOCKED" for item in checks)
    pending = sum(item["status"] == "PENDING" for item in checks)
    return {"environment": settings.app_env, "launch_ready": blockers == 0 and pending == 0, "blockers": blockers, "pending": pending, "checks": checks}
