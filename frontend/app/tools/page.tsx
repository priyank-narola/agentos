"use client";

import { useEffect, useState } from "react";

import { Action, Tool, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function ToolsPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [actionsByTool, setActionsByTool] = useState<Record<string, Action[]>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

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
      <p className="mb-6 max-w-3xl text-sm leading-6 text-slate-500">
        Capabilities group the protected actions an agent may request. Every action carries its own risk classification — an agent that can read data is not automatically allowed to move money.
      </p>
      {loading && <StateMessage>Loading capabilities…</StateMessage>}
      {error && <StateMessage tone="error">Unable to load tools. Confirm the API is running. {error}</StateMessage>}
      {!loading && !error && tools.length === 0 && <StateMessage>No capabilities registered yet.</StateMessage>}
      {tools.length > 0 && (
        <div className="grid gap-5 md:grid-cols-2">
          {tools.map((tool) => {
            const actions = actionsByTool[tool.id] ?? [];
            return (
              <div key={tool.id} className="border border-slate-200 bg-white p-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-semibold text-ink">{tool.name}</h2>
                    <p className="mt-1 text-sm leading-6 text-slate-500">{tool.description}</p>
                  </div>
                  <StatusPill value={tool.status} />
                </div>
                <div className="mt-5 border-t border-slate-100 pt-4">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Actions ({actions.length})</p>
                  {actions.length === 0 ? <p className="mt-2 text-sm text-slate-400">No actions registered under this capability.</p> : (
                    <ul className="mt-3 space-y-2">
                      {actions.map((action) => (
                        <li key={action.id} className="flex items-center justify-between gap-3 border-b border-slate-100 pb-2 text-sm">
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
