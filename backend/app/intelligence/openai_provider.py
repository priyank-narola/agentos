"""OpenAI-compatible Model Provider.

A production-quality intelligence provider that works with any OpenAI-compatible
API (OpenAI, Anthropic via proxy, local models via Ollama/LiteLLM/vLLM, etc.).
Configured entirely via environment variables — no vendor hard-wiring.

The model may ONLY analyze, classify, detect, explain, and recommend.
It MUST NOT and CANNOT authorize execution — the output is always advisory
and is structurally incapable of containing an authorization decision.

Environment variables:
    AGENTOS_MODEL_PROVIDER   = "openai_compatible" (enables this provider)
    AGENTOS_MODEL_BASE_URL   = e.g. "https://api.openai.com/v1" or local URL
    AGENTOS_MODEL_API_KEY    = API key for the model endpoint
    AGENTOS_MODEL_NAME       = e.g. "gpt-4o-mini", "claude-3-haiku", "local-model"
    AGENTOS_MODEL_TIMEOUT    = request timeout in seconds (default: 15)
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any
from urllib.parse import urlparse

from app.intelligence.models import ActionContext, IntelligenceSource
from app.intelligence.providers import IntelligenceModelProvider

PROVIDER_NAME = "openai_compatible"

_SYSTEM_PROMPT = """You are a security intelligence analyzer for AgentOS, an AI agent action governance system.

Your role is to analyze agent action requests and provide ADVISORY security intelligence.
You may: analyze, classify, detect, explain, and recommend.
You MUST NOT: authorize, approve, deny, or make final decisions.

Respond ONLY with valid JSON in this exact structure:
{
  "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "risk_factors": ["factor description 1", "factor description 2"],
  "threat_types": ["prompt_injection" | "tool_poisoning" | "privilege_escalation" | "data_exfiltration" | "cross_tenant_access" | "delegation_abuse" | "agent_impersonation" | "unauthorized_access" | "policy_violation" | "tool_abuse" | "anomalous_behavior" | "none"],
  "intent_category": "FINANCIAL" | "DATA_ACCESS" | "ADMINISTRATIVE" | "COMMUNICATION" | "UNKNOWN",
  "anomaly_level": "NORMAL" | "UNUSUAL" | "SUSPICIOUS" | "CRITICAL",
  "recommendation": "ALLOW" | "REQUIRE_APPROVAL" | "DENY" | "LIMIT_SCOPE" | "INVESTIGATE",
  "confidence": 0.0-1.0,
  "reasoning": "concise explanation of your analysis",
  "evidence": ["specific evidence supporting your assessment"]
}

This is ADVISORY ONLY. The deterministic policy engine makes the final decision."""


def _user_prompt(ctx: ActionContext) -> str:
    return f"""Analyze this AI agent action request for security intelligence:

