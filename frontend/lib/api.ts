const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Agent = { id: string; name: string; description?: string | null; owner_principal_id: string; purpose: string; version: string; status: "ACTIVE" | "SUSPENDED" | "RETIRED"; risk_classification: "LOW" | "MEDIUM" | "HIGH"; };
export type Action = { id: string; tool_id: string; name: string; description: string; risk_level: "LOW" | "MEDIUM" | "HIGH"; status: "ACTIVE" | "DISABLED" | "RETIRED"; };
export type Tool = { id: string; name: string; description: string; status: "ACTIVE" | "DISABLED" | "RETIRED"; };
export type Resource = { id: string; resource_type: string; resource_key: string; sensitivity: "LOW" | "MEDIUM" | "HIGH"; owner_reference?: string | null; status: "ACTIVE" | "RESTRICTED" | "RETIRED"; };

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`API request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export const api = {
  agents: () => request<Agent[]>("/api/v1/agents"),
  agent: (id: string) => request<Agent>(`/api/v1/agents/${id}`),
  tools: () => request<Tool[]>("/api/v1/tools"),
  toolActions: (id: string) => request<Action[]>(`/api/v1/tools/${id}/actions`),
  resources: () => request<Resource[]>("/api/v1/resources"),
};
