"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ActionRequest, Approval, ApproverCandidate, Principal, api } from "@/lib/api";
import { RegistryShell, StateMessage } from "@/components/registry-shell";
import { Breadcrumbs } from "@/components/ui/Breadcrumbs";
import { Status } from "@/components/ui/Status";
import { Disclosure } from "@/components/ui/Disclosure";
import { formatDateTime, formatMoney, shortId } from "@/lib/format";

export default function ApprovalDetail({ params }: { params: Promise<{ id: string }> }) {
  const [approval, setApproval] = useState<Approval | null>(null);
  const [request, setRequest] = useState<ActionRequest | null>(null);
  const [principals, setPrincipals] = useState<Principal[]>([]);
  const [approvers, setApprovers] = useState<ApproverCandidate[]>([]);
  const [approverId, setApproverId] = useState<string>("");
  const [decisionReason, setDecisionReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(() => {
    params
      .then(({ id }) => api.approval(id))
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
          if (approverData.approvers.length > 0) setApproverId((current) => current || approverData.approvers[0].id);
        });
      })
      .catch((reason: Error) => setError(reason.message));
  }, [params]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const principalName = useMemo(() => {
    const map = new Map(principals.map((p) => [p.id, p.name]));
    return (id?: string | null, name?: string | null) => name ?? (id ? (map.get(id) ?? shortId(id)) : "Unavailable");
  }, [principals]);

  const act = (operation: "approve" | "reject") => {
    if (!approval || !approverId) return;
    if (!decisionReason.trim()) { setError("A decision reason is required before approving or rejecting this action."); return; }
    setError(null);
    setBusy(true);
    api[operation](approval.id, approverId, decisionReason.trim())
      .then(async (updated) => {
        setApproval(updated);
        setRequest(await api.actionRequest(updated.action_request_id).catch(() => null));
        const approvals = await api.approvals().catch(() => []);
        const latest = approvals.find((item) => item.id === updated.id) ?? updated;
        setApproval(latest);
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setBusy(false));
  };

  if (!approval && !error) {
    return (
      <RegistryShell>
        <StateMessage>Loading approval…</StateMessage>
      </RegistryShell>
    );
  }

  const requester = approval?.principal_id;
  const requesterName = principalName(approval?.principal_id, approval?.principal_name);
  const approvedBy = principalName(approval?.decided_by);
  const rawAmount = approval?.parameters?.amount;
  const amountLine =
    typeof rawAmount === "number" || typeof rawAmount === "string"
      ? formatMoney(rawAmount as number | string, String(approval?.parameters?.currency ?? "USD"))
      : null;
  const executionStatus = approval?.execution_status ?? request?.execution_status ?? "NOT_EXECUTED";

  return (
    <RegistryShell>
      <div className="mb-6">
        <Breadcrumbs
          items={[
            { label: "Control center", href: "/" },
            { label: "Approvals", href: "/approvals" },
            { label: "Approval review" },
          ]}
        />
      </div>

      {error && <StateMessage tone="error">Approval action failed. {error}</StateMessage>}

      {approval && (
        <div className="space-y-6">
          {/* Question header */}
          <header className="rounded-card border border-hairline bg-surface p-6 lg:p-8">
            <div className="flex flex-wrap items-start justify-between gap-5">
              <div className="min-w-0">
                <p className="eyebrow text-inkFaint">Approval review</p>
                <h1 className="mt-1.5 text-2xl font-semibold tracking-tight text-ink lg:text-3xl">
                  {approval.status === "PENDING" ? "Do you authorize this specific action?" : "Approval decided"}
                </h1>
                <div className="mt-4 flex flex-wrap items-center gap-2.5">
                  <span className="text-sm font-medium text-inkSubtle">Status</span>
                  <Status value={approval.status} />
                  <span className="mx-1 text-inkFaint">·</span>
                  <span className="text-sm font-medium text-inkSubtle">Execution</span>
                  <Status value={executionStatus} />
                </div>
                <p className="mt-3 max-w-2xl text-[15px] leading-7 text-inkSubtle">
                  {approval.reason}
                </p>
              </div>
              {amountLine && approval.status === "PENDING" && (
                <div className="shrink-0 rounded-card border border-hairline bg-surfaceMuted px-5 py-4">
                  <p className="text-[11px] uppercase tracking-wide text-inkFaint">Amount to authorize</p>
                  <p className="tnum mt-1 text-3xl font-semibold tracking-tight text-ink">{amountLine}</p>
                  <p className="mt-1 text-xs text-inkSubtle">digest-bound · any change blocks execution</p>
                </div>
              )}
            </div>
          </header>

          {approval.action_context && (
            <section className="rounded-card border border-hairline bg-surface p-6">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="eyebrow text-inkFaint">Business intent & recovery</p>
                  <p className="mt-2 text-[15px] font-semibold text-ink">{approval.action_context.summary}</p>
                </div>
                <Status value={approval.action_context.recovery_class} />
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <p className="text-[13px] leading-6 text-inkSubtle"><span className="font-medium text-ink">Target system:</span> {approval.action_context.target_system}</p>
                <p className="text-[13px] leading-6 text-inkSubtle"><span className="font-medium text-ink">Recovery:</span> {approval.action_context.recovery_plan}</p>
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="rounded-card border border-hairline bg-surfaceMuted p-4">
                  <p className="text-[11px] uppercase tracking-wide text-inkFaint">Current state</p>
                  <pre className="mt-2 overflow-x-auto text-xs leading-5 text-inkMuted">{JSON.stringify(approval.action_context.before, null, 2)}</pre>
                </div>
                <div className="rounded-card border border-hairline bg-surfaceMuted p-4">
                  <p className="text-[11px] uppercase tracking-wide text-inkFaint">Proposed state</p>
                  <pre className="mt-2 overflow-x-auto text-xs leading-5 text-inkMuted">{JSON.stringify(approval.action_context.proposed_change, null, 2)}</pre>
                </div>
              </div>
              <p className="mt-4 text-xs leading-5 text-inkSubtle">These values are included in the digest-bound action payload. Any change after this approval request was created blocks execution.</p>
            </section>
          )}

          {/* WHO / WHAT / WHY / RISK */}
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <section className="rounded-card border border-hairline bg-surface p-5">
              <p className="eyebrow text-inkFaint">Who is acting</p>
              <p className="mt-3 text-[15px] font-semibold text-ink">{approval.agent_name}</p>
              <p className="mt-1 text-[13px] leading-5 text-inkSubtle">
                Acting for <span className="font-medium text-inkMuted">{requesterName}</span>
              </p>
            </section>
            <section className="rounded-card border border-hairline bg-surface p-5">
              <p className="eyebrow text-inkFaint">What will happen</p>
              <p className="mt-3 text-[15px] font-semibold text-ink">{approval.action_name}</p>
              <p className="mt-1 text-[13px] text-inkSubtle">
                via {approval.tool_name} · <span className="font-mono">{approval.resource_type}</span>
              </p>
            </section>
            <section className="rounded-card border border-hairline bg-surface p-5">
              <p className="eyebrow text-inkFaint">Why approval is required</p>
              <div className="mt-3">
                <Status value={approval.risk_classification ?? "LOW"} />
                {approval.risk_score !== null && approval.risk_score !== undefined && (
                  <span className="tnum ml-2 text-sm font-medium text-inkMuted">{approval.risk_score}/100</span>
                )}
              </div>
              <p className="mt-2 text-[13px] leading-5 text-inkSubtle">High-risk actions require a distinct human approver (separation of duties).</p>
            </section>
            <section className="rounded-card border border-hairline bg-surface p-5">
              <p className="eyebrow text-inkFaint">Resource</p>
              <p className="mt-3 break-all text-[15px] font-semibold text-ink">{approval.resource_type}</p>
              <p className="mt-1 break-all font-mono text-xs text-inkSubtle">{approval.resource_key}</p>
            </section>
          </div>

          {/* Payload & risk evidence */}
          <div className="grid gap-4 lg:grid-cols-2">
            <Disclosure title="Exact payload under review" defaultOpen>
              <div className="overflow-x-auto rounded-card border border-hairline bg-surfaceSunken p-3">
                <pre className="text-xs leading-5 text-inkMuted">{JSON.stringify(approval.parameters, null, 2)}</pre>
              </div>
            </Disclosure>
            <Disclosure title={`Why this is risky (${approval.risk_factors.length} factors)`}>
              {approval.risk_factors.length === 0 ? (
                <p className="text-inkSubtle">No risk factors were recorded.</p>
              ) : (
                <ul className="divide-y divide-hairline">
                  {approval.risk_factors.map((factor) => (
                    <li key={factor.code} className="flex items-baseline justify-between gap-4 py-2.5">
                      <div>
                        <p className="font-medium text-ink">{factor.code}</p>
                        <p className="mt-0.5 text-[13px] text-inkSubtle">{factor.explanation}</p>
                      </div>
                      <span className="tnum shrink-0 text-sm font-semibold text-signal">+{factor.contribution}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Disclosure>
          </div>

          {/* Decision */}
          {approval.status === "PENDING" && (
            <section className="rounded-card border border-hairline bg-surface p-6">
              <div className="flex flex-wrap items-start justify-between gap-6">
                <div className="max-w-xl">
                  <p className="text-[15px] font-semibold text-ink">Make your decision</p>
                  <p className="mt-1.5 text-[13px] leading-6 text-inkSubtle">
                    Approving authorizes execution of this exact payload in the sandbox only. Any modification after approval is detected and blocks
                    execution automatically. The requester can never approve their own request.
                  </p>
                </div>
                <div className="w-full max-w-xs">
                  <label className="text-[11px] font-semibold uppercase tracking-wide text-inkFaint" htmlFor="approver-select">
                    Approve as
                  </label>
                  <select
                    id="approver-select"
                    value={approverId}
                    onChange={(event) => setApproverId(event.target.value)}
                    disabled={approvers.length === 0 || busy}
                    className="mt-1.5 h-9 w-full rounded-control border border-hairlineStrong bg-surface px-3 text-sm text-ink focus-visible:outline-2"
                  >
                    {approvers.length === 0 && <option value="">No eligible approver</option>}
                    {approvers.map((candidate) => (
                      <option key={candidate.id} value={candidate.id}>
                        {candidate.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-hairline pt-5">
                <label className="w-full text-[11px] font-semibold uppercase tracking-wide text-inkFaint" htmlFor="approval-decision-reason">
                  Decision reason <span className="text-danger">required</span>
                  <textarea id="approval-decision-reason" value={decisionReason} onChange={(event) => setDecisionReason(event.target.value)} disabled={busy} rows={3} placeholder="Explain why this exact action should be approved or rejected." className="mt-1.5 w-full rounded-control border border-hairlineStrong bg-surface px-3 py-2 text-sm normal-case tracking-normal text-ink outline-none placeholder:text-inkFaint focus-visible:ring-2 focus-visible:ring-focusRing" />
                </label>
                <button
                  type="button"
                  onClick={() => act("reject")}
                  disabled={busy || approvers.length === 0 || !decisionReason.trim()}
                  className="min-h-[40px] rounded-control border border-dangerBorder bg-dangerBg px-5 text-sm font-semibold text-danger transition-colors hover:bg-danger hover:text-white disabled:opacity-40"
                >
                  Reject
                </button>
                <button
                  type="button"
                  onClick={() => act("approve")}
                  disabled={busy || approvers.length === 0 || !decisionReason.trim()}
                  className="min-h-[40px] rounded-control bg-signal px-6 text-sm font-semibold text-white transition-colors hover:bg-signalHover disabled:opacity-40"
                >
                  {busy ? "Processing…" : `Approve as ${approvers.find((a) => a.id === approverId)?.name ?? "approver"}`}
                </button>
                {approvers.length === 0 && <p className="text-xs text-inkSubtle">No distinct, active human approver exists in this tenant yet.</p>}
              </div>
            </section>
          )}

          {/* Decided state */}
          {approval.status !== "PENDING" && (
            <section className="rounded-card border border-hairline bg-surface p-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="text-[15px] font-semibold text-ink">
                    {approval.status === "APPROVED" && "Authorized"}
                    {approval.status === "REJECTED" && "Rejected"}
                    {approval.status === "EXPIRED" && "Expired before decision"}
                    {approval.status === "CANCELLED" && "Cancelled"}
                  </p>
                  <p className="mt-1 text-[13px] text-inkSubtle">
                    {approval.decided_at ? `Decided by ${approvedBy} · ${formatDateTime(approval.decided_at)}` : "No decision was recorded"}
                    {executionStatus === "EXECUTED" ? " · Executed in the sandbox provider." : executionStatus === "FAILED" ? " · Execution failed in the sandbox provider." : " · No execution recorded."}
                  </p>
                  {approval.decision_reason && <p className="mt-3 rounded-control border border-hairline bg-surfaceMuted px-3 py-2 text-sm leading-6 text-inkSubtle"><span className="font-semibold text-ink">Recorded decision reason:</span> {approval.decision_reason}</p>}
                </div>
                <div className="flex items-center gap-2.5">
                  <Status value={approval.status} />
                  <Status value={executionStatus} />
                </div>
              </div>
            </section>
          )}

          <div className="flex flex-wrap items-center gap-2">
            <Link href={`/action-requests/${approval.action_request_id}`} className="text-[13px] font-semibold text-signal hover:text-signalHover">
              Open the action case file →
            </Link>
            <span className="mx-1 text-inkFaint">·</span>
            <Link href={`/agents/${approval.agent_id}`} className="text-[13px] font-medium text-inkSubtle hover:text-ink">
              Agent: {approval.agent_name}
            </Link>
            <span className="text-xs text-inkFaint">reference {shortId(requester)}</span>
          </div>
        </div>
      )}
    </RegistryShell>
  );
}
