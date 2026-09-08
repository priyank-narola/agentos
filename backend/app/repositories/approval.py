from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Action, ActionRequest, ApprovalRequest


class ApprovalRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, approval_id: UUID, lock: bool = False, tenant_id: UUID | None = None) -> ApprovalRequest | None:
        if lock:
            stmt = select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
            if tenant_id is not None:
                stmt = stmt.where(ApprovalRequest.tenant_id == tenant_id)
            return self.db.scalar(stmt.with_for_update())
        query = select(ApprovalRequest).options(joinedload(ApprovalRequest.action_request).joinedload(ActionRequest.agent), joinedload(ApprovalRequest.action_request).joinedload(ActionRequest.principal), joinedload(ApprovalRequest.action_request).joinedload(ActionRequest.action).joinedload(Action.tool), joinedload(ApprovalRequest.action_request).joinedload(ActionRequest.resource), joinedload(ApprovalRequest.action_request).joinedload(ActionRequest.decisions), joinedload(ApprovalRequest.action_request).joinedload(ActionRequest.audit_events)).where(ApprovalRequest.id == approval_id)
        if tenant_id is not None:
            query = query.where(ApprovalRequest.tenant_id == tenant_id)
        return self.db.scalar(query)

    def list(self, tenant_id: UUID | None = None) -> list[ApprovalRequest]:
        query = select(ApprovalRequest).options(joinedload(ApprovalRequest.action_request).joinedload(ActionRequest.agent), joinedload(ApprovalRequest.action_request).joinedload(ActionRequest.principal), joinedload(ApprovalRequest.action_request).joinedload(ActionRequest.action).joinedload(Action.tool), joinedload(ApprovalRequest.action_request).joinedload(ActionRequest.resource), joinedload(ApprovalRequest.action_request).joinedload(ActionRequest.decisions), joinedload(ApprovalRequest.action_request).joinedload(ActionRequest.audit_events)).order_by(ApprovalRequest.expires_at, ApprovalRequest.id)
        if tenant_id is not None:
            query = query.where(ApprovalRequest.tenant_id == tenant_id)
        return list(self.db.scalars(query).unique().all())

    def for_action_request(self, request_id: UUID) -> ApprovalRequest | None:
        return self.db.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == request_id))
