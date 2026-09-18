from uuid import UUID
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import TenantRole
from app.api.authorization import require_tenant_roles
from app.schemas import ApprovalActionRequest, ApprovalDetailSchema
from app.services.approval import ApprovalConflictError, ApprovalService, ApprovalTenantForbiddenError
from app.services.errors import RegistryValidationError
from app.api.ratelimit import check_rate_limit

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])
approval_reader_required = require_tenant_roles({TenantRole.ADMIN, TenantRole.APPROVER, TenantRole.AUDITOR, TenantRole.OPERATOR})


def service(db: Session = Depends(get_db)) -> ApprovalService:
    return ApprovalService(db)


@router.get("", response_model=list[ApprovalDetailSchema], dependencies=[Depends(approval_reader_required)])
def list_approvals(request: Request, approvals: ApprovalService = Depends(service)) -> list[ApprovalDetailSchema]:
    return approvals.list(tenant_id=getattr(request.state, "tenant_id", None))


@router.get("/{approval_id}", response_model=ApprovalDetailSchema, dependencies=[Depends(approval_reader_required)])
def get_approval(approval_id: UUID, request: Request, approvals: ApprovalService = Depends(service)) -> ApprovalDetailSchema:
    approval = approvals.get(approval_id, tenant_id=getattr(request.state, "tenant_id", None))
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")
    return approval


@router.get("/{approval_id}/approvers", response_model=dict[str, Any], dependencies=[Depends(approval_reader_required)])
def list_eligible_approvers(approval_id: UUID, request: Request, approvals: ApprovalService = Depends(service)) -> dict[str, Any]:
    """Return ACTIVE human principals in the approval's tenant who are eligible to
    decide this approval under separation of duties (never the requester)."""
    approval = approvals.get(approval_id, tenant_id=getattr(request.state, "tenant_id", None))
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")
    return {
        "approval_id": str(approval_id),
        "approvers": approvals.eligible_approvers(approval_id, tenant_id=getattr(request.state, "tenant_id", None)),
    }


def transition(operation):
    try:
        return operation()
    except ApprovalTenantForbiddenError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    except ApprovalConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except RegistryValidationError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/{approval_id}/approve", response_model=ApprovalDetailSchema, dependencies=[Depends(check_rate_limit)])
def approve(approval_id: UUID, payload: ApprovalActionRequest, request: Request, approvals: ApprovalService = Depends(service)) -> ApprovalDetailSchema:
    if "decision_reason" not in payload.model_fields_set or payload.decision_reason is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="decision_reason is required when approving an action")
    principal = getattr(request.state, "principal", None)
    if principal is not None and payload.approver_principal_id != principal.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authenticated principal cannot approve as another principal")
    return transition(lambda: approvals.approve(approval_id, payload, tenant_id=getattr(request.state, "tenant_id", None)))


@router.post("/{approval_id}/reject", response_model=ApprovalDetailSchema, dependencies=[Depends(check_rate_limit)])
def reject(approval_id: UUID, payload: ApprovalActionRequest, request: Request, approvals: ApprovalService = Depends(service)) -> ApprovalDetailSchema:
    if "decision_reason" not in payload.model_fields_set or payload.decision_reason is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="decision_reason is required when rejecting an action")
    principal = getattr(request.state, "principal", None)
    if principal is not None and payload.approver_principal_id != principal.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authenticated principal cannot reject as another principal")
    return transition(lambda: approvals.reject(approval_id, payload, tenant_id=getattr(request.state, "tenant_id", None)))


@router.post("/{approval_id}/cancel", response_model=ApprovalDetailSchema, dependencies=[Depends(check_rate_limit)])
def cancel(approval_id: UUID, payload: ApprovalActionRequest, request: Request, approvals: ApprovalService = Depends(service)) -> ApprovalDetailSchema:
    principal = getattr(request.state, "principal", None)
    if principal is not None and payload.approver_principal_id != principal.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authenticated principal cannot cancel as another principal")
    return transition(lambda: approvals.cancel(approval_id, payload, tenant_id=getattr(request.state, "tenant_id", None)))
