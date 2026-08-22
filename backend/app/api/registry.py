from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import (
    Action,
    Agent,
    AgentStatus,
    Delegation,
    Principal,
    Resource,
    Tool,
)
from app.db.session import get_db
from app.schemas import (
    ActionCreate,
    ActionSchema,
    ActionUpdate,
    AgentCreate,
    AgentSchema,
    AgentUpdate,
    DelegationCreate,
    DelegationSchema,
    PrincipalCreate,
    PrincipalSchema,
    ResourceCreate,
    ResourceSchema,
    ResourceUpdate,
    ToolCreate,
    ToolSchema,
    ToolUpdate,
)
from app.services.registry import RegistryService
from app.services.errors import RegistryConflictError, RegistryValidationError

router = APIRouter(prefix="/api/v1", tags=["registries"])


def service(db: Session = Depends(get_db)) -> RegistryService:
    return RegistryService(db)


def not_found(entity: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity} not found")


def persist(callable_):
    try:
        return callable_()
    except RegistryConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.post("/principals", response_model=PrincipalSchema, status_code=status.HTTP_201_CREATED)
def create_principal(payload: PrincipalCreate, registry: RegistryService = Depends(service)) -> Principal:
    return persist(lambda: registry.create_principal(payload))


@router.get("/principals", response_model=list[PrincipalSchema])
def list_principals(registry: RegistryService = Depends(service)) -> list[Principal]:
    return registry.list_principals()


@router.get("/principals/{principal_id}", response_model=PrincipalSchema)
def get_principal(principal_id: UUID, registry: RegistryService = Depends(service)) -> Principal:
    principal = registry.get_principal(principal_id)
    if principal is None:
        raise not_found("Principal")
    return principal


@router.post("/agents", response_model=AgentSchema, status_code=status.HTTP_201_CREATED)
def create_agent(payload: AgentCreate, registry: RegistryService = Depends(service)) -> Agent:
    try:
        return persist(lambda: registry.create_agent(payload))
    except RegistryValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/agents", response_model=list[AgentSchema])
def list_agents(registry: RegistryService = Depends(service)) -> list[Agent]:
    return registry.list_agents()


@router.get("/agents/{agent_id}", response_model=AgentSchema)
def get_agent(agent_id: UUID, registry: RegistryService = Depends(service)) -> Agent:
    agent = registry.get_agent(agent_id)
    if agent is None:
        raise not_found("Agent")
    return agent


@router.patch("/agents/{agent_id}", response_model=AgentSchema)
def update_agent(agent_id: UUID, payload: AgentUpdate, registry: RegistryService = Depends(service)) -> Agent:
    agent = registry.update_agent(agent_id, payload)
    if agent is None:
        raise not_found("Agent")
    return persist(lambda: agent)


@router.post("/agents/{agent_id}/suspend", response_model=AgentSchema)
def suspend_agent(agent_id: UUID, registry: RegistryService = Depends(service)) -> Agent:
    agent = registry.set_agent_status(agent_id, AgentStatus.SUSPENDED)
    if agent is None:
        raise not_found("Agent")
    return agent


@router.post("/agents/{agent_id}/retire", response_model=AgentSchema)
def retire_agent(agent_id: UUID, registry: RegistryService = Depends(service)) -> Agent:
    agent = registry.set_agent_status(agent_id, AgentStatus.RETIRED)
    if agent is None:
        raise not_found("Agent")
    return agent


@router.post("/tools", response_model=ToolSchema, status_code=status.HTTP_201_CREATED)
def create_tool(payload: ToolCreate, registry: RegistryService = Depends(service)) -> Tool:
    return persist(lambda: registry.create_tool(payload))


@router.get("/tools", response_model=list[ToolSchema])
def list_tools(registry: RegistryService = Depends(service)) -> list[Tool]:
    return registry.list_tools()


@router.get("/tools/{tool_id}", response_model=ToolSchema)
def get_tool(tool_id: UUID, registry: RegistryService = Depends(service)) -> Tool:
    tool = registry.get_tool(tool_id)
    if tool is None:
        raise not_found("Tool")
    return tool


@router.patch("/tools/{tool_id}", response_model=ToolSchema)
def update_tool(tool_id: UUID, payload: ToolUpdate, registry: RegistryService = Depends(service)) -> Tool:
    tool = registry.update_tool(tool_id, payload)
    if tool is None:
        raise not_found("Tool")
    return tool


@router.post("/tools/{tool_id}/actions", response_model=ActionSchema, status_code=status.HTTP_201_CREATED)
def create_action(tool_id: UUID, payload: ActionCreate, registry: RegistryService = Depends(service)) -> Action:
    try:
        action = registry.create_action(tool_id, payload)
        if action is None:
            raise not_found("Tool")
        return action
    except RegistryConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.get("/tools/{tool_id}/actions", response_model=list[ActionSchema])
def list_actions(tool_id: UUID, registry: RegistryService = Depends(service)) -> list[Action]:
    if registry.get_tool(tool_id) is None:
        raise not_found("Tool")
    return registry.list_actions(tool_id)


@router.get("/actions/{action_id}", response_model=ActionSchema)
def get_action(action_id: UUID, registry: RegistryService = Depends(service)) -> Action:
    action = registry.get_action(action_id)
    if action is None:
        raise not_found("Action")
    return action


@router.patch("/actions/{action_id}", response_model=ActionSchema)
def update_action(action_id: UUID, payload: ActionUpdate, registry: RegistryService = Depends(service)) -> Action:
    action = registry.update_action(action_id, payload)
    if action is None:
        raise not_found("Action")
    return action


@router.post("/resources", response_model=ResourceSchema, status_code=status.HTTP_201_CREATED)
def create_resource(payload: ResourceCreate, registry: RegistryService = Depends(service)) -> Resource:
    return persist(lambda: registry.create_resource(payload))


@router.get("/resources", response_model=list[ResourceSchema])
def list_resources(registry: RegistryService = Depends(service)) -> list[Resource]:
    return registry.list_resources()


@router.get("/resources/{resource_id}", response_model=ResourceSchema)
def get_resource(resource_id: UUID, registry: RegistryService = Depends(service)) -> Resource:
    resource = registry.get_resource(resource_id)
    if resource is None:
        raise not_found("Resource")
    return resource


@router.patch("/resources/{resource_id}", response_model=ResourceSchema)
def update_resource(resource_id: UUID, payload: ResourceUpdate, registry: RegistryService = Depends(service)) -> Resource:
    resource = registry.update_resource(resource_id, payload)
    if resource is None:
        raise not_found("Resource")
    return resource


@router.post("/delegations", response_model=DelegationSchema, status_code=status.HTTP_201_CREATED)
def create_delegation(payload: DelegationCreate, registry: RegistryService = Depends(service)) -> Delegation:
    try:
        return registry.create_delegation(payload)
    except RegistryValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/delegations", response_model=list[DelegationSchema])
def list_delegations(registry: RegistryService = Depends(service)) -> list[Delegation]:
    return registry.list_delegations()


@router.get("/delegations/{delegation_id}", response_model=DelegationSchema)
def get_delegation(delegation_id: UUID, registry: RegistryService = Depends(service)) -> Delegation:
    delegation = registry.get_delegation(delegation_id)
    if delegation is None:
        raise not_found("Delegation")
    return delegation