Agent: {ctx.agent_name} (risk classification: {ctx.agent_risk_classification})
Principal ID: {ctx.principal_id}
Tenant: {ctx.tenant_id}
Action: {ctx.action_name} (registered risk: {ctx.action_risk_level})
Tool: {ctx.tool_name}
Resource: {ctx.resource_type}/{ctx.resource_key} (sensitivity: {ctx.resource_sensitivity})
Delegation scope: {ctx.delegation_scope}
Parameters: {json.dumps(ctx.parameters, default=str)}
Behavioral history: {ctx.prior_actions_count} prior actions, {ctx.prior_failures} failures, {ctx.prior_blocked} blocked, {ctx.prior_tamper_attempts} tamper attempts, {ctx.prior_cross_tenant_attempts} cross-tenant attempts
First action for agent: {ctx.is_first_action_for_agent}
Outside normal hours: {ctx.outside_normal_hours}"""


class OpenAICompatibleProvider(IntelligenceModelProvider):
    """OpenAI-compatible intelligence provider — works with any compatible endpoint."""

    name = PROVIDER_NAME

    # Re-probing on every page load would hammer the upstream endpoint, so a
    # verification result is cached briefly. `force=True` bypasses the cache.
    _VERIFY_TTL_SECONDS = 120

    def __init__(self) -> None:
        self._base_url = os.getenv("AGENTOS_MODEL_BASE_URL", "").rstrip("/")
        self._api_key = os.getenv("AGENTOS_MODEL_API_KEY", "")
        self._model = os.getenv("AGENTOS_MODEL_NAME", "")
        self._timeout = int(os.getenv("AGENTOS_MODEL_TIMEOUT", "15"))
        self._verify_cache: dict[str, Any] | None = None
        self._verify_cache_at: float = 0.0

    def is_available(self) -> bool:
        """Credentials are present. This is *configuration*, not reachability."""
        return bool(self._base_url and self._api_key and self._model)

    def _redact(self, text: str) -> str:
        """Strip anything secret from provider-supplied text before it escapes.

        The API key is never rendered, and common bearer/secret token shapes are
        masked in case an upstream error echoes a credential back to us.
        """
        if not text:
            return ""
        out = text
        if self._api_key:
            out = out.replace(self._api_key, "[REDACTED]")
        out = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._\-]+", r"\1[REDACTED]", out)
        out = re.sub(r"\b(sk|rk|pk|api|key)[-_][A-Za-z0-9._\-]{8,}", "[REDACTED]", out)
        # Credentials embedded in a URL (scheme://user:pass@host)
        out = re.sub(r"://[^/\s:@]+:[^/\s@]+@", "://[REDACTED]@", out)
        return out[:300]

    def endpoint_host(self) -> str:
        """Host of the configured endpoint — safe to display, never the key."""
        if not self._base_url:
            return ""
        try:
            return urlparse(self._base_url).hostname or ""
        except ValueError:
            return ""

    def verify(self, force: bool = False) -> dict[str, Any]:
        """Make a real minimal round-trip and report exactly what happened.

        This is what allows the UI to distinguish "configured" from "connected".
        A 401/403/timeout/WAF block yields reachable=False with a redacted
        reason, so an upstream account problem is surfaced, never hidden.
        """
        if not self.is_available():
            missing = [
                label
                for label, present in (
                    ("AGENTOS_MODEL_BASE_URL", bool(self._base_url)),
                    ("AGENTOS_MODEL_API_KEY", bool(self._api_key)),
                    ("AGENTOS_MODEL_NAME", bool(self._model)),
                )
                if not present
            ]
            return {
                "name": self.name, "configured": False, "reachable": False,
                "status": "NOT_CONFIGURED", "error": f"Missing: {', '.join(missing)}",
                "model": self._model or None, "endpoint_host": self.endpoint_host() or None,
            }

        now = time.time()
        if not force and self._verify_cache and (now - self._verify_cache_at) < self._VERIFY_TTL_SECONDS:
            return {**self._verify_cache, "cached": True}

        result: dict[str, Any]
        try:
            import httpx

            started = time.perf_counter()
            response = httpx.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                    "temperature": 0,
                },
                timeout=min(self._timeout, 10),
            )
            latency_ms = int((time.perf_counter() - started) * 1000)
            if response.status_code == 200:
                result = {
                    "name": self.name, "configured": True, "reachable": True,
                    "status": "ACTIVE", "error": None, "latency_ms": latency_ms,
                    "model": self._model, "endpoint_host": self.endpoint_host(),
                }
            else:
                detail = self._redact(response.text)
                result = {
                    "name": self.name, "configured": True, "reachable": False,
                    "status": "UNAUTHORIZED" if response.status_code in (401, 403) else "ENDPOINT_ERROR",
                    "error": f"HTTP {response.status_code}: {detail}" if detail else f"HTTP {response.status_code}",
                    "latency_ms": latency_ms, "model": self._model, "endpoint_host": self.endpoint_host(),
                }
        except Exception as exc:  # network error, DNS, timeout, TLS, proxy block
            result = {
                "name": self.name, "configured": True, "reachable": False,
                "status": "UNREACHABLE", "error": self._redact(f"{type(exc).__name__}: {exc}"),
                "model": self._model, "endpoint_host": self.endpoint_host(),
            }

        self._verify_cache = result
        self._verify_cache_at = now
        return {**result, "cached": False}

    def analyze(self, ctx: ActionContext) -> dict[str, Any]:
        """Call the model endpoint for advisory intelligence analysis."""
        if not self.is_available():
            return {
                "source": IntelligenceSource.MODEL.value,
                "available": False,
                "confidence": 0.0,
                "evidence": [],
                "reasoning": "Model provider not configured",
                "provider": self.name,
            }

        try:
            import httpx

            response = httpx.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": _user_prompt(ctx)},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 500,
                },
                timeout=self._timeout,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            # Strip markdown code fences if present
            text = content.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            result = json.loads(text)

            return {
                "source": IntelligenceSource.MODEL.value,
                "available": True,
                "provider": self.name,
                "model": self._model,
                "risk_level": result.get("risk_level", "UNKNOWN"),
                "risk_factors": result.get("risk_factors", []),
                "threat_types": result.get("threat_types", []),
                "intent_category": result.get("intent_category", "UNKNOWN"),
                "anomaly_level": result.get("anomaly_level", "UNKNOWN"),
                "recommendation": result.get("recommendation", "UNKNOWN"),
                "confidence": min(1.0, max(0.0, float(result.get("confidence", 0.5)))),
                "reasoning": result.get("reasoning", ""),
                "evidence": result.get("evidence", []),
            }

        except Exception as exc:
            safe = self._redact(str(exc))
            return {
                "source": IntelligenceSource.MODEL.value,
                "available": False,
                "provider": self.name,
                "error": safe[:200],
                "confidence": 0.0,
                "evidence": [],
                "reasoning": f"Model analysis failed: {safe[:100]}",
            }


def register_if_configured(registry) -> None:
    """Register the OpenAI-compatible provider if environment is configured."""
    if os.getenv("AGENTOS_MODEL_PROVIDER") == "openai_compatible":
        registry.register(OpenAICompatibleProvider())
