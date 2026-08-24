from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import ApprovalActionRequest, ApprovalDetailSchema
from app.services.approval import ApprovalConflictError, ApprovalService
from app.services.errors import RegistryValidationError

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


def service(db: Session = Depends(get_db)) -> ApprovalService:
    return ApprovalService(db)


@router.get("", response_model=list[ApprovalDetailSchema])
def list_approvals(approvals: ApprovalService = Depends(service)) -> list[ApprovalDetailSchema]:
    return approvals.list()


@router.get("/{approval_id}", response_model=ApprovalDetailSchema)
def get_approval(approval_id: UUID, approvals: ApprovalService = Depends(service)) -> ApprovalDetailSchema:
    approval = approvals.get(approval_id)
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")
    return approval


def transition(operation):
    try:
        return operation()
    except ApprovalConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except RegistryValidationError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/{approval_id}/approve", response_model=ApprovalDetailSchema)
def approve(approval_id: UUID, payload: ApprovalActionRequest, approvals: ApprovalService = Depends(service)) -> ApprovalDetailSchema:
    return transition(lambda: approvals.approve(approval_id, payload))


@router.post("/{approval_id}/reject", response_model=ApprovalDetailSchema)
def reject(approval_id: UUID, payload: ApprovalActionRequest, approvals: ApprovalService = Depends(service)) -> ApprovalDetailSchema:
    return transition(lambda: approvals.reject(approval_id, payload))


@router.post("/{approval_id}/cancel", response_model=ApprovalDetailSchema)
def cancel(approval_id: UUID, payload: ApprovalActionRequest, approvals: ApprovalService = Depends(service)) -> ApprovalDetailSchema:
    return transition(lambda: approvals.cancel(approval_id, payload))
