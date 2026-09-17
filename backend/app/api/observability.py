from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import DEFAULT_TENANT_ID
from app.db.models import TenantRole
from app.api.authorization import require_tenant_roles
from app.runtime import runtime_metrics
from app.services.observability import ObservabilityService

router = APIRouter(prefix="/api/v1/observability", tags=["observability"])
observability_reader_required = require_tenant_roles({TenantRole.ADMIN, TenantRole.AUDITOR, TenantRole.OPERATOR})
operations_reader_required = require_tenant_roles({TenantRole.ADMIN, TenantRole.OPERATOR})


def get_tenant_id(
    request: Request,
    x_tenant_id: UUID | None = Header(None, alias="X-Tenant-ID"),
    tenant_id: UUID | None = Query(None)
) -> UUID:
    """
    Resolve the trusted tenant scope.

    When REST authentication is enforced the tenant comes exclusively from the
    authenticated Principal (never from client headers/query). Otherwise, for the
    local development demo, it defaults to the canonical default tenant, and an
    explicit header/query mismatch still fails closed with 403.
    """
    enforced_tenant = getattr(request.state, "tenant_id", None)
    if enforced_tenant is not None:
        if x_tenant_id and x_tenant_id != enforced_tenant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-tenant access forbidden: header tenant does not match authenticated tenant"
            )
        if tenant_id and tenant_id != enforced_tenant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-tenant access forbidden: query tenant does not match authenticated tenant"
            )
        return enforced_tenant
    if x_tenant_id and tenant_id and x_tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant access forbidden: header and query tenant mismatch"
        )
    return x_tenant_id or tenant_id or DEFAULT_TENANT_ID


@router.get("/timeline", response_model=dict[str, Any], dependencies=[Depends(observability_reader_required)])
def get_security_timeline(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    event_type: str | None = Query(None),
    tenant: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Read-only security event timeline endpoint."""
    service = ObservabilityService(db)
    return service.get_security_timeline(tenant_id=tenant, limit=limit, offset=offset, event_type=event_type)


@router.get("/action-requests/{request_id}", response_model=dict[str, Any], dependencies=[Depends(observability_reader_required)])
def get_action_request_detail(
    request_id: UUID,
    tenant: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Read-only action request security detail endpoint."""
    service = ObservabilityService(db)
    detail = service.get_action_request_detail(tenant_id=tenant, request_id=request_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ActionRequest {request_id} not found in tenant context"
        )
    return detail


@router.get("/metrics", response_model=dict[str, Any], dependencies=[Depends(observability_reader_required)])
def get_security_dashboard_metrics(
    tenant: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Read-only security metrics dashboard endpoint."""
    service = ObservabilityService(db)
    return service.get_security_dashboard_metrics(tenant_id=tenant)


@router.get("/runtime", response_model=dict[str, Any], dependencies=[Depends(operations_reader_required)])
def get_runtime_operations_metrics() -> dict[str, Any]:
    """Payload-free process telemetry for release and incident operators.

    Metrics remain local to one application process; this endpoint is a
    diagnostic view, not a substitute for aggregated production monitoring.
    """
    return runtime_metrics.snapshot()


@router.get("/risk", response_model=dict[str, Any], dependencies=[Depends(observability_reader_required)])
def get_risk_dashboard(
    tenant: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Read-only risk telemetry & risk distribution endpoint."""
    service = ObservabilityService(db)
    return service.get_risk_dashboard(tenant_id=tenant)


@router.get("/agents/{agent_id}/posture", response_model=dict[str, Any], dependencies=[Depends(observability_reader_required)])
def get_agent_security_posture(
    agent_id: UUID,
    tenant: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Read-only per-agent security posture telemetry endpoint."""
    service = ObservabilityService(db)
    posture = service.get_agent_security_posture(tenant_id=tenant, agent_id=agent_id)
    if not posture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found in tenant context"
        )
    return posture


@router.get("/tenant/posture", response_model=dict[str, Any], dependencies=[Depends(observability_reader_required)])
def get_tenant_security_posture(
    tenant: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Read-only tenant-wide security posture summary endpoint."""
    service = ObservabilityService(db)
    return service.get_tenant_security_posture(tenant_id=tenant)


@router.get("/audit/verify", response_model=dict[str, Any], dependencies=[Depends(observability_reader_required)])
def verify_audit_integrity(
    tenant: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Read-only audit trail verification endpoint for detecting integrity violations."""
    service = ObservabilityService(db)
    return service.verify_audit_integrity(tenant_id=tenant)
