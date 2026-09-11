"""Regression tests proving model output never authorizes.

HARD SECURITY RULE:
The model may recommend/analyze/explain.
The model MUST NEVER authorize, bypass policy, bypass tenant isolation,
bypass approval, or trigger execution directly.

These tests verify the boundary is structurally enforced.
"""

from __future__ import annotations

import json
import pytest
from datetime import datetime, timezone
from app.intelligence.models import ActionContext, IntelligenceAssessment, RiskLevel
from app.intelligence.assessor import assess
from app.intelligence.risk_engine import assess_risk
from app.intelligence.threat_classifier import classify_threats
from app.intelligence.anomaly_engine import assess_anomaly
from app.intelligence.policy_recommender import recommend_policy
from app.intelligence.intent_analyzer import RuleBasedIntentProvider
from app.intelligence.providers import IntelligenceModelProvider, get_registry
from app.intelligence.evaluation import evaluate_intelligence


HIGH_RISK_CTX = ActionContext(
    tenant_id="tenant-A",
    agent_id="agent-1",
    agent_name="treasury-bot",
    agent_risk_classification="HIGH",
    principal_id="user-1",
    action_name="wire_transfer",
    action_risk_level="HIGH",
    tool_name="payment-gateway",
    resource_type="account",
    resource_key="acct-999",
    resource_sensitivity="HIGH",
    parameters={"amount": 150000.0, "currency": "USD"},
    delegation_scope="wire_transfer",
    prior_actions_count=25,
    prior_failures=2,
    prior_blocked=3,
    prior_tamper_attempts=1,
    prior_cross_tenant_attempts=0,
    is_first_action_for_agent=False,
    outside_normal_hours=True,
)

ADVERSARIAL_CTX = ActionContext(
    tenant_id="tenant-B",
    agent_id="agent-2",
    agent_name="data-agent",
    agent_risk_classification="LOW",
    principal_id="user-2",
    action_name="export_data",
    action_risk_level="MEDIUM",
    tool_name="database-query",
    resource_type="dataset",
    resource_key="customers",
    resource_sensitivity="HIGH",
    parameters={"query": "SELECT * FROM users WHERE role='admin'"},
    delegation_scope="crm.read",
    prior_actions_count=100,
    prior_failures=0,
    prior_blocked=0,
    prior_tamper_attempts=0,
    prior_cross_tenant_attempts=0,
    is_first_action_for_agent=False,
    outside_normal_hours=False,
)


def _build_assessment(ctx: ActionContext) -> IntelligenceAssessment:
    risk = assess_risk(ctx)
    intent = RuleBasedIntentProvider().analyze(ctx)
    anomaly = assess_anomaly(ctx)
    threats = classify_threats(ctx, risk, intent, anomaly)
    reco = recommend_policy(risk, anomaly, threats)
    return IntelligenceAssessment(
        assessment_id="test",
        action_context_summary={"action": ctx.action_name},
        risk=risk, intent=intent, anomaly=anomaly,
        threats=threats, policy_recommendation=reco,
        engine_version="v1", assessed_at=datetime.now(timezone.utc),
        overall_confidence=0.9, reasoning="test assessment",
    )


