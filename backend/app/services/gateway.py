import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ActionRequest, ActionRequestStatus, Action, Agent, ApprovalRequest, AuditEvent, ActorType, Decision, DecisionType, Delegation, Resource, Tool, Principal, DEFAULT_TENANT_ID
from app.policy import DeterministicPolicyEvaluator, EvaluationInput, ResolvedRecords
from app.repositories.gateway import GatewayRepository
from app.repositories.policy import PolicyRepository
from app.schemas import ActionRequestDetailSchema, GatewayRequestCreate, GatewayResponse
from app.risk import RiskAssessment, RiskContext, RiskEngine
from app.services.errors import RegistryConflictError
from app.services.approval import ApprovalService


from app.financial import validate_financial_action_parameters, compute_payload_digest, FinancialValidationError
from app.execution import SandboxPaymentProvider, ExecutionStatus
from app.services.execution_ledger import persist_execution_result


class GatewayIdempotencyConflict(RegistryConflictError):
    pass


class GatewayService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = GatewayRepository(db)
        self.policies = PolicyRepository(db)
        self.evaluator = DeterministicPolicyEvaluator()
        self.risk_engine = RiskEngine()
        self.approvals = ApprovalService(db)
        self.execution_provider = SandboxPaymentProvider()

    def submit(self, payload: GatewayRequestCreate) -> GatewayResponse:
        principal = self.db.get(Principal, payload.principal_id)
        agent = self.db.get(Agent, payload.agent_id)
        action = self.db.get(Action, payload.action_id)
        resource = self.db.get(Resource, payload.resource_id)
        tool = self.db.get(Tool, action.tool_id) if action is not None else None
        if any(record is None for record in (principal, agent, action, resource, tool)):
            raise GatewayIdempotencyConflict("Referenced principal, agent, action, resource, or derived tool does not exist")
        if action.tool_id != tool.id:
            raise GatewayIdempotencyConflict("Action tool relationship is invalid")

        # Multi-Tenant Consistency Validation
        tenant_id = principal.tenant_id
        if agent.tenant_id != tenant_id or resource.tenant_id != tenant_id:
            raise GatewayIdempotencyConflict("Tenant mismatch: cross-tenant reference detected")

        existing = self.repository.get_by_idempotency_key(payload.idempotency_key, tenant_id=tenant_id)
        if existing is not None:
            if self._canonical_payload(payload) != self.repository.canonical_content(existing):
                raise GatewayIdempotencyConflict("Idempotency key is already used with different request content")
            return self._response(existing)

        # Financial Action Parameter Validation & Digest Generation
        try:
            clean_params, payload_digest = validate_financial_action_parameters(action.name, payload.parameters)
        except FinancialValidationError as e:
            raise GatewayIdempotencyConflict(str(e)) from e

        request = ActionRequest(
            tenant_id=tenant_id,
            agent_id=agent.id,
            principal_id=principal.id,
            action_id=action.id,
            resource_id=resource.id,
            parameters=clean_params,
            idempotency_key=payload.idempotency_key,
            status=ActionRequestStatus.RECEIVED
        )
        self.db.add(request)
        self.db.flush()
        self._audit("ACTION_REQUEST_RECEIVED", principal.id, agent.id, request.id, None, {
            "action_id": str(action.id),
            "payload_digest": payload_digest
        }, tenant_id=tenant_id)

        evaluated_at = datetime.now(timezone.utc)
        delegations = list(self.db.scalars(select(Delegation).where(
            Delegation.agent_id == agent.id,
            Delegation.principal_id == principal.id,
            Delegation.tenant_id == tenant_id
        )).all())
        risk = self.risk_engine.evaluate(RiskContext(agent=agent, tool=tool, action=action, resource=resource, delegations=tuple(delegations), parameters=clean_params, evaluated_at=evaluated_at))
        self._audit("RISK_EVALUATED", principal.id, agent.id, request.id, None, {**self._risk_data(risk), "payload_digest": payload_digest}, tenant_id=tenant_id)
        result = self.evaluator.evaluate(EvaluationInput(principal.id, agent.id, tool.id, action.id, resource.id, clean_params, {"risk_score": risk.score, "risk_classification": risk.classification}, evaluated_at, risk.score, risk.classification), ResolvedRecords(principal, agent, tool, action, resource, delegations, self.policies.list_active_policies(tenant_id=tenant_id)))
        self._audit("POLICY_EVALUATED", principal.id, agent.id, request.id, None, {"decision": result.decision, "reason_code": result.reason_code, "payload_digest": payload_digest}, tenant_id=tenant_id)
        decision_value = DecisionType.ALLOW if result.decision == "ALLOW" else DecisionType.BLOCK if result.decision == "DENY" else DecisionType.REQUIRE_APPROVAL
        request.status = ActionRequestStatus.APPROVAL_PENDING if result.decision == "REQUIRE_APPROVAL" else ActionRequestStatus.EVALUATED
        matched = result.matched_policies[0] if result.matched_policies else None
        decision = Decision(action_request_id=request.id, tenant_id=tenant_id, decision=decision_value, reason=f"{result.reason_code}: {result.reason}", policy_id=matched.policy_id if matched else None, policy_version=matched.policy_version if matched else None, risk_score=risk.score)
        self.db.add(decision)
        self.db.flush()

        exec_status = "NOT_EXECUTED"
        if result.decision == "REQUIRE_APPROVAL":
            self.approvals.create_for_request(
                ApprovalRequest(
                    tenant_id=tenant_id,
                    action_request=request,
                    requested_by=principal.id,
                    reason=f"{result.reason_code}: {result.reason} [payload_digest:{payload_digest}]"
                ),
                evaluated_at
            )
        elif result.decision == "ALLOW" and action.name == "wire_transfer":
            # Immediate Execution for Authorized Low-Risk Financial Actions
            self._audit("EXECUTION_STARTED", principal.id, agent.id, request.id, decision.id, {
                "provider": "SandboxPaymentProvider",
                "payload_digest": payload_digest
            }, tenant_id=tenant_id)
            exec_res = self.execution_provider.execute(request.id, clean_params, payload.idempotency_key, tenant_id=tenant_id)
            exec_status = exec_res.status.value
            event_name = "EXECUTION_SUCCEEDED" if exec_res.status == ExecutionStatus.EXECUTION_SUCCEEDED else "EXECUTION_FAILED"
            persist_execution_result(self.db, action_request_id=request.id, tenant_id=tenant_id, result=exec_res, parameters=clean_params)
            self._audit(event_name, principal.id, agent.id, request.id, decision.id, {
                "execution_id": exec_res.execution_id,
                "status": exec_res.status.value,
                "transaction_reference": exec_res.transaction_reference,
                "error_message": exec_res.error_message,
                "payload_digest": payload_digest
            }, tenant_id=tenant_id)

        event_type = "ACTION_AUTHORIZED" if result.decision == "ALLOW" else "APPROVAL_REQUIRED" if result.decision == "REQUIRE_APPROVAL" else "ACTION_BLOCKED"
        self._audit(event_type, principal.id, agent.id, request.id, decision.id, {"execution_status": exec_status, "payload_digest": payload_digest}, tenant_id=tenant_id)
        self.db.commit()
        self.db.refresh(request)
        return self._response(request)

    def list_requests(self, tenant_id: UUID | None = None) -> list[ActionRequestDetailSchema]:
        return [self._detail(request) for request in self.repository.list_requests(tenant_id=tenant_id)]

    def get_request(self, request_id: UUID, tenant_id: UUID | None = None) -> ActionRequestDetailSchema | None:
        request = self.repository.get_request(request_id, tenant_id=tenant_id)
        return self._detail(request) if request else None

    def _response(self, request: ActionRequest) -> GatewayResponse:
        decision = request.decisions[-1] if request.decisions else None
        decision_name = "DENY" if decision is not None and decision.decision == DecisionType.BLOCK else decision.decision.value if decision else "DENY"
        gateway_status = "AUTHORIZED" if decision_name == "ALLOW" else "PENDING_APPROVAL" if decision_name == "REQUIRE_APPROVAL" else "BLOCKED"
        reason = decision.reason if decision else "Request was blocked before policy evaluation"
        code, _, message = reason.partition(": ")
        risk = self._risk_evidence(request)
        exec_event = next((e for e in reversed(request.audit_events) if e.event_type in ("EXECUTION_SUCCEEDED", "EXECUTION_FAILED", "EXECUTION_STARTED")), None)
        exec_status = exec_event.event_data.get("status", "NOT_EXECUTED") if exec_event else "NOT_EXECUTED"
        return GatewayResponse(
            action_request_id=request.id,
            gateway_status=gateway_status,
            decision=decision_name,
            reason_code=code,
            reason=message or reason,
            risk_level=request.action.risk_level if request.action else None,
            risk_score=int(decision.risk_score) if decision and decision.risk_score is not None else None,
            risk_classification=risk.get("classification"),
            risk_factors=risk.get("factors", []),
            risk_engine_version=risk.get("engine_version"),
            approval_required=decision_name == "REQUIRE_APPROVAL",
            execution_status=exec_status,
            requested_at=request.requested_at,
            decided_at=decision.decided_at if decision else request.requested_at
        )



    def _detail(self, request: ActionRequest) -> ActionRequestDetailSchema:
        decision = request.decisions[-1] if request.decisions else None
        decision_name = "DENY" if decision and decision.decision == DecisionType.BLOCK else decision.decision.value if decision else None
        code, _, reason = (decision.reason.partition(": ") if decision else (None, None, None))
        risk = self._risk_evidence(request)
        return ActionRequestDetailSchema(id=request.id, agent_id=request.agent_id, agent_name=request.agent.name, principal_id=request.principal_id, action_id=request.action_id, action_name=request.action.name, tool_id=request.action.tool.id, tool_name=request.action.tool.name, resource_id=request.resource_id, resource_type=request.resource.resource_type, resource_key=request.resource.resource_key, parameters=request.parameters, status=request.status, idempotency_key=request.idempotency_key, requested_at=request.requested_at, decision=decision_name, reason=reason, reason_code=code, risk_level=request.action.risk_level, risk_score=int(decision.risk_score) if decision and decision.risk_score is not None else None, risk_classification=risk.get("classification"), risk_factors=risk.get("factors", []), risk_engine_version=risk.get("engine_version"), decided_at=decision.decided_at if decision else None)

    @staticmethod
    def _canonical_payload(payload: GatewayRequestCreate) -> str:
        return json.dumps({"principal_id": str(payload.principal_id), "agent_id": str(payload.agent_id), "action_id": str(payload.action_id), "resource_id": str(payload.resource_id), "parameters": payload.parameters}, sort_keys=True, separators=(",", ":"))

    def _audit(self, event_type, actor_id, agent_id, request_id, decision_id, data, tenant_id=None) -> None:
        self.db.add(AuditEvent(
            tenant_id=tenant_id or DEFAULT_TENANT_ID,
            event_type=event_type,
            actor_type=ActorType.PRINCIPAL,
            actor_id=actor_id,
            agent_id=agent_id,
            action_request_id=request_id,
            decision_id=decision_id,
            event_data=data
        ))


    @staticmethod
    def _risk_data(risk: RiskAssessment) -> dict:
        return {"score": risk.score, "classification": risk.classification, "engine_version": risk.engine_version, "evaluated_at": risk.evaluated_at.isoformat(), "factors": [{"code": factor.code, "contribution": factor.contribution, "explanation": factor.explanation} for factor in risk.factors]}

    @staticmethod
    def _risk_evidence(request: ActionRequest) -> dict:
        event = next((item for item in request.audit_events if item.event_type == "RISK_EVALUATED"), None)
        return event.event_data if event else {}
