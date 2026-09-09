const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

let accessToken: string | null = null;
let autoLoginAttempted = false;

export function setAccessToken(token: string | null) {
  accessToken = token;
}
export function getAccessToken() {
  return accessToken;
}

/** Development-only token issuance (mirrors POST /api/v1/auth/dev-token). */
async function fetchDevToken(externalId: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/dev-token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ external_id: externalId }),
  });
  if (!response.ok) throw new ApiError(response.status, `Unable to obtain a development token for ${externalId}`);
  const body = (await response.json()) as { access_token: string };
  setAccessToken(body.access_token);
  return body.access_token;
}

export function devTokenFor(externalId: string) {
  return fetchDevToken(externalId);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!API_BASE_URL) throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured");
  const attempt = async (): Promise<T> => {
    const headers: Record<string, string> = { "Content-Type": "application/json", ...(init?.headers as Record<string, string> | undefined) };
    if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;
    const response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store", headers, ...init });
    if (!response.ok) {
      let detail = "";
      try {
        const data = await response.json();
        detail = typeof data?.detail === "string" ? data.detail : "";
      } catch {
        /* ignore body */
      }
      throw new ApiError(response.status, detail || `API request failed (${response.status})`);
    }
    return response.json() as Promise<T>;
  };
  try {
    return await attempt();
  } catch (error) {
    // In an enforced deployment the first anonymous call returns 401. Auto-obtain a
    // development token (development mode only; production uses the real IdP token
    // injected by the host) and retry exactly once.
    if (error instanceof ApiError && error.status === 401 && !accessToken && !autoLoginAttempted) {
      autoLoginAttempted = true;
      const externalId = process.env.NEXT_PUBLIC_AUTH_DEV_PRINCIPAL || "demo-admin";
      try {
        await fetchDevToken(externalId);
        return await attempt();
      } catch {
        /* surface the original 401 if login fails */
      }
    }
    throw error;
  }
}

export type Agent = { id: string; name: string; description?: string | null; owner_principal_id: string; purpose: string; version: string; status: "ACTIVE" | "SUSPENDED" | "RETIRED"; risk_classification: "LOW" | "MEDIUM" | "HIGH"; };
export type Delegation = { id: string; principal_id: string; agent_id: string; scope: string; status: string; issued_at: string; expires_at?: string | null; };
export type Action = { id: string; tool_id: string; name: string; description: string; risk_level: "LOW" | "MEDIUM" | "HIGH"; status: "ACTIVE" | "DISABLED" | "RETIRED"; };
export type Tool = { id: string; name: string; description: string; status: "ACTIVE" | "DISABLED" | "RETIRED"; };
export type Resource = { id: string; resource_type: string; resource_key: string; sensitivity: "LOW" | "MEDIUM" | "HIGH"; owner_reference?: string | null; status: "ACTIVE" | "RESTRICTED" | "RETIRED"; };
export type PolicyRule = { id: string; policy_id: string; effect: "ALLOW" | "DENY"; action: string; resource_type: string; conditions?: Record<string, unknown> | null; priority: number; };
export type Policy = { id: string; name: string; description?: string | null; status: "DRAFT" | "ACTIVE" | "RETIRED"; version: number; priority: number; created_at: string; updated_at: string; rules?: PolicyRule[]; };
export type EvaluationTraceStep = { step: number; code: string; outcome: string; detail: string; };
export type PolicyEvaluation = { decision: "ALLOW" | "DENY" | "REQUIRE_APPROVAL"; reason_code: string; reason: string; matched_policies: Array<{ policy_id: string; policy_name: string; policy_version: number; policy_priority: number; rule_id: string; rule_effect: "ALLOW" | "DENY"; rule_priority: number; conditions?: Record<string, unknown> | null; }>; risk_level?: "LOW" | "MEDIUM" | "HIGH" | null; delegation_status?: "ACTIVE" | "REVOKED" | "EXPIRED" | null; approval_required: boolean; trace: EvaluationTraceStep[]; };
export type RiskFactor = { code: string; contribution: number; explanation: string; };
export type GatewayResponse = { action_request_id: string; gateway_status: "AUTHORIZED" | "BLOCKED" | "PENDING_APPROVAL"; decision: "ALLOW" | "DENY" | "REQUIRE_APPROVAL"; reason_code: string; reason: string; risk_level?: "LOW" | "MEDIUM" | "HIGH" | null; risk_score?: number | null; risk_classification?: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | null; risk_factors: RiskFactor[]; risk_engine_version?: string | null; approval_required: boolean; execution_status: string; requested_at: string; decided_at: string; };
export type ActionRequest = { id: string; tenant_id?: string; agent_id: string; agent_name: string; principal_id: string; action_id: string; action_name: string; tool_id: string; tool_name: string; resource_id: string; resource_type: string; resource_key: string; parameters: Record<string, unknown>; status: string; idempotency_key: string; requested_at: string; decision?: string | null; reason?: string | null; reason_code?: string | null; risk_level?: "LOW" | "MEDIUM" | "HIGH" | null; risk_score?: number | null; risk_classification?: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | null; risk_factors: RiskFactor[]; risk_engine_version?: string | null; decided_at?: string | null; };
export type Approval = { id: string; action_request_id: string; agent_id: string; agent_name: string; principal_id: string; action_id: string; action_name: string; tool_id: string; tool_name: string; resource_id: string; resource_type: string; resource_key: string; parameters: Record<string, unknown>; requested_by: string; status: "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED" | "CANCELLED"; reason: string; risk_score?: number | null; risk_classification?: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | null; risk_factors: RiskFactor[]; policy_id?: string | null; policy_version?: number | null; decided_by?: string | null; decided_at?: string | null; requested_at: string; expires_at: string; };
export type Principal = { id: string; type: "HUMAN" | "ORGANIZATION"; name: string; external_id: string; status: "ACTIVE" | "SUSPENDED" | "RETIRED"; created_at: string; updated_at: string; };
export type ApproverCandidate = { id: string; name: string; external_id: string; type: string; };
export type TreasuryManifest = { tenant_id: string; tenant_name: string; sandbox_only: boolean; requester: { id: string; name: string; external_id: string; title: string }; approver: { id: string; name: string; external_id: string; title: string }; agent: { id: string; name: string; purpose: string }; action: { id: string; name: string; risk_level: string }; resource: { id: string; resource_type: string; resource_key: string; sensitivity: string }; policy: { id: string; name: string; version: number }; default_amount: string; default_currency: string; };
export type ObservabilityActionDetail = { action_request_id: string; tenant_id: string; gateway_status: string; risk: { score?: number | null; classification?: string | null }; policy: { decision?: string | null; reason_code?: string | null; reason?: string | null }; approval: { required: boolean; status?: string | null; requested_by?: string | null; decided_by?: string | null; decided_at?: string | null }; execution: { status?: string | null; provider_transaction_id?: string | null; provider_name?: string | null }; requested_at?: string | null; };
export type TimelineEvent = { id: string; event_type: string; actor_type: string; actor_id: string | null; action_request_id: string | null; event_data: Record<string, unknown>; created_at: string | null; };
export type ObservabilityMetrics = { tenant_id: string; total_action_requests: number; pending_approvals: number; approved_executions: number; rejected_actions: number; toctou_violations: number; payload_tampering_attempts: number; authentication_failures: number; cross_tenant_attempts: number; webhook_failures: number; idempotency_conflicts: number; execution_failures_timeouts: number; };
export type TenantPosture = { tenant_id: string; active_principals: number; active_agents: number; active_delegations: number; action_volume: number; approval_volume: number; execution_volume: number; security_violations: number; high_risk_activity: number; };
export type AuditVerify = { tenant_id: string; audit_integrity_status: string; total_requests_verified: number; violation_count: number; violations: Array<{ type: string; action_request_id: string; description?: string }>; };
export type WhoAmI = { authenticated: boolean; principal?: { id: string; name: string; external_id: string; type: string } | null; tenant_id?: string | null; tenant_name?: string | null; };

