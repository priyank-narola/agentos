"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Action, Tool, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function ToolsPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [actionsByTool, setActionsByTool] = useState<Record<string, Action[]>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("ALL");

  const visibleTools = useMemo(() => tools.filter((tool) => {
    const actions = actionsByTool[tool.id] ?? [];
    const needle = query.trim().toLowerCase();
    const matchesQuery = !needle || [tool.name, tool.description, ...actions.map((action) => action.name)].some((value) => value.toLowerCase().includes(needle));
    return matchesQuery && (status === "ALL" || tool.status === status);
  }), [actionsByTool, query, status, tools]);

  useEffect(() => {
    api.tools()
      .then(async (toolsData) => {
        setTools(toolsData);
        const entries = await Promise.all(toolsData.map(async (tool) => [tool.id, await api.toolActions(tool.id).catch(() => [] as Action[])] as const));
        setActionsByTool(Object.fromEntries(entries));
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <RegistryShell title="Capabilities" eyebrow="Tools & actions">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4"><div className="max-w-3xl"><p className="text-sm leading-6 text-inkSubtle">Capabilities group the protected actions an agent may request. Every action carries its own risk classification — an agent that can read data is not automatically allowed to move money.</p><p className="mt-2 text-xs text-inkFaint">Connector capabilities are sandbox/test-mode only. No live money movement is active.</p></div><Link href="/agents" className="text-xs font-semibold text-signal outline-none hover:text-signalHover focus-visible:ring-2 focus-visible:ring-focusRing">Agent registry →</Link></div>
      <section aria-label="Capability registry filters" className="mb-5 grid gap-3 rounded-card border border-hairline bg-surface p-4 sm:grid-cols-[minmax(0,1fr)_180px]"><div><label htmlFor="capability-search" className="mb-1.5 block text-xs font-medium text-inkMuted">Search tool or protected action</label><input id="capability-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search capabilities" className="w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink outline-none placeholder:text-inkFaint focus-visible:ring-2 focus-visible:ring-focusRing" /></div><div><label htmlFor="capability-status" className="mb-1.5 block text-xs font-medium text-inkMuted">Lifecycle status</label><select id="capability-status" value={status} onChange={(event) => setStatus(event.target.value)} className="w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing"><option value="ALL">All statuses</option><option value="ACTIVE">Active</option><option value="DISABLED">Disabled</option><option value="RETIRED">Retired</option></select></div><p aria-live="polite" className="sm:col-span-2 text-xs text-inkFaint">{visibleTools.length} of {tools.length} capabilities shown. Action permissions are evaluated by delegation and policy at request time.</p></section>
      {loading && <StateMessage>Loading capabilities…</StateMessage>}
      {error && <StateMessage tone="error">Unable to load tools. Confirm the API is running. {error}</StateMessage>}
      {!loading && !error && tools.length === 0 && <StateMessage>No capabilities registered yet.</StateMessage>}
      {tools.length > 0 && (
        <div className="grid gap-5 md:grid-cols-2">
          {visibleTools.map((tool) => {
            const actions = actionsByTool[tool.id] ?? [];
            return (
              <div key={tool.id} className="rounded-card border border-hairline bg-surface p-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-semibold text-ink">{tool.name}</h2>
                    <p className="mt-1 text-sm leading-6 text-inkSubtle">{tool.description}</p>
                  </div>
                  <StatusPill value={tool.status} />
                </div>
                <div className="mt-5 border-t border-hairline pt-4">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-inkFaint">Protected actions ({actions.length})</p>
                  {actions.length === 0 ? <p className="mt-2 text-sm text-inkFaint">No actions registered under this capability.</p> : (
                    <ul className="mt-3 space-y-2">
                      {actions.map((action) => (
                        <li key={action.id} className="flex items-center justify-between gap-3 border-b border-hairline pb-2 text-sm">
                          <span className="font-medium text-ink">{action.name}</span>
                          <StatusPill value={`${action.risk_level} risk`} />
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </RegistryShell>
  );
}
