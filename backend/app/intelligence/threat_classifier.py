"""Threat Classification — normalized taxonomy with explainable evidence."""

from __future__ import annotations

from datetime import datetime, timezone

from app.intelligence.models import (
    ActionContext, AnomalyAssessment, AnomalyLevel, IntelligenceEvidence,
    IntelligenceSource, IntentAnalysis, RecommendationType, RiskAssessment,
    RiskLevel, ThreatAssessment, ThreatSeverity, ThreatSignal, ThreatType,
)

ENGINE_VERSION = "agentos-intelligence-threat-v1"

_SEVERITY_ORDER = {ThreatSeverity.LOW: 0, ThreatSeverity.MEDIUM: 1, ThreatSeverity.HIGH: 2, ThreatSeverity.CRITICAL: 3}


def classify_threats(
    ctx: ActionContext,
    risk: RiskAssessment,
    intent: IntentAnalysis,
    anomaly: AnomalyAssessment,
) -> ThreatAssessment:
    """Classify threats from context, risk, intent, and anomaly signals."""
    threats: list[ThreatSignal] = []
    param_text = " ".join(str(v) for v in ctx.parameters.values()).lower()

    # 1. Prompt injection
    injection_markers = ["ignore previous", "system prompt", "you are now", "disregard", "override instructions", "jailbreak"]
    injection_hits = [m for m in injection_markers if m in param_text]
    if injection_hits:
        threats.append(ThreatSignal(
            threat_type=ThreatType.PROMPT_INJECTION,
            severity=ThreatSeverity.CRITICAL,
            confidence=0.90,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.RULE_ENGINE,
                fact=f"Parameters contain instruction-override markers: {injection_hits}.",
            ),
            reasoning="Instruction-override markers in agent-submitted parameters are a hallmark of prompt injection.",
            recommended_action=RecommendationType.DENY,
        ))

    # 2. Unauthorized access / no delegation
    if ctx.delegation_scope == "none":
        threats.append(ThreatSignal(
            threat_type=ThreatType.UNAUTHORIZED_ACCESS,
            severity=ThreatSeverity.HIGH,
            confidence=0.85,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.RULE_ENGINE,
                fact="No delegation exists for this principal-agent pair.",
            ),
            reasoning="An agent acting without any delegated authority is attempting unauthorized access.",
            recommended_action=RecommendationType.DENY,
        ))

    # 3. Delegation abuse (scope mismatch)
    action_verb = ctx.action_name.split("_")[0] if "_" in ctx.action_name else ctx.action_name
    if ctx.delegation_scope not in ("*", "none") and not (
        ctx.delegation_scope == ctx.action_name or ctx.delegation_scope.endswith(f".{action_verb}")
    ):
        threats.append(ThreatSignal(
            threat_type=ThreatType.DELEGATION_ABUSE,
            severity=ThreatSeverity.HIGH,
            confidence=0.75,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.RULE_ENGINE,
                fact=f"Delegated scope '{ctx.delegation_scope}' does not cover action '{ctx.action_name}'.",
            ),
            reasoning="Agent is requesting a capability beyond its delegated scope.",
            recommended_action=RecommendationType.DENY,
        ))

    # 4. Cross-tenant history
    if ctx.prior_cross_tenant_attempts > 0:
        threats.append(ThreatSignal(
            threat_type=ThreatType.CROSS_TENANT_ACCESS,
            severity=ThreatSeverity.MEDIUM,
            confidence=0.70,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.AUDIT_HISTORY,
                fact=f"Tenant history includes {ctx.prior_cross_tenant_attempts} cross-tenant attempt(s).",
            ),
            reasoning="Prior cross-tenant probing indicates ongoing isolation-testing behavior.",
            recommended_action=RecommendationType.INVESTIGATE,
        ))

    # 5. Payload tampering history
    if ctx.prior_tamper_attempts > 0:
        threats.append(ThreatSignal(
            threat_type=ThreatType.PAYLOAD_TAMPERING,
            severity=ThreatSeverity.HIGH,
            confidence=0.80,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.AUDIT_HISTORY,
                fact=f"Tenant history includes {ctx.prior_tamper_attempts} payload tampering event(s).",
            ),
            reasoning="Prior tampering attempts indicate active adversarial payload manipulation.",
            recommended_action=RecommendationType.REQUIRE_APPROVAL,
        ))

    # 6. Data exfiltration indicators
    if any(w in param_text for w in ("export", "download", "dump", "exfiltrate")) and ctx.resource_sensitivity == "HIGH":
        threats.append(ThreatSignal(
            threat_type=ThreatType.DATA_EXFILTRATION,
            severity=ThreatSeverity.HIGH,
            confidence=0.70,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.RULE_ENGINE,
                fact=f"Parameters reference data export from a HIGH-sensitivity resource ({ctx.resource_key}).",
            ),
            reasoning="Exporting from high-sensitivity resources is a primary exfiltration vector.",
            recommended_action=RecommendationType.REQUIRE_APPROVAL,
        ))

    # 7. Privilege escalation indicators
    if any(w in ctx.action_name.lower() for w in ("grant", "admin", "root", "sudo", "elevate")):
        threats.append(ThreatSignal(
            threat_type=ThreatType.PRIVILEGE_ESCALATION,
            severity=ThreatSeverity.HIGH,
            confidence=0.75,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.RULE_ENGINE,
                fact=f"Action name '{ctx.action_name}' references privilege escalation.",
            ),
            reasoning="Actions referencing privilege grant/elevation are classic escalation vectors.",
            recommended_action=RecommendationType.REQUIRE_APPROVAL,
        ))

    # 8. Anomalous behavior (from anomaly assessment)
    if anomaly.level in (AnomalyLevel.SUSPICIOUS, AnomalyLevel.CRITICAL):
        threats.append(ThreatSignal(
            threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
            severity=ThreatSeverity.HIGH if anomaly.level == AnomalyLevel.CRITICAL else ThreatSeverity.MEDIUM,
            confidence=0.70,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.BASELINE,
                fact=f"Behavioral baseline assessment: {anomaly.level.value} — {len(anomaly.signals)} signal(s).",
            ),
            reasoning="Behavior deviates significantly from the agent's established baseline.",
            recommended_action=RecommendationType.INVESTIGATE,
        ))

    # 9. Tool abuse (financial action on non-financial resource type, or extreme amount)
    amount = None
    for key in ("amount", "transfer_amount"):
        v = ctx.parameters.get(key)
        if v is not None:
            try:
                amount = float(str(v).replace(",", ""))
            except (ValueError, TypeError):
                pass
            break
    if amount is not None and amount >= 50000:
        threats.append(ThreatSignal(
            threat_type=ThreatType.TOOL_ABUSE,
            severity=ThreatSeverity.CRITICAL,
            confidence=0.85,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.RULE_ENGINE,
                fact=f"Financial amount {amount:,.2f} is at or above the critical threshold (50,000).",
            ),
            reasoning="Extreme financial amounts via agent tool-use indicate potential tool abuse.",
            recommended_action=RecommendationType.REQUIRE_APPROVAL,
        ))

    highest = ThreatSeverity.LOW
    if threats:
        highest = max((t.severity for t in threats), key=lambda s: _SEVERITY_ORDER[s])

    reasoning = f"{len(threats)} threat(s) classified; highest severity {highest.value}." if threats else "No threats detected."

    return ThreatAssessment(
        threats=tuple(threats),
        highest_severity=highest,
        engine_version=ENGINE_VERSION,
        assessed_at=datetime.now(timezone.utc),
        reasoning=reasoning,
    )
