"""Explicit connector selection for governed action execution.

This module is intentionally small: it provides a safe seam for future
connectors without silently choosing a live system or storing credentials.
The caller supplies both the default provider and any action-specific routing.
"""

from __future__ import annotations

from app.config import settings
from app.execution import ActionExecutionProvider, SandboxPaymentProvider
from app.services.stripe_refunds import StripeRefundProvider, UrllibStripeTransport


class ExecutionProviderRegistry:
    """Resolve an action to an execution provider with a safe default fallback."""

    def __init__(self, default_provider: ActionExecutionProvider) -> None:
        self._default_provider = default_provider
        self._providers_by_action: dict[str, ActionExecutionProvider] = {}

    def register(self, action_name: str, provider: ActionExecutionProvider) -> None:
        """Route one normalized action name to a connector implementation."""
        self._providers_by_action[self._normalized_action_name(action_name)] = provider

    def resolve(self, action_name: str) -> ActionExecutionProvider:
        """Return the action-specific connector, or the configured safe default."""
        return self._providers_by_action.get(
            self._normalized_action_name(action_name), self._default_provider
        )

    @staticmethod
    def _normalized_action_name(action_name: str) -> str:
        normalized = action_name.strip().lower()
        if not normalized:
            raise ValueError("Action name is required to resolve an execution provider")
        return normalized


def build_execution_provider_registry() -> ExecutionProviderRegistry:
    """Build the server-controlled routing configuration for one service.

    The Stripe mapping is opt-in and only becomes live through server-managed
    configuration. Without that explicit switch, every action stays in the
    sandbox provider, including the customer-remediation demo.
    """
    registry = ExecutionProviderRegistry(SandboxPaymentProvider())
    if settings.stripe_refund_connector_enabled:
        provider = StripeRefundProvider(
            settings.stripe_secret_key,
            UrllibStripeTransport(settings.stripe_api_base),
        )
        registry.register("issue_refund", provider)
        registry.register("refund_payment", provider)
    return registry
