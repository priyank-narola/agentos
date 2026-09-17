from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import TenantRole
from app.api.authorization import require_tenant_roles
from app.schemas import ActionEvidenceBundle, ActionPreflightRequest, ActionPreflightResponse, ActionRequestDetailSchema, GatewayRequestCreate, GatewayResponse
from app.services.errors import RegistryConflictError
from app.services.gateway import GatewayIdempotencyConflict, GatewayService
from app.api.ratelimit import check_rate_limit

router = APIRouter(prefix="/api/v1", tags=["runtime-gateway"])
governance_reader_required = require_tenant_roles({TenantRole.ADMIN, TenantRole.AUDITOR, TenantRole.OPERATOR})


def service(db: Session = Depends(get_db)) -> GatewayService:
    return GatewayService(db)


@router.post("/action-preflight", response_model=ActionPreflightResponse, dependencies=[Depends(check_rate_limit)])
def preflight_action(payload: ActionPreflightRequest, request: Request, gateway: GatewayService = Depends(service)) -> ActionPreflightResponse:
    """Preview the same policy/risk path as the gateway without persistence or execution."""
    principal = getattr(request.state, "principal", None)
    if principal is not None and payload.principal_id != principal.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authenticated principal cannot preview as another principal")
    try:
        return gateway.preflight(payload)
    except GatewayIdempotencyConflict as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except RegistryConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except Exception as error:
        gateway.db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action could not be preflighted") from error


@router.post("/action-requests", response_model=GatewayResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_rate_limit)])
def submit_action_request(payload: GatewayRequestCreate, request: Request, gateway: GatewayService = Depends(service)) -> GatewayResponse:
    principal = getattr(request.state, "principal", None)
    if principal is not None and payload.principal_id != principal.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authenticated principal cannot act as another principal")
    try:
        return gateway.submit(payload)
    except GatewayIdempotencyConflict as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except RegistryConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except Exception as error:
        gateway.db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action request could not be evaluated") from error


@router.get("/action-requests", response_model=list[ActionRequestDetailSchema], dependencies=[Depends(governance_reader_required)])
def list_action_requests(request: Request, gateway: GatewayService = Depends(service)) -> list[ActionRequestDetailSchema]:
    return gateway.list_requests(tenant_id=getattr(request.state, "tenant_id", None))


@router.get("/action-requests/{request_id}", response_model=ActionRequestDetailSchema, dependencies=[Depends(governance_reader_required)])
def get_action_request(request_id: UUID, request: Request, gateway: GatewayService = Depends(service)) -> ActionRequestDetailSchema:
    request_detail = gateway.get_request(request_id, tenant_id=getattr(request.state, "tenant_id", None))
    if request_detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action request not found")
    return request_detail


@router.get("/action-requests/{request_id}/evidence", response_model=ActionEvidenceBundle, dependencies=[Depends(governance_reader_required)])
def export_action_evidence(request_id: UUID, request: Request, gateway: GatewayService = Depends(service)) -> ActionEvidenceBundle:
    bundle = gateway.get_evidence_bundle(request_id, tenant_id=getattr(request.state, "tenant_id", None))
    if bundle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action request not found")
    return bundle
