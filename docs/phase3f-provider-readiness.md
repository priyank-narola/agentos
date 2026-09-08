# AgentOS Phase 3F — Production Provider Adapter Contract & Readiness Specification

**Document Version**: 1.0  
**Target Domain**: Production Payment & Corporate Banking Provider Integration  
**Current Baseline**: Safe Sandbox Provider (`SandboxPaymentProvider`)  

---

## 1. Provider Adapter Interface Contract

Before connecting any live financial institution, corporate banking gateway (e.g. Stripe, Chase Host-to-Host, SWIFT, Plaid, FIS, Jack Henry), the provider adapter MUST inherit from `PaymentExecutionProvider` and satisfy the following 10 mandatory criteria:

```python
class PaymentExecutionProvider(abc.ABC):
    @abc.abstractmethod
    def execute(self, request_id: UUID, parameters: dict[str, Any], idempotency_key: str, tenant_id: UUID | None = None) -> ExecutionResult:
        """Submit financial action to provider with provider-level idempotency."""
        pass

    @abc.abstractmethod
    def get_status(self, execution_id: str, provider_transaction_id: str | None = None) -> ExecutionStatus:
        """Poll or query status for an execution ID."""
        pass

    @abc.abstractmethod
    def verify_result(self, execution_id: str, provider_transaction_id: str | None = None, expected_digest: str | None = None) -> bool:
        """Verify execution settled and payload digest matches."""
        pass

    @abc.abstractmethod
    def cancel(self, execution_id: str, provider_transaction_id: str | None = None) -> ExecutionResult:
        """Attempt cancellation of pending/submitted execution."""
        pass
```

---

## 2. Mandatory Production Requirements

### 1. Authentication & Key Management
- Must use hardware security module (HSM) or secret vault (AWS Secrets Manager, GCP Secret Manager, Vault) for API credentials.
- Zero plaintext API keys or certificates stored in codebase or environment variables.
- Support mTLS (mutual TLS v1.3) where required by banking partners.

### 2. Request Signing & Payload Integrity
- Outbound API requests must be cryptographically signed (HMAC-SHA256 or RSA-SHA256) over canonical HTTP body bytes.
- Header signatures must include HTTP Method, Path, Timestamp (`Date`/`X-Timestamp`), and Digest hash.

### 3. Dual-Layer Idempotency
- **AgentOS Layer**: `ActionRequest` unique constraint on `(tenant_id, idempotency_key)`.
- **Provider Layer**: Pass `idempotency_key` in provider-native HTTP headers (e.g., `Idempotency-Key` or `X-Request-ID`). Re-submission must return cached execution result (`DUPLICATE`) without duplicate money movement.

### 4. Failure Classification & Timeout Safety
- HTTP 4xx errors (e.g., invalid account, insufficient funds) transition state machine to `EXECUTION_FAILED`.
- Network timeouts, HTTP 500/502/503/504 errors transition state machine to `TIMEOUT` or `UNKNOWN`.
- **NEVER** automatically retry `UNKNOWN` state requests without out-of-band status query or reconciliation.

### 5. Webhook Security Specification
- Inbound webhooks must implement `WebhookSecurityHandler`:
  - HMAC-SHA256 signature verification over raw body.
  - Replay protection with maximum 300-second timestamp skew window.
  - Event ID deduplication per tenant.
  - Tenant ID and transaction reference payload binding.

### 6. Out-of-Order Transition Safety
- Webhooks arriving out-of-order (e.g. `SETTLED` before `SUBMITTED`) must be validated against `ExecutionStateMachine` legal transitions. State machine must reject regression (e.g. `SUCCEEDED -> PENDING`).

### 7. Automated Daily Reconciliation
- Implement a periodic background job executing `verify_result()` to reconcile `UNKNOWN` or `RECONCILIATION_REQUIRED` executions against end-of-day bank statements.

---

## 3. Checklist for Enabling Production Provider

- [ ] Security Audit & Penetration Test completed.
- [ ] HSM / Vault credential storage configured.
- [ ] Provider sandbox integration tested for 1,000+ synthetic transactions.
- [ ] Webhook HMAC key rotation mechanism verified.
- [ ] CISO explicit approval signed off.
