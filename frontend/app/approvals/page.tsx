"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Approval, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    api.approvals().then(setApprovals).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false));
  }, []);

  return (
    <RegistryShell title="Approval queue" eyebrow="Human review boundary">
      <p className="mb-6 max-w-2xl text-sm leading-6 text-slate-500">
        Review high-risk actions that policy allowed only with a one-time human decision by a distinct approver. Approving executes the action inside the sandbox only — no real money movement.
      </p>
      {error && <StateMessage tone="error">Unable to load approvals. {error}</StateMessage>}
      {loading && !error && <StateMessage>Loading the approval queue…</StateMessage>}
      {!loading && !error && approvals.length === 0 && <StateMessage>No approvals are waiting for review.</StateMessage>}
      {approvals.length > 0 && (
        <div className="overflow-hidden border border-slate-200 bg-white">
          <div className="grid grid-cols-[1.3fr_1fr_0.9fr_0.9fr_0.9fr] gap-4 border-b border-slate-200 bg-slate-50 px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <span>Agent / action</span><span>Resource</span><span>Risk</span><span>Status</span><span>Expiry</span>
          </div>
          {approvals.map((approval) => (
            <Link key={approval.id} href={`/approvals/${approval.id}`} className="grid grid-cols-[1.3fr_1fr_0.9fr_0.9fr_0.9fr] gap-4 border-b border-slate-100 px-5 py-4 text-sm last:border-0 hover:bg-slate-50">
              <span><strong className="block font-medium text-ink">{approval.agent_name}</strong><small className="text-xs text-slate-400">{approval.action_name}</small></span>
              <span className="text-slate-500">{approval.resource_key}</span>
              <span><StatusPill value={`${approval.risk_classification ?? "UNKNOWN"} · ${approval.risk_score ?? "--"}`} /></span>
              <span><StatusPill value={approval.status} /></span>
              <span className="text-xs text-slate-400">{new Date(approval.expires_at).toLocaleString()}</span>
            </Link>
          ))}
        </div>
      )}
    </RegistryShell>
  );
}
