"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ActionRequest, Agent, Approval, api } from "@/lib/api";
import { AppNav } from "@/components/app-nav";
import { IdentityBar } from "@/components/identity-bar";
import { StateMessage, StatusPill } from "@/components/registry-shell";

const pipeline = [
  ["01", "AGENT", "Identity established", "Deterministic"],
  ["02", "ACTION REQUEST", "Intent captured", "Server boundary"],
  ["03", "RISK ENGINE", "Context assessed", "Deterministic"],
  ["04", "POLICY ENGINE", "Authority evaluated", "Deterministic"],
  ["05", "HUMAN APPROVAL", "Escalation when required", "Human-controlled"],
  ["06", "AUTHORIZATION", "Decision enforced", "Server-side"],
  ["07", "EXECUTION", "External action boundary", "Disabled"],
];

function decisionLabel(request: ActionRequest) {
  if (request.decision === "ALLOW") return "AUTHORIZED";
  if (request.decision === "REQUIRE_APPROVAL") return "PENDING_APPROVAL";
  if (request.decision === "DENY") return "BLOCKED";
  return request.status;
}

function decisionTone(value: string) {
  if (value === "AUTHORIZED") return "border-emerald-200 bg-emerald-50 text-emerald-800";
  if (value === "BLOCKED") return "border-red-200 bg-red-50 text-red-800";
  if (value === "PENDING_APPROVAL") return "border-amber-200 bg-amber-50 text-amber-800";
  return "border-slate-200 bg-slate-50 text-slate-600";
}