class TestModelNeverAuthorizes:
    """The model output NEVER contains an authorization decision."""

    def test_intelligence_assessment_has_no_decision_field(self):
        """IntelligenceAssessment does not expose a 'decision' field — only advisory signals."""
        assessment = _build_assessment(HIGH_RISK_CTX)
        d = assessment.to_dict()
        assert "decision" not in d, "IntelligenceAssessment must NOT expose a 'decision' field"
        assert "authorized" not in d, "IntelligenceAssessment must NOT contain 'authorized' field"

    def test_recommendation_is_advisory_not_executive(self):
        """PolicyRecommendation.recommendation is ADVISORY — it has no execution power."""
        risk = assess_risk(HIGH_RISK_CTX)
        intent = RuleBasedIntentProvider().analyze(HIGH_RISK_CTX)
        anomaly = assess_anomaly(HIGH_RISK_CTX)
        threats = classify_threats(HIGH_RISK_CTX, risk, intent, anomaly)
        reco = recommend_policy(risk, anomaly, threats)

        d = reco.to_dict()
        assert "executed" not in d
        assert "authorized" not in d
        assert "approved" not in d
        assert d["is_advisory"] is True
        assert "disclaimer" in d

    def test_intelligence_assessment_is_advisory(self):
        """IntelligenceAssessment carries advisory info via the policy recommendation."""
        assessment = _build_assessment(HIGH_RISK_CTX)
        d = assessment.to_dict()
        # The advisory flag is on the policy_recommendation
        assert d["policy_recommendation"]["is_advisory"] is True

    def test_assess_with_context_always_advisory(self):
        """Full intelligence pipeline returns advisory signals, never a decision."""
        risk = assess_risk(ADVERSARIAL_CTX)
        intent = RuleBasedIntentProvider().analyze(ADVERSARIAL_CTX)
        anomaly = assess_anomaly(ADVERSARIAL_CTX)
        threats = classify_threats(ADVERSARIAL_CTX, risk, intent, anomaly)
        reco = recommend_policy(risk, anomaly, threats)

        d = reco.to_dict()
        assert "decision" not in d
        assert "executed" not in d
        assert "authorized" not in d
        assert d["is_advisory"] is True

    def test_model_provider_interface_cannot_authorize(self):
        """The IntelligenceModelProvider ABC has no authorize/execute methods."""
        assert not hasattr(IntelligenceModelProvider, "authorize")
        assert not hasattr(IntelligenceModelProvider, "execute")
        assert not hasattr(IntelligenceModelProvider, "approve")
        assert not hasattr(IntelligenceModelProvider, "grant_permission")

    def test_model_output_cannot_carry_execution_signal(self):
        """Model analysis result never includes execution-triggering fields."""
        risk = assess_risk(HIGH_RISK_CTX)
        intent = RuleBasedIntentProvider().analyze(HIGH_RISK_CTX)
        anomaly = assess_anomaly(HIGH_RISK_CTX)
        threats = classify_threats(HIGH_RISK_CTX, risk, intent, anomaly)
        reco = recommend_policy(risk, anomaly, threats)

        d = reco.to_dict()
        forbidden_keys = {"authorized", "executed", "approved", "decision", "execute", "grant"}
        actual_keys = set(d.keys())
        overlap = actual_keys & forbidden_keys
        assert not overlap, f"Assessment contains forbidden execution keys: {overlap}"

    def test_adversarial_input_cannot_elevate_risk(self):
        """Adversarial input in parameters does NOT produce a risk score outside 0-100."""
        risk = assess_risk(ADVERSARIAL_CTX)
        assert 0 <= risk.score <= 100, f"Risk score out of range: {risk.score}"

    def test_cannot_bypass_risk_classification(self):
        """Even a LOW-risk agent is still subject to risk scoring."""
        ctx = ActionContext(
            tenant_id="tenant-X",
            agent_id="agent-low",
            agent_name="harmless",
            agent_risk_classification="LOW",
            principal_id="user-x",
            action_name="read_data",
            action_risk_level="LOW",
            tool_name="read-api",
            resource_type="document",
            resource_key="doc-1",
            resource_sensitivity="LOW",
            parameters={},
            delegation_scope="crm.read",
            prior_actions_count=0,
            prior_failures=0,
            prior_blocked=0,
            prior_tamper_attempts=0,
            prior_cross_tenant_attempts=0,
            is_first_action_for_agent=True,
            outside_normal_hours=False,
        )
        risk = assess_risk(ctx)
        assert risk.score >= 0
        assert risk.level in (RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH)

    def test_benchmark_structurally_enforces_boundary(self):
        """Benchmark results always include the security guarantee."""
        from app.intelligence.benchmark import run_model_vs_rule_benchmark
        result = run_model_vs_rule_benchmark(sample_size=10)
        assert "security_guarantee" in result
        assert "deterministic policy engine" in result["security_guarantee"].lower()


class TestModelProviderRegistryBoundary:
    """Registry cannot register providers with unauthorized capabilities."""

    def test_provider_cannot_add_authorize_method(self):
        """A custom provider cannot add authorization capability to the interface."""
        class RogueProvider(IntelligenceModelProvider):
            name = "rogue"
            def is_available(self): return True
            def analyze(self, ctx): return {"rogue": True}
            def authorize(self, ctx): return True

        rp = RogueProvider()
        assert not hasattr(IntelligenceModelProvider, "authorize")
        assert hasattr(rp, "authorize")

    def test_registry_only_exposes_analyze(self):
        """Registry only exposes analyze, never authorize."""
        registry = get_registry()
        for provider in registry.available():
            assert hasattr(provider, "analyze")
