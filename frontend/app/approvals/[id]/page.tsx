"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ActionRequest, Approval, ApproverCandidate, Principal, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function ApprovalDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const [approval, setApproval] = useState<Approval | null>(null);
  const [request, setRequest] = useState<ActionRequest | null>(null);
  const [principals, setPrincipals] = useState<Principal[]>([]);
  const [approvers, setApprovers] = useState<ApproverCandidate[]>([]);
  const [approverId, setApproverId] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(() => {
    params.then(({ id }) => api.approval(id))
      .then((approvalData) => {
        setApproval(approvalData);
        return Promise.all([
          api.actionRequest(approvalData.action_request_id).catch(() => null),
          api.principals().catch(() => [] as Principal[]),
          api.approvers(approvalData.id).catch(() => ({ approvers: [] as ApproverCandidate[] })),
        ]).then(([requestData, principalData, approverData]) => {
          setRequest(requestData);
          setPrincipals(principalData);
          setApprovers(approverData.approvers);
          if (approverData.approvers.length > 0) {
            setApproverId((current) => current || approverData.approvers[0].id);
          }
        });
      })
      .catch((reason: Error) => setError(reason.message));
  }, [params]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const principalName = useMemo(() => {
    const map = new Map(principals.map((p) => [p.id, p]));
    return (id?: string | null) => {
      if (!id) return "Unavailable";
      const match = map.get(id);
      return match ? match.name : id;
    };
  }, [principals]);

  const act = (operation: "approve" | "reject") => {
    if (!approval || !approverId) return;
    setError(null);
    setBusy(true);
    api[operation](approval.id, approverId)
      .then(async (updated) => {
        setApproval(updated);
        setRequest(await api.actionRequest(updated.action_request_id).catch(() => null));
        // Refetch approvals to surface authoritative terminal state and expiry.
        const approvals = await api.approvals().catch(() => []);
        const latest = approvals.find((item) => item.id === updated.id) ?? updated;
        setApproval(latest);
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setBusy(false));
  };

  if (!approval && !error) {
    return <RegistryShell title="Approval detail" eyebrow="Human review boundary"><StateMessage>Loading approval evidence...</StateMessage></RegistryShell>;
  }

  const amount = approval ? String(approval.parameters?.amount ?? "") : "";
  const currency = approval ? String(approval.parameters?.currency ?? "") : "";
  const executedInSandbox = request?.reason?.includes("executed via SandboxPaymentProvider") ?? false;
  const executionFailed = request?.reason?.includes("execution failed") ?? false;
  const requesterName = principalName(approval?.principal_id);
  const approvedBy = principalName(approval?.decided_by);

  const evaluatedFields = [
    ["Agent", approval?.agent_name],
    ["Principal", approval?.principal_id],
    ["Requester", requesterName],
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

      {approval && (
        <>
          <div className="mb-4 flex flex-wrap gap-2 text-sm">
            <Link href={`/action-requests/${approval.action_request_id}`} className="rounded border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-signal hover:border-signal">Open the action case file →</Link>
            <Link href={`/agents/${approval.agent_id}`} className="rounded border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-signal hover:border-signal">Agent: {approval.agent_name}</Link>
          </div>
          <div className="border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400">Approval status</p>
                <p className="mt-2 text-3xl font-semibold text-ink">{approval.status}</p>
                <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{approval.reason}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <StatusPill value={`${approval.risk_classification ?? "UNKNOWN"} · ${approval.risk_score ?? "--"}/100`} />
                <StatusPill value={approval.status} />
              </div>
            </div>

            <div className="mt-6 grid gap-4 border-t border-slate-100 pt-5 md:grid-cols-2">
              <div className="border border-slate-100 bg-slate-50 p-4">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Requester</p>
                <p className="mt-1 text-lg font-medium text-ink">{requesterName}</p>
                <p className="text-xs text-slate-500">The human principal who initiated the action request</p>
              </div>
              <div className="border border-signal/20 bg-emerald-50/60 p-4">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Approver</p>
                {approval.status === "PENDING" ? (
                  <select
                    value={approverId}
                    onChange={(event) => setApproverId(event.target.value)}
                    disabled={approvers.length === 0 || busy}
                    className="mt-1 w-full border border-slate-300 bg-white px-3 py-2 text-sm"
                    aria-label="Select approver"
                  >
                    {approvers.length === 0 && <option value="">No eligible approver</option>}
                    {approvers.map((candidate) => <option key={candidate.id} value={candidate.id}>{candidate.name}</option>)}
                  </select>
                ) : (
                  <p className="mt-1 text-lg font-medium text-ink">{approvedBy}</p>
                )}
                <p className="mt-1 text-xs text-slate-500">A different human than the requester (separation of duties)</p>
              </div>
            </div>

            {amount && currency && (
              <div className="mt-5 flex items-end justify-between border border-slate-200 bg-ink px-5 py-4 text-white">
                <div>
                  <p className="text-xs uppercase tracking-[0.15em] text-slate-400">Amount to authorize</p>
                  <p className="mt-1 text-3xl font-semibold tabular-nums">${Number(amount).toLocaleString("en-US", { minimumFractionDigits: 2 })} <span className="text-lg text-slate-300">{currency}</span></p>
                </div>
                <p className="text-xs font-medium text-amber-300">SANDBOX · NO REAL MONEY MOVEMENT</p>
              </div>
            )}
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
              <h2 className="font-semibold text-ink">Exact payload under review</h2>
              <p className="mt-2 text-xs text-slate-500">This payload is digest-bound to the approval; it cannot change after approval without detection.</p>
              <pre className="mt-4 overflow-auto bg-slate-50 p-4 text-xs text-slate-600">{JSON.stringify(approval.parameters, null, 2)}</pre>
            </section>
            <section className="border border-slate-200 bg-white p-6">
              <h2 className="font-semibold text-ink">Why approval is required</h2>
              <div className="mt-4 space-y-3">
                {approval.risk_factors.length === 0 && <p className="text-sm text-slate-500">Risk factors unavailable.</p>}
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
            <div className="mt-6 flex flex-wrap items-center gap-3">
              <button type="button" disabled={busy || approvers.length === 0} onClick={() => act("approve")} className="bg-signal px-5 py-3 text-sm font-medium text-white disabled:bg-slate-300">{busy ? "Processing…" : "APPROVE AS " + (principals.find((p) => p.id === approverId)?.name ?? "APPROVER")}</button>
              <button type="button" disabled={busy || approvers.length === 0} onClick={() => act("reject")} className="bg-red-700 px-5 py-3 text-sm font-medium text-white disabled:bg-slate-300">REJECT</button>
              {approvers.length === 0 && <p className="text-xs text-slate-500">No distinct, active human approver exists in this tenant yet.</p>}
            </div>
          )}

          {approval.status === "APPROVED" && (
            <div className="mt-6 border border-emerald-300 bg-emerald-50 p-6">
              <p className="text-2xl font-semibold text-emerald-800">AUTHORIZED BY {approvedBy}</p>
              <p className="mt-2 text-sm font-medium text-emerald-900">{executedInSandbox ? "Approved and EXECUTED IN SANDBOX." : executionFailed ? "Approved but sandbox execution failed." : "Approved."}</p>
              <p className="mt-1 text-xs text-amber-800">SANDBOX DEMONSTRATION — NO REAL MONEY MOVEMENT.</p>
            </div>
          )}
          {approval.status === "REJECTED" && (
            <div className="mt-6 border border-red-200 bg-red-50 p-6">
              <p className="text-2xl font-semibold text-red-800">BLOCKED — REJECTED BY {approvedBy}</p>
              <p className="mt-2 text-sm font-medium text-amber-800">NOT EXECUTED. No sandbox execution occurred.</p>
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