export default function Home() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [requests, setRequests] = useState<ActionRequest[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.agents(), api.actionRequests(), api.approvals()])
      .then(([agentData, requestData, approvalData]) => {
        setAgents(agentData);
        setRequests(requestData);
        setApprovals(approvalData);
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, []);

  const authorized = requests.filter((item) => item.decision === "ALLOW").length;
  const blocked = requests.filter((item) => item.decision === "DENY").length;
  const pending = requests.filter((item) => item.decision === "REQUIRE_APPROVAL").length;
  const highRisk = requests.filter((item) => item.risk_classification === "HIGH" || item.risk_classification === "CRITICAL").length;
  const decidedApprovals = approvals.filter((item) => item.status !== "PENDING").length;
  const approvedApprovals = approvals.filter((item) => item.status === "APPROVED").length;
  const executedCount = requests.filter((item) => (item.reason ?? "").includes("executed via SandboxPaymentProvider")).length;
  const failedCount = requests.filter((item) => (item.reason ?? "").includes("failed")).length;
  const deniedOrRejected = requests.filter((item) => item.decision === "DENY").length;
  const approvalRate = decidedApprovals ? `${Math.round((approvedApprovals / decidedApprovals) * 100)}%` : "--";
  const riskCounts = ["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((level) => ({ level, count: requests.filter((item) => item.risk_classification === level).length }));

  return (
    <main className="min-h-screen bg-[#f4f6f5] lg:flex">
      <aside className="border-b border-slate-200 bg-ink px-6 py-6 text-slate-300 lg:min-h-screen lg:w-64 lg:border-b-0 lg:border-r">
        <AppNav />
      </aside>
      <section className="min-w-0 flex-1 px-5 py-7 lg:px-10 lg:py-9">
        <header className="mb-7 flex flex-wrap items-end justify-between gap-5 border-b border-slate-200 pb-7">
          <div><p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-signal">AgentOS control center</p><h1 className="text-3xl font-semibold tracking-tight text-ink lg:text-4xl">AI Action Governance &amp; Control Plane</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">Before an AI agent can perform a consequential action, AgentOS decides whether it is authorized, evaluates its risk, obtains human approval when required, revalidates it, executes it in a sandbox, and records the evidence.</p></div>
          <div className="flex flex-col items-end gap-2">
            <IdentityBar />
            <Link href="/demo" className="bg-signal px-4 py-3 text-sm font-medium text-white hover:bg-signal/90">Run Treasury Governance Demo</Link>
            <div className="border border-amber-300 bg-white px-4 py-2"><p className="text-[10px] font-bold uppercase tracking-[0.16em] text-amber-600">Execution boundary</p><p className="mt-0.5 text-base font-semibold text-amber-800">SANDBOX ONLY</p></div>
          </div>
        </header>

        {loading && <StateMessage>Loading control-plane telemetry...</StateMessage>}
        {error && <StateMessage tone="error">Unable to load control-plane data. Confirm the API is running. {error}</StateMessage>}
        {!loading && !error && <>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
            {[["Total action requests", requests.length, "all intercepted requests"], ["Authorized", authorized, "policy allowed"], ["Blocked", blocked, "policy denied"], ["Pending approval", pending, "human review"], ["High / critical risk", highRisk, "server risk evidence"], ["Approval rate", approvalRate, "of decided approvals"]].map(([label, value, note]) => <div key={label as string} className="border border-slate-200 bg-white p-4"><p className="text-xs font-medium text-slate-500">{label}</p><p className="mt-3 text-3xl font-semibold text-ink">{value}</p><p className="mt-2 text-[11px] text-slate-400">{note}</p></div>)}
          </div>

          <section className="mt-7 border border-slate-200 bg-ink p-6 text-white lg:p-7"><div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-300">Governance pipeline</p><h2 className="mt-2 text-2xl font-semibold">Every consequential action passes through control.</h2></div><p className="text-xs text-slate-400">No model output is authorization.</p></div><div className="mt-8 grid gap-2 md:grid-cols-7">{pipeline.map(([number, label, description, state], index) => <div key={label} className="relative border border-white/10 bg-white/[0.04] p-4"><p className="text-[10px] font-bold tracking-[0.16em] text-emerald-300">{number}</p><p className="mt-5 text-xs font-semibold tracking-wide">{label}</p><p className="mt-2 min-h-8 text-[11px] leading-4 text-slate-400">{description}</p><p className={`mt-4 text-[10px] font-medium ${state === "Disabled" ? "text-red-300" : "text-slate-300"}`}>{state}</p>{index < pipeline.length - 1 && <span className="absolute -right-2 top-1/2 z-10 hidden text-emerald-300 md:block">→</span>}</div>)}</div></section>

          <div className="mt-7 grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
            <section className="border border-slate-200 bg-white p-6"><div className="flex items-center justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-signal">Risk overview</p><h2 className="mt-1 text-lg font-semibold text-ink">Observed request distribution</h2></div><span className="text-xs text-slate-400">server-returned evidence</span></div><div className="mt-7 grid gap-3 sm:grid-cols-4">{riskCounts.map(({ level, count }) => <div key={level} className={`border p-4 ${level === "HIGH" || level === "CRITICAL" ? "border-red-200 bg-red-50" : "border-slate-200 bg-slate-50"}`}><p className="text-xs font-semibold tracking-wide text-slate-500">{level}</p><p className="mt-3 text-3xl font-semibold text-ink">{count}</p><div className="mt-4 h-1.5 bg-slate-200"><div className={`h-full ${level === "CRITICAL" ? "bg-red-700" : level === "HIGH" ? "bg-orange-500" : "bg-signal"}`} style={{ width: `${requests.length ? Math.max((count / requests.length) * 100, count ? 8 : 0) : 0}%` }} /></div></div>)}</div></section>
            <section className="border border-slate-200 bg-white p-6"><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-signal">System state</p><h2 className="mt-1 text-lg font-semibold text-ink">Control posture</h2></div><Link href="/observability" className="text-xs font-semibold text-signal hover:underline">Open observability →</Link></div><div className="mt-6 space-y-4 text-sm"><p className="flex justify-between border-b border-slate-100 pb-3"><span className="text-slate-500">Registered agents</span><strong>{agents.length}</strong></p><p className="flex justify-between border-b border-slate-100 pb-3"><span className="text-slate-500">Successful executions</span><strong>{executedCount}</strong></p><p className="flex justify-between border-b border-slate-100 pb-3"><span className="text-slate-500">Blocked / rejected actions</span><strong>{deniedOrRejected}</strong></p><p className="flex justify-between border-b border-slate-100 pb-3"><span className="text-slate-500">Execution failures</span><strong>{failedCount}</strong></p><p className="flex justify-between border-b border-slate-100 pb-3"><span className="text-slate-500">Risk engine</span><strong className="text-signal">Deterministic</strong></p><p className="flex justify-between border-b border-slate-100 pb-3"><span className="text-slate-500">Policy engine</span><strong className="text-signal">Deterministic</strong></p><p className="flex justify-between"><span className="text-slate-500">Human approval</span><strong className="text-amber-700">Controlled</strong></p></div></section>
          </div>

          <div className="mt-7 grid gap-6 xl:grid-cols-[1.4fr_0.8fr]">
            <section className="border border-slate-200 bg-white p-6"><div className="flex items-end justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-signal">Recent actions</p><h2 className="mt-1 text-lg font-semibold text-ink">Latest intercepted requests</h2></div><Link href="/action-requests" className="text-xs font-semibold text-signal hover:underline">View all →</Link></div>{requests.length === 0 ? <div className="mt-6"><StateMessage>No action requests recorded yet.</StateMessage></div> : <div className="mt-5 overflow-x-auto"><div className="min-w-[680px]"><div className="grid grid-cols-[1.1fr_1fr_0.8fr_0.8fr_0.8fr] gap-3 border-b border-slate-200 pb-3 text-[10px] font-bold uppercase tracking-wide text-slate-400"><span>Agent / action</span><span>Tool / resource</span><span>Risk</span><span>Decision</span><span>Time</span></div>{requests.slice(0, 6).map((request) => { const decision = decisionLabel(request); return <Link href={`/action-requests/${request.id}`} key={request.id} className="grid grid-cols-[1.1fr_1fr_0.8fr_0.8fr_0.8fr] gap-3 border-b border-slate-100 py-4 text-sm last:border-0 hover:bg-slate-50"><span><strong className="block font-medium text-ink">{request.agent_name}</strong><small className="text-xs text-slate-400">{request.action_name}</small></span><span className="text-slate-500">{request.tool_name}<small className="block text-xs text-slate-400">{request.resource_key}</small></span><span><StatusPill value={`${request.risk_classification ?? "--"} · ${request.risk_score ?? "--"}`} /></span><span><span className={`inline-block rounded-full border px-2 py-1 text-[10px] font-semibold ${decisionTone(decision)}`}>{decision}</span></span><span className="text-xs text-slate-400">{new Date(request.requested_at).toLocaleString()}</span></Link>; })}</div></div>}</section>
            <section className="border border-slate-200 bg-white p-6"><div className="flex items-end justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-signal">Approval queue</p><h2 className="mt-1 text-lg font-semibold text-ink">Human review required</h2></div><Link href="/approvals" className="text-xs font-semibold text-signal hover:underline">View queue →</Link></div>{approvals.filter((item) => item.status === "PENDING").length === 0 ? <div className="mt-6"><StateMessage>No pending approvals.</StateMessage></div> : <div className="mt-5 space-y-3">{approvals.filter((item) => item.status === "PENDING").slice(0, 4).map((approval) => <Link href={`/approvals/${approval.id}`} key={approval.id} className="block border border-amber-100 bg-amber-50/50 p-4 hover:border-amber-300"><div className="flex justify-between gap-3"><strong className="text-sm text-ink">{approval.agent_name}</strong><StatusPill value={`${approval.risk_classification} · ${approval.risk_score}`} /></div><p className="mt-2 text-xs text-slate-600">{approval.action_name} · {approval.reason}</p><p className="mt-3 text-[11px] text-amber-800">Expires {new Date(approval.expires_at).toLocaleString()}</p></Link>)}</div>}</section>
          </div>
        </>}
      </section>
    </main>
  );
}
