from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal
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
    TenantRole,
    WorkforceGoalStatus,
    WorkforceWorkItemStatus,
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


class PrincipalRoleSchema(DomainSchema):
    id: UUID
    tenant_id: UUID
    principal_id: UUID
    role: TenantRole
    granted_by_principal_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class PrincipalRoleGrant(BaseModel):
    """An administrator grants one tenant-scoped product role."""

    actor_principal_id: UUID
    principal_id: UUID
    role: TenantRole


class PrincipalRoleRevoke(BaseModel):
    """An administrator removes one existing tenant-scoped role grant."""

    actor_principal_id: UUID


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


class WorkforceGoalSchema(DomainSchema):
    id: UUID
    tenant_id: UUID
    title: str
    description: str | None = None
    status: WorkforceGoalStatus
    parent_goal_id: UUID | None = None
    owner_agent_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class WorkforceGoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str | None = None
    status: WorkforceGoalStatus = WorkforceGoalStatus.PLANNED
    parent_goal_id: UUID | None = None
    owner_agent_id: UUID | None = None


class WorkforceGoalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = None
    status: WorkforceGoalStatus | None = None
    parent_goal_id: UUID | None = None
    owner_agent_id: UUID | None = None


class WorkforceProjectSchema(DomainSchema):
    id: UUID
    tenant_id: UUID
    name: str
    description: str | None = None
    status: str
    goal_id: UUID | None = None
    owner_agent_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class WorkforceProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: Literal["ACTIVE", "PAUSED", "COMPLETED", "CANCELLED"] = "ACTIVE"
    goal_id: UUID | None = None
    owner_agent_id: UUID | None = None


class WorkforceProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: Literal["ACTIVE", "PAUSED", "COMPLETED", "CANCELLED"] | None = None
    goal_id: UUID | None = None
    owner_agent_id: UUID | None = None


class WorkforceWorkItemSchema(DomainSchema):
    id: UUID
    tenant_id: UUID
    project_id: UUID
    goal_id: UUID | None = None
    title: str
    description: str | None = None
    status: WorkforceWorkItemStatus
    priority: str
    assignee_agent_id: UUID | None = None
    action_request_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class WorkforceWorkItemCreate(BaseModel):
    project_id: UUID
    title: str = Field(min_length=1, max_length=280)
    description: str | None = None
    goal_id: UUID | None = None
    status: WorkforceWorkItemStatus = WorkforceWorkItemStatus.BACKLOG
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    assignee_agent_id: UUID | None = None


class WorkforceWorkItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=280)
    description: str | None = None
    goal_id: UUID | None = None
    status: WorkforceWorkItemStatus | None = None
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] | None = None
    assignee_agent_id: UUID | None = None


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


class PolicyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    # Policies always enter through the draft lifecycle.  A caller must add
    # rules and explicitly publish; accepting ACTIVE here would allow a live
    # authorization change to bypass that control.
    status: PolicyStatus = PolicyStatus.DRAFT
    version: int = Field(ge=1)
    priority: int = Field(ge=0)

    @model_validator(mode="after")
    def require_draft_status(self) -> "PolicyCreate":
        if self.status != PolicyStatus.DRAFT:
            raise ValueError("New policies must be created as DRAFT and published explicitly")
        return self


class PolicyRuleCreate(BaseModel):
    effect: PolicyEffect
    action: str = Field(min_length=1, max_length=200)
    resource_type: str = Field(min_length=1, max_length=100)
    conditions: dict[str, Any] | None = None
    priority: int = Field(ge=0)


class PolicyEvaluationRequest(BaseModel):
    principal_id: UUID
    agent_id: UUID
    tool_id: UUID
    action_id: UUID
    resource_id: UUID
    parameters: dict[str, Any] = Field(default_factory=dict)
    policy_context: dict[str, Any] = Field(default_factory=dict)
    evaluated_at: datetime | None = None


class EvaluationTraceStep(BaseModel):
    step: int
    code: str
    outcome: str
    detail: str


class MatchedPolicyRule(BaseModel):
    policy_id: UUID
    policy_name: str
    policy_version: int
    policy_priority: int
    rule_id: UUID
    rule_effect: PolicyEffect
    rule_priority: int
    conditions: dict[str, Any] | None = None


class PolicyEvaluationResult(BaseModel):
    decision: str
    reason_code: str
    reason: str
    matched_policies: list[MatchedPolicyRule] = Field(default_factory=list)
    risk_level: RiskClassification | None = None
    delegation_status: DelegationStatus | None = None
    approval_required: bool
    trace: list[EvaluationTraceStep]


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


class RecoveryClass(str, Enum):
    """How the business action can be made safe after execution."""

    REVERSIBLE = "REVERSIBLE"
    COMPENSATABLE = "COMPENSATABLE"
    IRREVERSIBLE = "IRREVERSIBLE"


class ActionContext(BaseModel):
    """Business evidence captured and bound to a governed action.

    This is deliberately separate from provider-facing parameters: it tells a
    reviewer what will change, why, and what recovery option remains if the
    action succeeds but later needs to be corrected.
    """

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=500)
    target_system: str = Field(min_length=1, max_length=100)
    before: dict[str, Any] = Field(default_factory=dict)
    proposed_change: dict[str, Any] = Field(default_factory=dict)
    recovery_class: RecoveryClass
    recovery_plan: str = Field(min_length=1, max_length=500)


class ExecutionReceipt(BaseModel):
    """Authoritative provider evidence plus the declared recovery posture."""

    status: str
    evidence_status: str
    provider_name: str | None = None
    provider_reference: str | None = None
    provider_request_id: str | None = None
    payload_digest: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    recorded_at: datetime | None = None
    recovery_status: str
    recovery_plan: str | None = None


