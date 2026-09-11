from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.db.models import Action, Agent, Delegation, DelegationStatus, Resource, ResourceSensitivity, ResourceStatus, RiskClassification, Tool


@dataclass(frozen=True)
class RiskFactor:
    code: str
    contribution: int
    explanation: str


@dataclass(frozen=True)
class RiskAssessment:
    score: int
    classification: str
    factors: tuple[RiskFactor, ...]
    evaluated_at: datetime
    engine_version: str


@dataclass(frozen=True)
class RiskContext:
    agent: Agent
    tool: Tool
    action: Action
    resource: Resource
    delegations: tuple[Delegation, ...]
    parameters: dict[str, Any]
    evaluated_at: datetime


class RiskEngine:
    VERSION = "agentos-risk-v1"

    ACTION_WEIGHTS = {RiskClassification.LOW: 5, RiskClassification.MEDIUM: 15, RiskClassification.HIGH: 30}
    AGENT_WEIGHTS = {RiskClassification.LOW: 0, RiskClassification.MEDIUM: 10, RiskClassification.HIGH: 20}
    RESOURCE_WEIGHTS = {ResourceSensitivity.LOW: 0, ResourceSensitivity.MEDIUM: 15, ResourceSensitivity.HIGH: 25}

    def evaluate(self, context: RiskContext) -> RiskAssessment:
        factors: list[RiskFactor] = []
        self._add(factors, f"ACTION_RISK_{context.action.risk_level.value}", self.ACTION_WEIGHTS[context.action.risk_level], f"Action is registered as {context.action.risk_level.value} risk.")
        self._add(factors, f"AGENT_RISK_{context.agent.risk_classification.value}", self.AGENT_WEIGHTS[context.agent.risk_classification], f"Agent has {context.agent.risk_classification.value} risk classification.")
        self._add(factors, f"RESOURCE_SENSITIVITY_{context.resource.sensitivity.value}", self.RESOURCE_WEIGHTS[context.resource.sensitivity], f"Resource has {context.resource.sensitivity.value} sensitivity.")

        if context.resource.status != ResourceStatus.ACTIVE:
            self._add(factors, "RESOURCE_NOT_ACTIVE", 20, f"Resource status is {context.resource.status.value}.")
        if context.action.tool_id != context.tool.id:
            self._add(factors, "TOOL_ACTION_MISMATCH", 30, "Action does not belong to the resolved tool.")
        if not context.delegations:
            self._add(factors, "DELEGATION_MISSING", 20, "No delegation exists for the resolved principal and agent context.")
        elif not any(self._delegation_valid(item, context.evaluated_at) for item in context.delegations):
            self._add(factors, "DELEGATION_INVALID", 20, "All matching delegations are revoked or expired.")

        amount_val = context.parameters.get("amount")
        if amount_val is not None:
            try:
                from decimal import Decimal
                from app.financial import FinancialRiskConfig
                fin_config = FinancialRiskConfig()
                amt = Decimal(str(amount_val))
                if amt >= fin_config.critical_threshold:
                    self._add(factors, "FINANCIAL_CRITICAL_TRANSACTION", 35, f"Transaction amount {amt} exceeds critical threshold {fin_config.critical_threshold}.")
                elif amt > 10000:
                    self._add(factors, "LARGE_TRANSACTION", 20, "Transaction amount exceeds 10,000 units.")
                elif amt > 5000:
                    self._add(factors, "ELEVATED_TRANSACTION", 10, "Transaction amount exceeds 5,000 units.")
                elif amt >= fin_config.low_threshold:
                    self._add(factors, "FINANCIAL_MEDIUM_TRANSACTION", 5, f"Transaction amount {amt} exceeds low threshold {fin_config.low_threshold}.")
            except (ValueError, TypeError, ArithmeticError):
                pass

        score = min(100, sum(factor.contribution for factor in factors))
        classification = self.classify(score)
        return RiskAssessment(score=score, classification=classification, factors=tuple(factors), evaluated_at=context.evaluated_at, engine_version=self.VERSION)

    @staticmethod
    def classify(score: int) -> str:
        bounded = max(0, min(100, score))
        if bounded >= 75:
            return "CRITICAL"
        if bounded >= 50:
            return "HIGH"
        if bounded >= 25:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _delegation_valid(delegation: Delegation, evaluated_at: datetime) -> bool:
        if delegation.status != DelegationStatus.ACTIVE:
            return False
        if delegation.expires_at is None:
            return True
        # Normalize both to naive UTC for comparison (SQLite strips tzinfo)
        expires = delegation.expires_at.replace(tzinfo=None) if delegation.expires_at.tzinfo else delegation.expires_at
        evaluated = evaluated_at.replace(tzinfo=None) if evaluated_at.tzinfo else evaluated_at
        return expires > evaluated

    @staticmethod
    def _add(factors: list[RiskFactor], code: str, contribution: int, explanation: str) -> None:
        if contribution:
            factors.append(RiskFactor(code=code, contribution=contribution, explanation=explanation))
