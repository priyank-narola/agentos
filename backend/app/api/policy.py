from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.models import Policy, PolicyRule
from app.db.models import TenantRole
from app.db.session import get_db
from app.api.authorization import require_tenant_roles
from app.policy_schemas import PolicyDetailSchema
from app.schemas import PolicyCreate, PolicyEvaluationRequest, PolicyEvaluationResult, PolicyRuleCreate, PolicyRuleSchema, PolicySchema
from app.services.errors import RegistryConflictError, RegistryValidationError
from app.services.policy import PolicyService

router = APIRouter(prefix="/api/v1", tags=["policies"])
policy_author_required = require_tenant_roles({TenantRole.ADMIN, TenantRole.POLICY_AUTHOR})


def service(db: Session = Depends(get_db)) -> PolicyService:
    return PolicyService(db)


def tenant_of(request: Request) -> UUID | None:
    return getattr(request.state, "tenant_id", None)


def actor_of(request: Request) -> UUID | None:
    principal = getattr(request.state, "principal", None)
    return principal.id if principal is not None else None


def lifecycle_error(error: RegistryValidationError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


@router.post("/policies", response_model=PolicySchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(policy_author_required)])
def create_policy(payload: PolicyCreate, request: Request, policies: PolicyService = Depends(service)) -> Policy:
    try:
        return policies.create_policy(payload, tenant_id=tenant_of(request))
    except (RegistryConflictError, RegistryValidationError) as error:
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


@router.post("/policies/{policy_id}/rules", response_model=PolicyRuleSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(policy_author_required)])
def create_rule(policy_id: UUID, payload: PolicyRuleCreate, request: Request, policies: PolicyService = Depends(service)) -> PolicyRule:
    try:
        rule = policies.create_rule(policy_id, payload, tenant_id=tenant_of(request))
    except (RegistryConflictError, RegistryValidationError) as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return rule


@router.delete("/policies/{policy_id}/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(policy_author_required)])
def delete_rule(policy_id: UUID, rule_id: UUID, request: Request, policies: PolicyService = Depends(service)) -> None:
    try:
        deleted = policies.delete_rule(policy_id, rule_id, tenant_id=tenant_of(request))
    except RegistryValidationError as error:
        raise lifecycle_error(error) from error
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy rule not found")


@router.post("/policies/{policy_id}/versions", response_model=PolicyDetailSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(policy_author_required)])
def create_next_version(policy_id: UUID, request: Request, policies: PolicyService = Depends(service)) -> Policy:
    try:
        policy = policies.create_next_version(policy_id, tenant_id=tenant_of(request), actor_id=actor_of(request))
    except RegistryConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return policy


@router.post("/policies/{policy_id}/publish", response_model=PolicyDetailSchema, dependencies=[Depends(policy_author_required)])
def publish_policy(policy_id: UUID, request: Request, policies: PolicyService = Depends(service)) -> Policy:
    try:
        policy = policies.publish_policy(policy_id, tenant_id=tenant_of(request), actor_id=actor_of(request))
    except (RegistryConflictError, RegistryValidationError) as error:
        raise lifecycle_error(error) from error
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return policy


@router.post("/policies/{policy_id}/retire", response_model=PolicyDetailSchema, dependencies=[Depends(policy_author_required)])
def retire_policy(policy_id: UUID, request: Request, policies: PolicyService = Depends(service)) -> Policy:
    try:
        policy = policies.retire_policy(policy_id, tenant_id=tenant_of(request), actor_id=actor_of(request))
    except RegistryValidationError as error:
        raise lifecycle_error(error) from error
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return policy


@router.post("/policies/{policy_id}/simulate", response_model=PolicyEvaluationResult, dependencies=[Depends(policy_author_required)])
def simulate_draft_policy(policy_id: UUID, payload: PolicyEvaluationRequest, request: Request, policies: PolicyService = Depends(service)) -> PolicyEvaluationResult:
    try:
        result = policies.simulate_draft(policy_id, payload, tenant_id=tenant_of(request))
    except RegistryValidationError as error:
        raise lifecycle_error(error) from error
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return result


@router.post("/policy-evaluations", response_model=PolicyEvaluationResult)
def evaluate_policy(payload: PolicyEvaluationRequest, request: Request, policies: PolicyService = Depends(service)) -> PolicyEvaluationResult:
    return policies.evaluate(payload, tenant_id=tenant_of(request))
