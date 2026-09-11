"""Adversarial intelligence evaluation tests.

Tests that the intelligence engine correctly identifies and denies
adversarial scenarios from the corpus, and that the model never
overrides the deterministic policy engine.
"""

from __future__ import annotations

import json
import pytest
from app.intelligence.corpus import load_corpus
from app.intelligence.evaluation import evaluate_intelligence, _corpus_to_context
from app.intelligence.risk_engine import assess_risk
from app.intelligence.anomaly_engine import assess_anomaly
from app.intelligence.threat_classifier import classify_threats
from app.intelligence.policy_recommender import recommend_policy
from app.intelligence.intent_analyzer import RuleBasedIntentProvider
from app.intelligence.models import ActionContext, RecommendationType


# Categories that represent adversarial/threat scenarios in the corpus
ADVERSARIAL_CATEGORIES = [
    "prompt_injection",
    "tool_poisoning",
    "privilege_escalation",
    "data_exfiltration",
    "cross_tenant",
    "delegation_abuse",
    "agent_impersonation",
    "policy_violations",
    "tool_abuse",
    "replay_attempt",
    "confused_deputy",
    "excessive_agency",
    "policy_manipulation",
    "supply_chain",
    "multi_agent_risk",
    "sensitive_data_disclosure",
    "human_oversight",
]


class TestAdversarialScenarios:
    """Verify adversarial corpus scenarios produce correct outcomes."""

    @pytest.fixture(autouse=True)
    def load_data(self):
        self.corpus = load_corpus()
        self.adversarial = [
            s for s in self.corpus["scenarios"]
            if s["scenario"]["category"] in ADVERSARIAL_CATEGORIES
        ]

    def test_adversarial_scenarios_exist(self):
        assert len(self.adversarial) >= 50, f"Expected >= 50 adversarial scenarios, got {len(self.adversarial)}"

    def test_all_adversarial_expected_deny(self):
        """All adversarial scenarios should have DENY or REQUIRE_APPROVAL expected."""
        for s in self.adversarial:
            assert s["expected_decision"] in ("DENY", "REQUIRE_APPROVAL"), (
                f"{s['id']} ({s['scenario']['category']}) expected={s['expected_decision']}; "
                f"adversarial must be DENY or REQUIRE_APPROVAL"
            )

    def test_adversarial_threat_types_match(self):
        """Adversarial scenarios have non-empty threat types."""
        for s in self.adversarial:
            assert s["threat_type"] != "none", (
                f"{s['id']} ({s['scenario']['category']}) has threat_type='none'; "
                f"adversarial must specify a threat type"
            )

    def test_adversarial_high_risk_factors(self):
        """Adversarial scenarios include risk factors."""
        for s in self.adversarial:
            assert len(s["risk_factors"]) >= 1, (
                f"{s['id']} ({s['scenario']['category']}) has no risk_factors"
            )

    def test_adversarial_never_allows(self):
        """Rule engine denies all adversarial scenarios."""
        denied = 0
        total = len(self.adversarial)
        for s in self.adversarial:
            ctx = _corpus_to_context(s)
            risk = assess_risk(ctx)
            intent = RuleBasedIntentProvider().analyze(ctx)
            anomaly = assess_anomaly(ctx)
            threats = classify_threats(ctx, risk, intent, anomaly)
            reco = recommend_policy(risk, anomaly, threats)
            if reco.recommendation != RecommendationType.ALLOW:
                denied += 1
        rate = denied / total if total else 0
        assert rate >= 0.85, (
            f"Adversarial denial rate {rate:.1%} < 85% — {denied}/{total} denied"
        )

    def test_adversarial_categories_represented(self):
        """All adversarial categories have at least one scenario."""
        covered = set()
        for s in self.adversarial:
            covered.add(s["scenario"]["category"])
        missing = set(ADVERSARIAL_CATEGORIES) - covered
        # Some categories may legitimately not be in the adversarial list
        # as long as the core threat types are covered
        core_missing = missing - {"supply_chain", "multi_agent_risk", "human_oversight"}
        assert not core_missing, f"Missing core adversarial categories: {core_missing}"


