"use client";

import { useEffect, useState } from "react";

import { Approval, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function ApprovalDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const [approval, setApproval] = useState<Approval | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    params.then(({ id }) => {
      api.approval(id).then(setApproval).catch((reason: Error) => setError(reason.message));
    });
  }, [params]);

  const act = (operation: "approve" | "reject" | "cancel") => {
    if (!approval) return;
    setBusy(true);
    api[operation](approval.id, approval.principal_id)
      .then(setApproval)
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setBusy(false));
  };

  const evaluatedFields = [
    ["Agent", approval?.agent_name],
    ["Principal", approval?.principal_id],
    ["Tool", approval?.tool_name],
    ["Action", approval?.action_name],
    ["Resource", approval ? `${approval.resource_type} / ${approval.resource_key}` : ""],
    ["Requested", approval ? new Date(approval.requested_at).toLocaleString() : ""],
    ["Expires", approval ? new Date(approval.expires_at).toLocaleString() : ""],
    ["Policy", approval ? `${approval.policy_id ?? "none"} v${approval.policy_version ?? "--"}` : ""],
  ];

  return (
    <RegistryShell title="Approval detail" eyebrow="Human review boundary">
      {error && <StateMessage tone="error">Approval action failed. {error}</StateMessage>}
      {!approval && !error && <StateMessage>Loading approval evidence...</StateMessage>}
      {approval && (
        <>
          <div className="flex flex-wrap items-start justify-between gap-4 border border-slate-200 bg-white p-6">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-400">Approval status</p>
              <p className="mt-2 text-3xl font-semibold text-ink">{approval.status}</p>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">{approval.reason}</p>
            </div>
            <div className="flex gap-2">
              <StatusPill value={`${approval.risk_classification ?? "UNKNOWN"} · ${approval.risk_score ?? "--"}`} />
              <StatusPill value={approval.status} />
            </div>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {evaluatedFields.map(([label, value]) => (
              <div key={label} className="border border-slate-200 bg-white p-5">
                <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
                <p className="mt-2 break-all text-sm text-ink">{value}</p>
              </div>
            ))}
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <section className="border border-slate-200 bg-white p-6">
              <h2 className="font-semibold text-ink">Evaluated request</h2>
              <pre className="mt-4 overflow-auto bg-slate-50 p-4 text-xs text-slate-600">
                {JSON.stringify(approval.parameters, null, 2)}
              </pre>
            </section>
            <section className="border border-slate-200 bg-white p-6">
              <h2 className="font-semibold text-ink">Risk factors</h2>
              <div className="mt-4 space-y-3">
                {approval.risk_factors.map((factor) => (
                  <div key={factor.code} className="flex justify-between gap-4 border-b border-slate-100 pb-3 text-sm">
                    <div>
                      <p className="font-medium text-ink">{factor.code}</p>
                      <p className="mt-1 text-xs text-slate-500">{factor.explanation}</p>
                    </div>
                    <span className="font-mono text-signal">+{factor.contribution}</span>
                  </div>
                ))}
              </div>
            </section>
          </div>

          {approval.status === "PENDING" && (
            <div className="mt-6 flex flex-wrap gap-3">
              <button type="button" disabled={busy} onClick={() => act("approve")} className="bg-signal px-5 py-3 text-sm font-medium text-white disabled:bg-slate-300">APPROVE</button>
              <button type="button" disabled={busy} onClick={() => act("reject")} className="bg-red-700 px-5 py-3 text-sm font-medium text-white disabled:bg-slate-300">REJECT</button>
              <button type="button" disabled={busy} onClick={() => act("cancel")} className="border border-slate-300 px-5 py-3 text-sm font-medium text-slate-600 disabled:text-slate-300">CANCEL</button>
            </div>
          )}

          {approval.status === "APPROVED" && (
            <div className="mt-6 border border-signal/30 bg-emerald-50 p-6">
              <p className="text-2xl font-semibold text-signal">AUTHORIZED FOR EXECUTION</p>
              <p className="mt-2 text-sm font-medium text-amber-800">NOT EXECUTED. External execution is disabled.</p>
            </div>
          )}
          {approval.status === "REJECTED" && (
            <div className="mt-6 border border-red-200 bg-red-50 p-6">
              <p className="text-2xl font-semibold text-red-800">BLOCKED</p>
              <p className="mt-2 text-sm font-medium text-amber-800">NOT EXECUTED.</p>
            </div>
          )}
          {approval.status === "EXPIRED" && (
            <div className="mt-6 border border-amber-200 bg-amber-50 p-6">
              <p className="text-2xl font-semibold text-amber-800">EXPIRED</p>
              <p className="mt-2 text-sm font-medium text-red-800">BLOCKED. NOT EXECUTED.</p>
            </div>
          )}
          {approval.status === "CANCELLED" && (
            <div className="mt-6 border border-slate-200 bg-slate-50 p-6">
              <p className="text-2xl font-semibold text-slate-700">CANCELLED</p>
              <p className="mt-2 text-sm font-medium text-amber-800">NOT EXECUTED.</p>
            </div>
          )}
        </>
      )}
    </RegistryShell>
  );
}
