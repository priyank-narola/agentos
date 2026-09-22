"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { Agent, WorkforceGoal, WorkforceProject, WorkforceWorkItem, api } from "@/lib/api";
import { Breadcrumbs } from "@/components/ui/Breadcrumbs";
import { Status } from "@/components/ui/Status";
import { RegistryShell, StateMessage } from "@/components/registry-shell";

const PROJECT_STATUSES: WorkforceProject["status"][] = ["ACTIVE", "PAUSED", "COMPLETED", "CANCELLED"];

export default function WorkforceProjectPage({ params }: { params: Promise<{ projectId: string }> }) {
  const [project, setProject] = useState<WorkforceProject | null>(null);
  const [goals, setGoals] = useState<WorkforceGoal[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [items, setItems] = useState<WorkforceWorkItem[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<WorkforceProject["status"]>("ACTIVE");
  const [goalId, setGoalId] = useState("");
  const [ownerId, setOwnerId] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    params.then(({ projectId }) => Promise.all([api.workforceProject(projectId), api.workforceGoals(), api.agents(), api.workforceWorkItems(projectId)]))
      .then(([projectData, goalData, agentData, workData]) => {
        setProject(projectData); setGoals(goalData); setAgents(agentData); setItems(workData);
        setName(projectData.name); setDescription(projectData.description ?? ""); setStatus(projectData.status); setGoalId(projectData.goal_id ?? ""); setOwnerId(projectData.owner_agent_id ?? "");
      })
      .catch((reason: Error) => setError(reason.message));
  }, [params]);

  const activeAgents = useMemo(() => agents.filter((agent) => agent.status === "ACTIVE"), [agents]);
  const statusCounts = useMemo(() => items.reduce<Record<string, number>>((counts, item) => ({ ...counts, [item.status]: (counts[item.status] ?? 0) + 1 }), {}), [items]);
  const save = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); if (!project || !name.trim()) return;
    setSaving(true); setError(null);
    try { const updated = await api.updateWorkforceProject(project.id, { name: name.trim(), description: description.trim() || undefined, status, goal_id: goalId || null, owner_agent_id: ownerId || null }); setProject(updated); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to save project."); }
    finally { setSaving(false); }
  };

  if (!project) return <RegistryShell><StateMessage>{error ? `Unable to load project. ${error}` : "Loading project…"}</StateMessage></RegistryShell>;
  return <RegistryShell actions={<Link href="/workforce/projects" className="rounded-control border border-hairline bg-surface px-3 py-2 text-xs font-semibold text-ink hover:bg-surfaceMuted">Back to work queue</Link>}>
    <Breadcrumbs items={[{ label: "Workforce", href: "/workforce" }, { label: "Projects & work", href: "/workforce/projects" }, { label: project.name }]} />
    <div className="mt-5 flex flex-wrap items-start justify-between gap-4"><div><p className="eyebrow text-inkFaint">Project workspace</p><h1 className="mt-1 text-2xl font-semibold tracking-tight text-ink">{project.name}</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-inkSubtle">A durable planning space. Work stays non-executing until a separate governed action is requested.</p></div><Status value={project.status} dot /></div>
    {error ? <div className="mt-5"><StateMessage tone="error">{error}</StateMessage></div> : null}
    <div className="mt-7 grid gap-6 xl:grid-cols-[minmax(0,1fr)_22rem]"><form onSubmit={save} className="rounded-card border border-hairline bg-surface p-6"><div className="flex items-center justify-between gap-4"><div><p className="eyebrow text-inkFaint">Project context</p><h2 className="mt-1 text-lg font-semibold text-ink">Outcome, owner, and state</h2></div><button disabled={saving} className="rounded-control bg-signal px-4 py-2 text-sm font-semibold text-white hover:bg-signalHover disabled:opacity-50">{saving ? "Saving…" : "Save changes"}</button></div><div className="mt-6 space-y-5"><label className="block text-sm font-medium text-ink">Project name<input required value={name} onChange={(event) => setName(event.target.value)} maxLength={200} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-focusRing" /></label><label className="block text-sm font-medium text-ink">Planning context<textarea value={description} onChange={(event) => setDescription(event.target.value)} maxLength={4000} rows={6} placeholder="Describe the project outcome and constraints." className="mt-2 w-full resize-y rounded-control border border-hairline bg-surface px-3 py-2 text-sm leading-6 outline-none placeholder:text-inkFaint focus-visible:ring-2 focus-visible:ring-focusRing" /></label><div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-medium text-ink">Project state<select value={status} onChange={(event) => setStatus(event.target.value as WorkforceProject["status"])} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-focusRing">{PROJECT_STATUSES.map((value) => <option key={value} value={value}>{value}</option>)}</select></label><label className="text-sm font-medium text-ink">Linked goal<select value={goalId} onChange={(event) => setGoalId(event.target.value)} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-focusRing"><option value="">No goal linked</option>{goals.map((goal) => <option key={goal.id} value={goal.id}>{goal.title}</option>)}</select></label><label className="text-sm font-medium text-ink sm:col-span-2">Owner agent<select value={ownerId} onChange={(event) => setOwnerId(event.target.value)} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-focusRing"><option value="">Unassigned</option>{activeAgents.map((agent) => <option key={agent.id} value={agent.id}>{agent.name}</option>)}</select></label></div></div></form>
      <aside className="space-y-4"><section className="rounded-card border border-hairline bg-surface p-5"><p className="eyebrow text-inkFaint">Work distribution</p><h2 className="mt-1 text-base font-semibold text-ink">{items.length} planned work items</h2><dl className="mt-4 grid grid-cols-2 gap-3">{["BACKLOG", "READY", "IN_PROGRESS", "IN_REVIEW", "BLOCKED", "DONE"].map((state) => <div key={state} className="rounded-control bg-surfaceMuted p-3"><dt className="text-[11px] font-semibold tracking-wide text-inkFaint">{state.replaceAll("_", " ")}</dt><dd className="mt-1 text-xl font-semibold text-ink">{statusCounts[state] ?? 0}</dd></div>)}</dl></section><section className="rounded-card border border-hairline bg-surface p-5"><p className="eyebrow text-inkFaint">Governance boundary</p><p className="mt-2 text-sm leading-6 text-inkSubtle">Project updates only manage planning data. They never start an agent, invoke a connector, approve an action, or perform external work.</p></section></aside>
    </div>
    <section className="mt-6 rounded-card border border-hairline bg-surface p-6"><div className="flex flex-wrap items-end justify-between gap-3"><div><p className="eyebrow text-inkFaint">Work items</p><h2 className="mt-1 text-lg font-semibold text-ink">Project queue</h2></div><Link href="/workforce/projects#new-work-item" className="rounded-control border border-hairline px-3 py-2 text-xs font-semibold text-ink hover:bg-surfaceMuted">Plan new work</Link></div>{items.length ? <ul className="mt-5 divide-y divide-hairline">{items.map((item) => <li key={item.id}><Link href={`/workforce/projects/${item.id}`} className="flex flex-wrap items-center justify-between gap-3 py-3 transition-colors hover:bg-surfaceMuted"><span><span className="block text-sm font-semibold text-ink">{item.title}</span><span className="mt-0.5 block text-xs text-inkFaint">{item.description ?? "No planning context recorded."}</span></span><span className="flex gap-2"><Status value={item.priority} /><Status value={item.status} /></span></Link></li>)}</ul> : <p className="mt-5 text-sm text-inkSubtle">No work items are planned for this project yet.</p>}</section>
  </RegistryShell>;
}
