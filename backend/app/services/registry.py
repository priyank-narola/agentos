from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Action, Agent, AgentStatus, Delegation, Principal, Resource, Tool
from app.repositories.registry import RegistryRepository
from app.schemas import (
    ActionCreate,
    ActionUpdate,
    AgentCreate,
    AgentUpdate,
    DelegationCreate,
    PrincipalCreate,
    ResourceCreate,
    ResourceUpdate,
    ToolCreate,
    ToolUpdate,
)
from app.services.errors import RegistryValidationError


class RegistryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = RegistryRepository(db)

    def create_principal(self, payload: PrincipalCreate) -> Principal:
        return self.repository.save(Principal(**payload.model_dump()))

    def list_principals(self) -> list[Principal]:
        return self.repository.list(Principal)

    def get_principal(self, record_id: UUID) -> Principal | None:
        return self.repository.get(Principal, record_id)

    def create_agent(self, payload: AgentCreate) -> Agent:
        if self.get_principal(payload.owner_principal_id) is None:
            raise RegistryValidationError("owner_principal_id must reference an existing principal")
        return self.repository.save(Agent(**payload.model_dump()))

    def list_agents(self) -> list[Agent]:
        return self.repository.list(Agent)

    def get_agent(self, record_id: UUID) -> Agent | None:
        return self.repository.get(Agent, record_id)

    def update_agent(self, record_id: UUID, payload: AgentUpdate) -> Agent | None:
        record = self.get_agent(record_id)
        if record is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(record, key, value)
        return self.repository.save(record)

    def set_agent_status(self, record_id: UUID, status: AgentStatus) -> Agent | None:
        record = self.get_agent(record_id)
        if record is None:
            return None
        record.status = status
        return self.repository.save(record)

    def create_tool(self, payload: ToolCreate) -> Tool:
        return self.repository.save(Tool(**payload.model_dump()))

    def list_tools(self) -> list[Tool]:
        return self.repository.list(Tool)

    def get_tool(self, record_id: UUID) -> Tool | None:
        return self.repository.get(Tool, record_id)

    def update_tool(self, record_id: UUID, payload: ToolUpdate) -> Tool | None:
        record = self.get_tool(record_id)
        if record is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(record, key, value)
        return self.repository.save(record)

    def create_action(self, tool_id: UUID, payload: ActionCreate) -> Action | None:
        tool = self.get_tool(tool_id)
        if tool is None:
            return None
        return self.repository.save(Action(tool_id=tool.id, **payload.model_dump()))

    def list_actions(self, tool_id: UUID) -> list[Action]:
        return self.repository.list_actions(tool_id)

    def get_action(self, record_id: UUID) -> Action | None:
        return self.repository.get(Action, record_id)

    def update_action(self, record_id: UUID, payload: ActionUpdate) -> Action | None:
        record = self.get_action(record_id)
        if record is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(record, key, value)
        return self.repository.save(record)

    def create_resource(self, payload: ResourceCreate) -> Resource:
        return self.repository.save(Resource(**payload.model_dump()))

    def list_resources(self) -> list[Resource]:
        return self.repository.list(Resource)

    def get_resource(self, record_id: UUID) -> Resource | None:
        return self.repository.get(Resource, record_id)

    def update_resource(self, record_id: UUID, payload: ResourceUpdate) -> Resource | None:
        record = self.get_resource(record_id)
        if record is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(record, key, value)
        return self.repository.save(record)

    def create_delegation(self, payload: DelegationCreate) -> Delegation | None:
        if self.get_principal(payload.principal_id) is None or self.get_agent(payload.agent_id) is None:
            raise RegistryValidationError("principal_id and agent_id must reference existing records")
        data = payload.model_dump()
        data["metadata_"] = data.pop("metadata")
        return self.repository.save(Delegation(**data))

    def list_delegations(self) -> list[Delegation]:
        return list(self.db.scalars(select(Delegation).order_by(Delegation.issued_at.desc())).all())

    def get_delegation(self, record_id: UUID) -> Delegation | None:
        return self.repository.get(Delegation, record_id)
