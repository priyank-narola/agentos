"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ActionRequest, Resource, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function ResourceDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const [resource, setResource] = useState<Resource | null>(null);
  const [requests, setRequests] = useState<ActionRequest[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    params.then(({ id }) => {
      Promise.all([api.resource(id), api.actionRequests().catch(() => [] as ActionRequest[])])
        .then(([resourceData, requestData]) => {
          setResource(resourceData);
          setRequests(requestData.filter((r) => r.resource_id === resourceData.id).sort((a, b) => b.requested_at.localeCompare(a.requested_at)));
        })
        .catch((reason: Error) => setError(reason.message));
    });
  }, [params]);

  if (!resource && !error) {
    return <RegistryShell title="Resource detail" eyebrow="Protected resource"><StateMessage>Loading resource…</StateMessage></RegistryShell>;
  }

  const riskHint = resource?.sensitivity === "HIGH" ? "High-sensitivity resource — actions against it are governed strictly and high-risk actions require approval." : resource?.sensitivity === "MEDIUM" ? "Medium-sensitivity resource — governed actions apply." : "Low-sensitivity resource.";

  return (
    <RegistryShell title={resource ? `${resource.resource_type} / ${resource.resource_key}` : "Resource detail"} eyebrow="Protected resource">
      {error && <StateMessage tone="error">Unable to load resource. {error}</StateMessage>}
      {resource && (
        <>
          <section className="border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400">Resource</p>
                <p className="mt-1 text-2xl font-semibold text-ink">{resource.resource_key}</p>
                <p className="mt-1 text-sm text-slate-500">Type: {resource.resource_type}</p>
              </div>
              <div className="flex gap-2">
                <StatusPill value={`${resource.sensitivity} sensitivity`} />
                <StatusPill value={resource.status} />
              </div>
            </div>
            <p className="mt-4 max-w-3xl rounded border border-slate-100 bg-slate-50 p-3 text-sm leading-6 text-slate-600">{riskHint} {resource.owner_reference ? `Owner reference: ${resource.owner_reference}.` : ""}</p>
          </section>

          <section className="mt-6 border border-slate-200 bg-white p-6">
            <div className="flex items-end justify-between gap-4">
              <h2 className="font-semibold text-ink">Actions attempted against this resource</h2>
              <Link href="/action-requests" className="text-xs font-semibold text-signal hover:underline">All actions →</Link>
            </div>
            {requests.length === 0 ? <div className="mt-4"><StateMessage>No governed actions have targeted this resource yet.</StateMessage></div> : (
              <ul className="mt-4 space-y-2">
                {requests.slice(0, 20).map((req) => (
                  <li key={req.id}>
                    <Link href={`/action-requests/${req.id}`} className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 py-2.5 text-sm hover:bg-slate-50">
                      <span><strong className="text-ink">{req.agent_name}</strong><small className="ml-2 text-slate-400">{req.action_name}</small></span>
                      <span className="flex gap-2"><StatusPill value={req.decision ?? req.status} /><StatusPill value={req.risk_classification ? `${req.risk_classification} · ${req.risk_score}` : req.status} /><span className="text-xs text-slate-400">{new Date(req.requested_at).toLocaleString()}</span></span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </RegistryShell>
  );
}