export const api = {
  me: () => request<WhoAmI>("/api/v1/auth/me"),
  principals: () => request<Principal[]>("/api/v1/principals"),
  delegations: () => request<Delegation[]>("/api/v1/delegations"),
  agents: () => request<Agent[]>("/api/v1/agents"),
  agent: (id: string) => request<Agent>(`/api/v1/agents/${id}`),
  tools: () => request<Tool[]>("/api/v1/tools"),
  toolActions: (id: string) => request<Action[]>(`/api/v1/tools/${id}/actions`),
  resources: () => request<Resource[]>("/api/v1/resources"),
  policies: () => request<Policy[]>("/api/v1/policies"),
  evaluate: (payload: Record<string, unknown>) => request<PolicyEvaluation>('/api/v1/policy-evaluations', { method: "POST", body: JSON.stringify(payload) }),
  gateway: (payload: Record<string, unknown>) => request<GatewayResponse>("/api/v1/action-requests", { method: "POST", body: JSON.stringify(payload) }),
  actionRequests: () => request<ActionRequest[]>("/api/v1/action-requests"),
  actionRequest: (id: string) => request<ActionRequest>(`/api/v1/action-requests/${id}`),
  approvals: () => request<Approval[]>("/api/v1/approvals"),
  approval: (id: string) => request<Approval>(`/api/v1/approvals/${id}`),
  approvers: (id: string) => request<{ approval_id: string; approvers: ApproverCandidate[] }>(`/api/v1/approvals/${id}/approvers`),
  approve: (id: string, approver_principal_id: string) => request<Approval>(`/api/v1/approvals/${id}/approve`, { method: "POST", body: JSON.stringify({ approver_principal_id }) }),
  reject: (id: string, approver_principal_id: string) => request<Approval>(`/api/v1/approvals/${id}/reject`, { method: "POST", body: JSON.stringify({ approver_principal_id }) }),
  cancel: (id: string, approver_principal_id: string) => request<Approval>(`/api/v1/approvals/${id}/cancel`, { method: "POST", body: JSON.stringify({ approver_principal_id }) }),
  treasuryBootstrap: () => request<TreasuryManifest>("/api/v1/demo/treasury/bootstrap", { method: "POST" }),
  scenarioRun: (key: string) => request<Record<string, unknown>>(`/api/v1/demo/scenarios/${key}/run`, { method: "POST" }),
  observabilityActionRequest: (id: string, tenantId: string) => request<ObservabilityActionDetail>(`/api/v1/observability/action-requests/${id}?tenant_id=${encodeURIComponent(tenantId)}`),
  timeline: (tenantId?: string) => request<{ total: number; events: TimelineEvent[] }>(`/api/v1/observability/timeline${tenantId ? `?tenant_id=${encodeURIComponent(tenantId)}` : ""}`),
  metrics: (tenantId?: string) => request<ObservabilityMetrics>(`/api/v1/observability/metrics${tenantId ? `?tenant_id=${encodeURIComponent(tenantId)}` : ""}`),
  tenantPosture: (tenantId?: string) => request<TenantPosture>(`/api/v1/observability/tenant/posture${tenantId ? `?tenant_id=${encodeURIComponent(tenantId)}` : ""}`),
  auditVerify: (tenantId?: string) => request<AuditVerify>(`/api/v1/observability/audit/verify${tenantId ? `?tenant_id=${encodeURIComponent(tenantId)}` : ""}`),
};
