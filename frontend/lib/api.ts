const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Agent = { id: string; name: string; description?: string | null; owner_principal_id: string; purpose: string; version: string; status: "ACTIVE" | "SUSPENDED" | "RETIRED"; risk_classification: "LOW" | "MEDIUM" | "HIGH"; };
export type Action = { id: string; tool_id: string; name: string; description: string; risk_level: "LOW" | "MEDIUM" | "HIGH"; status: "ACTIVE" | "DISABLED" | "RETIRED"; };
export type Tool = { id: string; name: string; description: string; status: "ACTIVE" | "DISABLED" | "RETIRED"; };
export type Resource = { id: string; resource_type: string; resource_key: string; sensitivity: "LOW" | "MEDIUM" | "HIGH"; owner_reference?: string | null; status: "ACTIVE" | "RESTRICTED" | "RETIRED"; };
export type PolicyRule = { id: string; policy_id: string; effect: "ALLOW" | "DENY"; action: string; resource_type: string; conditions?: Record<string, unknown> | null; priority: number; };
export type Policy = { id: string; name: string; description?: string | null; status: "DRAFT" | "ACTIVE" | "RETIRED"; version: number; priority: number; created_at: string; updated_at: string; rules?: PolicyRule[]; };
export type EvaluationTraceStep = { step: number; code: string; outcome: string; detail: string; };
export type PolicyEvaluation = { decision: "ALLOW" | "DENY" | "REQUIRE_APPROVAL"; reason_code: string; reason: string; matched_policies: Array<{ policy_id: string; policy_name: string; policy_version: number; policy_priority: number; rule_id: string; rule_effect: "ALLOW" | "DENY"; rule_priority: number; conditions?: Record<string, unknown> | null; }>; risk_level?: "LOW" | "MEDIUM" | "HIGH" | null; delegation_status?: "ACTIVE" | "REVOKED" | "EXPIRED" | null; approval_required: boolean; trace: EvaluationTraceStep[]; };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
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
};
