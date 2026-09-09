"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ActionRequest, Approval, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function IntelligencePage() {
  const [requests, setRequests] = useState<ActionRequest[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.actionRequests().catch(() => [] as ActionRequest[]), api.approvals().catch(() => [] as Approval[])])
      .then(([reqData, apprData]) => { setRequests(reqData); setApprovals(apprData); })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, []);

  const riskCounts = ["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((level) => ({ level, count: requests.filter((r) => r.risk_classification === level).length }));
  const executed = requests.filter((r) => (r.reason ?? "").includes("executed via SandboxPaymentProvider")).length;
  const failedExec = requests.filter((r) => (r.reason ?? "").includes("failed")).length;
  const policyDenied = requests.filter((r) => (r.reason_code ?? "").startsWith("POLICY_DENY") || (r.reason_code ?? "").startsWith("DEFAULT_DENY")).length;
  const approvalRequired = requests.filter((r) => r.decision === "REQUIRE_APPROVAL" || (r.reason_code ?? "").startsWith("HIGH_RISK_APPROVAL")).length;
  const pendingApprovals = approvals.filter((a) => a.status === "PENDING").length;
  const tamper = requests.filter((r) => (r.reason_code ?? "").startsWith("SECURITY_PAYLOAD_TAMPERED")).length;
  const toctou = requests.filter((r) => (r.reason_code ?? "").startsWith("SECURITY_TOCTOU_REVALIDATION_FAILED")).length;
  const sod = requests.filter((r) => (r.reason_code ?? "").startsWith("SECURITY_SEPARATION_OF_DUTIES_VIOLATION")).length;

  const signals: Array<[string, number, string]> = [
    ["Executed in sandbox", executed, "successful governed executions (real ledger-backed)"],
    ["Blocked by policy", policyDenied, "actions denied by policy evaluation"],
    ["Require approval", approvalRequired, "high-risk actions that needed a human"],
    ["Awaiting approval", pendingApprovals, "open approvals in the queue"],
    ["Failed executions", failedExec, "executions that did not succeed"],
    ["Tamper attempts", tamper, "approved-payload integrity violations"],
    ["Revoked-delegation blocks", toctou, "TOCTOU revalidation failures"],
    ["SoD violations", sod, "self-approval attempts rejected"],
  ];

  return (
    <RegistryShell title="Risk & intelligence" eyebrow="Security & intelligence">
      <p className="mb-6 max-w-3xl text-sm leading-6 text-slate-500">
        Deterministic governance signals drawn from real governed actions. Risk and threat telemetry here is explainable and audit-backed — there are no invented scores.
      </p>
      {loading && <StateMessage>Loading governance telemetry…</StateMessage>}
      {error && <StateMessage tone="error">Unable to load telemetry. {error}</StateMessage>}
      {!loading && requests.length === 0 && <StateMessage>No governed actions yet. Run the Treasury Governance Demo or submit an action to populate risk and threat signals.</StateMessage>}
      {requests.length > 0 && (
        <>
          <section className="border border-slate-200 bg-white p-6">
            <h2 className="font-semibold text-ink">Risk exposure</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-4">
              {riskCounts.map(({ level, count }) => (
                <div key={level} className={`border p-4 ${level === "HIGH" || level === "CRITICAL" ? "border-red-200 bg-red-50" : "border-slate-200 bg-slate-50"}`}>
                  <p className="text-xs font-semibold text-slate-500">{level}</p>
                  <p className="mt-2 text-3xl font-semibold text-ink">{count}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="mt-6 border border-slate-200 bg-white p-6">
            <h2 className="font-semibold text-ink">Governance signals</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {signals.map(([label, value, note]) => (
                <div key={label} className="border border-slate-100 p-4">
                  <p className="text-sm font-medium text-ink">{label}</p>
                  <p className="mt-1 text-2xl font-semibold text-ink">{value}</p>
                  <p className="mt-1 text-[11px] leading-4 text-slate-400">{note}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="mt-6 border border-slate-200 bg-white p-6">
            <div className="flex items-end justify-between gap-4">
              <h2 className="font-semibold text-ink">High-risk governed actions</h2>
              <Link href="/action-requests" className="text-xs font-semibold text-signal hover:underline">All actions →</Link>
            </div>
            {requests.filter((r) => r.risk_classification === "HIGH" || r.risk_classification === "CRITICAL").length === 0 ? (
              <div className="mt-4"><StateMessage>No high-risk actions recorded.</StateMessage></div>
            ) : (
              <ul className="mt-4 space-y-2">
                {requests.filter((r) => r.risk_classification === "HIGH" || r.risk_classification === "CRITICAL").slice(0, 10).map((req) => (
                  <li key={req.id}>
                    <Link href={`/action-requests/${req.id}`} className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 py-2.5 text-sm hover:bg-slate-50">
                      <span><strong className="text-ink">{req.agent_name}</strong><small className="ml-2 text-slate-400">{req.action_name}</small></span>
                      <span className="flex gap-2"><StatusPill value={`${req.risk_classification} · ${req.risk_score}`} /><StatusPill value={req.decision ?? req.status} /></span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="mt-6 border border-slate-200 bg-white p-6">
            <h2 className="font-semibold text-ink">Intelligence layer</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Today, every signal on this screen is a deterministic, auditable governance event — authorization is never decided by a model.
              The future contract adds AI <em>assistance</em> (risk intelligence, anomaly detection, intent classification, policy recommendation, and human-readable explanations) that feeds the same deterministic policy engine. No model will ever be the final authorization authority.
            </p>
            <p className="mt-3 text-xs text-slate-400">Schema for the planned Security Intelligence Corpus: see docs/AGENTOS_SECURITY_INTELLIGENCE_CORPUS.md.</p>
          </section>
        </>
      )}
    </RegistryShell>
  );
}
