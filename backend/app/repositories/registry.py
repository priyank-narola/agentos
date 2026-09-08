import uuid
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.models import Action, Agent, Delegation, Principal, Resource, Tool
from app.services.errors import RegistryConflictError

# Tools/actions are the only catalog models whose tenant_id is nullable; a NULL
# tenant denotes genuinely global/static capability metadata visible to all
# tenants. Every other catalog model is strictly tenant-owned.
GLOBAL_ALLOWED_MODELS = {Tool, Action}


def _tenant_filter(model, tenant_id: UUID):
    if model in GLOBAL_ALLOWED_MODELS:
        return or_(model.tenant_id == tenant_id, model.tenant_id.is_(None))
    return model.tenant_id == tenant_id


class RegistryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, model, record_id: UUID, tenant_id: UUID | None = None):
        record = self.db.get(model, record_id)
        if tenant_id is not None and record is not None and hasattr(model, "tenant_id"):
            if model in GLOBAL_ALLOWED_MODELS:
                if record.tenant_id is not None and record.tenant_id != tenant_id:
                    return None
            elif record.tenant_id != tenant_id:
                return None
        return record

    def list(self, model, tenant_id: UUID | None = None):
        order_column = model.name if hasattr(model, "name") else model.id
        stmt = select(model)
        if tenant_id is not None and hasattr(model, "tenant_id"):
            stmt = stmt.where(_tenant_filter(model, tenant_id))
        return list(self.db.scalars(stmt.order_by(order_column)).all())

    def list_actions(self, tool_id: UUID, tenant_id: UUID | None = None):
        stmt = select(Action).where(Action.tool_id == tool_id)
        if tenant_id is not None:
            stmt = stmt.where(_tenant_filter(Action, tenant_id))
        return list(self.db.scalars(stmt.order_by(Action.name)).all())

    def save(self, record):
        try:
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record
        except IntegrityError as error:
            self.db.rollback()
            raise RegistryConflictError("A registry record with the same unique identity already exists") from error

    def delete_pending_changes(self) -> None:
        self.db.rollback()
