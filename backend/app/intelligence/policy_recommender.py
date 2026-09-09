"""Policy Recommendation Engine — advisory only.

Produces a RECOMMENDATION (ALLOW/DENY/REQUIRE_APPROVAL/LIMIT_SCOPE/
REVOKE_DELEGATION/INVESTIGATE). This NEVER directly authorizes execution.
The deterministic policy engine independently evaluates the final decision.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.intelligence.models import (
    AnomalyAssessment, AnomalyLevel, IntelligenceEvidence, IntelligenceSource,
    PolicyRecommendation, RecommendationType, RiskAssessment, RiskLevel,
    ThreatAssessment, ThreatSeverity,
)

ENGINE_VERSION = "agentos-intelligence-recommendation-v1"


def recommend_policy(
    risk: RiskAssessment,
    anomaly: AnomalyAssessment,
    threats: ThreatAssessment,
) -> PolicyRecommendation:
    """Produce an advisory policy recommendation from intelligence signals."""
    evidence: list[IntelligenceEvidence] = []
    reasoning_parts: list[str] = []

    # Start from risk-recommended control
    recommendation = risk.recommended_control
    reasoning_parts.append(f"Risk assessment ({risk.level.value}, {risk.score}/100) suggests {risk.recommended_control.value}.")
    evidence.append(IntelligenceEvidence(
        source=IntelligenceSource.RULE_ENGINE,
        fact=f"Risk level {risk.level.value} with {len(risk.factors)} factor(s); score {risk.score}.",
    ))

    # Escalate on critical threats
    has_critical_threat = any(t.severity == ThreatSeverity.CRITICAL for t in threats.threats)
    if has_critical_threat and recommendation != RecommendationType.DENY:
        critical_types = [t.threat_type.value for t in threats.threats if t.severity == ThreatSeverity.CRITICAL]
        recommendation = RecommendationType.DENY
        reasoning_parts.append(f"Escalated to DENY: critical threat(s) detected — {critical_types}.")
        evidence.append(IntelligenceEvidence(
            source=IntelligenceSource.RULE_ENGINE,
            fact=f"Critical threats: {critical_types}.",
        ))

    # Escalate on suspicious/critical anomaly
    if anomaly.level == AnomalyLevel.CRITICAL and recommendation not in (RecommendationType.DENY, RecommendationType.REVOKE_DELEGATION):
        recommendation = RecommendationType.INVESTIGATE
        reasoning_parts.append(f"Escalated to INVESTIGATE: behavioral anomaly is CRITICAL.")
        evidence.append(IntelligenceEvidence(
            source=IntelligenceSource.BASELINE,
            fact=f"Anomaly level CRITICAL with {len(anomaly.signals)} signal(s).",
        ))
    elif anomaly.level == AnomalyLevel.SUSPICIOUS and recommendation == RecommendationType.ALLOW:
        recommendation = RecommendationType.REQUIRE_APPROVAL
        reasoning_parts.append(f"Escalated to REQUIRE_APPROVAL: behavioral anomaly is SUSPICIOUS.")

    # Recommend scope limitation for delegation mismatch without full denial
    if recommendation == RecommendationType.ALLOW and risk.level == RiskLevel.MEDIUM:
        recommendation = RecommendationType.LIMIT_SCOPE
        reasoning_parts.append("Recommended LIMIT_SCOPE: medium risk with non-trivial factors.")

    # Recommend delegation revocation for repeated delegation abuse
    delegation_abuse = any(t.threat_type.value == "delegation_abuse" for t in threats.threats)
    if delegation_abuse and anomaly.level in (AnomalyLevel.SUSPICIOUS, AnomalyLevel.CRITICAL):
        recommendation = RecommendationType.REVOKE_DELEGATION
        reasoning_parts.append("Recommended REVOKE_DELEGATION: repeated delegation abuse with anomalous behavior.")
        evidence.append(IntelligenceEvidence(
            source=IntelligenceSource.RULE_ENGINE,
            fact="Delegation abuse threat combined with anomalous behavioral pattern.",
        ))

    reasoning = " ".join(reasoning_parts)
    confidence = min(0.95, risk.confidence * 0.8 + (0.15 if threats.threats else 0.0))

    return PolicyRecommendation(
        recommendation=recommendation,
        confidence=confidence,
        reasoning=reasoning,
        evidence=tuple(evidence),
        engine_version=ENGINE_VERSION,
        recommended_at=datetime.now(timezone.utc),
        is_advisory=True,
    )
