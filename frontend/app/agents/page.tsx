"use client";

import { useEffect, useState } from "react";
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

  useEffect(() => {
    Promise.all([api.agents(), api.principals().catch(() => [] as Principal[])])
      .then(([agentData, principalData]) => {
        setAgents(agentData);
        setPrincipals(principalData);
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, []);

  const ownerName = (id: string) => principals.find((p) => p.id === id)?.name ?? shortId(id);
  const activeCount = agents.filter((a) => a.status === "ACTIVE").length;

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
        <span className="text-xs text-inkFaint">
          {agents.length} registered · <span className="font-medium text-signal">{activeCount} active</span>
        </span>
      </div>

      {loading && <StateMessage>Loading agents…</StateMessage>}
      {error && <StateMessage tone="error">Unable to load agents. {error}</StateMessage>}
      {!loading && !error && agents.length === 0 && <StateMessage>No agents registered yet. Run the guided demo to create a governed agent.</StateMessage>}
      {agents.length > 0 && (
        <DataTable<Agent>
          columns={columns}
          rows={agents}
          rowKey={(a) => a.id}
          onRowClick={(a) => router.push(`/agents/${a.id}`)}
          caption="Registered agents"
          minWidth={760}
        />
      )}
    </RegistryShell>
  );
}
