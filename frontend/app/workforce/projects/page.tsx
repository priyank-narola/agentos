"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";

import { Agent, WorkforceGoal, WorkforceProject, WorkforceWorkItem, api } from "@/lib/api";
import { RegistryShell, StateMessage } from "@/components/registry-shell";
import { DataTable, type DataColumn } from "@/components/ui/DataTable";
import { Status } from "@/components/ui/Status";
import { CollectionToolbar } from "@/components/ui/CollectionToolbar";

const WORK_STATUSES: WorkforceWorkItem["status"][] = ["BACKLOG", "READY", "IN_PROGRESS", "IN_REVIEW", "BLOCKED", "DONE", "CANCELLED"];
const BOARD_STATUSES: WorkforceWorkItem["status"][] = ["BACKLOG", "READY", "IN_PROGRESS", "IN_REVIEW", "BLOCKED", "DONE"];

function statusLabel(status: WorkforceWorkItem["status"]) {
  return status.replaceAll("_", " ");
}

export default function WorkforceProjectsPage() {
  const [goals, setGoals] = useState<WorkforceGoal[]>([]);
  const [projects, setProjects] = useState<WorkforceProject[]>([]);
  const [items, setItems] = useState<WorkforceWorkItem[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [projectName, setProjectName] = useState("");
  const [projectGoal, setProjectGoal] = useState("");
  const [projectOwner, setProjectOwner] = useState("");
  const [workProject, setWorkProject] = useState("");
  const [workTitle, setWorkTitle] = useState("");
  const [workGoal, setWorkGoal] = useState("");
  const [workAgent, setWorkAgent] = useState("");
  const [workPriority, setWorkPriority] = useState<WorkforceWorkItem["priority"]>("MEDIUM");
  const [search, setSearch] = useState("");
  const [projectFilter, setProjectFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState<"ALL" | WorkforceWorkItem["status"]>("ALL");
  const [sort, setSort] = useState<"updated" | "priority" | "status">("updated");
  const [view, setView] = useState<"list" | "board">("list");
  const [saving, setSaving] = useState<"project" | "work" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => Promise.all([api.workforceGoals(), api.workforceProjects(), api.workforceWorkItems(), api.agents()]).then(([goalData, projectData, itemData, agentData]) => { setGoals(goalData); setProjects(projectData); setItems(itemData); setAgents(agentData); });
  useEffect(() => { load().catch((reason: Error) => setError(reason.message)); }, []);
  useEffect(() => { if (!workProject && projects[0]) setWorkProject(projects[0].id); }, [projects, workProject]);

  const activeAgents = useMemo(() => agents.filter((agent) => agent.status === "ACTIVE"), [agents]);
  const agentName = useCallback((id?: string | null) => agents.find((agent) => agent.id === id)?.name ?? "Unassigned", [agents]);
  const projectNameById = useCallback((id: string) => projects.find((project) => project.id === id)?.name ?? "Unavailable project", [projects]);
  const visibleItems = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    return items
      .filter((item) => projectFilter === "ALL" || item.project_id === projectFilter)
      .filter((item) => statusFilter === "ALL" || item.status === statusFilter)
      .filter((item) => !normalizedSearch || [item.title, item.description ?? "", agentName(item.assignee_agent_id), projectNameById(item.project_id)].join(" ").toLowerCase().includes(normalizedSearch))
      .sort((left, right) => {
        if (sort === "priority") return ["CRITICAL", "HIGH", "MEDIUM", "LOW"].indexOf(left.priority) - ["CRITICAL", "HIGH", "MEDIUM", "LOW"].indexOf(right.priority);
        if (sort === "status") return left.status.localeCompare(right.status);
        return right.updated_at.localeCompare(left.updated_at);
      });
  }, [agentName, items, projectFilter, projectNameById, search, sort, statusFilter]);

  const createProject = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); if (!projectName.trim()) return; setSaving("project"); setError(null);
    try { const created = await api.createWorkforceProject({ name: projectName.trim(), goal_id: projectGoal || null, owner_agent_id: projectOwner || null }); setProjects((current) => [created, ...current]); setProjectName(""); setProjectGoal(""); setProjectOwner(""); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to create project."); } finally { setSaving(null); }
  };
  const createWork = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); if (!workProject || !workTitle.trim()) return; setSaving("work"); setError(null);
    try { const created = await api.createWorkforceWorkItem({ project_id: workProject, title: workTitle.trim(), goal_id: workGoal || null, assignee_agent_id: workAgent || null, priority: workPriority }); setItems((current) => [created, ...current]); setWorkTitle(""); setWorkGoal(""); setWorkAgent(""); setWorkPriority("MEDIUM"); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to create work item."); } finally { setSaving(null); }
  };
  const changeStatus = async (item: WorkforceWorkItem, status: WorkforceWorkItem["status"]) => {
    setError(null);
    try { const updated = await api.updateWorkforceWorkItem(item.id, { status }); setItems((current) => current.map((entry) => entry.id === updated.id ? updated : entry)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to change work status."); }
  };
  const columns: DataColumn<WorkforceWorkItem>[] = [
    { key: "item", header: "Work item", render: (item) => <div><p className="font-medium text-ink">{item.title}</p><p className="mt-0.5 text-xs text-inkFaint">{projectNameById(item.project_id)}</p></div> },
    { key: "agent", header: "Assigned agent", render: (item) => <span className="text-inkMuted">{agentName(item.assignee_agent_id)}</span> },
    { key: "priority", header: "Priority", render: (item) => <Status value={item.priority} /> },
    { key: "status", header: "Work status", render: (item) => <select aria-label={`Update status for ${item.title}`} value={item.status} onChange={(event) => void changeStatus(item, event.target.value as WorkforceWorkItem["status"])} className="rounded-control border border-hairline bg-surface px-2 py-1 text-xs font-medium text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing">{WORK_STATUSES.map((value) => <option key={value} value={value}>{statusLabel(value)}</option>)}</select> },
    { key: "bridge", header: "Action governance", render: (item) => item.action_request_id ? <Link href={`/action-requests/${item.action_request_id}`} className="text-xs font-semibold text-signal hover:text-signalHover">Evidence →</Link> : <span className="text-xs text-inkFaint">No action requested</span> },
  ];

  return <RegistryShell title="Projects & work" eyebrow="Durable work queue" actions={<Link href="/workforce/goals" className="rounded-control border border-hairline bg-surface px-3 py-2 text-xs font-semibold text-ink hover:bg-surfaceMuted">Open goals</Link>}>
    <p className="mb-6 max-w-3xl text-sm leading-6 text-inkSubtle">Projects bound work to an outcome. Moving a work item does not invoke an agent, a connector, or a protected action; it only records planning state.</p>
    {error && <StateMessage tone="error">{error}</StateMessage>}
    <div className="grid gap-6 lg:grid-cols-2">
      <section className="rounded-card border border-hairline bg-surface p-6"><p className="eyebrow text-inkFaint">New project</p><h2 className="mt-1 text-lg font-semibold tracking-tight text-ink">Create a bounded work space</h2><form onSubmit={createProject} className="mt-5 space-y-4"><label className="block text-sm font-medium text-ink">Project name<input required value={projectName} onChange={(event) => setProjectName(event.target.value)} maxLength={200} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-focusRing" /></label><div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-medium text-ink">Goal<select value={projectGoal} onChange={(event) => setProjectGoal(event.target.value)} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm"><option value="">No goal linked</option>{goals.map((goal) => <option key={goal.id} value={goal.id}>{goal.title}</option>)}</select></label><label className="text-sm font-medium text-ink">Owner agent<select value={projectOwner} onChange={(event) => setProjectOwner(event.target.value)} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm"><option value="">Unassigned</option>{activeAgents.map((agent) => <option key={agent.id} value={agent.id}>{agent.name}</option>)}</select></label></div><button disabled={saving !== null} className="rounded-control bg-signal px-4 py-2 text-sm font-semibold text-white hover:bg-signalHover disabled:opacity-50">{saving === "project" ? "Creating…" : "Create project"}</button></form></section>
      <section id="new-work-item" className="rounded-card border border-hairline bg-surface p-6"><p className="eyebrow text-inkFaint">New work item</p><h2 className="mt-1 text-lg font-semibold tracking-tight text-ink">Plan work without starting it</h2><form onSubmit={createWork} className="mt-5 space-y-4"><label className="block text-sm font-medium text-ink">Work title<input required disabled={!projects.length} value={workTitle} onChange={(event) => setWorkTitle(event.target.value)} maxLength={280} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm disabled:bg-surfaceMuted" /></label><div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-medium text-ink">Project<select required value={workProject} onChange={(event) => setWorkProject(event.target.value)} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm"><option value="">Select project</option>{projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</select></label><label className="text-sm font-medium text-ink">Priority<select value={workPriority} onChange={(event) => setWorkPriority(event.target.value as WorkforceWorkItem["priority"])} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm">{["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((value) => <option key={value} value={value}>{value}</option>)}</select></label><label className="text-sm font-medium text-ink">Goal<select value={workGoal} onChange={(event) => setWorkGoal(event.target.value)} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm"><option value="">No goal linked</option>{goals.map((goal) => <option key={goal.id} value={goal.id}>{goal.title}</option>)}</select></label><label className="text-sm font-medium text-ink">Assign agent<select value={workAgent} onChange={(event) => setWorkAgent(event.target.value)} className="mt-2 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm"><option value="">Unassigned</option>{activeAgents.map((agent) => <option key={agent.id} value={agent.id}>{agent.name}</option>)}</select></label></div><button disabled={saving !== null || !projects.length} className="rounded-control bg-signal px-4 py-2 text-sm font-semibold text-white hover:bg-signalHover disabled:opacity-50">{saving === "work" ? "Creating…" : "Create work item"}</button></form></section>
    </div>
    <section className="mt-8"><div className="mb-4 flex flex-wrap items-end justify-between gap-3"><div><p className="eyebrow text-inkFaint">Work queue</p><h2 className="mt-1 text-lg font-semibold tracking-tight text-ink">Current work</h2></div><div className="inline-flex rounded-control border border-hairline bg-surfaceMuted p-1" aria-label="Work queue view" role="group"><button type="button" aria-pressed={view === "list"} onClick={() => setView("list")} className={`rounded-[5px] px-3 py-1.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focusRing ${view === "list" ? "bg-surface text-ink shadow-sm" : "text-inkMuted hover:text-ink"}`}>List</button><button type="button" aria-pressed={view === "board"} onClick={() => setView("board")} className={`rounded-[5px] px-3 py-1.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focusRing ${view === "board" ? "bg-surface text-ink shadow-sm" : "text-inkMuted hover:text-ink"}`}>Board</button></div></div>{items.length ? <CollectionToolbar
      ariaLabel="Work queue controls"
      context={<span className="rounded-full bg-signalSoft px-2.5 py-1 text-xs font-semibold text-signal">{visibleItems.length} of {items.length} work items</span>}
      search={<><label className="sr-only" htmlFor="work-search">Search work items</label><input id="work-search" type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search work, project, or agent…" className="w-full rounded-control border border-hairline bg-surface px-3 py-2 text-xs text-ink outline-none placeholder:text-inkFaint focus-visible:ring-2 focus-visible:ring-focusRing" /></>}
      controls={<><select aria-label="Filter work by project" value={projectFilter} onChange={(event) => setProjectFilter(event.target.value)} className="rounded-control border border-hairline bg-surface px-2 py-2 text-xs text-ink"><option value="ALL">All projects</option>{projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</select><select aria-label="Filter work by status" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as "ALL" | WorkforceWorkItem["status"])} className="rounded-control border border-hairline bg-surface px-2 py-2 text-xs text-ink"><option value="ALL">All statuses</option>{WORK_STATUSES.map((status) => <option key={status} value={status}>{statusLabel(status)}</option>)}</select><select aria-label="Sort work items" value={sort} onChange={(event) => setSort(event.target.value as "updated" | "priority" | "status")} className="rounded-control border border-hairline bg-surface px-2 py-2 text-xs text-ink"><option value="updated">Recently updated</option><option value="priority">Priority</option><option value="status">Status</option></select></>}
      actions={<a href="#new-work-item" className="rounded-control bg-ink px-3 py-2 text-xs font-semibold text-white hover:bg-ink/90">New work item</a>}
      feedback={search || projectFilter !== "ALL" || statusFilter !== "ALL" ? <button type="button" onClick={() => { setSearch(""); setProjectFilter("ALL"); setStatusFilter("ALL"); }} className="text-xs font-semibold text-signal hover:text-signalHover">Clear active filters</button> : null}
    /> : null}{items.length ? (visibleItems.length ? view === "list" ? <div className="mt-4"><DataTable columns={columns} rows={visibleItems} rowKey={(item) => item.id} caption="Workforce work queue" minWidth={900} /></div> : <div className="mt-4 overflow-x-auto pb-2"><div className="grid min-w-[980px] grid-cols-6 gap-3" aria-label="Work queue board">{BOARD_STATUSES.map((status) => { const columnItems = visibleItems.filter((item) => item.status === status); return <section key={status} aria-labelledby={`board-${status}`} className="min-h-[260px] rounded-card border border-hairline bg-surfaceMuted/60 p-3"><div className="mb-3 flex items-center justify-between gap-2"><h3 id={`board-${status}`} className="text-xs font-bold tracking-wide text-ink">{statusLabel(status)}</h3><span className="rounded-full bg-surface px-2 py-0.5 text-xs font-semibold text-inkMuted">{columnItems.length}</span></div><div className="space-y-2">{columnItems.length ? columnItems.map((item) => <article key={item.id} className="rounded-control border border-hairline bg-surface p-3 shadow-sm transition-shadow hover:shadow-card"><div className="flex items-start justify-between gap-2"><p className="text-sm font-semibold leading-5 text-ink">{item.title}</p><Status value={item.priority} className="shrink-0 px-2 text-[10px]" /></div><p className="mt-2 truncate text-xs text-inkMuted">{projectNameById(item.project_id)}</p><div className="mt-3 flex items-center justify-between gap-2"><span className="truncate text-xs text-inkSubtle">{agentName(item.assignee_agent_id)}</span>{item.action_request_id ? <Link href={`/action-requests/${item.action_request_id}`} className="text-xs font-semibold text-signal hover:text-signalHover">Evidence</Link> : null}</div><label className="mt-3 block"><span className="sr-only">Move {item.title} to status</span><select aria-label={`Move ${item.title} to status`} value={item.status} onChange={(event) => void changeStatus(item, event.target.value as WorkforceWorkItem["status"])} className="w-full rounded-control border border-hairline bg-surface px-2 py-1.5 text-xs font-medium text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing">{WORK_STATUSES.map((value) => <option key={value} value={value}>{statusLabel(value)}</option>)}</select></label></article>) : <p className="rounded-control border border-dashed border-hairline px-3 py-5 text-center text-xs text-inkFaint">No work here</p>}</div></section>; })}</div></div> : <StateMessage>No work items match these filters.</StateMessage>) : <StateMessage>Create a project before planning work.</StateMessage>}</section>
  </RegistryShell>;
}
