from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import ActionRequestDetailSchema, GatewayRequestCreate, GatewayResponse
from app.services.errors import RegistryConflictError
from app.services.gateway import GatewayIdempotencyConflict, GatewayService
from app.api.ratelimit import check_rate_limit

router = APIRouter(prefix="/api/v1", tags=["runtime-gateway"])


def service(db: Session = Depends(get_db)) -> GatewayService:
    return GatewayService(db)


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


@router.get("/action-requests", response_model=list[ActionRequestDetailSchema])
def list_action_requests(request: Request, gateway: GatewayService = Depends(service)) -> list[ActionRequestDetailSchema]:
    return gateway.list_requests(tenant_id=getattr(request.state, "tenant_id", None))


@router.get("/action-requests/{request_id}", response_model=ActionRequestDetailSchema)
def get_action_request(request_id: UUID, request: Request, gateway: GatewayService = Depends(service)) -> ActionRequestDetailSchema:
    request_detail = gateway.get_request(request_id, tenant_id=getattr(request.state, "tenant_id", None))
    if request_detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action request not found")
    return request_detail
