"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ActionRequest, Agent, Delegation, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function AgentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const [agent, setAgent] = useState<Agent | null>(null);
  const [delegations, setDelegations] = useState<Delegation[]>([]);
  const [requests, setRequests] = useState<ActionRequest[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    params.then(({ id }) => {
      Promise.all([api.agent(id), api.delegations().catch(() => [] as Delegation[]), api.actionRequests().catch(() => [] as ActionRequest[])])
        .then(([agentData, delegationData, requestData]) => {
          setAgent(agentData);
          setDelegations(delegationData.filter((d) => d.agent_id === agentData.id));
          setRequests(requestData.filter((r) => r.agent_id === agentData.id));
        })
        .catch((reason: Error) => setError(reason.message));
    });
  }, [params]);

  if (!agent && !error) {
    return <RegistryShell title="Agent detail" eyebrow="Identity record"><StateMessage>Loading identity record…</StateMessage></RegistryShell>;
  }

  return <RegistryShell title={agent?.name ?? "Agent detail"} eyebrow="Identity record">
    {error && <StateMessage tone="error">Unable to load agent. {error}</StateMessage>}
    {agent && <>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[["Status", agent.status], ["Risk classification", agent.risk_classification], ["Version", agent.version], ["Owner principal", agent.owner_principal_id]].map(([label, value]) => (
          <div key={label} className="border border-slate-200 bg-white p-5">
            <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
            <p className="mt-3 text-sm font-medium text-ink">{label === "Status" || label === "Risk classification" ? <StatusPill value={value} /> : value}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <section className="border border-slate-200 bg-white p-6">
          <h2 className="font-semibold text-ink">Purpose</h2>
          <p className="mt-3 text-sm leading-6 text-slate-500">{agent.purpose}</p>
          {agent.description && <p className="mt-3 text-sm leading-6 text-slate-500">{agent.description}</p>}
        </section>

        <section className="border border-slate-200 bg-white p-6">
          <h2 className="font-semibold text-ink">Delegated authority</h2>
          {delegations.length === 0
            ? <p className="mt-4 text-sm text-slate-500">No active delegation records for this agent.</p>
            : <ul className="mt-4 space-y-2">{delegations.map((delegation) => (
                <li key={delegation.id} className="flex items-center justify-between gap-3 border-b border-slate-100 pb-2 text-sm">
                  <span className="font-mono text-slate-600">{delegation.scope}</span>
                  <StatusPill value={delegation.status} />
                </li>
              ))}</ul>}
        </section>
      </div>

      <div className="mt-6 border border-slate-200 bg-white p-6">
        <div className="flex items-end justify-between gap-4">
          <h2 className="font-semibold text-ink">Recent action requests</h2>
          <Link href="/action-requests" className="text-xs font-semibold text-signal hover:underline">View all →</Link>
        </div>
        {requests.length === 0
          ? <div className="mt-4"><StateMessage>No action requests recorded for this agent yet.</StateMessage></div>
          : <ul className="mt-4 space-y-2">{requests.slice(0, 10).map((request) => (
              <li key={request.id}>
                <Link href={`/action-requests/${request.id}`} className="flex items-center justify-between gap-3 border-b border-slate-100 py-2 text-sm hover:bg-slate-50">
                  <span className="text-ink">{request.action_name}</span>
                  <span className="flex gap-2"><StatusPill value={`${request.risk_classification ?? "--"} · ${request.risk_score ?? "--"}`} /><StatusPill value={request.status} /></span>
                </Link>
              </li>
            ))}</ul>}
      </div>
    </>}
  </RegistryShell>;
}
