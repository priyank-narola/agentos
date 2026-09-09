"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Resource, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function ResourcesPage() {
  const [resources, setResources] = useState<Resource[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    api.resources().then(setResources).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false));
  }, []);

  return (
    <RegistryShell title="Resources" eyebrow="What AgentOS protects">
      <p className="mb-6 max-w-2xl text-sm leading-6 text-slate-500">
        Resources are the things AI agents try to affect. AgentOS evaluates every request against the resource that would be changed — a bank account is governed far more strictly than a customer record.
      </p>
      {loading && <StateMessage>Loading resources…</StateMessage>}
      {error && <StateMessage tone="error">Unable to load resources. {error}</StateMessage>}
      {!loading && !error && resources.length === 0 && <StateMessage>No resources registered yet.</StateMessage>}
      {resources.length > 0 && (
        <div className="overflow-hidden border border-slate-200 bg-white">
          <div className="grid grid-cols-[1fr_1.5fr_1fr_0.9fr_0.8fr_0.7fr] gap-4 border-b border-slate-200 bg-slate-50 px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <span>Type</span><span>Resource</span><span>Sensitivity</span><span>Status</span><span>Owner reference</span><span />
          </div>
          {resources.map((resource) => (
            <Link key={resource.id} href={`/resources/${resource.id}`} className="grid grid-cols-[1fr_1.5fr_1fr_0.9fr_0.8fr_0.7fr] gap-4 border-b border-slate-100 px-5 py-4 text-sm last:border-0 hover:bg-slate-50">
              <span className="font-medium text-ink">{resource.resource_type}</span>
              <span className="font-mono text-xs text-slate-500">{resource.resource_key}</span>
              <span><StatusPill value={resource.sensitivity} /></span>
              <span><StatusPill value={resource.status} /></span>
              <span className="truncate text-xs text-slate-400">{resource.owner_reference ?? "—"}</span>
              <span className="text-right text-xs font-semibold text-signal">Open →</span>
            </Link>
          ))}
        </div>
      )}
    </RegistryShell>
  );
}
