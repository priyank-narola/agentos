from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SqlEnum

from app.db.base import Base


class StrEnum(str, enum.Enum):
    pass


class PrincipalType(StrEnum):
    HUMAN = "HUMAN"
    ORGANIZATION = "ORGANIZATION"


class PrincipalStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


class TenantRole(StrEnum):
    """Product roles granted per tenant, independent from external identity claims."""

    ADMIN = "ADMIN"
    POLICY_AUTHOR = "POLICY_AUTHOR"
    APPROVER = "APPROVER"
    OPERATOR = "OPERATOR"
    AUDITOR = "AUDITOR"


class AgentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


class RiskClassification(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DelegationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class CapabilityStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    RETIRED = "RETIRED"


class ResourceSensitivity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ResourceStatus(StrEnum):
    ACTIVE = "ACTIVE"
    RESTRICTED = "RESTRICTED"
    RETIRED = "RETIRED"


class PolicyStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class PolicyEffect(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class ActionRequestStatus(StrEnum):
    RECEIVED = "RECEIVED"
    EVALUATED = "EVALUATED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class DecisionType(StrEnum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


class ApprovalStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ActorType(StrEnum):
    PRINCIPAL = "PRINCIPAL"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"


class ExecutionState(StrEnum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


class ReconciliationJobStatus(StrEnum):
    """Durable status-readback job states; never an action-execution state."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    ESCALATED = "ESCALATED"


def enum_type(enum_class: type[enum.Enum]) -> SqlEnum:
    return SqlEnum(enum_class, name=enum_class.__name__.lower(), native_enum=True, create_constraint=True)


JSON_PAYLOAD = JSONB().with_variant(JSON(), "sqlite")
DEFAULT_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Tenant(TimestampMixin, Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")


class Principal(TimestampMixin, Base):
    __tablename__ = "principals"
    __table_args__ = (UniqueConstraint("tenant_id", "type", "external_id", name="uq_principals_tenant_type_external_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, default=DEFAULT_TENANT_ID)
    type: Mapped[PrincipalType] = mapped_column(enum_type(PrincipalType), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    external_id: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[PrincipalStatus] = mapped_column(enum_type(PrincipalStatus), nullable=False, default=PrincipalStatus.ACTIVE)
    tenant: Mapped[Tenant] = relationship()
    owned_agents: Mapped[list["Agent"]] = relationship(back_populates="owner", foreign_keys="Agent.owner_principal_id")


class PrincipalRole(TimestampMixin, Base):
    """A tenant-scoped role grant for one human principal.

    External OIDC identity tells us *who* made the request; this table tells us
    what operational authority that identity has in a tenant.
    """

    __tablename__ = "principal_roles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "principal_id", "role", name="uq_principal_roles_tenant_principal_role"),
        Index("ix_principal_roles_tenant_principal", "tenant_id", "principal_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)
    principal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("principals.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[TenantRole] = mapped_column(enum_type(TenantRole), nullable=False)
    granted_by_principal_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("principals.id", ondelete="SET NULL"))
    tenant: Mapped[Tenant] = relationship()
    principal: Mapped[Principal] = relationship(foreign_keys=[principal_id])


class Agent(TimestampMixin, Base):
    __tablename__ = "agents"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_agents_tenant_name"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, default=DEFAULT_TENANT_ID)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    owner_principal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[AgentStatus] = mapped_column(enum_type(AgentStatus), nullable=False, default=AgentStatus.ACTIVE)
    risk_classification: Mapped[RiskClassification] = mapped_column(enum_type(RiskClassification), nullable=False)
    tenant: Mapped[Tenant] = relationship()
    owner: Mapped[Principal] = relationship(back_populates="owned_agents", foreign_keys=[owner_principal_id])
    delegations: Mapped[list["Delegation"]] = relationship(back_populates="agent")
    action_requests: Mapped[list["ActionRequest"]] = relationship(back_populates="agent")


class Delegation(Base):
    __tablename__ = "delegations"
    __table_args__ = (
        Index("ix_delegations_agent_status", "agent_id", "status"),
        Index("ix_delegations_tenant_agent", "tenant_id", "agent_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, default=DEFAULT_TENANT_ID)
    principal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False)
    scope: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[DelegationStatus] = mapped_column(enum_type(DelegationStatus), nullable=False, default=DelegationStatus.ACTIVE)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON_PAYLOAD)
    tenant: Mapped[Tenant] = relationship()
    principal: Mapped[Principal] = relationship()
    agent: Mapped[Agent] = relationship(back_populates="delegations")


class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CapabilityStatus] = mapped_column(enum_type(CapabilityStatus), nullable=False, default=CapabilityStatus.ACTIVE)
    actions: Mapped[list["Action"]] = relationship(back_populates="tool", cascade="all, delete-orphan")


class Action(Base):
    __tablename__ = "actions"
    __table_args__ = (UniqueConstraint("tool_id", "name", name="uq_actions_tool_name"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    tool_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tools.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[RiskClassification] = mapped_column(enum_type(RiskClassification), nullable=False)
    status: Mapped[CapabilityStatus] = mapped_column(enum_type(CapabilityStatus), nullable=False, default=CapabilityStatus.ACTIVE)
    tool: Mapped[Tool] = relationship(back_populates="actions")
    action_requests: Mapped[list["ActionRequest"]] = relationship(back_populates="action")


class Resource(Base):
    __tablename__ = "resources"
    __table_args__ = (UniqueConstraint("tenant_id", "resource_type", "resource_key", name="uq_resources_tenant_type_key"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, default=DEFAULT_TENANT_ID)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_key: Mapped[str] = mapped_column(String(300), nullable=False)
    sensitivity: Mapped[ResourceSensitivity] = mapped_column(enum_type(ResourceSensitivity), nullable=False)
    owner_reference: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[ResourceStatus] = mapped_column(enum_type(ResourceStatus), nullable=False, default=ResourceStatus.ACTIVE)
    tenant: Mapped[Tenant] = relationship()
    action_requests: Mapped[list["ActionRequest"]] = relationship(back_populates="resource")


class Policy(TimestampMixin, Base):
    __tablename__ = "policies"
    __table_args__ = (UniqueConstraint("tenant_id", "name", "version", name="uq_policies_tenant_name_version"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, default=DEFAULT_TENANT_ID)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[PolicyStatus] = mapped_column(enum_type(PolicyStatus), nullable=False, default=PolicyStatus.DRAFT)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    tenant: Mapped[Tenant] = relationship()
    rules: Mapped[list["PolicyRule"]] = relationship(back_populates="policy", cascade="all, delete-orphan")


class PolicyRule(Base):
    __tablename__ = "policy_rules"
    __table_args__ = (Index("ix_policy_rules_policy_priority", "policy_id", "priority"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("policies.id", ondelete="RESTRICT"), nullable=False)
    effect: Mapped[PolicyEffect] = mapped_column(enum_type(PolicyEffect), nullable=False)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    conditions: Mapped[dict[str, Any] | None] = mapped_column(JSON_PAYLOAD)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    policy: Mapped[Policy] = relationship(back_populates="rules")


class ActionRequest(Base):
    __tablename__ = "action_requests"
    __table_args__ = (
        Index("ix_action_requests_agent_requested_at", "agent_id", "requested_at"),
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_action_requests_tenant_idempotency"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, default=DEFAULT_TENANT_ID)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False)
    principal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False)
    action_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("actions.id", ondelete="RESTRICT"), nullable=False)
    resource_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resources.id", ondelete="RESTRICT"), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON_PAYLOAD, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status: Mapped[ActionRequestStatus] = mapped_column(enum_type(ActionRequestStatus), nullable=False, default=ActionRequestStatus.RECEIVED)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    tenant: Mapped[Tenant] = relationship()
    agent: Mapped[Agent] = relationship(back_populates="action_requests")
    principal: Mapped[Principal] = relationship()
    action: Mapped[Action] = relationship(back_populates="action_requests")
    resource: Mapped[Resource] = relationship(back_populates="action_requests")
    decisions: Mapped[list["Decision"]] = relationship(back_populates="action_request")
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(back_populates="action_request")
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="action_request")


class Decision(Base):
    __tablename__ = "decisions"
    __table_args__ = (Index("ix_decisions_action_request_decided_at", "action_request_id", "decided_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)
    action_request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("action_requests.id", ondelete="RESTRICT"), nullable=False)
    decision: Mapped[DecisionType] = mapped_column(enum_type(DecisionType), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    policy_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("policies.id", ondelete="RESTRICT"))
    policy_version: Mapped[int | None] = mapped_column(Integer)
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    tenant: Mapped[Tenant] = relationship()
    action_request: Mapped[ActionRequest] = relationship(back_populates="decisions")
    policy: Mapped[Policy | None] = relationship()
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="decision")


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, default=DEFAULT_TENANT_ID)
    action_request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("action_requests.id", ondelete="RESTRICT"), nullable=False)
    requested_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[ApprovalStatus] = mapped_column(enum_type(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    decided_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("principals.id", ondelete="RESTRICT"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tenant: Mapped[Tenant] = relationship()
    action_request: Mapped[ActionRequest] = relationship(back_populates="approval_requests")
    requester: Mapped[Principal] = relationship(foreign_keys=[requested_by])
    decider: Mapped[Principal | None] = relationship(foreign_keys=[decided_by])


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_action_request_created_at", "action_request_id", "created_at"),
        Index("ix_audit_events_action_request_sequence", "action_request_id", "event_sequence"),
        UniqueConstraint("action_request_id", "event_sequence", name="uq_audit_events_action_request_sequence"),
        Index("ix_audit_events_agent_created_at", "agent_id", "created_at"),
        Index("ix_audit_events_tenant_created_at", "tenant_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, default=DEFAULT_TENANT_ID)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_type: Mapped[ActorType] = mapped_column(enum_type(ActorType), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("principals.id", ondelete="SET NULL"))
    agent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"))
    action_request_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("action_requests.id", ondelete="RESTRICT"))
    decision_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("decisions.id", ondelete="RESTRICT"))
    event_sequence: Mapped[int | None] = mapped_column(Integer)
    event_data: Mapped[dict[str, Any]] = mapped_column(JSON_PAYLOAD, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    tenant: Mapped[Tenant] = relationship()
    agent: Mapped[Agent | None] = relationship()
    action_request: Mapped[ActionRequest | None] = relationship(back_populates="audit_events")
    decision: Mapped[Decision | None] = relationship(back_populates="audit_events")


class FinancialExecution(TimestampMixin, Base):
    __tablename__ = "financial_executions"
    __table_args__ = (
        Index("ix_financial_executions_tenant_status", "tenant_id", "status"),
        Index("ix_financial_executions_provider_tx", "provider_name", "provider_transaction_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, default=DEFAULT_TENANT_ID)
    action_request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("action_requests.id", ondelete="RESTRICT"), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_transaction_id: Mapped[str] = mapped_column(String(200), nullable=False)
    provider_request_id: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[ExecutionState] = mapped_column(enum_type(ExecutionState), nullable=False, default=ExecutionState.PENDING)
    payload_digest: Mapped[str] = mapped_column(String(100), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    tenant: Mapped[Tenant] = relationship()
    action_request: Mapped[ActionRequest] = relationship()


class ReconciliationJob(TimestampMixin, Base):
    """A durable request to read a provider outcome after an uncertain write.

    A job has no executable action parameters by design. Processing it can only
    query a provider's status reference and record that readback.
    """

    __tablename__ = "reconciliation_jobs"
    __table_args__ = (
        UniqueConstraint("action_request_id", name="uq_reconciliation_jobs_action_request"),
        Index("ix_reconciliation_jobs_tenant_status_due", "tenant_id", "status", "next_check_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)
    action_request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("action_requests.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ReconciliationJobStatus.PENDING.value)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_check_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    tenant: Mapped[Tenant] = relationship()
    action_request: Mapped[ActionRequest] = relationship()


class WebhookEvent(TimestampMixin, Base):
    """Durable record of a verified webhook delivery (idempotency + audit).

    tenant_id is derived server-side from the signed payload/execution record;
    event_id uniqueness per tenant provides durable deduplication.
    """

    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "event_id", name="uq_webhook_events_tenant_event"),
        Index("ix_webhook_events_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, default=DEFAULT_TENANT_ID)
    event_id: Mapped[str] = mapped_column(String(200), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_PAYLOAD, nullable=False)
    tenant: Mapped[Tenant] = relationship()
