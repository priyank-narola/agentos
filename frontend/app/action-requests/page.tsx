"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ActionRequest, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function ActionRequestsPage() {
  const [requests, setRequests] = useState<ActionRequest[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    api.actionRequests().then(setRequests).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false));
  }, []);

  return (
    <RegistryShell title="Action requests" eyebrow="Governed actions">
      <p className="mb-6 max-w-2xl text-sm leading-6 text-slate-500">
        Every governed action request and its server-generated decision chain — open a request to see identity, policy, risk, approval, execution, and audit for that single action.
      </p>
      {error && <StateMessage tone="error">Unable to load action requests. {error}</StateMessage>}
      {loading && !error && <StateMessage>Loading governed actions…</StateMessage>}
      {!loading && !error && requests.length === 0 && <StateMessage>No action requests recorded yet.</StateMessage>}
      {requests.length > 0 && (
        <div className="overflow-hidden border border-slate-200 bg-white">
          <div className="grid grid-cols-[1.3fr_1fr_1fr_0.9fr_0.9fr] gap-4 border-b border-slate-200 bg-slate-50 px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <span>Agent / action</span><span>Resource</span><span>Risk</span><span>Decision</span><span>Requested</span>
          </div>
          {requests.map((request) => (
            <Link key={request.id} href={`/action-requests/${request.id}`} className="grid grid-cols-[1.3fr_1fr_1fr_0.9fr_0.9fr] gap-4 border-b border-slate-100 px-5 py-4 text-sm last:border-0 hover:bg-slate-50">
              <span><strong className="block font-medium text-ink">{request.agent_name}</strong><small className="text-xs text-slate-400">{request.action_name}</small></span>
              <span className="text-slate-500">{request.resource_key}</span>
              <span>{request.risk_classification ? <StatusPill value={`${request.risk_classification} · ${request.risk_score}`} /> : <span className="text-xs text-slate-400">—</span>}</span>
              <span><StatusPill value={request.decision ?? request.status} /></span>
              <span className="text-xs text-slate-400">{new Date(request.requested_at).toLocaleString()}</span>
            </Link>
          ))}
        </div>
      )}
    </RegistryShell>
  );
}
