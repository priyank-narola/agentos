"""Tenant-scoped planning service for the Workforce module.

This is intentionally a planning system, not an execution runtime. Any later
protected action from a work item must use the existing AgentOS gateway.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import (
    DEFAULT_TENANT_ID,
    Agent,
    AgentStatus,
    WorkforceGoal,
    WorkforceProject,
    WorkforceWorkItem,
)
from app.schemas import (
    WorkforceGoalCreate,
    WorkforceGoalUpdate,
    WorkforceProjectCreate,
    WorkforceProjectUpdate,
    WorkforceWorkItemCreate,
    WorkforceWorkItemUpdate,
)


class WorkforceConflictError(Exception):
    pass


class WorkforceValidationError(Exception):
    pass


class WorkforceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _tenant(tenant_id: UUID | None) -> UUID:
        return tenant_id or DEFAULT_TENANT_ID

    def _save(self, record):
        try:
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record
        except IntegrityError as error:
            self.db.rollback()
            raise WorkforceConflictError("A Workforce record with the same tenant identity already exists") from error

    def _agent(self, agent_id: UUID | None, tenant_id: UUID) -> Agent | None:
        if agent_id is None:
            return None
        return self.db.scalar(select(Agent).where(Agent.id == agent_id, Agent.tenant_id == tenant_id))

    def _validate_active_agent(self, agent_id: UUID | None, tenant_id: UUID, field: str) -> None:
        if agent_id is None:
            return
        agent = self._agent(agent_id, tenant_id)
        if agent is None:
            raise WorkforceValidationError(f"{field} must reference an agent in this tenant")
        if agent.status != AgentStatus.ACTIVE:
            raise WorkforceValidationError(f"{field} must reference an active agent")

    def list_goals(self, tenant_id: UUID | None = None) -> list[WorkforceGoal]:
        return list(self.db.scalars(select(WorkforceGoal).where(WorkforceGoal.tenant_id == self._tenant(tenant_id)).order_by(WorkforceGoal.created_at.desc())).all())

    def get_goal(self, goal_id: UUID, tenant_id: UUID | None = None) -> WorkforceGoal | None:
        return self.db.scalar(select(WorkforceGoal).where(WorkforceGoal.id == goal_id, WorkforceGoal.tenant_id == self._tenant(tenant_id)))

    def create_goal(self, payload: WorkforceGoalCreate, tenant_id: UUID | None = None) -> WorkforceGoal:
        scoped_tenant = self._tenant(tenant_id)
        self._validate_goal_refs(payload.parent_goal_id, payload.owner_agent_id, scoped_tenant)
        return self._save(WorkforceGoal(tenant_id=scoped_tenant, **payload.model_dump()))

    def update_goal(self, goal_id: UUID, payload: WorkforceGoalUpdate, tenant_id: UUID | None = None) -> WorkforceGoal | None:
        scoped_tenant = self._tenant(tenant_id)
        goal = self.get_goal(goal_id, scoped_tenant)
        if goal is None:
            return None
        changes = payload.model_dump(exclude_unset=True)
        parent_goal_id = changes.get("parent_goal_id", goal.parent_goal_id)
        if parent_goal_id == goal.id:
            raise WorkforceValidationError("A goal cannot be its own parent")
        self._validate_goal_refs(parent_goal_id, changes.get("owner_agent_id", goal.owner_agent_id), scoped_tenant)
        for field, value in changes.items():
            setattr(goal, field, value)
        return self._save(goal)

    def _validate_goal_refs(self, parent_goal_id: UUID | None, owner_agent_id: UUID | None, tenant_id: UUID) -> None:
        if parent_goal_id is not None and self.get_goal(parent_goal_id, tenant_id) is None:
            raise WorkforceValidationError("parent_goal_id must reference a goal in this tenant")
        self._validate_active_agent(owner_agent_id, tenant_id, "owner_agent_id")

    def list_projects(self, tenant_id: UUID | None = None) -> list[WorkforceProject]:
        return list(self.db.scalars(select(WorkforceProject).where(WorkforceProject.tenant_id == self._tenant(tenant_id)).order_by(WorkforceProject.created_at.desc())).all())

    def get_project(self, project_id: UUID, tenant_id: UUID | None = None) -> WorkforceProject | None:
        return self.db.scalar(select(WorkforceProject).where(WorkforceProject.id == project_id, WorkforceProject.tenant_id == self._tenant(tenant_id)))

    def create_project(self, payload: WorkforceProjectCreate, tenant_id: UUID | None = None) -> WorkforceProject:
        scoped_tenant = self._tenant(tenant_id)
        self._validate_project_refs(payload.goal_id, payload.owner_agent_id, scoped_tenant)
        return self._save(WorkforceProject(tenant_id=scoped_tenant, **payload.model_dump()))

    def update_project(self, project_id: UUID, payload: WorkforceProjectUpdate, tenant_id: UUID | None = None) -> WorkforceProject | None:
        scoped_tenant = self._tenant(tenant_id)
        project = self.get_project(project_id, scoped_tenant)
        if project is None:
            return None
        changes = payload.model_dump(exclude_unset=True)
        self._validate_project_refs(changes.get("goal_id", project.goal_id), changes.get("owner_agent_id", project.owner_agent_id), scoped_tenant)
        for field, value in changes.items():
            setattr(project, field, value)
        return self._save(project)

    def _validate_project_refs(self, goal_id: UUID | None, owner_agent_id: UUID | None, tenant_id: UUID) -> None:
        if goal_id is not None and self.get_goal(goal_id, tenant_id) is None:
            raise WorkforceValidationError("goal_id must reference a goal in this tenant")
        self._validate_active_agent(owner_agent_id, tenant_id, "owner_agent_id")

    def list_work_items(self, tenant_id: UUID | None = None, project_id: UUID | None = None) -> list[WorkforceWorkItem]:
        stmt = select(WorkforceWorkItem).where(WorkforceWorkItem.tenant_id == self._tenant(tenant_id))
        if project_id is not None:
            stmt = stmt.where(WorkforceWorkItem.project_id == project_id)
        return list(self.db.scalars(stmt.order_by(WorkforceWorkItem.created_at.desc())).all())

    def get_work_item(self, work_item_id: UUID, tenant_id: UUID | None = None) -> WorkforceWorkItem | None:
        return self.db.scalar(select(WorkforceWorkItem).where(WorkforceWorkItem.id == work_item_id, WorkforceWorkItem.tenant_id == self._tenant(tenant_id)))

    def create_work_item(self, payload: WorkforceWorkItemCreate, tenant_id: UUID | None = None) -> WorkforceWorkItem:
        scoped_tenant = self._tenant(tenant_id)
        self._validate_work_item_refs(payload.project_id, payload.goal_id, payload.assignee_agent_id, scoped_tenant)
        return self._save(WorkforceWorkItem(tenant_id=scoped_tenant, **payload.model_dump()))

    def update_work_item(self, work_item_id: UUID, payload: WorkforceWorkItemUpdate, tenant_id: UUID | None = None) -> WorkforceWorkItem | None:
        scoped_tenant = self._tenant(tenant_id)
        item = self.get_work_item(work_item_id, scoped_tenant)
        if item is None:
            return None
        changes = payload.model_dump(exclude_unset=True)
        self._validate_work_item_refs(item.project_id, changes.get("goal_id", item.goal_id), changes.get("assignee_agent_id", item.assignee_agent_id), scoped_tenant)
        for field, value in changes.items():
            setattr(item, field, value)
        return self._save(item)

    def _validate_work_item_refs(self, project_id: UUID, goal_id: UUID | None, assignee_agent_id: UUID | None, tenant_id: UUID) -> None:
        if self.get_project(project_id, tenant_id) is None:
            raise WorkforceValidationError("project_id must reference a project in this tenant")
        if goal_id is not None and self.get_goal(goal_id, tenant_id) is None:
            raise WorkforceValidationError("goal_id must reference a goal in this tenant")
        self._validate_active_agent(assignee_agent_id, tenant_id, "assignee_agent_id")
