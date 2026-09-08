"use client";

import { useEffect, useState } from "react";

import { ActionRequest, Approval, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function ActionRequestDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const [request, setRequest] = useState<ActionRequest | null>(null);
  const [approval, setApproval] = useState<Approval | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    params.then(({ id }) => {
      Promise.all([api.actionRequest(id), api.approvals()])
        .then(([requestData, approvalData]) => {
          setRequest(requestData);
          setApproval(approvalData.find((item) => item.action_request_id === id) ?? null);
        })
        .catch((reason: Error) => setError(reason.message));
    });
  }, [params]);

  if (!request) {
    return <RegistryShell title="Action request detail" eyebrow="Decision evidence">{error ? <StateMessage tone="error">Unable to load action request. {error}</StateMessage> : <StateMessage>Loading request evidence...</StateMessage>}</RegistryShell>;
  }

  const finalState = approval?.status === "APPROVED" ? "AUTHORIZED FOR EXECUTION" : approval?.status === "REJECTED" || approval?.status === "EXPIRED" || approval?.status === "CANCELLED" ? "BLOCKED" : request.decision === "REQUIRE_APPROVAL" ? "PENDING APPROVAL" : request.decision === "ALLOW" ? "AUTHORIZED" : "BLOCKED";
  const executedInSandbox = request.reason?.includes("executed via SandboxPaymentProvider") ?? false;
  const executionFailed = request.reason?.includes("execution failed") ?? false;
  const executionLine = executedInSandbox ? "EXECUTED IN SANDBOX" : executionFailed ? "SANDBOX EXECUTION FAILED" : "NOT EXECUTED";
  const timeline = [
    ["REQUESTED", new Date(request.requested_at).toLocaleString(), true],
    ["RISK EVALUATED", request.risk_classification ? `${request.risk_classification} · ${request.risk_score}/100 · ${request.risk_engine_version}` : "Risk evidence unavailable", Boolean(request.risk_classification)],
    ["POLICY EVALUATED", request.reason_code ? `${request.reason_code} · ${request.reason}` : "Policy evidence unavailable", Boolean(request.reason_code)],
    [request.decision === "REQUIRE_APPROVAL" ? "APPROVAL REQUIRED" : request.decision === "ALLOW" ? "AUTHORIZED" : "BLOCKED", request.decision ?? request.status, Boolean(request.decision)],
    ["HUMAN DECISION", approval ? `${approval.status}${approval.decided_at ? ` · ${new Date(approval.decided_at).toLocaleString()}` : ""}` : "Not applicable or unavailable", Boolean(approval)],
    ["FINAL AUTHORIZATION", finalState, true],
    ["SANDBOX EXECUTION", executionLine, executedInSandbox || executionFailed],
  ];

  return (
    <RegistryShell title="Action request detail" eyebrow="Decision evidence">
      <div className="flex flex-wrap items-start justify-between gap-4 border border-slate-200 bg-white p-6">
        <div><p className="text-xs uppercase tracking-wide text-slate-400">Final state</p><p className="mt-2 text-3xl font-semibold text-ink">{finalState}</p><p className="mt-3 text-sm text-slate-600">{request.reason ?? "No decision reason recorded."}</p></div>
        <div className="flex flex-wrap gap-2">{request.reason_code && <StatusPill value={request.reason_code} />}{request.risk_classification && <StatusPill value={`${request.risk_classification} · ${request.risk_score}/100`} />}</div>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[0.72fr_1.28fr]">
        <section className="border border-slate-200 bg-ink p-6 text-white"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-300">Request lifecycle</p><div className="mt-6 space-y-1">{timeline.map(([label, detail, available], index) => <div key={label as string} className="relative flex gap-4 pb-6"><div className={`relative z-10 mt-0.5 h-3 w-3 shrink-0 rounded-full border ${available ? "border-emerald-300 bg-emerald-300" : "border-slate-600 bg-ink"}`} />{index < timeline.length - 1 && <span className="absolute left-[5px] top-3 h-full w-px bg-white/15" />}<div><p className={`text-xs font-semibold tracking-wide ${available ? "text-white" : "text-slate-500"}`}>{label}</p><p className="mt-1 text-xs leading-5 text-slate-400">{detail}</p></div></div>)}</div></section>
        <div><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[["Agent", request.agent_name], ["Principal", request.principal_id], ["Tool", request.tool_name], ["Action", request.action_name], ["Resource", `${request.resource_type} / ${request.resource_key}`], ["Request status", request.status], ["Requested", new Date(request.requested_at).toLocaleString()], ["Decided", request.decided_at ? new Date(request.decided_at).toLocaleString() : "Unavailable"]].map(([label, value]) => <div key={label} className="border border-slate-200 bg-white p-4"><p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">{label}</p><p className="mt-2 break-all text-sm text-ink">{value}</p></div>)}</div><div className="mt-4 grid gap-4 lg:grid-cols-2"><section className="border border-slate-200 bg-white p-5"><h2 className="font-semibold text-ink">Request parameters</h2><pre className="mt-4 overflow-auto bg-slate-50 p-4 text-xs text-slate-600">{JSON.stringify(request.parameters, null, 2)}</pre></section><section className="border border-slate-200 bg-white p-5"><h2 className="font-semibold text-ink">Risk factors</h2><div className="mt-4 space-y-3">{request.risk_factors.length === 0 ? <p className="text-sm text-slate-500">Risk factors unavailable.</p> : request.risk_factors.map((factor) => <div key={factor.code} className="flex justify-between gap-4 border-b border-slate-100 pb-3 text-sm"><div><p className="font-medium text-ink">{factor.code}</p><p className="mt-1 text-xs text-slate-500">{factor.explanation}</p></div><span className="font-mono text-signal">+{factor.contribution}</span></div>)}</div></section></div></div>
      </div>
      <p className="mt-6 border border-amber-200 bg-amber-50 p-4 text-xs font-semibold text-amber-800">SANDBOX DEMONSTRATION — NO REAL MONEY MOVEMENT. Authorized executions run in the sandbox provider only.</p>
    </RegistryShell>
  );
}
