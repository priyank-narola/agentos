from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import (
    ActionRequestStatus,
    AgentStatus,
    ApprovalStatus,
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


class DelegationSchema(DomainSchema):
    id: UUID
    principal_id: UUID
    agent_id: UUID
    scope: str
    status: DelegationStatus
    issued_at: datetime
    expires_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class ToolSchema(DomainSchema):
    id: UUID
    name: str
    description: str
    status: str


class ActionSchema(DomainSchema):
    id: UUID
    tool_id: UUID
    name: str
    description: str
    risk_level: RiskClassification
    status: str


class ResourceSchema(DomainSchema):
    id: UUID
    resource_type: str
    resource_key: str
    sensitivity: ResourceSensitivity
    owner_reference: str | None = None
    status: ResourceStatus


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
