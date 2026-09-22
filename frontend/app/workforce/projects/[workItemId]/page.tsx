"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { Agent, WorkforceGoal, WorkforceProject, WorkforceWorkItem, api } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { Breadcrumbs } from "@/components/ui/Breadcrumbs";
import { Status } from "@/components/ui/Status";
import { RegistryShell, StateMessage } from "@/components/registry-shell";

const STATUSES: WorkforceWorkItem["status"][] = ["BACKLOG", "READY", "IN_PROGRESS", "IN_REVIEW", "BLOCKED", "DONE", "CANCELLED"];
const PRIORITIES: WorkforceWorkItem["priority"][] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

function label(value: string) {
  return value.replaceAll("_", " ");
}

export default function WorkforceWorkItemPage({ params }: { params: Promise<{ workItemId: string }> }) {
  const [item, setItem] = useState<WorkforceWorkItem | null>(null);
  const [projects, setProjects] = useState<WorkforceProject[]>([]);
  const [goals, setGoals] = useState<WorkforceGoal[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<WorkforceWorkItem["status"]>("BACKLOG");
  const [priority, setPriority] = useState<WorkforceWorkItem["priority"]>("MEDIUM");
  const [goalId, setGoalId] = useState("");
  const [agentId, setAgentId] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    params.then(({ workItemId }) => Promise.all([api.workforceWorkItem(workItemId), api.workforceProjects(), api.workforceGoals(), api.agents()]))
      .then(([workItem, projectData, goalData, agentData]) => {
        setItem(workItem); setProjects(projectData); setGoals(goalData); setAgents(agentData);
        setTitle(workItem.title); setDescription(workItem.description ?? ""); setStatus(workItem.status); setPriority(workItem.priority);
        setGoalId(workItem.goal_id ?? ""); setAgentId(workItem.assignee_agent_id ?? "");
      })
      .catch((reason: Error) => setError(reason.message));
  }, [params]);

  const project = useMemo(() => projects.find((entry) => entry.id === item?.project_id), [item?.project_id, projects]);
  const activeAgents = useMemo(() => agents.filter((agent) => agent.status === "ACTIVE"), [agents]);

  const save = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!item || !title.trim()) return;
    setSaving(true); setError(null);
    try {
      const updated = await api.updateWorkforceWorkItem(item.id, { title: title.trim(), description: description.trim() || undefined, status, priority, goal_id: goalId || null, assignee_agent_id: agentId || null });
      setItem(updated); setTitle(updated.title); setDescription(updated.description ?? "");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to save work item.");
    } finally { setSaving(false); }
  };

  if (!item) return <RegistryShell><StateMessage>{error ? `Unable to load work item. ${error}` : "Loading work item…"}</StateMessage></RegistryShell>;

  return <RegistryShell actions={<Link href="/workforce/projects" className="rounded-control border border-hairline bg-surface px-3 py-2 text-xs font-semibold text-ink hover:bg-surfaceMuted">Back to work queue</Link>}>
    <Breadcrumbs items={[{ label: "Workforce", href: "/workforce" }, { label: "Projects & work", href: "/workforce/projects" }, { label: item.title }]} />
    <div className="mt-5 flex flex-wrap items-start justify-between gap-4"><div><p className="eyebrow text-inkFaint">Planning record</p><h1 className="mt-1 text-2xl font-semibold tracking-tight text-ink">{item.title}</h1><p className="mt-2 text-sm text-inkSubtle">{project ? <Link href={`/workforce/projects/project/${project.id}`} className="font-medium text-signal hover:text-signalHover">{project.name}</Link> : "Workforce project"} · Updated {formatDateTime(item.updated_at)}</p></div><div className="flex flex-wrap items-center gap-2"><Status value={item.status} dot /><Status value={item.priority} /></div></div>
    {error ? <div className="mt-5"><StateMessage tone="error">{error}</StateMessage></div> : null}
    <div className="mt-7 grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]"><form onSubmit={save} className="rounded-card border border-hairline bg-surface p-6"><div className="flex items-center justify-between gap-4"><div><p className="eyebrow text-inkFaint">Work details</p><h2 className="mt-1 text-lg font-semibold text-ink">Keep the planning record current</h2></div><button disabled={saving} className="rounded-control bg-signal px-4 py-2 text-sm font-semibold text-white hover:bg-signalHover disabled:opacity-50">{saving ? "Saving…" : "Save changes"}</button></div><div className="mt-6 space-y-5"><label className="block text-sm font-medium text-ink">Title<input required value={title} onChange={(event) => setTitle(event.target.value)} maxLength={280} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-focusRing" /></label><label className="block text-sm font-medium text-ink">Planning context<textarea value={description} onChange={(event) => setDescription(event.target.value)} maxLength={4000} rows={7} placeholder="What outcome, context, or constraint should this work retain?" className="mt-2 w-full resize-y rounded-control border border-hairline bg-surface px-3 py-2 text-sm leading-6 outline-none placeholder:text-inkFaint focus-visible:ring-2 focus-visible:ring-focusRing" /></label><div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-medium text-ink">Status<select value={status} onChange={(event) => setStatus(event.target.value as WorkforceWorkItem["status"])} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-focusRing">{STATUSES.map((value) => <option key={value} value={value}>{label(value)}</option>)}</select></label><label className="text-sm font-medium text-ink">Priority<select value={priority} onChange={(event) => setPriority(event.target.value as WorkforceWorkItem["priority"])} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-focusRing">{PRIORITIES.map((value) => <option key={value} value={value}>{value}</option>)}</select></label><label className="text-sm font-medium text-ink">Goal<select value={goalId} onChange={(event) => setGoalId(event.target.value)} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-focusRing"><option value="">No goal linked</option>{goals.map((goal) => <option key={goal.id} value={goal.id}>{goal.title}</option>)}</select></label><label className="text-sm font-medium text-ink">Assigned agent<select value={agentId} onChange={(event) => setAgentId(event.target.value)} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-focusRing"><option value="">Unassigned</option>{activeAgents.map((agent) => <option key={agent.id} value={agent.id}>{agent.name}</option>)}</select></label></div></div></form>
      <aside className="space-y-4"><section className="rounded-card border border-hairline bg-surface p-5"><p className="eyebrow text-inkFaint">Action governance</p><h2 className="mt-1 text-base font-semibold text-ink">Planning is not execution</h2>{item.action_request_id ? <><p className="mt-3 text-sm leading-6 text-inkSubtle">A protected action request is linked to this record. Its evidence and approval route remain in the governance system.</p><Link href={`/action-requests/${item.action_request_id}`} className="mt-4 inline-flex rounded-control bg-ink px-3 py-2 text-xs font-semibold text-white hover:bg-ink/90">Open action evidence</Link></> : <p className="mt-3 text-sm leading-6 text-inkSubtle">No protected action is linked. Updating this planning record does not invoke an agent, connector, or external system.</p>}</section><section className="rounded-card border border-hairline bg-surface p-5"><p className="eyebrow text-inkFaint">Record</p><dl className="mt-3 space-y-3 text-sm"><div><dt className="text-inkFaint">Project</dt><dd className="mt-1 font-medium text-ink">{project?.name ?? "Unavailable project"}</dd></div><div><dt className="text-inkFaint">Created</dt><dd className="mt-1 text-ink">{formatDateTime(item.created_at)}</dd></div><div><dt className="text-inkFaint">Last updated</dt><dd className="mt-1 text-ink">{formatDateTime(item.updated_at)}</dd></div></dl></section></aside>
    </div>
  </RegistryShell>;
}
