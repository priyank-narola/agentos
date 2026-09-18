"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { Agent, Delegation, Principal, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function DelegationsPage() {
  const [delegations, setDelegations] = useState<Delegation[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [principals, setPrincipals] = useState<Principal[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [revoking, setRevoking] = useState<string | null>(null);
  const [issuing, setIssuing] = useState(false);
  const [principalId, setPrincipalId] = useState("");
  const [agentId, setAgentId] = useState("");
  const [scope, setScope] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.delegations(), api.agents(), api.principals()])
      .then(([d, a, p]) => { setDelegations(d); setAgents(a); setPrincipals(p); })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  const agentName = (id: string) => agents.find((a) => a.id === id)?.name ?? id;
  const principalName = (id: string) => principals.find((p) => p.id === id)?.name ?? id;
  const activeAgents = useMemo(() => agents.filter((agent) => agent.status === "ACTIVE"), [agents]);
  const activeHumanPrincipals = useMemo(() => principals.filter((principal) => principal.type === "HUMAN" && principal.status === "ACTIVE"), [principals]);

  useEffect(() => {
    setPrincipalId((current) => current || activeHumanPrincipals[0]?.id || "");
    setAgentId((current) => current || activeAgents[0]?.id || "");
  }, [activeAgents, activeHumanPrincipals]);

  const issue = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalizedScope = scope.trim();
    if (!principalId || !agentId || !normalizedScope || !confirmed) {
      setError("Choose an active human, an active agent, an exact scope, and confirm the grant.");
      return;
    }
    const normalizedExpiry = expiresAt ? new Date(expiresAt) : null;
    if (normalizedExpiry && (Number.isNaN(normalizedExpiry.getTime()) || normalizedExpiry <= new Date())) {
      setError("Expiry must be a valid time in the future, or leave it blank for no expiry.");
      return;
    }
    setIssuing(true); setError(null); setMessage(null);
    try {
      const delegation = await api.createDelegation({ principal_id: principalId, agent_id: agentId, scope: normalizedScope, issued_at: new Date().toISOString(), expires_at: normalizedExpiry?.toISOString() ?? null });
      setDelegations((current) => [delegation, ...current]);
      setScope(""); setExpiresAt(""); setConfirmed(false);
      setMessage("Delegation issued. Only the named agent, principal, and exact scope are authorized.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to issue delegation.");
    } finally { setIssuing(false); }
  };

  const revoke = async (delegation: Delegation) => {
    if (!window.confirm(`Revoke ${delegation.scope} authority? Future governed requests will be blocked.`)) return;
    setRevoking(delegation.id); setError(null); setMessage(null);
    try { const updated = await api.revokeDelegation(delegation.id); setDelegations((current) => current.map((item) => item.id === updated.id ? updated : item)); setMessage("Delegation revoked. Future governed requests outside other valid authority will be blocked."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to revoke delegation."); }
    finally { setRevoking(null); }
  };

  return (
    <RegistryShell title="Delegations" eyebrow="Delegated authority">
      <p className="mb-6 max-w-3xl text-sm leading-6 text-slate-500">
        A delegation is the authority a human principal grants to an agent. AgentOS only ever allows an agent to act within the exact scope it was delegated.
      </p>
      {error && <StateMessage tone="error">Unable to load delegations. {error}</StateMessage>}
      {message && <p className="mb-5 rounded-control border border-successBorder bg-successBg px-3 py-2 text-sm text-success">{message}</p>}
      <section className="mb-6 border border-hairline bg-surface p-6">
        <p className="eyebrow">Issue authority</p>
        <h2 className="mt-1 text-base font-semibold text-ink">Grant a narrow, reviewable delegation</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-inkSubtle">This does not approve an action and cannot let a requester self-approve. The policy engine still evaluates every later request against the exact delegated scope and active policies.</p>
        <form onSubmit={issue} className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <label className="text-sm font-medium text-ink">Human principal<select required value={principalId} onChange={(event) => setPrincipalId(event.target.value)} className="mt-2 w-full border border-hairlineStrong bg-surface px-3 py-2 text-sm"><option value="">Select principal…</option>{activeHumanPrincipals.map((principal) => <option key={principal.id} value={principal.id}>{principal.name} · {principal.external_id}</option>)}</select></label>
          <label className="text-sm font-medium text-ink">Agent<select required value={agentId} onChange={(event) => setAgentId(event.target.value)} className="mt-2 w-full border border-hairlineStrong bg-surface px-3 py-2 text-sm"><option value="">Select agent…</option>{activeAgents.map((agent) => <option key={agent.id} value={agent.id}>{agent.name} · {agent.risk_classification} risk</option>)}</select></label>
          <label className="text-sm font-medium text-ink">Exact scope<input required maxLength={200} value={scope} onChange={(event) => setScope(event.target.value)} placeholder="e.g. billing.refund" className="mt-2 w-full border border-hairlineStrong bg-surface px-3 py-2 text-sm" /></label>
          <label className="text-sm font-medium text-ink">Expiry <span className="font-normal text-inkFaint">optional</span><input type="datetime-local" value={expiresAt} onChange={(event) => setExpiresAt(event.target.value)} className="mt-2 w-full border border-hairlineStrong bg-surface px-3 py-2 text-sm" /></label>
          <label className="flex items-start gap-2 text-sm leading-5 text-ink md:col-span-2 xl:col-span-3"><input required checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} type="checkbox" className="mt-1 h-4 w-4 accent-signal" /><span>I confirm this is a least-privilege authority grant for the selected human, agent, and exact scope.</span></label>
          <div className="flex items-end"><button disabled={issuing || activeAgents.length === 0 || activeHumanPrincipals.length === 0} className="w-full rounded-control bg-signal px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{issuing ? "Issuing…" : "Issue delegation"}</button></div>
        </form>
        {(activeAgents.length === 0 || activeHumanPrincipals.length === 0) && <p className="mt-4 text-xs text-danger">An active human principal and active agent are required before a delegation can be issued.</p>}
      </section>
      {!error && delegations.length === 0 && <StateMessage>No delegation records yet. Issue only an exact, least-privilege capability scope.</StateMessage>}
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
