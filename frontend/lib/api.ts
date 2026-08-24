const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export type Agent = { id: string; name: string; description?: string | null; owner_principal_id: string; purpose: string; version: string; status: "ACTIVE" | "SUSPENDED" | "RETIRED"; risk_classification: "LOW" | "MEDIUM" | "HIGH"; };
export type Action = { id: string; tool_id: string; name: string; description: string; risk_level: "LOW" | "MEDIUM" | "HIGH"; status: "ACTIVE" | "DISABLED" | "RETIRED"; };
export type Tool = { id: string; name: string; description: string; status: "ACTIVE" | "DISABLED" | "RETIRED"; };
export type Resource = { id: string; resource_type: string; resource_key: string; sensitivity: "LOW" | "MEDIUM" | "HIGH"; owner_reference?: string | null; status: "ACTIVE" | "RESTRICTED" | "RETIRED"; };
export type PolicyRule = { id: string; policy_id: string; effect: "ALLOW" | "DENY"; action: string; resource_type: string; conditions?: Record<string, unknown> | null; priority: number; };
export type Policy = { id: string; name: string; description?: string | null; status: "DRAFT" | "ACTIVE" | "RETIRED"; version: number; priority: number; created_at: string; updated_at: string; rules?: PolicyRule[]; };
export type EvaluationTraceStep = { step: number; code: string; outcome: string; detail: string; };
export type PolicyEvaluation = { decision: "ALLOW" | "DENY" | "REQUIRE_APPROVAL"; reason_code: string; reason: string; matched_policies: Array<{ policy_id: string; policy_name: string; policy_version: number; policy_priority: number; rule_id: string; rule_effect: "ALLOW" | "DENY"; rule_priority: number; conditions?: Record<string, unknown> | null; }>; risk_level?: "LOW" | "MEDIUM" | "HIGH" | null; delegation_status?: "ACTIVE" | "REVOKED" | "EXPIRED" | null; approval_required: boolean; trace: EvaluationTraceStep[]; };
export type RiskFactor = { code: string; contribution: number; explanation: string; };
export type GatewayResponse = { action_request_id: string; gateway_status: "AUTHORIZED" | "BLOCKED" | "PENDING_APPROVAL"; decision: "ALLOW" | "DENY" | "REQUIRE_APPROVAL"; reason_code: string; reason: string; risk_level?: "LOW" | "MEDIUM" | "HIGH" | null; risk_score?: number | null; risk_classification?: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | null; risk_factors: RiskFactor[]; risk_engine_version?: string | null; approval_required: boolean; execution_status: "NOT_EXECUTED"; requested_at: string; decided_at: string; };
export type ActionRequest = { id: string; agent_id: string; agent_name: string; principal_id: string; action_id: string; action_name: string; tool_id: string; tool_name: string; resource_id: string; resource_type: string; resource_key: string; parameters: Record<string, unknown>; status: string; idempotency_key: string; requested_at: string; decision?: string | null; reason?: string | null; reason_code?: string | null; risk_level?: "LOW" | "MEDIUM" | "HIGH" | null; risk_score?: number | null; risk_classification?: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | null; risk_factors: RiskFactor[]; risk_engine_version?: string | null; decided_at?: string | null; };
export type Approval = { id: string; action_request_id: string; agent_id: string; agent_name: string; principal_id: string; action_id: string; action_name: string; tool_id: string; tool_name: string; resource_id: string; resource_type: string; resource_key: string; parameters: Record<string, unknown>; requested_by: string; status: "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED" | "CANCELLED"; reason: string; risk_score?: number | null; risk_classification?: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | null; risk_factors: RiskFactor[]; policy_id?: string | null; policy_version?: number | null; decided_by?: string | null; decided_at?: string | null; requested_at: string; expires_at: string; };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!API_BASE_URL) throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured");
  const response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store", headers: { "Content-Type": "application/json" }, ...init });
  if (!response.ok) throw new Error(`API request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export const api = {
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
  approve: (id: string, approver_principal_id: string) => request<Approval>(`/api/v1/approvals/${id}/approve`, { method: "POST", body: JSON.stringify({ approver_principal_id }) }),
  reject: (id: string, approver_principal_id: string) => request<Approval>(`/api/v1/approvals/${id}/reject`, { method: "POST", body: JSON.stringify({ approver_principal_id }) }),
  cancel: (id: string, approver_principal_id: string) => request<Approval>(`/api/v1/approvals/${id}/cancel`, { method: "POST", body: JSON.stringify({ approver_principal_id }) }),
};
