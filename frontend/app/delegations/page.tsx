"use client";

import { useEffect, useState } from "react";

import { Agent, Delegation, Principal, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function DelegationsPage() {
  const [delegations, setDelegations] = useState<Delegation[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [principals, setPrincipals] = useState<Principal[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [revoking, setRevoking] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.delegations(), api.agents(), api.principals()])
      .then(([d, a, p]) => { setDelegations(d); setAgents(a); setPrincipals(p); })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  const agentName = (id: string) => agents.find((a) => a.id === id)?.name ?? id;
  const principalName = (id: string) => principals.find((p) => p.id === id)?.name ?? id;
  const revoke = async (delegation: Delegation) => {
    if (!window.confirm(`Revoke ${delegation.scope} authority? Future governed requests will be blocked.`)) return;
    setRevoking(delegation.id); setError(null);
    try { const updated = await api.revokeDelegation(delegation.id); setDelegations((current) => current.map((item) => item.id === updated.id ? updated : item)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to revoke delegation."); }
    finally { setRevoking(null); }
  };

  return (
    <RegistryShell title="Delegations" eyebrow="Delegated authority">
      <p className="mb-6 max-w-3xl text-sm leading-6 text-slate-500">
        A delegation is the authority a human principal grants to an agent. AgentOS only ever allows an agent to act within the exact scope it was delegated.
      </p>
      {error && <StateMessage tone="error">Unable to load delegations. {error}</StateMessage>}
      {!error && delegations.length === 0 && <StateMessage>No delegation records yet. Delegations are created when a principal grants an agent a capability scope.</StateMessage>}
      {delegations.length > 0 && (
        <div className="overflow-hidden border border-slate-200 bg-white">
          <div className="grid grid-cols-[1.2fr_1.2fr_1fr_0.7fr_0.8fr] gap-4 border-b border-slate-200 bg-slate-50 px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
              <span>Agent</span><span>Granted by (principal)</span><span>Scope</span><span>Status</span><span>Expires / control</span>
          </div>
          {delegations.map((d) => (
            <div key={d.id} className="grid grid-cols-[1.2fr_1.2fr_1fr_0.7fr_0.8fr] gap-4 border-b border-slate-100 px-5 py-4 text-sm last:border-0">
              <span className="font-medium text-ink">{agentName(d.agent_id)}</span>
              <span className="text-slate-600">{principalName(d.principal_id)}</span>
              <span className="font-mono text-slate-600">{d.scope}</span>
              <span><StatusPill value={d.status} /></span>
              <span className="text-xs text-slate-400">{d.expires_at ? new Date(d.expires_at).toLocaleString() : "Never"}{d.status === "ACTIVE" && <button type="button" onClick={() => void revoke(d)} disabled={revoking !== null} className="mt-2 block text-xs font-semibold text-rose-700 outline-none hover:underline focus-visible:ring-2 focus-visible:ring-focusRing disabled:opacity-50">{revoking === d.id ? "Revoking…" : "Revoke"}</button>}</span>
            </div>
          ))}
        </div>
      )}
    </RegistryShell>
  );
}