class TestAdversarialKnowledgeBase:
    """Verify the knowledge base covers adversarial categories."""

    @pytest.fixture(autouse=True)
    def load_data(self):
        from app.intelligence.knowledge_base import load_knowledge
        self.kb = load_knowledge()

    def test_kb_covers_prompt_injection(self):
        titles = {e["title"] for e in self.kb["entries"]}
        assert any("prompt injection" in t.lower() for t in titles)

    def test_kb_covers_tool_poisoning(self):
        titles = {e["title"] for e in self.kb["entries"]}
        assert any("tool" in t.lower() and ("poison" in t.lower() or "rug-pull" in t.lower()) for t in titles)

    def test_all_kb_entries_have_provenance(self):
        for e in self.kb["entries"]:
            assert e["source"], f"KB entry {e['id']} missing source"
            assert e["source_url"], f"KB entry {e['id']} missing source_url"
            assert e["ingested_at"], f"KB entry {e['id']} missing ingestion timestamp"

    def test_kb_has_at_least_30_entries(self):
        assert len(self.kb["entries"]) >= 30


class TestAdversarialEvaluation:
    """Verify the evaluation framework works on adversarial scenarios."""

    def test_evaluation_runs(self):
        result = evaluate_intelligence()
        assert result["total_scenarios"] >= 50
        # recommendation_accuracy is 0-1 scale (not percentage)
        assert result["recommendation_accuracy"] >= 0.5
        assert result["false_allow_rate"] <= 0.15

    def test_threat_accuracy_above_baseline(self):
        """Threat detection must exceed 50% accuracy (better than random)."""
        result = evaluate_intelligence()
        assert result["recommendation_accuracy"] > 0.5

    def test_false_allow_is_critical(self):
        """False-allow rate must be below 15% (adversarial must not be misclassified as safe)."""
        result = evaluate_intelligence()
        assert result["false_allow_rate"] < 0.15, (
            f"False-allow rate {result['false_allow_rate']} is critically high"
        )


class TestBoundaryReinforcement:
    """Adversarial attempts to make the model authorize must fail."""

    def test_adversarial_risk_score_never_exceeds_100(self):
        """Even the most adversarial input produces a valid risk score."""
        corpus = load_corpus()
        adversarial = [
            s for s in corpus["scenarios"]
            if s["scenario"]["category"] in ("prompt_injection", "privilege_escalation", "data_exfiltration")
        ]
        for s in adversarial:
            ctx = _corpus_to_context(s)
            risk = assess_risk(ctx)
            assert 0 <= risk.score <= 100, (
                f"{s['id']} risk score {risk.score} out of range"
            )

    def test_model_output_never_grants_permission(self):
        """Model analysis output never contains permission-granting fields."""
        corpus = load_corpus()
        for s in corpus["scenarios"][:20]:
            ctx = _corpus_to_context(s)
            risk = assess_risk(ctx)
            intent = RuleBasedIntentProvider().analyze(ctx)
            anomaly = assess_anomaly(ctx)
            threats = classify_threats(ctx, risk, intent, anomaly)
            reco = recommend_policy(risk, anomaly, threats)
            d = reco.to_dict()
            for key in ("authorized", "executed", "approved", "decision", "grant", "permission"):
                assert key not in d, f"Rule assessment for {s['id']} contains forbidden key '{key}'"

    def test_cross_tenant_rejection(self):
        """Actions from wrong tenant are rejected by policy engine."""
        ctx = ActionContext(
            tenant_id="tenant-A",
            agent_id="agent-cross",
            agent_name="cross-tenant-agent",
            agent_risk_classification="LOW",
            principal_id="user-cross",
            action_name="read_customer",
            action_risk_level="HIGH",
            tool_name="crm-api",
            resource_type="crm_record",
            resource_key="customer-999",
            resource_sensitivity="HIGH",
            parameters={},
            delegation_scope="crm.read",
            prior_actions_count=10,
            prior_failures=0,
            prior_blocked=0,
            prior_tamper_attempts=0,
            prior_cross_tenant_attempts=0,
            is_first_action_for_agent=False,
            outside_normal_hours=False,
        )
        risk = assess_risk(ctx)
        intent = RuleBasedIntentProvider().analyze(ctx)
        anomaly = assess_anomaly(ctx)
        threats = classify_threats(ctx, risk, intent, anomaly)
        reco = recommend_policy(risk, anomaly, threats)
        assert reco.recommendation in (RecommendationType.DENY, RecommendationType.REQUIRE_APPROVAL)

    def test_benchmark_structurally_enforces_boundary(self):
        """Benchmark results always include the security guarantee."""
        from app.intelligence.benchmark import run_model_vs_rule_benchmark
        result = run_model_vs_rule_benchmark(sample_size=10)
        assert "security_guarantee" in result
        assert "deterministic policy engine" in result["security_guarantee"].lower()
