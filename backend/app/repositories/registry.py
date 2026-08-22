from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.models import Action, Agent, Delegation, Principal, Resource, Tool
from app.services.errors import RegistryConflictError


class RegistryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, model, record_id: UUID):
        return self.db.get(model, record_id)

    def list(self, model):
        order_column = model.name if hasattr(model, "name") else model.id
        return list(self.db.scalars(select(model).order_by(order_column)).all())

    def list_actions(self, tool_id: UUID):
        return list(self.db.scalars(select(Action).where(Action.tool_id == tool_id).order_by(Action.name)).all())

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
