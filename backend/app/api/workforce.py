"""Workforce planning APIs: no direct runtime or protected-action execution."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.authorization import require_tenant_roles
from app.db.models import TenantRole, WorkforceGoal, WorkforceProject, WorkforceWorkItem
from app.db.session import get_db
from app.schemas import (
    WorkforceGoalCreate,
    WorkforceGoalSchema,
    WorkforceGoalUpdate,
    WorkforceProjectCreate,
    WorkforceProjectSchema,
    WorkforceProjectUpdate,
    WorkforceWorkItemCreate,
    WorkforceWorkItemSchema,
    WorkforceWorkItemUpdate,
)
from app.services.workforce import WorkforceConflictError, WorkforceService, WorkforceValidationError


router = APIRouter(prefix="/api/v1/workforce", tags=["workforce"])
reader_required = require_tenant_roles({TenantRole.ADMIN, TenantRole.OPERATOR, TenantRole.AUDITOR, TenantRole.POLICY_AUTHOR})
writer_required = require_tenant_roles({TenantRole.ADMIN, TenantRole.OPERATOR})


def service(db: Session = Depends(get_db)) -> WorkforceService:
    return WorkforceService(db)


def tenant_of(request: Request) -> UUID | None:
    return getattr(request.state, "tenant_id", None)


def errors(callable_):
    try:
        return callable_()
    except WorkforceValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except WorkforceConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


def require(record, label: str):
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return record


@router.get("/goals", response_model=list[WorkforceGoalSchema], dependencies=[Depends(reader_required)])
def list_goals(request: Request, workforce: WorkforceService = Depends(service)) -> list[WorkforceGoal]:
    return workforce.list_goals(tenant_of(request))


@router.post("/goals", response_model=WorkforceGoalSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(writer_required)])
def create_goal(payload: WorkforceGoalCreate, request: Request, workforce: WorkforceService = Depends(service)) -> WorkforceGoal:
    return errors(lambda: workforce.create_goal(payload, tenant_of(request)))


@router.get("/goals/{goal_id}", response_model=WorkforceGoalSchema, dependencies=[Depends(reader_required)])
def get_goal(goal_id: UUID, request: Request, workforce: WorkforceService = Depends(service)) -> WorkforceGoal:
    return require(workforce.get_goal(goal_id, tenant_of(request)), "Goal")


@router.patch("/goals/{goal_id}", response_model=WorkforceGoalSchema, dependencies=[Depends(writer_required)])
def update_goal(goal_id: UUID, payload: WorkforceGoalUpdate, request: Request, workforce: WorkforceService = Depends(service)) -> WorkforceGoal:
    return require(errors(lambda: workforce.update_goal(goal_id, payload, tenant_of(request))), "Goal")


@router.get("/projects", response_model=list[WorkforceProjectSchema], dependencies=[Depends(reader_required)])
def list_projects(request: Request, workforce: WorkforceService = Depends(service)) -> list[WorkforceProject]:
    return workforce.list_projects(tenant_of(request))


@router.post("/projects", response_model=WorkforceProjectSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(writer_required)])
def create_project(payload: WorkforceProjectCreate, request: Request, workforce: WorkforceService = Depends(service)) -> WorkforceProject:
    return errors(lambda: workforce.create_project(payload, tenant_of(request)))


@router.get("/projects/{project_id}", response_model=WorkforceProjectSchema, dependencies=[Depends(reader_required)])
def get_project(project_id: UUID, request: Request, workforce: WorkforceService = Depends(service)) -> WorkforceProject:
    return require(workforce.get_project(project_id, tenant_of(request)), "Project")


@router.patch("/projects/{project_id}", response_model=WorkforceProjectSchema, dependencies=[Depends(writer_required)])
def update_project(project_id: UUID, payload: WorkforceProjectUpdate, request: Request, workforce: WorkforceService = Depends(service)) -> WorkforceProject:
    return require(errors(lambda: workforce.update_project(project_id, payload, tenant_of(request))), "Project")


@router.get("/work-items", response_model=list[WorkforceWorkItemSchema], dependencies=[Depends(reader_required)])
def list_work_items(request: Request, project_id: UUID | None = None, workforce: WorkforceService = Depends(service)) -> list[WorkforceWorkItem]:
    return workforce.list_work_items(tenant_of(request), project_id)


@router.post("/work-items", response_model=WorkforceWorkItemSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(writer_required)])
def create_work_item(payload: WorkforceWorkItemCreate, request: Request, workforce: WorkforceService = Depends(service)) -> WorkforceWorkItem:
    return errors(lambda: workforce.create_work_item(payload, tenant_of(request)))


@router.get("/work-items/{work_item_id}", response_model=WorkforceWorkItemSchema, dependencies=[Depends(reader_required)])
def get_work_item(work_item_id: UUID, request: Request, workforce: WorkforceService = Depends(service)) -> WorkforceWorkItem:
    return require(workforce.get_work_item(work_item_id, tenant_of(request)), "Work item")


@router.patch("/work-items/{work_item_id}", response_model=WorkforceWorkItemSchema, dependencies=[Depends(writer_required)])
def update_work_item(work_item_id: UUID, payload: WorkforceWorkItemUpdate, request: Request, workforce: WorkforceService = Depends(service)) -> WorkforceWorkItem:
    return require(errors(lambda: workforce.update_work_item(work_item_id, payload, tenant_of(request))), "Work item")
