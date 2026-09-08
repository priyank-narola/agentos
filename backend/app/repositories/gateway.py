import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Action, ActionRequest


class GatewayRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_idempotency_key(self, key: str, tenant_id: UUID | None = None) -> ActionRequest | None:
        stmt = select(ActionRequest).options(joinedload(ActionRequest.decisions)).where(ActionRequest.idempotency_key == key)
        if tenant_id is not None:
            stmt = stmt.where(ActionRequest.tenant_id == tenant_id)
        return self.db.scalar(stmt)

    def get_request(self, request_id: UUID, tenant_id: UUID | None = None) -> ActionRequest | None:
        stmt = select(ActionRequest).options(joinedload(ActionRequest.agent), joinedload(ActionRequest.principal), joinedload(ActionRequest.action).joinedload(Action.tool), joinedload(ActionRequest.resource), joinedload(ActionRequest.decisions)).where(ActionRequest.id == request_id)
        if tenant_id is not None:
            stmt = stmt.where(ActionRequest.tenant_id == tenant_id)
        return self.db.scalar(stmt)

    def list_requests(self, tenant_id: UUID | None = None) -> list[ActionRequest]:
        stmt = select(ActionRequest).options(joinedload(ActionRequest.agent), joinedload(ActionRequest.principal), joinedload(ActionRequest.action).joinedload(Action.tool), joinedload(ActionRequest.resource), joinedload(ActionRequest.decisions)).order_by(ActionRequest.requested_at.desc())
        if tenant_id is not None:
            stmt = stmt.where(ActionRequest.tenant_id == tenant_id)
        return list(self.db.scalars(stmt).unique().all())

    @staticmethod
    def canonical_content(request: ActionRequest) -> str:
        return json.dumps({"principal_id": str(request.principal_id), "agent_id": str(request.agent_id), "action_id": str(request.action_id), "resource_id": str(request.resource_id), "parameters": request.parameters}, sort_keys=True, separators=(",", ":"))
