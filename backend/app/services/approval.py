from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    ActionRequestStatus, ApprovalRequest, ApprovalStatus, AuditEvent, ActorType, Decision, DecisionType,
    Principal, PrincipalStatus, PrincipalType, Agent, AgentStatus, Delegation, DelegationStatus, Resource, ResourceStatus,
    Action, CapabilityStatus, Tool
)
from app.repositories.approval import ApprovalRepository
from app.schemas import ActionContext, ApprovalActionRequest, ApprovalDetailSchema
from app.services.errors import RegistryConflictError, RegistryValidationError

from app.financial import ACTION_CONTEXT_PARAMETER_KEY, compute_payload_digest, executable_parameters
from app.execution import ExecutionStatus
from app.services.execution_ledger import persist_execution_result
from app.services.execution_receipt import build_execution_receipt
from app.services.audit_sequence import next_action_event_sequence
from app.services.execution_provider_registry import ExecutionProviderRegistry, build_execution_provider_registry
from app.services.authorization import RoleAuthorizationError, require_any_role
from app.config import settings
from app.db.models import TenantRole



class ApprovalConflictError(RegistryConflictError):
    pass


class ApprovalTenantForbiddenError(ApprovalConflictError):
    """Raised when an operation crosses the authenticated tenant boundary."""


class ApprovalRoleForbiddenError(ApprovalTenantForbiddenError):
    """Raised when a production reviewer lacks approval authority."""


