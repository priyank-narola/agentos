"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";

import { Agent, WorkforceGoal, api } from "@/lib/api";
import { RegistryShell, StateMessage } from "@/components/registry-shell";
import { Status } from "@/components/ui/Status";

const GOAL_STATUSES: WorkforceGoal["status"][] = ["PLANNED", "ACTIVE", "AT_RISK", "ACHIEVED", "CANCELLED"];

export default function WorkforceGoalsPage() {
  const [goals, setGoals] = useState<WorkforceGoal[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [owner, setOwner] = useState("");
  const [parent, setParent] = useState("");
  const [status, setStatus] = useState<WorkforceGoal["status"]>("PLANNED");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => Promise.all([api.workforceGoals(), api.agents()]).then(([goalData, agentData]) => { setGoals(goalData); setAgents(agentData); });
  useEffect(() => { load().catch((reason: Error) => setError(reason.message)); }, []);

  const activeAgents = useMemo(() => agents.filter((agent) => agent.status === "ACTIVE"), [agents]);
  const rootGoals = goals.filter((goal) => !goal.parent_goal_id);
  const children = (goalId: string) => goals.filter((goal) => goal.parent_goal_id === goalId);
  const ownerName = (id?: string | null) => agents.find((agent) => agent.id === id)?.name ?? "No accountable agent";

  const create = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!title.trim()) return;
    setSaving(true); setError(null);
    try {
      const created = await api.createWorkforceGoal({ title: title.trim(), description: description.trim() || undefined, status, parent_goal_id: parent || null, owner_agent_id: owner || null });
      setGoals((current) => [created, ...current]);
      setTitle(""); setDescription(""); setOwner(""); setParent(""); setStatus("PLANNED");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to create goal."); }
    finally { setSaving(false); }
  };

  return (
    <RegistryShell title="Workforce goals" eyebrow="Mission → measurable work" actions={<Link href="/workforce/projects" className="rounded-control border border-hairline bg-surface px-3 py-2 text-xs font-semibold text-ink hover:bg-surfaceMuted">Open projects & work</Link>}>
      <p className="mb-6 max-w-3xl text-sm leading-6 text-inkSubtle">Goals provide the “why” for agent work. Ownership is accountable, but it does not grant an agent action authority or an approval right.</p>
      {error && <StateMessage tone="error">{error}</StateMessage>}

      <section className="rounded-card border border-hairline bg-surface p-6">
        <p className="eyebrow text-inkFaint">New goal</p><h2 className="mt-1 text-lg font-semibold tracking-tight text-ink">Create an accountable outcome</h2>
        <form onSubmit={create} className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <label className="text-sm font-medium text-ink">Goal title<input required value={title} onChange={(event) => setTitle(event.target.value)} maxLength={240} placeholder="e.g. Reduce approval delay" className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-focusRing" /></label>
          <label className="text-sm font-medium text-ink">Goal status<select value={status} onChange={(event) => setStatus(event.target.value as WorkforceGoal["status"])} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-focusRing">{GOAL_STATUSES.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select></label>
          <label className="text-sm font-medium text-ink">Parent goal <span className="font-normal text-inkFaint">optional</span><select value={parent} onChange={(event) => setParent(event.target.value)} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-focusRing"><option value="">Mission-level goal</option>{goals.map((goal) => <option key={goal.id} value={goal.id}>{goal.title}</option>)}</select></label>
          <label className="text-sm font-medium text-ink">Accountable agent <span className="font-normal text-inkFaint">optional</span><select value={owner} onChange={(event) => setOwner(event.target.value)} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-focusRing"><option value="">Unassigned</option>{activeAgents.map((agent) => <option key={agent.id} value={agent.id}>{agent.name}</option>)}</select></label>
          <label className="text-sm font-medium text-ink md:col-span-2 xl:col-span-3">Description <span className="font-normal text-inkFaint">optional</span><input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Outcome and decision context" className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-focusRing" /></label>
          <div className="flex items-end"><button disabled={saving} className="w-full rounded-control bg-signal px-4 py-2 text-sm font-semibold text-white hover:bg-signalHover disabled:opacity-50">{saving ? "Creating…" : "Create goal"}</button></div>
        </form>
      </section>

      <section className="mt-8"><p className="eyebrow text-inkFaint">Goal hierarchy</p><h2 className="mt-1 text-lg font-semibold tracking-tight text-ink">Mission alignment</h2>
        {goals.length === 0 ? <StateMessage>No Workforce goals yet. Create a mission-level goal to begin.</StateMessage> : <div className="mt-4 space-y-4">
          {rootGoals.map((goal) => <article key={goal.id} className="rounded-card border border-hairline bg-surface p-5"><GoalRow goal={goal} ownerName={ownerName} /><div className="ml-5 mt-4 border-l border-hairline pl-5">{children(goal.id).length ? children(goal.id).map((child) => <GoalRow key={child.id} goal={child} ownerName={ownerName} nested />) : <p className="text-xs text-inkFaint">No nested goals yet.</p>}</div></article>)}
        </div>}
      </section>
    </RegistryShell>
  );
}

function GoalRow({ goal, ownerName, nested = false }: { goal: WorkforceGoal; ownerName: (id?: string | null) => string; nested?: boolean }) {
  return <div className={nested ? "py-1" : ""}><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="font-medium text-ink">{goal.title}</p>{goal.description && <p className="mt-1 max-w-2xl text-sm leading-6 text-inkSubtle">{goal.description}</p>}<p className="mt-2 text-xs text-inkFaint">Accountable agent: {ownerName(goal.owner_agent_id)}</p></div><Status value={goal.status} /></div></div>;
}
