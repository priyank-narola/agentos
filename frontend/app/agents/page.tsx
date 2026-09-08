"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Agent, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]); const [error, setError] = useState<string | null>(null); const [loading, setLoading] = useState(true);
  useEffect(() => { api.agents().then(setAgents).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false)); }, []);
  return <RegistryShell title="Agent registry" eyebrow="Identity inventory"><div className="mb-6 flex items-center justify-between"><p className="max-w-xl text-sm leading-6 text-slate-500">Registered software identities and their human owners. Each agent acts under delegated authority granted by its owner.</p><span className="text-xs text-slate-400">{agents.length} records</span></div>{loading && <StateMessage>Loading registered agents…</StateMessage>}{error && <StateMessage tone="error">Unable to load agents. Confirm the FastAPI service is running. {error}</StateMessage>}{!loading && !error && agents.length === 0 && <StateMessage>No agents registered yet. Run the demo seed or use the registry API to add agents.</StateMessage>}{agents.length > 0 && <div className="overflow-hidden border border-slate-200 bg-white"><div className="grid grid-cols-[1.4fr_1fr_0.8fr_0.8fr] gap-4 border-b border-slate-200 bg-slate-50 px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500"><span>Agent</span><span>Purpose</span><span>Risk</span><span>Status</span></div>{agents.map((agent) => <Link href={`/agents/${agent.id}`} key={agent.id} className="grid grid-cols-[1.4fr_1fr_0.8fr_0.8fr] gap-4 border-b border-slate-100 px-5 py-4 text-sm last:border-0 hover:bg-slate-50"><span><strong className="block font-medium text-ink">{agent.name}</strong><small className="text-xs text-slate-400">v{agent.version}</small></span><span className="text-slate-500">{agent.purpose}</span><span><StatusPill value={agent.risk_classification} /></span><span><StatusPill value={agent.status} /></span></Link>)}</div>}</RegistryShell>;
}
