import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ActionRequest, ActionRequestStatus, Action, Agent, ApprovalRequest, AuditEvent, ActorType, Decision, DecisionType, Delegation, Resource, Tool, Principal, DEFAULT_TENANT_ID

logger = logging.getLogger(__name__)
from app.policy import DeterministicPolicyEvaluator, EvaluationInput, ResolvedRecords
from app.repositories.gateway import GatewayRepository
from app.repositories.policy import PolicyRepository
from app.schemas import (
    ActionContext,
    ActionEvidenceBundle,
    ActionPreflightRequest,
    ActionPreflightResponse,
    ActionRequestDetailSchema,
    AuditEvidenceEvent,
    EvidenceApproval,
    GatewayRequestCreate,
    GatewayResponse,
)
from app.risk import RiskAssessment, RiskContext, RiskEngine
from app.services.errors import RegistryConflictError
from app.services.evidence_integrity import build_evidence_integrity
from app.services.approval import ApprovalService


from app.financial import (
    ACTION_CONTEXT_PARAMETER_KEY,
    FinancialValidationError,
    executable_parameters,
    validate_financial_action_parameters,
)
from app.execution import ExecutionStatus
from app.services.execution_ledger import persist_execution_result
from app.services.execution_receipt import build_execution_receipt
from app.services.audit_sequence import next_action_event_sequence
from app.services.execution_provider_registry import ExecutionProviderRegistry, build_execution_provider_registry


class GatewayIdempotencyConflict(RegistryConflictError):
    pass


