"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Agent, WorkforceGoal, WorkforceProject, WorkforceWorkItem, api } from "@/lib/api";
import { RegistryShell, StateMessage } from "@/components/registry-shell";
import { DataTable, type DataColumn } from "@/components/ui/DataTable";
import { Metric } from "@/components/ui/Metric";
import { Status } from "@/components/ui/Status";

function agentName(agents: Agent[], id?: string | null) {
  if (!id) return "Unassigned";
  return agents.find((agent) => agent.id === id)?.name ?? "Unavailable agent";
}

export default function WorkforcePage() {
  const [goals, setGoals] = useState<WorkforceGoal[]>([]);
  const [projects, setProjects] = useState<WorkforceProject[]>([]);
  const [items, setItems] = useState<WorkforceWorkItem[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.workforceGoals(), api.workforceProjects(), api.workforceWorkItems(), api.agents()])
      .then(([goalData, projectData, itemData, agentData]) => {
        setGoals(goalData);
        setProjects(projectData);
        setItems(itemData);
        setAgents(agentData);
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, []);

  const activeGoals = goals.filter((goal) => goal.status === "ACTIVE" || goal.status === "AT_RISK").length;
  const activeWork = items.filter((item) => ["READY", "IN_PROGRESS", "IN_REVIEW", "BLOCKED"].includes(item.status));
  const blocked = items.filter((item) => item.status === "BLOCKED").length;
  const unassigned = items.filter((item) => !item.assignee_agent_id).length;
  const projectById = useMemo(() => new Map(projects.map((project) => [project.id, project])), [projects]);

  const columns: DataColumn<WorkforceWorkItem>[] = [
    {
      key: "work",
      header: "Work item",
      render: (item) => (
        <div className="min-w-0">
          <p className="font-medium text-ink">{item.title}</p>
          <p className="mt-0.5 truncate text-xs text-inkFaint">{projectById.get(item.project_id)?.name ?? "Project unavailable"}</p>
        </div>
      ),
    },
    { key: "assignee", header: "Assigned agent", render: (item) => <span className="text-inkMuted">{agentName(agents, item.assignee_agent_id)}</span> },
    { key: "priority", header: "Priority", render: (item) => <Status value={item.priority} /> },
    { key: "status", header: "Status", render: (item) => <Status value={item.status} /> },
    {
      key: "governance",
      header: "Governance link",
      render: (item) => item.action_request_id ? (
        <Link href={`/action-requests/${item.action_request_id}`} className="text-xs font-semibold text-signal hover:text-signalHover">View governed action →</Link>
      ) : <span className="text-xs text-inkFaint">No action requested</span>,
    },
  ];

  return (
    <RegistryShell title="Workforce" eyebrow="Plan work. Govern consequential actions." actions={<Link href="/agents" className="rounded-control border border-hairline bg-surface px-3 py-2 text-xs font-semibold text-ink hover:bg-surfaceMuted">View governed agents</Link>}>
      <div className="mb-7 rounded-card border border-infoBorder bg-infoBg px-5 py-4 text-sm leading-6 text-inkMuted">
        <span className="font-semibold text-ink">Planning layer, not an execution bypass.</span> Workforce organizes goals, projects, and agent work. Any protected action still enters AgentOS policy, risk, separation-of-duties approval, reconciliation, and evidence controls.
      </div>

      {error && <StateMessage tone="error">Unable to load Workforce records. Confirm the migrated AgentOS API is running. {error}</StateMessage>}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Workforce posture">
        <Metric label="Active goals" value={loading ? "—" : activeGoals} note={`${goals.length} recorded`} />
        <Metric label="Active work" value={loading ? "—" : activeWork.length} note="ready, in progress, review, or blocked" />
        <Metric label="Blocked work" value={loading ? "—" : blocked} note="requires operator attention" tone={blocked ? "warning" : "success"} />
        <Metric label="Unassigned work" value={loading ? "—" : unassigned} note="does not start an agent automatically" tone={unassigned ? "warning" : "default"} />
      </section>

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <section className="rounded-card border border-hairline bg-surface p-6">
          <div className="flex items-baseline justify-between gap-4">
            <div>
              <p className="eyebrow text-inkFaint">Mission and goals</p>
              <h2 className="mt-1 text-lg font-semibold tracking-tight text-ink">What the workforce is working toward</h2>
            </div>
            <span className="text-xs text-inkFaint">{goals.length} total</span>
          </div>
          {loading ? <p className="mt-5 text-sm text-inkSubtle">Loading goals…</p> : goals.length === 0 ? <p className="mt-5 text-sm text-inkSubtle">No goals exist yet.</p> : (
            <ul className="mt-5 divide-y divide-hairline">
              {goals.slice(0, 4).map((goal) => (
                <li key={goal.id} className="flex items-start justify-between gap-4 py-3 first:pt-0 last:pb-0">
                  <div className="min-w-0"><p className="font-medium text-ink">{goal.title}</p><p className="mt-1 text-xs text-inkSubtle">Owner: {agentName(agents, goal.owner_agent_id)}{goal.parent_goal_id ? " · nested goal" : " · mission-level"}</p></div>
                  <Status value={goal.status} />
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-card border border-hairline bg-surface p-6">
          <p className="eyebrow text-inkFaint">Projects</p>
          <h2 className="mt-1 text-lg font-semibold tracking-tight text-ink">Bounded work spaces</h2>
          {loading ? <p className="mt-5 text-sm text-inkSubtle">Loading projects…</p> : projects.length === 0 ? <p className="mt-5 text-sm text-inkSubtle">No projects exist yet.</p> : (
            <ul className="mt-5 space-y-3">
              {projects.slice(0, 4).map((project) => <li key={project.id} className="rounded-control border border-hairline bg-surfaceMuted px-4 py-3"><div className="flex items-center justify-between gap-3"><p className="truncate text-sm font-medium text-ink">{project.name}</p><Status value={project.status} /></div><p className="mt-1 text-xs text-inkSubtle">Owner: {agentName(agents, project.owner_agent_id)}</p></li>)}
            </ul>
          )}
        </section>
      </div>

      <section className="mt-8">
        <div className="mb-4 flex items-end justify-between gap-4"><div><p className="eyebrow text-inkFaint">Work queue</p><h2 className="mt-1 text-lg font-semibold tracking-tight text-ink">Tracked workforce work</h2></div><span className="text-xs text-inkFaint">No autonomous execution in this increment</span></div>
        {loading ? <StateMessage>Loading work items…</StateMessage> : items.length === 0 ? <StateMessage>No Workforce work items exist yet.</StateMessage> : <DataTable columns={columns} rows={items} rowKey={(item) => item.id} caption="Workforce work queue" minWidth={820} />}
      </section>
    </RegistryShell>
  );
}
