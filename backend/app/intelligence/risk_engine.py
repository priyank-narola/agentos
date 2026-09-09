"""Risk Intelligence V1 — explainable risk assessment.

Deterministic rule-based scoring from real ActionContext. Every factor carries
evidence and reasoning. Never returns an unexplained score.
"""

from __future__ import annotations

from app.intelligence.models import (
    ActionContext, AnomalyLevel, IntelligenceEvidence, IntelligenceSource,
    RecommendationType, RiskAssessment, RiskLevel, RiskSignal,
)

ENGINE_VERSION = "agentos-intelligence-risk-v1"

# Financial thresholds (aligned with FinancialRiskConfig)
_FIN_LOW = 1000
_FIN_ELEVATED = 5000
_FIN_CRITICAL = 50000


def _classify(score: int) -> RiskLevel:
    if score >= 80:
        return RiskLevel.CRITICAL
    if score >= 55:
        return RiskLevel.HIGH
    if score >= 30:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _financial_amount(ctx: ActionContext) -> float | None:
    for key in ("amount", "transfer_amount", "value"):
        val = ctx.parameters.get(key)
        if val is not None:
            try:
                return float(str(val).replace(",", ""))
            except (ValueError, TypeError):
                return None
    return None


def assess_risk(ctx: ActionContext) -> RiskAssessment:
    """Produce an explainable risk assessment with recommended control."""
    factors: list[RiskSignal] = []

    # 1. Action risk level (from registered action metadata)
    action_weight = {"LOW": 8, "MEDIUM": 18, "HIGH": 30}.get(ctx.action_risk_level, 15)
    if action_weight > 0:
        factors.append(RiskSignal(
            code="ACTION_RISK_LEVEL",
            label=f"Action registered as {ctx.action_risk_level} risk",
            weight=action_weight,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.RULE_ENGINE,
                fact=f"Action '{ctx.action_name}' is classified {ctx.action_risk_level} risk in the capability registry.",
            ),
            reasoning=f"Registered action risk level contributes {action_weight} points.",
        ))

    # 2. Resource sensitivity
    resource_weight = {"LOW": 0, "MEDIUM": 12, "HIGH": 25}.get(ctx.resource_sensitivity, 10)
    if resource_weight > 0:
        factors.append(RiskSignal(
            code="RESOURCE_SENSITIVITY",
            label=f"Target resource has {ctx.resource_sensitivity} sensitivity",
            weight=resource_weight,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.RULE_ENGINE,
                fact=f"Resource '{ctx.resource_key}' ({ctx.resource_type}) is classified {ctx.resource_sensitivity} sensitivity.",
            ),
            reasoning=f"Resource sensitivity contributes {resource_weight} points.",
        ))

    # 3. Agent risk classification
    agent_weight = {"LOW": 0, "MEDIUM": 10, "HIGH": 20}.get(ctx.agent_risk_classification, 10)
    if agent_weight > 0:
        factors.append(RiskSignal(
            code="AGENT_RISK_CLASS",
            label=f"Agent has {ctx.agent_risk_classification} risk classification",
            weight=agent_weight,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.RULE_ENGINE,
                fact=f"Agent '{ctx.agent_name}' is registered with {ctx.agent_risk_classification} risk classification.",
            ),
            reasoning=f"Agent classification contributes {agent_weight} points.",
        ))

    # 4. Financial impact
    amount = _financial_amount(ctx)
    if amount is not None:
        if amount >= _FIN_CRITICAL:
            factors.append(RiskSignal(
                code="FINANCIAL_IMPACT_CRITICAL",
                label=f"Critical financial impact ({amount:,.2f})",
                weight=35,
                evidence=IntelligenceEvidence(
                    source=IntelligenceSource.RULE_ENGINE,
                    fact=f"Transaction amount {amount:,.2f} exceeds the critical threshold of {_FIN_CRITICAL:,}.",
                ),
                reasoning="Amount at or above critical financial threshold.",
            ))
        elif amount >= _FIN_ELEVATED:
            factors.append(RiskSignal(
                code="FINANCIAL_IMPACT_ELEVATED",
                label=f"Elevated financial impact ({amount:,.2f})",
                weight=20,
                evidence=IntelligenceEvidence(
                    source=IntelligenceSource.RULE_ENGINE,
                    fact=f"Transaction amount {amount:,.2f} exceeds the elevated threshold of {_FIN_ELEVATED:,}.",
                ),
                reasoning="Amount above elevated financial threshold.",
            ))
        elif amount >= _FIN_LOW:
            factors.append(RiskSignal(
                code="FINANCIAL_IMPACT_LOW",
                label=f"Financial impact ({amount:,.2f})",
                weight=5,
                evidence=IntelligenceEvidence(
                    source=IntelligenceSource.RULE_ENGINE,
                    fact=f"Transaction amount {amount:,.2f} exceeds the low threshold of {_FIN_LOW:,}.",
                ),
                reasoning="Modest financial impact detected.",
            ))

    # 5. Delegation scope fit
    action_verb = ctx.action_name.split("_")[0] if "_" in ctx.action_name else ctx.action_name
    scope_fits = (
        ctx.delegation_scope in ("*", ctx.action_name)
        or ctx.delegation_scope.endswith(f".{action_verb}")
        or ctx.delegation_scope == "none"
    )
    if ctx.delegation_scope == "none":
        factors.append(RiskSignal(
            code="NO_DELEGATION",
            label="No delegation scope found for this agent/principal",
            weight=20,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.RULE_ENGINE,
                fact="No active delegation record matches this principal-agent pair.",
            ),
            reasoning="Absence of delegation increases risk of unauthorized action.",
        ))
    elif not scope_fits:
        factors.append(RiskSignal(
            code="DELEGATION_SCOPE_MISMATCH",
            label=f"Delegation scope '{ctx.delegation_scope}' may not cover action '{ctx.action_name}'",
            weight=15,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.RULE_ENGINE,
                fact=f"Delegated scope is '{ctx.delegation_scope}'; action requires '{action_verb}' capability.",
            ),
            reasoning="Action may exceed delegated authority.",
        ))

    # 6. Historical signals
    if ctx.prior_tamper_attempts > 0:
        factors.append(RiskSignal(
            code="PRIOR_TAMPER_HISTORY",
            label=f"{ctx.prior_tamper_attempts} prior tampering attempt(s) in this tenant",
            weight=10,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.AUDIT_HISTORY,
                fact=f"Audit history shows {ctx.prior_tamper_attempts} payload tampering event(s).",
            ),
            reasoning="Prior tampering increases likelihood of repeat attempts.",
        ))
    if ctx.prior_cross_tenant_attempts > 0:
        factors.append(RiskSignal(
            code="PRIOR_CROSS_TENANT_HISTORY",
            label=f"{ctx.prior_cross_tenant_attempts} prior cross-tenant attempt(s)",
            weight=8,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.AUDIT_HISTORY,
                fact=f"Audit history shows {ctx.prior_cross_tenant_attempts} cross-tenant access denial(s).",
            ),
            reasoning="Prior cross-tenant attempts indicate probing behavior.",
        ))
    if ctx.is_first_action_for_agent:
        factors.append(RiskSignal(
            code="FIRST_ACTION_FOR_AGENT",
            label="This is the agent's first governed action",
            weight=5,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.AUDIT_HISTORY,
                fact="No prior action requests exist for this agent in this tenant.",
            ),
            reasoning="No behavioral baseline exists; first actions carry slight additional uncertainty.",
        ))
    if ctx.prior_failures > 2:
        factors.append(RiskSignal(
            code="REPEATED_FAILURES",
            label=f"{ctx.prior_failures} prior failed executions",
            weight=5,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.AUDIT_HISTORY,
                fact=f"Agent has {ctx.prior_failures} prior execution failure(s).",
            ),
            reasoning="Repeated execution failures may indicate misconfiguration or adversarial probing.",
        ))

    # 7. Time pattern
    if ctx.outside_normal_hours:
        factors.append(RiskSignal(
            code="OUTSIDE_NORMAL_HOURS",
            label="Action requested outside normal business hours (22:00-06:00 UTC)",
            weight=5,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.RULE_ENGINE,
                fact="Current time falls outside 06:00-22:00 UTC.",
            ),
            reasoning="Off-hours activity is a mild anomaly indicator for financial operations.",
        ))

    # 8. Suspicious parameter indicators (prompt injection / exfiltration heuristics)
    param_text = " ".join(str(v) for v in ctx.parameters.values()).lower()
    injection_markers = ["ignore previous", "ignore all previous", "ignore prior", "system prompt", "you are now", "disregard", "override instructions", "override all", "jailbreak", "system override"]
    injection_hits = [m for m in injection_markers if m in param_text]
    if injection_hits:
        factors.append(RiskSignal(
            code="PROMPT_INJECTION_INDICATOR",
            label=f"Parameter content contains instruction-override markers: {', '.join(injection_hits)}",
            weight=30,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.RULE_ENGINE,
                fact=f"Action parameters contain suspicious instruction markers: {injection_hits}.",
            ),
            reasoning="Instruction-override markers in action parameters strongly suggest prompt injection.",
        ))
    if any(w in param_text for w in ("password", "api_key", "secret", "private_key", "credential")):
        factors.append(RiskSignal(
            code="SENSITIVE_DATA_INDICATOR",
            label="Parameters reference credentials/secrets",
            weight=15,
            evidence=IntelligenceEvidence(
                source=IntelligenceSource.RULE_ENGINE,
                fact="Action parameters contain references to secrets or credentials.",
            ),
            reasoning="Credential references in parameters increase data-exfiltration risk.",
        ))

    # Compute score
    raw_score = sum(f.weight for f in factors)
    score = min(100, raw_score)
    level = _classify(score)

    # Recommended control
    has_critical_threat_factor = any(f.code == "PROMPT_INJECTION_INDICATOR" for f in factors)
    has_no_delegation = any(f.code == "NO_DELEGATION" for f in factors)
    has_scope_mismatch = any(f.code == "DELEGATION_SCOPE_MISMATCH" for f in factors)

    if has_critical_threat_factor:
        recommended = RecommendationType.DENY
    elif has_no_delegation:
        recommended = RecommendationType.DENY
    elif level == RiskLevel.CRITICAL:
        recommended = RecommendationType.REQUIRE_APPROVAL
    elif has_scope_mismatch:
        recommended = RecommendationType.DENY
    elif level == RiskLevel.HIGH:
        recommended = RecommendationType.REQUIRE_APPROVAL
    elif level == RiskLevel.MEDIUM:
        recommended = RecommendationType.ALLOW
    else:
        recommended = RecommendationType.ALLOW

    top = sorted(factors, key=lambda f: f.weight, reverse=True)[:3]
    reasoning = f"Risk {level.value} ({score}/100) driven by: " + "; ".join(f"{f.label} (+{f.weight})" for f in top) if top else f"Risk {level.value} ({score}/100); no elevated signals detected."

    return RiskAssessment(
        score=score,
        level=level,
        factors=tuple(factors),
        recommended_control=recommended,
        engine_version=ENGINE_VERSION,
        assessed_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        confidence=0.95,  # rule-based; deterministic given context
        reasoning=reasoning,
    )
