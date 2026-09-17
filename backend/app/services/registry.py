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

# Tenant-owned models that accept an explicit tenant on creation.
_TENANT_OWNED = (Principal, Agent, Resource, Delegation, Tool, Action)


class RegistryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = RegistryRepository(db)

    def create_principal(self, payload: PrincipalCreate, tenant_id: UUID | None = None) -> Principal:
        data = payload.model_dump()
        if tenant_id is not None:
            data["tenant_id"] = tenant_id
        return self.repository.save(Principal(**data))

    def list_principals(self, tenant_id: UUID | None = None) -> list[Principal]:
        return self.repository.list(Principal, tenant_id=tenant_id)

    def get_principal(self, record_id: UUID, tenant_id: UUID | None = None) -> Principal | None:
        return self.repository.get(Principal, record_id, tenant_id=tenant_id)

    def create_agent(self, payload: AgentCreate, tenant_id: UUID | None = None) -> Agent:
        if self.get_principal(payload.owner_principal_id, tenant_id=tenant_id) is None:
            raise RegistryValidationError("owner_principal_id must reference an existing principal")
        data = payload.model_dump()
        if tenant_id is not None:
            data["tenant_id"] = tenant_id
        return self.repository.save(Agent(**data))

    def list_agents(self, tenant_id: UUID | None = None) -> list[Agent]:
        return self.repository.list(Agent, tenant_id=tenant_id)

    def get_agent(self, record_id: UUID, tenant_id: UUID | None = None) -> Agent | None:
        return self.repository.get(Agent, record_id, tenant_id=tenant_id)

    def update_agent(self, record_id: UUID, payload: AgentUpdate, tenant_id: UUID | None = None) -> Agent | None:
        record = self.get_agent(record_id, tenant_id=tenant_id)
        if record is None:
            return None
        changes = payload.model_dump(exclude_unset=True)
        if "status" in changes:
            raise RegistryValidationError("Use the dedicated activate, suspend, or retire lifecycle operation to change an agent status")
        for key, value in changes.items():
            setattr(record, key, value)
        return self.repository.save(record)

    def set_agent_status(self, record_id: UUID, status: AgentStatus, tenant_id: UUID | None = None) -> Agent | None:
        record = self.get_agent(record_id, tenant_id=tenant_id)
        if record is None:
            return None
        if record.status == status:
            return record
        if record.status == AgentStatus.RETIRED:
            raise RegistryValidationError("A retired agent cannot be reactivated or changed")
        allowed_transitions = {
            AgentStatus.ACTIVE: {AgentStatus.SUSPENDED, AgentStatus.RETIRED},
            AgentStatus.SUSPENDED: {AgentStatus.ACTIVE, AgentStatus.RETIRED},
        }
        if status not in allowed_transitions.get(record.status, set()):
            raise RegistryValidationError(f"Cannot change agent status from {record.status} to {status}")
        record.status = status
        return self.repository.save(record)

    def create_tool(self, payload: ToolCreate, tenant_id: UUID | None = None) -> Tool:
        data = payload.model_dump()
        if tenant_id is not None:
            data["tenant_id"] = tenant_id
        return self.repository.save(Tool(**data))

    def list_tools(self, tenant_id: UUID | None = None) -> list[Tool]:
        return self.repository.list(Tool, tenant_id=tenant_id)

    def get_tool(self, record_id: UUID, tenant_id: UUID | None = None) -> Tool | None:
        return self.repository.get(Tool, record_id, tenant_id=tenant_id)

    def update_tool(self, record_id: UUID, payload: ToolUpdate, tenant_id: UUID | None = None) -> Tool | None:
        record = self.get_tool(record_id, tenant_id=tenant_id)
        if record is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(record, key, value)
        return self.repository.save(record)

    def create_action(self, tool_id: UUID, payload: ActionCreate, tenant_id: UUID | None = None) -> Action | None:
        tool = self.get_tool(tool_id, tenant_id=tenant_id)
        if tool is None:
            return None
        data = payload.model_dump()
        if tenant_id is not None:
            data["tenant_id"] = tenant_id
        return self.repository.save(Action(tool_id=tool.id, **data))

    def list_actions(self, tool_id: UUID, tenant_id: UUID | None = None) -> list[Action]:
        return self.repository.list_actions(tool_id, tenant_id=tenant_id)

    def get_action(self, record_id: UUID, tenant_id: UUID | None = None) -> Action | None:
        return self.repository.get(Action, record_id, tenant_id=tenant_id)

    def update_action(self, record_id: UUID, payload: ActionUpdate, tenant_id: UUID | None = None) -> Action | None:
        record = self.get_action(record_id, tenant_id=tenant_id)
        if record is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(record, key, value)
        return self.repository.save(record)

    def create_resource(self, payload: ResourceCreate, tenant_id: UUID | None = None) -> Resource:
        data = payload.model_dump()
        if tenant_id is not None:
            data["tenant_id"] = tenant_id
        return self.repository.save(Resource(**data))

    def list_resources(self, tenant_id: UUID | None = None) -> list[Resource]:
        return self.repository.list(Resource, tenant_id=tenant_id)

    def get_resource(self, record_id: UUID, tenant_id: UUID | None = None) -> Resource | None:
        return self.repository.get(Resource, record_id, tenant_id=tenant_id)

    def update_resource(self, record_id: UUID, payload: ResourceUpdate, tenant_id: UUID | None = None) -> Resource | None:
        record = self.get_resource(record_id, tenant_id=tenant_id)
        if record is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(record, key, value)
        return self.repository.save(record)

    def create_delegation(self, payload: DelegationCreate, tenant_id: UUID | None = None) -> Delegation | None:
        if self.get_principal(payload.principal_id, tenant_id=tenant_id) is None or self.get_agent(payload.agent_id, tenant_id=tenant_id) is None:
            raise RegistryValidationError("principal_id and agent_id must reference existing records")
        data = payload.model_dump()
        data["metadata_"] = data.pop("metadata")
        if tenant_id is not None:
            data["tenant_id"] = tenant_id
        return self.repository.save(Delegation(**data))

    def list_delegations(self, tenant_id: UUID | None = None) -> list[Delegation]:
        stmt = select(Delegation).order_by(Delegation.issued_at.desc())
        if tenant_id is not None:
            stmt = stmt.where(Delegation.tenant_id == tenant_id)
        return list(self.db.scalars(stmt).all())

    def get_delegation(self, record_id: UUID, tenant_id: UUID | None = None) -> Delegation | None:
        return self.repository.get(Delegation, record_id, tenant_id=tenant_id)
