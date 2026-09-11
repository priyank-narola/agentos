"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ActionRequest, Agent, Delegation, Principal, api } from "@/lib/api";
import { RegistryShell, StateMessage } from "@/components/registry-shell";
import { Breadcrumbs } from "@/components/ui/Breadcrumbs";
import { Status } from "@/components/ui/Status";
import { KeyValueList } from "@/components/ui/KeyValue";
import { formatDateTime, shortId } from "@/lib/format";

export default function AgentCaseFile({ params }: { params: Promise<{ id: string }> }) {
  const [agent, setAgent] = useState<Agent | null>(null);
  const [delegations, setDelegations] = useState<Delegation[]>([]);
  const [requests, setRequests] = useState<ActionRequest[]>([]);
  const [principals, setPrincipals] = useState<Principal[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    params.then(({ id }) => {
      Promise.all([
        api.agent(id),
        api.delegations().catch(() => [] as Delegation[]),
        api.actionRequests().catch(() => [] as ActionRequest[]),
        api.principals().catch(() => [] as Principal[]),
      ])
        .then(([agentData, delegationData, requestData, principalData]) => {
          setAgent(agentData);
          setDelegations(delegationData.filter((d) => d.agent_id === agentData.id));
          setRequests(requestData.filter((r) => r.agent_id === agentData.id).sort((a, b) => b.requested_at.localeCompare(a.requested_at)));
          setPrincipals(principalData);
        })
        .catch((reason: Error) => setError(reason.message));
    });
  }, [params]);

  if (!agent && !error) {
    return (
      <RegistryShell>
        <StateMessage>Loading agent file…</StateMessage>
      </RegistryShell>
    );
  }

  const principalName = (id?: string | null) => {
    if (!id) return "Unavailable";
    return principals.find((p) => p.id === id)?.name ?? shortId(id);
  };

  const activeDelegations = delegations.filter((d) => d.status === "ACTIVE");
  const outcomes = {
    authorized: requests.filter((r) => r.decision === "ALLOW" && r.execution_status === "EXECUTED").length,
    blocked: requests.filter((r) => r.decision === "DENY").length,
    pending: requests.filter((r) => r.decision === "REQUIRE_APPROVAL").length,
  };

  return (
    <RegistryShell>
      <div className="mb-6">
        <Breadcrumbs
          items={[
            { label: "Control center", href: "/" },
            { label: "Agents", href: "/agents" },
            { label: agent?.name ?? "Agent" },
          ]}
        />
      </div>

      {error && <StateMessage tone="error">Unable to load agent. {error}</StateMessage>}

      {agent && (
        <div className="space-y-6">
          <header className="rounded-card border border-hairline bg-surface p-6 lg:p-8">
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div>
                <p className="eyebrow text-inkFaint">Agent case file</p>
                <h1 className="mt-1.5 text-2xl font-semibold tracking-tight text-ink lg:text-3xl">{agent.name}</h1>
                <p className="mt-2 max-w-2xl text-[15px] leading-7 text-inkSubtle">{agent.purpose}</p>
                {agent.description && <p className="mt-2 text-[13px] leading-6 text-inkSubtle">{agent.description}</p>}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Status value={agent.status} />
                <Status value={agent.risk_classification} />
                <span className="rounded-full border border-hairline bg-surfaceMuted px-2.5 py-0.5 text-xs font-medium text-inkMuted">v{agent.version}</span>
              </div>
            </div>
            <div className="mt-6 grid gap-6 border-t border-hairline pt-5 lg:grid-cols-2">
              <div>
                <p className="eyebrow text-inkFaint">Acting for</p>
                <p className="mt-1.5 text-[15px] font-medium text-ink">{principalName(agent.owner_principal_id)}</p>
                <p className="mt-0.5 font-mono text-[11px] text-inkFaint">owner {shortId(agent.owner_principal_id, 8)}</p>
              </div>
              <div>
                <p className="eyebrow text-inkFaint">Activity</p>
                <p className="mt-1.5 text-sm text-inkSubtle">
                  <span className="tnum font-semibold text-ink">{outcomes.authorized}</span> executed · <span className="tnum font-semibold text-ink">{outcomes.blocked}</span> blocked ·{" "}
                  <span className="tnum font-semibold text-ink">{outcomes.pending}</span> pending
                </p>
              </div>
            </div>
          </header>

          <div className="grid gap-6 xl:grid-cols-2">
            <section className="rounded-card border border-hairline bg-surface p-6">
              <div className="flex items-baseline justify-between">
                <div>
                  <p className="eyebrow text-inkFaint">Delegated authority</p>
                  <h2 className="mt-1 text-base font-semibold tracking-tight text-ink">Delegations</h2>
                </div>
                <span className="text-xs text-inkFaint">{delegations.length} total · {activeDelegations.length} active</span>
              </div>
              {delegations.length === 0 ? (
                <p className="mt-4 text-sm text-inkSubtle">No delegation records for this agent.</p>
              ) : (
                <ul className="mt-4 divide-y divide-hairline">
                  {delegations.map((d) => (
                    <li key={d.id} className="flex items-center justify-between gap-4 py-3">
                      <div className="min-w-0">
                        <p className="font-mono text-[13px] text-ink">{d.scope}</p>
                        <p className="mt-0.5 text-xs text-inkSubtle">
                          Granted by {principalName(d.principal_id)} · {d.expires_at ? `expires ${formatDateTime(d.expires_at)}` : "no expiry"}
                        </p>
                      </div>
                      <Status value={d.status} />
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="rounded-card border border-hairline bg-surface p-6">
              <div className="flex items-baseline justify-between">
                <div>
                  <p className="eyebrow text-inkFaint">Recent governed actions</p>
                  <h2 className="mt-1 text-base font-semibold tracking-tight text-ink">Action history</h2>
                </div>
                <Link href="/action-requests" className="text-[13px] font-semibold text-signal hover:text-signalHover">
                  View all →
                </Link>
              </div>
              {requests.length === 0 ? (
                <p className="mt-4 text-sm text-inkSubtle">No governed actions recorded for this agent yet.</p>
              ) : (
                <ul className="mt-4 space-y-1">
                  {requests.slice(0, 8).map((r) => (
                    <li key={r.id}>
                      <Link href={`/action-requests/${r.id}`} className="flex items-center justify-between gap-3 rounded-control px-1 py-2 transition-colors hover:bg-surfaceMuted">
                        <span className="min-w-0">
                          <span className="block truncate text-sm font-medium text-ink">{r.action_name}</span>
                          <span className="block text-xs text-inkFaint">{formatDateTime(r.requested_at)}</span>
                        </span>
                        <span className="flex shrink-0 gap-2">
                          <Status value={r.decision ?? r.status} />
                          <Status value={r.execution_status ?? "NOT_EXECUTED"} />
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>

          <section className="rounded-card border border-hairline bg-surface p-6">
            <p className="eyebrow text-inkFaint">Identity record</p>
            <div className="mt-4 max-w-xl">
              <KeyValueList
                items={[
                  { label: "ID", value: shortId(agent.id, 12), mono: true },
                  { label: "Version", value: agent.version },
                  { label: "Status", value: agent.status },
                  { label: "Risk classification", value: agent.risk_classification },
                  { label: "Owner", value: principalName(agent.owner_principal_id) },
                ]}
              />
            </div>
          </section>
        </div>
      )}
    </RegistryShell>
  );
}