class ActionPreflightRequest(BaseModel):
    """A non-persistent request to evaluate a proposed governed action."""

    model_config = ConfigDict(extra="forbid")
    principal_id: UUID
    agent_id: UUID
    action_id: UUID
    resource_id: UUID
    parameters: dict[str, Any] = Field(default_factory=dict)
    action_context: ActionContext | None = None


class GatewayRequestCreate(ActionPreflightRequest):
    idempotency_key: str = Field(min_length=1, max_length=200)


class ActionPreflightResponse(BaseModel):
    """Decision preview that never creates, approves, or executes an action."""

    decision: str
    reason_code: str
    reason: str
    risk_level: RiskClassification | None = None
    risk_score: int | None = Field(default=None, ge=0, le=100)
    risk_classification: str | None = None
    risk_factors: list[dict[str, Any]] = Field(default_factory=list)
    risk_engine_version: str | None = None
    approval_required: bool
    matched_policies: list[MatchedPolicyRule] = Field(default_factory=list)
    connector_provider: str
    execution_plan: str
    payload_digest: str
    action_context: ActionContext | None = None
    evaluated_at: datetime
    warnings: list[str] = Field(default_factory=list)


class GatewayResponse(BaseModel):
    action_request_id: UUID
    gateway_status: str
    decision: str
    reason_code: str
    reason: str
    risk_level: RiskClassification | None = None
    risk_score: int | None = Field(default=None, ge=0, le=100)
    risk_classification: str | None = None
    risk_factors: list[dict[str, Any]] = Field(default_factory=list)
    risk_engine_version: str | None = None
    approval_required: bool
    execution_status: str
    execution_receipt: ExecutionReceipt
    action_context: ActionContext | None = None
    requested_at: datetime
    decided_at: datetime


class ActionRequestDetailSchema(BaseModel):
    id: UUID
    tenant_id: UUID
    agent_id: UUID
    agent_name: str
    principal_id: UUID
    principal_name: str | None = None
    action_id: UUID
    action_name: str
    tool_id: UUID
    tool_name: str
    resource_id: UUID
    resource_type: str
    resource_key: str
    parameters: dict[str, Any]
    action_context: ActionContext | None = None
    status: ActionRequestStatus
    idempotency_key: str
    requested_at: datetime
    decision: str | None = None
    reason: str | None = None
    reason_code: str | None = None
    risk_level: RiskClassification | None = None
    risk_score: int | None = Field(default=None, ge=0, le=100)
    risk_classification: str | None = None
    risk_factors: list[dict[str, Any]] = Field(default_factory=list)
    risk_engine_version: str | None = None
    execution_status: str = "NOT_EXECUTED"
    execution_receipt: ExecutionReceipt
    decided_at: datetime | None = None


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
    decision_reason: str | None = None
    decided_by: UUID | None = None
    decided_at: datetime | None = None
    expires_at: datetime | None = None


class ApprovalDetailSchema(BaseModel):
    id: UUID
    action_request_id: UUID
    agent_id: UUID
    agent_name: str
    principal_id: UUID
    principal_name: str | None = None
    action_id: UUID
    action_name: str
    tool_id: UUID
    tool_name: str
    resource_id: UUID
    resource_type: str
    resource_key: str
    parameters: dict[str, Any]
    action_context: ActionContext | None = None
    requested_by: UUID
    status: ApprovalStatus
    reason: str
    decision_reason: str | None = None
    risk_score: int | None = None
    risk_classification: str | None = None
    risk_factors: list[dict[str, Any]] = Field(default_factory=list)
    policy_id: UUID | None = None
    policy_version: int | None = None
    execution_status: str = "NOT_EXECUTED"
    execution_receipt: ExecutionReceipt
    decided_by: UUID | None = None
    decided_at: datetime | None = None
    requested_at: datetime
    expires_at: datetime


class EvidenceApproval(BaseModel):
    id: UUID
    status: ApprovalStatus
    requested_by: UUID
    decision_reason: str | None = None
    decided_by: UUID | None = None
    decided_at: datetime | None = None
    expires_at: datetime | None = None


class AuditEvidenceEvent(BaseModel):
    id: UUID
    event_type: str
    sequence: int | None = None
    occurred_at: datetime
    event_data: dict[str, Any]


class EvidenceIntegrity(BaseModel):
    """Digest metadata for the stable contents of a portable evidence export."""

    algorithm: Literal["SHA-256"] = "SHA-256"
    digest: str
    excluded_fields: list[str] = ["exported_at", "integrity"]


class ActionEvidenceBundle(BaseModel):
    """Portable, tenant-scoped evidence record for one governed action."""

    evidence_version: str = "1.0"
    exported_at: datetime
    action_request: ActionRequestDetailSchema
    approval: EvidenceApproval | None = None
    execution_receipt: ExecutionReceipt
    audit_events: list[AuditEvidenceEvent]
    integrity: EvidenceIntegrity


class ReconciliationCheckRequest(BaseModel):
    """Independent operator identity for a reconciliation status check."""

    actor_principal_id: UUID


class ReconciliationCase(BaseModel):
    """An execution whose provider outcome still needs verified resolution."""

    action_request_id: UUID
    requester_principal_id: UUID
    action_name: str
    resource_key: str
    execution_state: str
    provider_name: str
    provider_reference: str
    provider_request_id: str
    error_code: str | None = None
    error_message: str | None = None
    requested_at: datetime
    updated_at: datetime


class ReconciliationResult(ReconciliationCase):
    previous_state: str
    observed_provider_status: str
    reconciled_at: datetime


class ApprovalActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    approver_principal_id: UUID
    decision_reason: str | None = Field(default=None, min_length=1, max_length=4000)
