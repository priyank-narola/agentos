"""IntelligenceAssessor — the facade that orchestrates the full intelligence pipeline.

    ActionContext → Risk → Intent → Anomaly → Threats → Policy Recommendation

The output is an IntelligenceAssessment (advisory only). The deterministic
policy engine independently produces the final decision.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Action, Agent, Principal, Resource, Tool
from app.intelligence.models import (
    ActionContext, IntelligenceAssessment,
)
from app.intelligence.context_builder import build_action_context
from app.intelligence.risk_engine import assess_risk, ENGINE_VERSION as RISK_V
from app.intelligence.intent_analyzer import RuleBasedIntentProvider
from app.intelligence.anomaly_engine import assess_anomaly, ENGINE_VERSION as ANOMALY_V
from app.intelligence.threat_classifier import classify_threats, ENGINE_VERSION as THREAT_V
from app.intelligence.policy_recommender import recommend_policy, ENGINE_VERSION as RECO_V

FACADE_VERSION = f"facade-v1({RISK_V},{ANOMALY_V},{THREAT_V},{RECO_V})"


def assess(
    db: Session,
    agent: Agent,
    principal: Principal,
    action: Action,
    tool: Tool,
    resource: Resource,
    parameters: dict,
    tenant_id,
) -> IntelligenceAssessment:
    """Run the full intelligence pipeline for a single action request."""
    ctx = build_action_context(db, agent, principal, action, tool, resource, parameters, tenant_id)

    risk = assess_risk(ctx)
    intent = RuleBasedIntentProvider().analyze(ctx)
    anomaly = assess_anomaly(ctx)
    threats = classify_threats(ctx, risk, intent, anomaly)
    recommendation = recommend_policy(risk, anomaly, threats)

    overall_confidence = min(risk.confidence, intent.confidence, anomaly.confidence)
    reasoning = (
        f"Intelligence assessment: risk {risk.level.value} ({risk.score}/100), "
        f"intent {intent.category.value}, anomaly {anomaly.level.value}, "
        f"{len(threats.threats)} threat(s) (highest {threats.highest_severity.value}). "
        f"Recommendation: {recommendation.recommendation.value} (advisory). "
        f"The deterministic policy engine makes the final decision."
    )

    return IntelligenceAssessment(
        assessment_id=str(uuid.uuid4()),
        action_context_summary={
            "agent": ctx.agent_name,
            "principal_id": ctx.principal_id,
            "action": ctx.action_name,
            "resource": f"{ctx.resource_type}/{ctx.resource_key}",
            "delegation_scope": ctx.delegation_scope,
            "prior_actions": ctx.prior_actions_count,
        },
        risk=risk,
        intent=intent,
        anomaly=anomaly,
        threats=threats,
        policy_recommendation=recommendation,
        engine_version=FACADE_VERSION,
        assessed_at=datetime.now(timezone.utc),
        overall_confidence=overall_confidence,
        reasoning=reasoning,
    )
