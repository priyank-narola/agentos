from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ActionRequestStatus, ApprovalRequest, ApprovalStatus, AuditEvent, ActorType, Decision, DecisionType, Principal
from app.repositories.approval import ApprovalRepository
from app.schemas import ApprovalActionRequest, ApprovalDetailSchema
from app.services.errors import RegistryConflictError, RegistryValidationError


class ApprovalConflictError(RegistryConflictError):
    pass


class ApprovalService:
    EXPIRY_MINUTES = 15

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ApprovalRepository(db)

    def list(self) -> list[ApprovalDetailSchema]:
        return [self._detail(item) for item in self.repository.list()]

    def get(self, approval_id: UUID) -> ApprovalDetailSchema | None:
        item = self.repository.get(approval_id)
        return self._detail(item) if item else None

    def create_for_request(self, request: ApprovalRequest, now: datetime | None = None) -> ApprovalRequest:
        with self.db.no_autoflush:
            existing = self.repository.for_action_request(request.action_request_id)
        if existing is not None:
            return existing
        request.expires_at = request.expires_at or (now or datetime.now(timezone.utc)) + timedelta(minutes=self.EXPIRY_MINUTES)
        self.db.add(request)
        self.db.flush()
        self._audit("APPROVAL_REQUESTED", request.requested_by, request, {"status": ApprovalStatus.PENDING.value})
        return request

    def approve(self, approval_id: UUID, payload: ApprovalActionRequest) -> ApprovalDetailSchema:
        return self._transition(approval_id, payload.approver_principal_id, ApprovalStatus.APPROVED)

    def reject(self, approval_id: UUID, payload: ApprovalActionRequest) -> ApprovalDetailSchema:
        return self._transition(approval_id, payload.approver_principal_id, ApprovalStatus.REJECTED)

    def expire(self, approval_id: UUID) -> ApprovalDetailSchema:
        return self._transition(approval_id, None, ApprovalStatus.EXPIRED)

    def cancel(self, approval_id: UUID, payload: ApprovalActionRequest) -> ApprovalDetailSchema:
        return self._transition(approval_id, payload.approver_principal_id, ApprovalStatus.CANCELLED)

    def _transition(self, approval_id: UUID, actor_id: UUID | None, target: ApprovalStatus) -> ApprovalDetailSchema:
        approval = self.repository.get(approval_id, lock=True)
        if approval is None:
            raise RegistryValidationError("Approval request not found")
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

    def _final_allow(self, approval: ApprovalRequest, actor_id: UUID) -> None:
        request = approval.action_request
        request.status = ActionRequestStatus.COMPLETED
        original = self._original_decision(request)
        decision = Decision(action_request_id=request.id, decision=DecisionType.ALLOW, reason="HUMAN_APPROVAL: approved for execution; external execution remains disabled", policy_id=original.policy_id, policy_version=original.policy_version, risk_score=original.risk_score)
        self.db.add(decision)
        self.db.flush()
        self._audit("APPROVAL_APPROVED", actor_id, approval, {"status": ApprovalStatus.APPROVED.value, "decision_id": str(decision.id), "execution_status": "NOT_EXECUTED"}, decision.id)

    def _final_block(self, approval: ApprovalRequest, event_type: str, reason: str, actor_id: UUID | None) -> None:
        request = approval.action_request
        request.status = ActionRequestStatus.REJECTED
        original = self._original_decision(request)
        decision = Decision(action_request_id=request.id, decision=DecisionType.BLOCK, reason=f"{event_type}: {reason}", policy_id=original.policy_id, policy_version=original.policy_version, risk_score=original.risk_score)
        self.db.add(decision)
        self.db.flush()
        self._audit(event_type, actor_id or approval.requested_by, approval, {"status": approval.status.value, "decision_id": str(decision.id), "execution_status": "NOT_EXECUTED"}, decision.id)

    def _audit(self, event_type, actor_id, approval, data, decision_id=None) -> None:
        request = approval.action_request
        self.db.add(AuditEvent(event_type=event_type, actor_type=ActorType.PRINCIPAL, actor_id=actor_id, agent_id=request.agent_id, action_request_id=request.id, decision_id=decision_id, event_data={"approval_id": str(approval.id), "action_request_id": str(request.id), **data}))

    def _detail(self, approval: ApprovalRequest) -> ApprovalDetailSchema:
        request = approval.action_request
        original = self._original_decision(request) if request.decisions else None
        risk_event = next((event for event in request.audit_events if event.event_type == "RISK_EVALUATED"), None)
        risk = risk_event.event_data if risk_event else {}
        return ApprovalDetailSchema(id=approval.id, action_request_id=request.id, agent_id=request.agent_id, agent_name=request.agent.name, principal_id=request.principal_id, action_id=request.action_id, action_name=request.action.name, tool_id=request.action.tool.id, tool_name=request.action.tool.name, resource_id=request.resource_id, resource_type=request.resource.resource_type, resource_key=request.resource.resource_key, parameters=request.parameters, requested_by=approval.requested_by, status=approval.status, reason=approval.reason, risk_score=int(original.risk_score) if original and original.risk_score is not None else None, risk_classification=risk.get("classification"), risk_factors=risk.get("factors", []), policy_id=original.policy_id if original else None, policy_version=original.policy_version if original else None, decided_by=approval.decided_by, decided_at=approval.decided_at, requested_at=request.requested_at, expires_at=approval.expires_at)

    @staticmethod
    def _original_decision(request):
        return min(request.decisions, key=lambda item: (item.decided_at or datetime.min.replace(tzinfo=timezone.utc), str(item.id)))
