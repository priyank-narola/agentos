from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from app.db.models import (
    ActionRequestStatus,
    AgentStatus,
    ApprovalStatus,
    CapabilityStatus,
    DecisionType,
    DelegationStatus,
    PolicyEffect,
    PolicyStatus,
    PrincipalStatus,
    PrincipalType,
    ResourceSensitivity,
    ResourceStatus,
    RiskClassification,
)


class DomainSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PrincipalSchema(DomainSchema):
    id: UUID
    type: PrincipalType
    name: str
    external_id: str
    status: PrincipalStatus
    created_at: datetime
    updated_at: datetime


class PrincipalCreate(BaseModel):
    type: PrincipalType = PrincipalType.HUMAN
    name: str = Field(min_length=1, max_length=200)
    external_id: str = Field(min_length=1, max_length=200)
    status: PrincipalStatus = PrincipalStatus.ACTIVE


class AgentSchema(DomainSchema):
    id: UUID
    name: str
    description: str | None = None
    owner_principal_id: UUID
    purpose: str
    version: str
    status: AgentStatus
    risk_classification: RiskClassification
    created_at: datetime
    updated_at: datetime


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    owner_principal_id: UUID
    purpose: str = Field(min_length=1)
    version: str = Field(min_length=1, max_length=50)
    risk_classification: RiskClassification
    description: str | None = None


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    purpose: str | None = Field(default=None, min_length=1)
    version: str | None = Field(default=None, min_length=1, max_length=50)
    risk_classification: RiskClassification | None = None
    description: str | None = None
    status: AgentStatus | None = None


class DelegationSchema(DomainSchema):
    id: UUID
    principal_id: UUID
    agent_id: UUID
    scope: str
    status: DelegationStatus
    issued_at: datetime
    expires_at: datetime | None = None
    metadata: dict[str, Any] | None = Field(default=None, validation_alias=AliasChoices("metadata", "metadata_"))

    @model_validator(mode="before")
    @classmethod
    def read_reserved_metadata_column(cls, value: Any) -> Any:
        if hasattr(value, "metadata_"):
            return {"id": value.id, "principal_id": value.principal_id, "agent_id": value.agent_id, "scope": value.scope, "status": value.status, "issued_at": value.issued_at, "expires_at": value.expires_at, "metadata": value.metadata_}
        return value


class DelegationCreate(BaseModel):
    principal_id: UUID
    agent_id: UUID
    scope: str = Field(min_length=1, max_length=200)
    issued_at: datetime
    expires_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class ToolSchema(DomainSchema):
    id: UUID
    name: str
    description: str
    status: CapabilityStatus


class ToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    status: CapabilityStatus = CapabilityStatus.ACTIVE


class ToolUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    status: CapabilityStatus | None = None


class ActionSchema(DomainSchema):
    id: UUID
    tool_id: UUID
    name: str
    description: str
    risk_level: RiskClassification
    status: CapabilityStatus


class ActionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    risk_level: RiskClassification
    status: CapabilityStatus = CapabilityStatus.ACTIVE


class ActionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    risk_level: RiskClassification | None = None
    status: CapabilityStatus | None = None


class ResourceSchema(DomainSchema):
    id: UUID
    resource_type: str
    resource_key: str
    sensitivity: ResourceSensitivity
    owner_reference: str | None = None
    status: ResourceStatus


class ResourceCreate(BaseModel):
    resource_type: str = Field(min_length=1, max_length=100)
    resource_key: str = Field(min_length=1, max_length=300)
    sensitivity: ResourceSensitivity
    status: ResourceStatus = ResourceStatus.ACTIVE
    owner_reference: str | None = Field(default=None, max_length=200)


class ResourceUpdate(BaseModel):
    sensitivity: ResourceSensitivity | None = None
    status: ResourceStatus | None = None
    owner_reference: str | None = Field(default=None, max_length=200)


class PolicySchema(DomainSchema):
    id: UUID
    name: str
    description: str | None = None
    status: PolicyStatus
    version: int
    priority: int
    created_at: datetime
    updated_at: datetime


class ActionRequestSchema(DomainSchema):
    id: UUID
    agent_id: UUID
    principal_id: UUID
    action_id: UUID
    resource_id: UUID
    parameters: dict[str, Any]
    requested_at: datetime
    status: ActionRequestStatus
    idempotency_key: str


class DecisionSchema(DomainSchema):
    id: UUID
    action_request_id: UUID
    decision: DecisionType
    reason: str
    policy_id: UUID | None = None
    policy_version: int | None = None
    risk_score: Decimal | None = Field(default=None, ge=0, le=100)
    decided_at: datetime


class PolicyRuleSchema(DomainSchema):
    id: UUID
    policy_id: UUID
    effect: PolicyEffect
    action: str
    resource_type: str
    conditions: dict[str, Any] | None = None
    priority: int


class ApprovalRequestSchema(DomainSchema):
    id: UUID
    action_request_id: UUID
    requested_by: UUID
    status: ApprovalStatus
    reason: str
    decided_by: UUID | None = None
    decided_at: datetime | None = None
    expires_at: datetime | None = None