class ApprovalService:
    EXPIRY_MINUTES = 15

    def __init__(self, db: Session, execution_providers: ExecutionProviderRegistry | None = None) -> None:
        self.db = db
        self.repository = ApprovalRepository(db)
        self.execution_providers = execution_providers or build_execution_provider_registry()

    def list(self, tenant_id: UUID | None = None) -> list[ApprovalDetailSchema]:
        approvals = self.repository.list(tenant_id=tenant_id)
        if any(self._is_due_for_expiry(item) for item in approvals):
            for item in approvals:
                if self._is_due_for_expiry(item):
                    self._transition(item.id, None, ApprovalStatus.EXPIRED, tenant_id=tenant_id)
            approvals = self.repository.list(tenant_id=tenant_id)
        return [self._detail(item) for item in approvals]

    def get(self, approval_id: UUID, tenant_id: UUID | None = None) -> ApprovalDetailSchema | None:
        item = self.repository.get(approval_id, tenant_id=tenant_id)
        if item is not None and self._is_due_for_expiry(item):
            self._transition(item.id, None, ApprovalStatus.EXPIRED, tenant_id=tenant_id)
            item = self.repository.get(approval_id, tenant_id=tenant_id)
        return self._detail(item) if item else None

    def eligible_approvers(self, approval_id: UUID, tenant_id: UUID | None = None) -> "list[dict]":
        """Return ACTIVE human principals in the approval's tenant who are not the
        requester (SoD-eligible approver candidates).

        The candidate list is presentation/UX only: the approve endpoint still
        independently enforces active status, tenant membership, and separation of
        duties against the actor it receives. Tenant is derived server-side from
        the approval record; no client-supplied tenant is trusted.
        """
        approval = self.repository.get(approval_id, tenant_id=tenant_id)
        if approval is None:
            return []
        if approval.status != ApprovalStatus.PENDING:
            return []
        requester_ids = {approval.requested_by}
        if approval.action_request is not None:
            requester_ids.add(approval.action_request.principal_id)
        principals = list(self.db.scalars(
            select(Principal)
            .where(
                Principal.tenant_id == approval.tenant_id,
                Principal.status == PrincipalStatus.ACTIVE,
                Principal.type == PrincipalType.HUMAN,
            )
            .order_by(Principal.name)
        ).all())
        return [
            {
                "id": str(principal.id),
                "name": principal.name,
                "external_id": principal.external_id,
                "type": principal.type.value if hasattr(principal.type, "value") else str(principal.type),
            }
            for principal in principals
            if principal.id not in requester_ids
        ]

    def create_for_request(self, request: ApprovalRequest, now: datetime | None = None) -> ApprovalRequest:
        with self.db.no_autoflush:
            existing = self.repository.for_action_request(request.action_request_id)
        if existing is not None:
            return existing
        request.expires_at = request.expires_at or (now or datetime.now(timezone.utc)) + timedelta(minutes=self.EXPIRY_MINUTES)
        self.db.add(request)
        self.db.flush()
        digest = compute_payload_digest(request.action_request.parameters)
        self._audit("APPROVAL_REQUESTED", request.requested_by, request, {
            "status": ApprovalStatus.PENDING.value,
            "payload_digest": digest
        })
        return request

    def approve(self, approval_id: UUID, payload: ApprovalActionRequest, tenant_id: UUID | None = None) -> ApprovalDetailSchema:
        return self._transition(approval_id, payload.approver_principal_id, ApprovalStatus.APPROVED, tenant_id=tenant_id)

    def reject(self, approval_id: UUID, payload: ApprovalActionRequest, tenant_id: UUID | None = None) -> ApprovalDetailSchema:
        return self._transition(approval_id, payload.approver_principal_id, ApprovalStatus.REJECTED, tenant_id=tenant_id)

    def expire(self, approval_id: UUID) -> ApprovalDetailSchema:
        return self._transition(approval_id, None, ApprovalStatus.EXPIRED)

    @staticmethod
    def _is_due_for_expiry(approval: ApprovalRequest, now: datetime | None = None) -> bool:
        """Return whether a pending approval crossed its expiry boundary.

        SQLite returns naive datetimes even for timezone-aware columns, while
        PostgreSQL preserves the UTC offset, so normalize before comparison.
        """
        if approval.status != ApprovalStatus.PENDING or approval.expires_at is None:
            return False
        expires_at = (
            approval.expires_at.replace(tzinfo=timezone.utc)
            if approval.expires_at.tzinfo is None
            else approval.expires_at
        )
        return expires_at <= (now or datetime.now(timezone.utc))

    def cancel(self, approval_id: UUID, payload: ApprovalActionRequest, tenant_id: UUID | None = None) -> ApprovalDetailSchema:
        return self._transition(approval_id, payload.approver_principal_id, ApprovalStatus.CANCELLED, tenant_id=tenant_id)

    def _transition(self, approval_id: UUID, actor_id: UUID | None, target: ApprovalStatus, tenant_id: UUID | None = None) -> ApprovalDetailSchema:
        approval = self.repository.get(approval_id, lock=True)
        if approval is None:
            raise RegistryValidationError("Approval request not found")
        if tenant_id is not None and approval.tenant_id != tenant_id:
            raise ApprovalTenantForbiddenError("Cross-tenant approval access forbidden")
        now = datetime.now(timezone.utc)
        if approval.status != ApprovalStatus.PENDING:
            raise ApprovalConflictError(f"Approval request is already {approval.status.value}")
        expires_at = approval.expires_at.replace(tzinfo=timezone.utc) if approval.expires_at.tzinfo is None else approval.expires_at
        if target in {ApprovalStatus.APPROVED, ApprovalStatus.REJECTED, ApprovalStatus.CANCELLED} and expires_at <= now:
            approval.status = ApprovalStatus.EXPIRED
            self._final_block(approval, "APPROVAL_EXPIRED", "Approval expired before reviewer action", actor_id)
            self.db.commit()
            raise ApprovalConflictError("Approval request has expired")
        if target != ApprovalStatus.EXPIRED and target in {ApprovalStatus.APPROVED, ApprovalStatus.REJECTED, ApprovalStatus.CANCELLED} and actor_id is None:
            raise RegistryValidationError("Approver principal is required")
        if actor_id is not None and self.db.get(Principal, actor_id) is None:
            raise RegistryValidationError("Approver principal not found")

        # Development data remains intentionally lightweight, but every staging
        # or production approval transition requires explicit tenant authority.
        # This check covers approve, reject, and cancel: an unprivileged user
        # must not be able to silently block or dispose of another user's case.
        if (
            settings.app_env != "development"
            and actor_id is not None
            and target in {ApprovalStatus.APPROVED, ApprovalStatus.REJECTED, ApprovalStatus.CANCELLED}
        ):
            try:
                require_any_role(
                    self.db,
                    tenant_id=approval.tenant_id,
                    principal_id=actor_id,
                    roles={TenantRole.ADMIN, TenantRole.APPROVER},
                )
            except RoleAuthorizationError as exc:
                raise ApprovalRoleForbiddenError(str(exc)) from exc

        if target == ApprovalStatus.APPROVED:
            # 1. Separation of Duties (SoD / Dual Control) Enforcement
            if actor_id == approval.requested_by or actor_id == approval.action_request.principal_id:
                approval.status = ApprovalStatus.REJECTED
                approval.decided_by = actor_id
                approval.decided_at = now
                self._final_block(
                    approval,
                    "SECURITY_SEPARATION_OF_DUTIES_VIOLATION",
                    "Separation of duties violation: Requester cannot approve their own action request",
                    actor_id
                )
                self.db.commit()
                raise ApprovalConflictError("Separation of duties violation: Requester cannot approve their own action request")

            # 2. Payload-Bound Approval Verification Invariant
            request = approval.action_request
            current_digest = compute_payload_digest(request.parameters)
            orig_digest = None
            if approval.reason and "[payload_digest:" in approval.reason:
                orig_digest = approval.reason.partition("[payload_digest:")[2].split("]")[0]
            if not orig_digest:
                orig_event = next((e for e in request.audit_events if e.event_data and "payload_digest" in e.event_data), None)
                if orig_event:
                    orig_digest = orig_event.event_data.get("payload_digest")

            if orig_digest and orig_digest != current_digest:
                approval.status = ApprovalStatus.REJECTED
                approval.decided_by = actor_id
                approval.decided_at = now
                self._final_block(
                    approval,
                    "SECURITY_PAYLOAD_TAMPERED",
                    "Action parameters were modified after approval request creation",
                    actor_id
                )
                self.db.commit()
                raise ApprovalConflictError("Payload tamper detected: Action parameters modified after approval request")

            # 3. Full TOCTOU Security Context Re-Validation
            toctou_failure = self._revalidate_security_context(approval, actor_id, now)
            if toctou_failure:
                approval.status = ApprovalStatus.REJECTED
                approval.decided_by = actor_id
                approval.decided_at = now
                self._final_block(
                    approval,
                    "SECURITY_TOCTOU_REVALIDATION_FAILED",
                    toctou_failure,
                    actor_id
                )
                self.db.commit()
                raise ApprovalConflictError(f"TOCTOU re-validation failed: {toctou_failure}")

        approval.status = target
        approval.decided_by = actor_id
        approval.decided_at = now
        if target == ApprovalStatus.APPROVED:
            self._final_allow(approval, actor_id)
        else:
            self._final_block(approval, "APPROVAL_EXPIRED" if target == ApprovalStatus.EXPIRED else f"APPROVAL_{target.value}", f"Approval request was {target.value.lower()}", actor_id)
        self.db.commit()
        self.db.refresh(approval)
        return self._detail(approval)

    def _revalidate_security_context(self, approval: ApprovalRequest, actor_id: UUID, now: datetime) -> str | None:
        """
        Re-evaluates the complete Security Context at the exact millisecond of approval execution.
        Verifies Principal, Agent, Delegation, Resource, Action, Tool, and Policy Engine state.
        Returns None if valid, or a descriptive failure reason string if invalid.
        """
        req = approval.action_request
        tenant_id = approval.tenant_id

        # 1. Requester Principal Active & Tenant Check
        requester = self.db.get(Principal, req.principal_id)
        if requester is None or requester.status != PrincipalStatus.ACTIVE or requester.tenant_id != tenant_id:
            return f"Requester principal '{req.principal_id}' is no longer active or valid for tenant '{tenant_id}'"

        # 2. Approver Principal Active & Tenant Check
        approver = self.db.get(Principal, actor_id)
        if approver is None or approver.status != PrincipalStatus.ACTIVE or approver.tenant_id != tenant_id:
            return f"Approver principal '{actor_id}' is no longer active or valid for tenant '{tenant_id}'"

        # 3. Agent Active & Tenant Check
        agent = self.db.get(Agent, req.agent_id)
        if agent is None or agent.status != AgentStatus.ACTIVE or agent.tenant_id != tenant_id:
            return f"Agent '{req.agent_id}' is no longer active or valid for tenant '{tenant_id}'"

        # 4. Delegation Active, Non-Expired & Tenant Check
        now_dt = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now
        delegations = list(self.db.scalars(
            select(Delegation).where(
                Delegation.agent_id == agent.id,
                Delegation.principal_id == requester.id,
                Delegation.tenant_id == tenant_id,
                Delegation.status == DelegationStatus.ACTIVE
            )
        ).all())
        valid_delegations = [
            d for d in delegations
            if d.expires_at is None or (
                d.expires_at.replace(tzinfo=timezone.utc) if d.expires_at.tzinfo is None else d.expires_at
            ) > now_dt
        ]
        if not valid_delegations:
            return f"No valid active delegation exists for Principal '{requester.id}' and Agent '{agent.id}' in tenant '{tenant_id}'"

        # 5. Resource Active & Tenant Check
        resource = self.db.get(Resource, req.resource_id)
        if resource is None or resource.status != ResourceStatus.ACTIVE or resource.tenant_id != tenant_id:
            return f"Target resource '{req.resource_id}' is no longer active or valid for tenant '{tenant_id}'"

        # 6. Action & Tool Active Check
        action = self.db.get(Action, req.action_id)
        if action is None or action.status != CapabilityStatus.ACTIVE:
            return f"Action '{req.action_id}' is no longer active"
        tool = self.db.get(Tool, action.tool_id)
        if tool is None or tool.status != CapabilityStatus.ACTIVE:
            return f"Derived tool '{action.tool_id}' is no longer active"

        # 7. Policy Engine Re-Evaluation
        from app.policy import DeterministicPolicyEvaluator, EvaluationInput, ResolvedRecords
        from app.repositories.policy import PolicyRepository
        from app.risk import RiskEngine, RiskContext

        evaluator = DeterministicPolicyEvaluator()
        policy_repo = PolicyRepository(self.db)
        risk_engine = RiskEngine()

        risk = risk_engine.evaluate(RiskContext(
            agent=agent,
            tool=tool,
            action=action,
            resource=resource,
            delegations=tuple(valid_delegations),
            parameters=req.parameters,
            evaluated_at=now
        ))

        policy_result = evaluator.evaluate(
            EvaluationInput(
                requester.id, agent.id, tool.id, action.id, resource.id,
                req.parameters,
                {"risk_score": risk.score, "risk_classification": risk.classification},
                now, risk.score, risk.classification
            ),
            ResolvedRecords(requester, agent, tool, action, resource, valid_delegations, policy_repo.list_active_policies(tenant_id=tenant_id))
        )

        if policy_result.decision == "DENY":
            return f"Policy re-evaluation evaluated to DENY ({policy_result.reason_code}: {policy_result.reason})"

        return None


    def _final_allow(self, approval: ApprovalRequest, actor_id: UUID) -> None:
        request = approval.action_request
        request.status = ActionRequestStatus.COMPLETED
        original = self._original_decision(request)
        digest = compute_payload_digest(request.parameters)

        # Route after the approval is payload-bound and fully revalidated. The
        # provider receives executable parameters only, never control-plane data.
        provider = self.execution_providers.resolve(request.action.name)
        self._audit("EXECUTION_STARTED", actor_id, approval, {
            "provider": provider.__class__.__name__,
            "payload_digest": digest
        })
        exec_res = provider.execute(request.id, executable_parameters(request.parameters), request.idempotency_key, tenant_id=approval.tenant_id)

        exec_status = exec_res.status.value
        reason_msg = (
            f"HUMAN_APPROVAL: Approved and executed via {exec_res.provider_name} (Status: {exec_status}, Ref: {exec_res.transaction_reference})"
            if exec_res.status == ExecutionStatus.EXECUTION_SUCCEEDED
            else f"HUMAN_APPROVAL: Approved but execution failed ({exec_res.error_message})"
        )
        decision = Decision(
            action_request_id=request.id,
            tenant_id=approval.tenant_id,
            decision=DecisionType.ALLOW,
            reason=reason_msg,
            policy_id=original.policy_id,
            policy_version=original.policy_version,
            risk_score=original.risk_score
        )
        self.db.add(decision)
        self.db.flush()
        persist_execution_result(self.db, action_request_id=request.id, tenant_id=approval.tenant_id, result=exec_res, parameters=request.parameters)

        event_name = "EXECUTION_SUCCEEDED" if exec_res.status == ExecutionStatus.EXECUTION_SUCCEEDED else "EXECUTION_FAILED"
        self._audit(event_name, actor_id, approval, {
            "execution_id": exec_res.execution_id,
            "status": exec_res.status.value,
            "transaction_reference": exec_res.transaction_reference,
            "error_message": exec_res.error_message,
            "payload_digest": digest
        }, decision.id)

        self._audit("APPROVAL_APPROVED", actor_id, approval, {
            "status": ApprovalStatus.APPROVED.value,
            "decision_id": str(decision.id),
            "execution_status": exec_status,
            "payload_digest": digest
        }, decision.id)

    def _final_block(self, approval: ApprovalRequest, event_type: str, reason: str, actor_id: UUID | None) -> None:
        request = approval.action_request
        request.status = ActionRequestStatus.REJECTED
        original = self._original_decision(request)
        digest = compute_payload_digest(request.parameters)
        decision = Decision(action_request_id=request.id, tenant_id=approval.tenant_id, decision=DecisionType.BLOCK, reason=f"{event_type}: {reason}", policy_id=original.policy_id, policy_version=original.policy_version, risk_score=original.risk_score)
        self.db.add(decision)
        self.db.flush()
        self._audit(event_type, actor_id or approval.requested_by, approval, {
            "status": approval.status.value,
            "decision_id": str(decision.id),
            "execution_status": "NOT_EXECUTED",
            "payload_digest": digest
        }, decision.id)


    def _audit(self, event_type, actor_id, approval, data, decision_id=None) -> None:
        request = approval.action_request
        self.db.add(AuditEvent(
            tenant_id=approval.tenant_id,
            event_type=event_type,
            actor_type=ActorType.PRINCIPAL,
            actor_id=actor_id,
            agent_id=request.agent_id,
            action_request_id=request.id,
            decision_id=decision_id,
            event_sequence=next_action_event_sequence(self.db, request.id),
            event_data={"approval_id": str(approval.id), "action_request_id": str(request.id), **data}
        ))

    def _detail(self, approval: ApprovalRequest) -> ApprovalDetailSchema:
        request = approval.action_request
        original = self._original_decision(request) if request.decisions else None
        risk_event = next((event for event in request.audit_events if event.event_type == "RISK_EVALUATED"), None)
        risk = risk_event.event_data if risk_event else {}
        context = request.parameters.get(ACTION_CONTEXT_PARAMETER_KEY)
        action_context = ActionContext.model_validate(context) if context else None
        receipt = build_execution_receipt(self.db, request.id, action_context)
        return ApprovalDetailSchema(id=approval.id, action_request_id=request.id, agent_id=request.agent_id, agent_name=request.agent.name, principal_id=request.principal_id, principal_name=request.principal.name if request.principal else None, action_id=request.action_id, action_name=request.action.name, tool_id=request.action.tool.id, tool_name=request.action.tool.name, resource_id=request.resource_id, resource_type=request.resource.resource_type, resource_key=request.resource.resource_key, parameters=executable_parameters(request.parameters), action_context=action_context, requested_by=approval.requested_by, status=approval.status, reason=approval.reason, risk_score=int(original.risk_score) if original and original.risk_score is not None else None, risk_classification=risk.get("classification"), risk_factors=risk.get("factors", []), policy_id=original.policy_id if original else None, policy_version=original.policy_version if original else None, execution_status=receipt.status, execution_receipt=receipt, decided_by=approval.decided_by, decided_at=approval.decided_at, requested_at=request.requested_at, expires_at=approval.expires_at)

    @staticmethod
    def _original_decision(request):
        return min(request.decisions, key=lambda item: (item.decided_at or datetime.min.replace(tzinfo=timezone.utc), str(item.id)))
