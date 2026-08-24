import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Action, ActionRequest


class GatewayRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_idempotency_key(self, key: str) -> ActionRequest | None:
        return self.db.scalar(select(ActionRequest).options(joinedload(ActionRequest.decisions)).where(ActionRequest.idempotency_key == key))

    def get_request(self, request_id: UUID) -> ActionRequest | None:
        return self.db.scalar(select(ActionRequest).options(joinedload(ActionRequest.agent), joinedload(ActionRequest.principal), joinedload(ActionRequest.action).joinedload(Action.tool), joinedload(ActionRequest.resource), joinedload(ActionRequest.decisions)).where(ActionRequest.id == request_id))

    def list_requests(self) -> list[ActionRequest]:
        return list(self.db.scalars(select(ActionRequest).options(joinedload(ActionRequest.agent), joinedload(ActionRequest.principal), joinedload(ActionRequest.action).joinedload(Action.tool), joinedload(ActionRequest.resource), joinedload(ActionRequest.decisions)).order_by(ActionRequest.requested_at.desc())).unique().all())

    @staticmethod
    def canonical_content(request: ActionRequest) -> str:
        return json.dumps({"principal_id": str(request.principal_id), "agent_id": str(request.agent_id), "action_id": str(request.action_id), "resource_id": str(request.resource_id), "parameters": request.parameters}, sort_keys=True, separators=(",", ":"))
