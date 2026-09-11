"""Intelligence Benchmark — model vs. rule evaluation with repeatable results.

Runs identical evaluation cases through:
  A. Deterministic intelligence (rule engine)
  B. Real model intelligence (if a model provider is configured)
  C. Final deterministic policy engine (always authoritative)

Stores benchmark results with model/provider, version, dataset version,
metrics, timestamp, and failure cases for future comparison.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.intelligence.corpus import load_corpus
from app.intelligence.evaluation import evaluate_intelligence, _corpus_to_context
from app.intelligence.models import RecommendationType
from app.intelligence.risk_engine import assess_risk
from app.intelligence.anomaly_engine import assess_anomaly
from app.intelligence.threat_classifier import classify_threats
from app.intelligence.intent_analyzer import RuleBasedIntentProvider
from app.intelligence.policy_recommender import recommend_policy
from app.intelligence.providers import get_registry

BENCHMARK_PATH = Path(__file__).parent / "data" / "benchmark_results.json"
BENCHMARK_VERSION = "benchmark-v1"


def run_model_vs_rule_benchmark(sample_size: int = 50) -> dict[str, Any]:
    """Run identical cases through rule-based and model-based intelligence."""
    corpus = load_corpus()
    scenarios = corpus["scenarios"][:sample_size]
    registry = get_registry()
    model_providers = registry.available()

    rule_results = {"correct": 0, "false_allow": 0, "false_deny": 0, "total": 0}
    model_results = {"correct": 0, "false_allow": 0, "false_deny": 0, "total": 0, "errors": 0, "unavailable": 0}
    failure_cases = []

    for s in scenarios:
        ctx = _corpus_to_context(s)
        expected = s["expected_decision"]

        # === A. Deterministic intelligence ===
        risk = assess_risk(ctx)
        intent = RuleBasedIntentProvider().analyze(ctx)
        anomaly = assess_anomaly(ctx)
        threats = classify_threats(ctx, risk, intent, anomaly)
        reco = recommend_policy(risk, anomaly, threats)

        rule_results["total"] += 1
        if reco.recommendation.value == expected:
            rule_results["correct"] += 1
        elif reco.recommendation == RecommendationType.ALLOW and expected in ("DENY", "REQUIRE_APPROVAL"):
            rule_results["false_allow"] += 1
            if len(failure_cases) < 10:
                failure_cases.append({"id": s["id"], "engine": "rule", "expected": expected, "got": "ALLOW"})
        elif reco.recommendation == RecommendationType.DENY and expected == "ALLOW":
            rule_results["false_deny"] += 1

        # === B. Model intelligence (if provider available) ===
        if model_providers:
            try:
                model_output = model_providers[0].analyze(ctx)
                if model_output.get("available"):
                    model_reco = model_output.get("recommendation", "UNKNOWN")
                    model_results["total"] += 1
                    if model_reco == expected:
                        model_results["correct"] += 1
                    elif model_reco == "ALLOW" and expected in ("DENY", "REQUIRE_APPROVAL"):
                        model_results["false_allow"] += 1
                        if len(failure_cases) < 10:
                            failure_cases.append({"id": s["id"], "engine": "model", "expected": expected, "got": "ALLOW"})
                    elif model_reco == "DENY" and expected == "ALLOW":
                        model_results["false_deny"] += 1
                else:
                    model_results["unavailable"] += 1
            except Exception:
                model_results["errors"] += 1
        else:
            model_results["unavailable"] = len(scenarios)

    # Build benchmark result
    now = datetime.now(timezone.utc).isoformat()
    provider_name = model_providers[0].name if model_providers else "none"

    def _rate(r): return round(r["correct"] / r["total"], 4) if r["total"] else None
    def _fa_rate(r): return round(r["false_allow"] / r["total"], 4) if r["total"] else None
    def _fd_rate(r): return round(r["false_deny"] / r["total"], 4) if r["total"] else None

    benchmark = {
        "benchmark_version": BENCHMARK_VERSION,
        "dataset_version": corpus["schema_version"],
        "dataset_size": len(scenarios),
        "timestamp": now,
        "model_provider": provider_name,
        "rule_engine": {
            "accuracy": _rate(rule_results),
            "false_allow_rate": _fa_rate(rule_results),
            "false_deny_rate": _fd_rate(rule_results),
            "total": rule_results["total"],
            "correct": rule_results["correct"],
            "false_allow": rule_results["false_allow"],
            "false_deny": rule_results["false_deny"],
        },
        "model_engine": {
            "accuracy": _rate(model_results),
            "false_allow_rate": _fa_rate(model_results),
            "false_deny_rate": _fd_rate(model_results),
            "total": model_results["total"],
            "correct": model_results["correct"],
            "false_allow": model_results["false_allow"],
            "false_deny": model_results["false_deny"],
            "errors": model_results["errors"],
            "unavailable": model_results["unavailable"],
        },
        "failure_cases": failure_cases,
        "security_guarantee": "The deterministic policy engine always makes the final decision. Intelligence recommendations (rule or model) are advisory only and cannot authorize execution.",
    }
    return benchmark


def save_benchmark(benchmark: dict[str, Any]) -> None:
    """Persist benchmark result for future comparison."""
    existing = []
    if BENCHMARK_PATH.exists():
        try:
            existing = json.loads(BENCHMARK_PATH.read_text()).get("benchmarks", [])
        except (json.JSONDecodeError, KeyError):
            existing = []
    existing.append(benchmark)
    # Keep last 50 benchmarks
    existing = existing[-50:]
    BENCHMARK_PATH.write_text(json.dumps({"benchmarks": existing}, indent=2))


def load_benchmarks() -> list[dict[str, Any]]:
    """Load all stored benchmark results."""
    if not BENCHMARK_PATH.exists():
        return []
    try:
        return json.loads(BENCHMARK_PATH.read_text()).get("benchmarks", [])
    except (json.JSONDecodeError, KeyError):
        return []
