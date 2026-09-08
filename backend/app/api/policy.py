from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.models import Policy, PolicyRule
from app.db.session import get_db
from app.policy_schemas import PolicyDetailSchema
from app.schemas import PolicyCreate, PolicyEvaluationRequest, PolicyEvaluationResult, PolicyRuleCreate, PolicyRuleSchema, PolicySchema
from app.services.errors import RegistryConflictError
from app.services.policy import PolicyService

router = APIRouter(prefix="/api/v1", tags=["policies"])


def service(db: Session = Depends(get_db)) -> PolicyService:
    return PolicyService(db)


def tenant_of(request: Request) -> UUID | None:
    return getattr(request.state, "tenant_id", None)


@router.post("/policies", response_model=PolicySchema, status_code=status.HTTP_201_CREATED)
def create_policy(payload: PolicyCreate, request: Request, policies: PolicyService = Depends(service)) -> Policy:
    try:
        return policies.create_policy(payload, tenant_id=tenant_of(request))
    except RegistryConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.get("/policies", response_model=list[PolicyDetailSchema])
def list_policies(request: Request, policies: PolicyService = Depends(service)) -> list[Policy]:
    return policies.list_policies(tenant_id=tenant_of(request))


@router.get("/policies/{policy_id}", response_model=PolicyDetailSchema)
def get_policy(policy_id: UUID, request: Request, policies: PolicyService = Depends(service)) -> Policy:
    policy = policies.get_policy(policy_id, tenant_id=tenant_of(request))
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return policy


@router.post("/policies/{policy_id}/rules", response_model=PolicyRuleSchema, status_code=status.HTTP_201_CREATED)
def create_rule(policy_id: UUID, payload: PolicyRuleCreate, request: Request, policies: PolicyService = Depends(service)) -> PolicyRule:
    try:
        rule = policies.create_rule(policy_id, payload, tenant_id=tenant_of(request))
    except RegistryConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return rule


@router.post("/policy-evaluations", response_model=PolicyEvaluationResult)
def evaluate_policy(payload: PolicyEvaluationRequest, request: Request, policies: PolicyService = Depends(service)) -> PolicyEvaluationResult:
    return policies.evaluate(payload, tenant_id=tenant_of(request))
