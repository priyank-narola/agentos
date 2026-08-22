"use client";

import { useEffect, useState } from "react";
import { Agent, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function AgentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const [agent, setAgent] = useState<Agent | null>(null); const [error, setError] = useState<string | null>(null);
  useEffect(() => { params.then(({ id }) => api.agent(id).then(setAgent).catch((reason: Error) => setError(reason.message))); }, [params]);
  return <RegistryShell title={agent?.name ?? "Agent detail"} eyebrow="Identity record">{error && <StateMessage tone="error">Unable to load agent. {error}</StateMessage>}{!agent && !error && <StateMessage>Loading identity record…</StateMessage>}{agent && <><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{[["Status", agent.status], ["Risk classification", agent.risk_classification], ["Version", agent.version], ["Owner principal", agent.owner_principal_id]].map(([label, value]) => <div key={label} className="border border-slate-200 bg-white p-5"><p className="text-xs uppercase tracking-wide text-slate-400">{label}</p><p className="mt-3 text-sm font-medium text-ink">{label === "Status" || label === "Risk classification" ? <StatusPill value={value} /> : value}</p></div>)}</div><div className="mt-6 grid gap-6 lg:grid-cols-2"><section className="border border-slate-200 bg-white p-6"><h2 className="font-semibold text-ink">Purpose</h2><p className="mt-3 text-sm leading-6 text-slate-500">{agent.purpose}</p>{agent.description && <p className="mt-3 text-sm leading-6 text-slate-500">{agent.description}</p>}</section><section className="border border-slate-200 bg-white p-6"><h2 className="font-semibold text-ink">Delegated authority</h2><p className="mt-3 text-sm leading-6 text-slate-500">Delegation records will be shown here. Authorization evaluation is not implemented in Phase 3.</p></section></div><div className="mt-6"><StateMessage>Recent action requests will appear here after the runtime gateway is implemented.</StateMessage></div></>}</RegistryShell>;
}
