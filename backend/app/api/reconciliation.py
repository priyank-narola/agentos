"""Tenant-safe reconciliation inbox for uncertain action outcomes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.authorization import require_tenant_roles
from app.api.ratelimit import check_rate_limit
from app.db.models import DEFAULT_TENANT_ID, TenantRole
from app.db.session import get_db
from app.schemas import ReconciliationCase, ReconciliationCheckRequest, ReconciliationResult
from app.services.reconciliation import (
    ReconciliationConflictError,
    ReconciliationForbiddenError,
    ReconciliationNotFoundError,
    ReconciliationService,
)


router = APIRouter(prefix="/api/v1/reconciliation", tags=["execution-reconciliation"])
operator_required = require_tenant_roles({TenantRole.ADMIN, TenantRole.OPERATOR})


def service(db: Session = Depends(get_db)) -> ReconciliationService:
    return ReconciliationService(db)


def trusted_tenant(request: Request) -> UUID:
    """Use authenticated tenant when available; development is canonical-demo only."""
    return getattr(request.state, "tenant_id", None) or DEFAULT_TENANT_ID


@router.get("", response_model=list[ReconciliationCase], dependencies=[Depends(operator_required)])
def list_reconciliation_cases(request: Request, reconciliation: ReconciliationService = Depends(service)) -> list[ReconciliationCase]:
    return reconciliation.list(trusted_tenant(request))


@router.post("/{action_request_id}/check", response_model=ReconciliationResult, dependencies=[Depends(check_rate_limit), Depends(operator_required)])
def check_reconciliation(
    action_request_id: UUID,
    payload: ReconciliationCheckRequest,
    request: Request,
    reconciliation: ReconciliationService = Depends(service),
) -> ReconciliationResult:
    principal = getattr(request.state, "principal", None)
    if principal is not None and payload.actor_principal_id != principal.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authenticated principal cannot reconcile as another operator")
    try:
        return reconciliation.reconcile(action_request_id, payload.actor_principal_id, trusted_tenant(request))
    except ReconciliationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ReconciliationForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ReconciliationConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
