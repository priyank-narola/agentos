"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Agent, Principal, api } from "@/lib/api";
import { RegistryShell, StateMessage } from "@/components/registry-shell";
import { Status } from "@/components/ui/Status";
import { DataTable, type DataColumn } from "@/components/ui/DataTable";
import { shortId } from "@/lib/format";

export default function AgentsPage() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [principals, setPrincipals] = useState<Principal[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("ALL");

  useEffect(() => {
    Promise.all([api.agents(), api.principals().catch(() => [] as Principal[])])
      .then(([agentData, principalData]) => {
        setAgents(agentData);
        setPrincipals(principalData);
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, []);

  const ownerName = useCallback((id: string) => principals.find((p) => p.id === id)?.name ?? shortId(id), [principals]);
  const activeCount = agents.filter((a) => a.status === "ACTIVE").length;
  const visibleAgents = useMemo(() => agents.filter((agent) => {
    const matchesQuery = !query.trim() || [agent.name, agent.purpose, agent.version, ownerName(agent.owner_principal_id)].some((value) => value.toLowerCase().includes(query.trim().toLowerCase()));
    return matchesQuery && (status === "ALL" || agent.status === status);
  }), [agents, query, status, ownerName]);

  const columns: DataColumn<Agent>[] = [
    {
      key: "agent",
      header: "Agent",
      render: (a) => (
        <div className="min-w-0">
          <p className="font-medium text-ink">{a.name}</p>
          <p className="mt-0.5 text-xs text-inkFaint">v{a.version} · {shortId(a.id, 8)}</p>
        </div>
      ),
    },
    {
      key: "owner",
      header: "Acting for",
      render: (a) => <span className="text-inkMuted">{ownerName(a.owner_principal_id)}</span>,
    },
    { key: "purpose", header: "Purpose", render: (a) => <p className="max-w-[26ch] truncate text-inkSubtle" title={a.purpose}>{a.purpose}</p> },
    { key: "risk", header: "Risk", render: (a) => <Status value={a.risk_classification} /> },
    { key: "status", header: "Status", render: (a) => <Status value={a.status} /> },
  ];

  return (
    <RegistryShell title="Agents" eyebrow="Agent governance">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-2xl text-sm leading-6 text-inkSubtle">
          Software identities that act on behalf of a principal. Each agent acts only within the authority delegated to it.
        </p>
        <div className="flex items-center gap-3"><Link href="/tools" className="text-xs font-semibold text-signal outline-none hover:text-signalHover focus-visible:ring-2 focus-visible:ring-focusRing">Tools & actions →</Link><span className="text-xs text-inkFaint">{agents.length} registered · <span className="font-medium text-signal">{activeCount} active</span></span></div>
      </div>

      <section aria-label="Agent registry filters" className="mb-5 grid gap-3 rounded-card border border-hairline bg-surface p-4 sm:grid-cols-[minmax(0,1fr)_180px]">
        <div><label htmlFor="agent-search" className="mb-1.5 block text-xs font-medium text-inkMuted">Search agent, owner, or purpose</label><input id="agent-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search registered agents" className="w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink outline-none placeholder:text-inkFaint focus-visible:ring-2 focus-visible:ring-focusRing" /></div>
        <div><label htmlFor="agent-status" className="mb-1.5 block text-xs font-medium text-inkMuted">Lifecycle status</label><select id="agent-status" value={status} onChange={(event) => setStatus(event.target.value)} className="w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing"><option value="ALL">All statuses</option><option value="ACTIVE">Active</option><option value="SUSPENDED">Suspended</option><option value="RETIRED">Retired</option></select></div>
        <p aria-live="polite" className="sm:col-span-2 text-xs text-inkFaint">{visibleAgents.length} of {agents.length} registered agents shown. Select an agent to inspect permitted authority and lifecycle controls.</p>
      </section>

      {loading && <StateMessage>Loading agents…</StateMessage>}
      {error && <StateMessage tone="error">Unable to load agents. {error}</StateMessage>}
      {!loading && !error && agents.length === 0 && <StateMessage>No agents registered yet. Run the guided demo to create a governed agent.</StateMessage>}
      {agents.length > 0 && (
        <DataTable<Agent>
          columns={columns}
          rows={visibleAgents}
          rowKey={(a) => a.id}
          onRowClick={(a) => router.push(`/agents/${a.id}`)}
          caption="Registered agents"
          minWidth={760}
        />
      )}
    </RegistryShell>
  );
}
