"""Anomaly Detection — deterministic behavioral baseline engine.

Computes a baseline from real action history and flags deviations.
Output: NORMAL / UNUSUAL / SUSPICIOUS / CRITICAL with explainable evidence.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.intelligence.models import (
    ActionContext, AnomalyAssessment, AnomalyLevel, AnomalySignal,
    IntelligenceEvidence, IntelligenceSource,
)

ENGINE_VERSION = "agentos-intelligence-anomaly-v1"


def _level_from_score(score: int) -> AnomalyLevel:
    if score >= 4:
        return AnomalyLevel.CRITICAL
    if score >= 3:
        return AnomalyLevel.SUSPICIOUS
    if score >= 1:
        return AnomalyLevel.UNUSUAL
    return AnomalyLevel.NORMAL


def assess_anomaly(ctx: ActionContext) -> AnomalyAssessment:
    """Assess behavioral deviation from baseline."""
    signals: list[AnomalySignal] = []
    baseline: dict = {
        "prior_actions_count": ctx.prior_actions_count,
        "prior_failures": ctx.prior_failures,
        "prior_blocked": ctx.prior_blocked,
        "has_baseline": ctx.prior_actions_count > 0,
    }

    # 1. First action (no baseline)
    if ctx.is_first_action_for_agent:
        signals.append(AnomalySignal(
            code="NO_BEHAVIORAL_BASELINE",
            label="First action for this agent — no baseline exists",
            level=AnomalyLevel.UNUSUAL,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.BASELINE,
                fact="This agent has zero prior governed actions in this tenant.",
            ),
            reasoning="Cannot assess normalcy without history; flagged as mildly unusual.",
        ))

    # 2. High failure rate
    if ctx.prior_actions_count >= 3 and ctx.prior_failures / ctx.prior_actions_count > 0.5:
        signals.append(AnomalySignal(
            code="HIGH_FAILURE_RATE",
            label=f"Agent failure rate is {ctx.prior_failures}/{ctx.prior_actions_count} (>50%)",
            level=AnomalyLevel.SUSPICIOUS,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.BASELINE,
                fact=f"{ctx.prior_failures} of {ctx.prior_actions_count} prior actions failed.",
            ),
            reasoning="Majority of prior executions failed — possible adversarial probing or misconfiguration.",
        ))

    # 3. Repeated blocks
    if ctx.prior_blocked >= 3:
        signals.append(AnomalySignal(
            code="REPEATED_BLOCKS",
            label=f"{ctx.prior_blocked} prior blocked actions",
            level=AnomalyLevel.SUSPICIOUS,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.BASELINE,
                fact=f"Agent has had {ctx.prior_blocked} prior actions blocked/rejected.",
            ),
            reasoning="Repeated blocks suggest the agent repeatedly attempts unauthorized actions.",
        ))

    # 4. Off-hours financial activity
    if ctx.outside_normal_hours and "transfer" in ctx.action_name.lower():
        signals.append(AnomalySignal(
            code="OFF_HOURS_FINANCIAL",
            label="Financial action requested outside normal hours",
            level=AnomalyLevel.UNUSUAL,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.RULE_ENGINE,
                fact="Financial action requested between 22:00-06:00 UTC.",
            ),
            reasoning="Off-hours financial operations are a mild behavioral anomaly.",
        ))

    # 5. Delegation scope probing
    if ctx.delegation_scope == "none":
        signals.append(AnomalySignal(
            code="ACTING_WITHOUT_DELEGATION",
            label="Agent acting without a delegation record",
            level=AnomalyLevel.SUSPICIOUS,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.BASELINE,
                fact="No delegation found for this principal-agent pair.",
            ),
            reasoning="An agent acting without delegated authority is anomalous and potentially adversarial.",
        ))

    # 6. Prior tamper attempts (strong anomaly)
    if ctx.prior_tamper_attempts > 0:
        signals.append(AnomalySignal(
            code="PRIOR_TAMPERING",
            label=f"{ctx.prior_tamper_attempts} prior payload tampering attempt(s)",
            level=AnomalyLevel.CRITICAL if ctx.prior_tamper_attempts >= 2 else AnomalyLevel.SUSPICIOUS,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.AUDIT_HISTORY,
                fact=f"Tenant audit history shows {ctx.prior_tamper_attempts} tampering event(s).",
            ),
            reasoning="Prior tampering in the tenant indicates active adversarial behavior.",
        ))

    # 7. Prior cross-tenant attempts
    if ctx.prior_cross_tenant_attempts > 0:
        signals.append(AnomalySignal(
            code="PRIOR_CROSS_TENANT",
            label=f"{ctx.prior_cross_tenant_attempts} prior cross-tenant attempt(s)",
            level=AnomalyLevel.SUSPICIOUS,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.AUDIT_HISTORY,
                fact=f"Tenant has {ctx.prior_cross_tenant_attempts} cross-tenant denial(s).",
            ),
            reasoning="Cross-tenant probing is an active isolation-testing behavior.",
        ))

    # Compute overall level from signal count and severity
    critical_count = sum(1 for s in signals if s.level == AnomalyLevel.CRITICAL)
    suspicious_count = sum(1 for s in signals if s.level == AnomalyLevel.SUSPICIOUS)
    unusual_count = sum(1 for s in signals if s.level == AnomalyLevel.UNUSUAL)
    anomaly_score = critical_count * 3 + suspicious_count * 2 + unusual_count
    level = _level_from_score(anomaly_score)

    reasoning = f"Anomaly {level.value}: {len(signals)} signal(s) — " + "; ".join(s.label for s in signals) if signals else f"Anomaly {level.value}: behavior consistent with baseline."

    return AnomalyAssessment(
        level=level,
        signals=tuple(signals),
        baseline_summary=baseline,
        engine_version=ENGINE_VERSION,
        assessed_at=datetime.now(timezone.utc),
        confidence=0.90,
        reasoning=reasoning,
    )