class GatewayService:
    def __init__(self, db: Session, execution_providers: ExecutionProviderRegistry | None = None) -> None:
        self.db = db
        self.repository = GatewayRepository(db)
        self.policies = PolicyRepository(db)
        self.evaluator = DeterministicPolicyEvaluator()
        self.risk_engine = RiskEngine()
        # The sandbox remains the explicit safe default until a pilot validates
        # a real connector. Routing is injectable so every action can later use
        # a connector selected by the product configuration, not hard-coded here.
        self.execution_providers = execution_providers or build_execution_provider_registry()
        self.approvals = ApprovalService(db, execution_providers=self.execution_providers)

    def preflight(self, payload: ActionPreflightRequest) -> ActionPreflightResponse:
        """Evaluate an action without writing evidence or calling a connector.

        Preflight is deliberately advisory: a later submission will evaluate
        again, and an approval path will revalidate immediately before
        execution. It is useful for safe policy design and pilot walkthroughs,
        but never grants a reusable authorization.
        """
        principal = self.db.get(Principal, payload.principal_id)
        agent = self.db.get(Agent, payload.agent_id)
        action = self.db.get(Action, payload.action_id)
        resource = self.db.get(Resource, payload.resource_id)
        tool = self.db.get(Tool, action.tool_id) if action is not None else None
        if any(record is None for record in (principal, agent, action, resource, tool)):
            raise GatewayIdempotencyConflict("Referenced principal, agent, action, resource, or derived tool does not exist")
        if action.tool_id != tool.id:
            raise GatewayIdempotencyConflict("Action tool relationship is invalid")

        tenant_id = principal.tenant_id
        if agent.tenant_id != tenant_id or resource.tenant_id != tenant_id:
            raise GatewayIdempotencyConflict("Tenant mismatch: cross-tenant reference detected")
        try:
            provider_params, _ = validate_financial_action_parameters(action.name, payload.parameters)
        except FinancialValidationError as error:
            raise GatewayIdempotencyConflict(str(error)) from error
        clean_params = dict(provider_params)
        if payload.action_context is not None:
            clean_params[ACTION_CONTEXT_PARAMETER_KEY] = payload.action_context.model_dump(mode="json")

        evaluated_at = datetime.now(timezone.utc)
        delegations = list(self.db.scalars(select(Delegation).where(
            Delegation.agent_id == agent.id,
            Delegation.principal_id == principal.id,
            Delegation.tenant_id == tenant_id,
        )).all())
        risk = self.risk_engine.evaluate(RiskContext(
            agent=agent,
            tool=tool,
            action=action,
            resource=resource,
            delegations=tuple(delegations),
            parameters=clean_params,
            evaluated_at=evaluated_at,
        ))
        result = self.evaluator.evaluate(
            EvaluationInput(
                principal.id,
                agent.id,
                tool.id,
                action.id,
                resource.id,
                clean_params,
                {"risk_score": risk.score, "risk_classification": risk.classification},
                evaluated_at,
                risk.score,
                risk.classification,
            ),
            ResolvedRecords(
                principal,
                agent,
                tool,
                action,
                resource,
                delegations,
                self.policies.list_active_policies(tenant_id=tenant_id),
            ),
        )
        provider = self.execution_providers.resolve(action.name)
        if result.decision == "DENY":
            execution_plan = "BLOCKED"
        elif result.decision == "REQUIRE_APPROVAL":
            execution_plan = "HUMAN_APPROVAL_AND_REVALIDATION_REQUIRED"
        else:
            execution_plan = "READY_TO_SUBMIT"
        return ActionPreflightResponse(
            decision=result.decision,
            reason_code=result.reason_code,
            reason=result.reason,
            risk_level=action.risk_level,
            risk_score=risk.score,
            risk_classification=risk.classification,
            risk_factors=self._risk_data(risk).get("factors", []),
            risk_engine_version=self._risk_data(risk).get("engine_version"),
            approval_required=result.approval_required,
            matched_policies=result.matched_policies,
            connector_provider=provider.__class__.__name__,
            execution_plan=execution_plan,
            payload_digest=self._payload_digest(clean_params),
            action_context=payload.action_context,
            evaluated_at=evaluated_at,
            warnings=[
                "This is a non-persistent preview. It did not create an action request, approval, audit event, or execution.",
                "A submitted action is evaluated again; approval paths are revalidated immediately before execution.",
            ],
        )

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

        # Validate provider-facing parameters before evaluating idempotency. This
        # creates one canonical, payload-bound representation for all retries.
        try:
            provider_params, _ = validate_financial_action_parameters(action.name, payload.parameters)
        except FinancialValidationError as e:
            raise GatewayIdempotencyConflict(str(e)) from e
        clean_params = dict(provider_params)
        if payload.action_context is not None:
            clean_params[ACTION_CONTEXT_PARAMETER_KEY] = payload.action_context.model_dump(mode="json")

        existing = self.repository.get_by_idempotency_key(payload.idempotency_key, tenant_id=tenant_id, lock=True)
        if existing is not None:
            if self._canonical_payload(payload, clean_params) != self.repository.canonical_content(existing):
                raise GatewayIdempotencyConflict("Idempotency key is already used with different request content")
            return self._response(existing)

        payload_digest = self._payload_digest(clean_params)

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
        if payload.action_context is not None:
            self._audit("ACTION_CONTEXT_CAPTURED", principal.id, agent.id, request.id, None, {
                "summary": payload.action_context.summary,
                "target_system": payload.action_context.target_system,
                "recovery_class": payload.action_context.recovery_class.value,
                "payload_digest": payload_digest,
            }, tenant_id=tenant_id)

        evaluated_at = datetime.now(timezone.utc)
        delegations = list(self.db.scalars(select(Delegation).where(
            Delegation.agent_id == agent.id,
            Delegation.principal_id == principal.id,
            Delegation.tenant_id == tenant_id
        )).all())
        risk = self.risk_engine.evaluate(RiskContext(agent=agent, tool=tool, action=action, resource=resource, delegations=tuple(delegations), parameters=clean_params, evaluated_at=evaluated_at))
        self._audit("RISK_EVALUATED", principal.id, agent.id, request.id, None, {**self._risk_data(risk), "payload_digest": payload_digest}, tenant_id=tenant_id)

        # Intelligence Assessment (advisory only — never replaces the policy engine)
        intelligence_result = None
        try:
            from app.intelligence.assessor import assess as intelligence_assess
            intel = intelligence_assess(self.db, agent, principal, action, tool, resource, clean_params, tenant_id)
            intel_dict = intel.to_dict()
            intel_dict["deterministic_decision"] = None  # filled after policy evaluation
            self._audit("INTELLIGENCE_ASSESSMENT", principal.id, agent.id, request.id, None, {
                "assessment_id": intel_dict["assessment_id"],
                "risk_level": intel_dict["risk"]["level"],
                "risk_score": intel_dict["risk"]["score"],
                "anomaly_level": intel_dict["anomaly"]["level"],
                "intent_category": intel_dict["intent"]["category"],
                "threat_count": len(intel_dict["threats"]["threats"]),
                "highest_threat_severity": intel_dict["threats"]["highest_severity"],
                "policy_recommendation": intel_dict["policy_recommendation"]["recommendation"],
                "engine_version": intel_dict["engine_version"],
                "reasoning": intel_dict["reasoning"],
                "security_rule": "AI/Intelligence recommends. The deterministic policy engine decides.",
                "payload_digest": payload_digest,
            }, tenant_id=tenant_id)
            intelligence_result = intel_dict
        except Exception:
            logger.warning("Intelligence assessment failed for action %s (tenant=%s): %s", action.name, tenant_id, exc_info=True)
            # Intelligence failure must never block the deterministic pipeline

        result = self.evaluator.evaluate(EvaluationInput(principal.id, agent.id, tool.id, action.id, resource.id, clean_params, {"risk_score": risk.score, "risk_classification": risk.classification}, evaluated_at, risk.score, risk.classification), ResolvedRecords(principal, agent, tool, action, resource, delegations, self.policies.list_active_policies(tenant_id=tenant_id)))
        self._audit("POLICY_EVALUATED", principal.id, agent.id, request.id, None, {"decision": result.decision, "reason_code": result.reason_code, "payload_digest": payload_digest}, tenant_id=tenant_id)
        if intelligence_result is not None:
            intelligence_result["deterministic_decision"] = result.decision
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
            provider = self.execution_providers.resolve(action.name)
            self._audit("EXECUTION_STARTED", principal.id, agent.id, request.id, decision.id, {
                "provider": provider.__class__.__name__,
                "payload_digest": payload_digest
            }, tenant_id=tenant_id)
            exec_res = provider.execute(request.id, executable_parameters(clean_params), payload.idempotency_key, tenant_id=tenant_id)
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

    def get_evidence_bundle(self, request_id: UUID, tenant_id: UUID | None = None) -> ActionEvidenceBundle | None:
        """Export a complete, portable evidence record for one action request.

        The request is retrieved through the tenant-scoped repository, so the
        export cannot become a cross-tenant data channel. The bundle contains
        product-safe API representations rather than raw ORM objects.
        """
        request = self.repository.get_request(request_id, tenant_id=tenant_id)
        if request is None:
            return None
        context = self._action_context(request.parameters)
        approval = self.db.scalar(select(ApprovalRequest).where(ApprovalRequest.action_request_id == request.id))
        bundle = ActionEvidenceBundle(
            exported_at=datetime.now(timezone.utc),
            action_request=self._detail(request),
            approval=EvidenceApproval(
                id=approval.id,
                status=approval.status,
                requested_by=approval.requested_by,
                decided_by=approval.decided_by,
                decided_at=approval.decided_at,
                expires_at=approval.expires_at,
            ) if approval is not None else None,
            execution_receipt=build_execution_receipt(self.db, request.id, context),
            audit_events=[
                AuditEvidenceEvent(
                    id=event.id,
                    event_type=event.event_type,
                    sequence=event.event_sequence,
                    occurred_at=event.created_at,
                    event_data=event.event_data,
                )
                for event in sorted(request.audit_events, key=lambda event: (event.event_sequence is None, event.event_sequence or 0, event.created_at, str(event.id)))
            ],
            integrity={"digest": "0" * 64},
        )
        return bundle.model_copy(update={"integrity": build_evidence_integrity(bundle)})

    def _response(self, request: ActionRequest) -> GatewayResponse:
        decision = request.decisions[-1] if request.decisions else None
        decision_name = "DENY" if decision is not None and decision.decision == DecisionType.BLOCK else decision.decision.value if decision else "DENY"
        gateway_status = "AUTHORIZED" if decision_name == "ALLOW" else "PENDING_APPROVAL" if decision_name == "REQUIRE_APPROVAL" else "BLOCKED"
        reason = decision.reason if decision else "Request was blocked before policy evaluation"
        code, _, message = reason.partition(": ")
        risk = self._risk_evidence(request)
        context = self._action_context(request.parameters)
        receipt = build_execution_receipt(self.db, request.id, context)
        # Preserve the existing gateway API contract: its immediate response
        # reports the raw provider event. The receipt exposes the normalized
        # product-facing status used by the case file and approval experience.
        exec_event = next((event for event in reversed(request.audit_events) if event.event_type in ("EXECUTION_SUCCEEDED", "EXECUTION_FAILED", "EXECUTION_STARTED")), None)
        execution_status = exec_event.event_data.get("status", "NOT_EXECUTED") if exec_event else "NOT_EXECUTED"
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
            execution_status=execution_status,
            execution_receipt=receipt,
            action_context=context,
            requested_at=request.requested_at,
            decided_at=decision.decided_at if decision else request.requested_at
        )



    def _detail(self, request: ActionRequest) -> ActionRequestDetailSchema:
        decision = request.decisions[-1] if request.decisions else None
        decision_name = "DENY" if decision and decision.decision == DecisionType.BLOCK else decision.decision.value if decision else None
        code, _, reason = (decision.reason.partition(": ") if decision else (None, None, None))
        risk = self._risk_evidence(request)
        context = self._action_context(request.parameters)
        receipt = build_execution_receipt(self.db, request.id, context)
        return ActionRequestDetailSchema(id=request.id, tenant_id=request.tenant_id, agent_id=request.agent_id, agent_name=request.agent.name, principal_id=request.principal_id, principal_name=request.principal.name if request.principal else None, action_id=request.action_id, action_name=request.action.name, tool_id=request.action.tool.id, tool_name=request.action.tool.name, resource_id=request.resource_id, resource_type=request.resource.resource_type, resource_key=request.resource.resource_key, parameters=executable_parameters(request.parameters), action_context=context, status=request.status, idempotency_key=request.idempotency_key, requested_at=request.requested_at, decision=decision_name, reason=reason, reason_code=code, risk_level=request.action.risk_level, risk_score=int(decision.risk_score) if decision and decision.risk_score is not None else None, risk_classification=risk.get("classification"), risk_factors=risk.get("factors", []), risk_engine_version=risk.get("engine_version"), execution_status=receipt.status, execution_receipt=receipt, decided_at=decision.decided_at if decision else None)

    @staticmethod
    def _canonical_payload(payload: GatewayRequestCreate, parameters: dict[str, Any]) -> str:
        return json.dumps({"principal_id": str(payload.principal_id), "agent_id": str(payload.agent_id), "action_id": str(payload.action_id), "resource_id": str(payload.resource_id), "parameters": parameters}, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _payload_digest(parameters: dict[str, Any]) -> str:
        from app.financial import compute_payload_digest
        return compute_payload_digest(parameters)

    @staticmethod
    def _action_context(parameters: dict[str, Any]) -> ActionContext | None:
        context = parameters.get(ACTION_CONTEXT_PARAMETER_KEY)
        return ActionContext.model_validate(context) if context else None

    def _audit(self, event_type, actor_id, agent_id, request_id, decision_id, data, tenant_id=None) -> None:
        self.db.add(AuditEvent(
            tenant_id=tenant_id or DEFAULT_TENANT_ID,
            event_type=event_type,
            actor_type=ActorType.PRINCIPAL,
            actor_id=actor_id,
            agent_id=agent_id,
            action_request_id=request_id,
            decision_id=decision_id,
            event_sequence=next_action_event_sequence(self.db, request_id),
            event_data=data
        ))


    @staticmethod
    def _risk_data(risk: RiskAssessment) -> dict:
        return {"score": risk.score, "classification": risk.classification, "engine_version": risk.engine_version, "evaluated_at": risk.evaluated_at.isoformat(), "factors": [{"code": factor.code, "contribution": factor.contribution, "explanation": factor.explanation} for factor in risk.factors]}

    @staticmethod
    def _risk_evidence(request: ActionRequest) -> dict:
        event = next((item for item in request.audit_events if item.event_type == "RISK_EVALUATED"), None)
        return event.event_data if event else {}
