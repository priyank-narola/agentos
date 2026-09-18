"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AuditVerify, ObservabilityMetrics, ReconciliationCase, RuntimeOperationsMetrics, TenantPosture, TimelineEvent, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function ObservabilityPage() {
  const [metrics, setMetrics] = useState<ObservabilityMetrics | null>(null);
  const [posture, setPosture] = useState<TenantPosture | null>(null);
  const [audit, setAudit] = useState<AuditVerify | null>(null);
  const [runtime, setRuntime] = useState<RuntimeOperationsMetrics | null>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [reconciliationCases, setReconciliationCases] = useState<ReconciliationCase[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.metrics(), api.tenantPosture(), api.auditVerify(), api.timeline(), api.runtimeMetrics(), api.reconciliationCases()])
      .then(([m, p, a, t, r, cases]) => {
        setMetrics(m); setPosture(p); setAudit(a); setEvents(t.events); setRuntime(r); setReconciliationCases(cases);
      })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  const kpis: Array<[string, number | string, string]> = [
    ["Action requests", metrics?.total_action_requests ?? "--", "intercepted"],
    ["Pending approvals", metrics?.pending_approvals ?? "--", "human review"],
    ["Approved executions", metrics?.approved_executions ?? "--", "sandbox ledger"],
    ["Rejected actions", metrics?.rejected_actions ?? "--", "blocked"],
    ["Security violations", posture?.security_violations ?? "--", "posture"],
    ["High-risk activity", posture?.high_risk_activity ?? "--", "action volume"],
  ];

  const blockedMarkers = ["BLOCKED", "SECURITY_", "TOCTOU", "PAYLOAD_TAMPER", "CROSS_TENANT", "AUTHENTICATION_FAILED", "IDEMPOTENCY_CONFLICT", "CANCELLED", "WEBHOOK"];
  const securityEvents = events.filter((e) => blockedMarkers.some((m) => e.event_type.startsWith(m) || e.event_type.includes(m)));
  const attentionItems = [
    {
      label: "Unconfirmed provider outcomes",
      value: reconciliationCases.length,
      detail: "Awaiting a status-only reconciliation check; no action is resubmitted.",
      href: "/reconciliation",
      tone: reconciliationCases.length > 0 ? "attention" : "clear",
    },
    {
      label: "Recorded execution failures/timeouts",
      value: metrics?.execution_failures_timeouts ?? null,
      detail: "Tenant-wide counter from the execution ledger; it is not a time-window rate.",
      href: "/evidence",
      tone: (metrics?.execution_failures_timeouts ?? 0) > 0 ? "attention" : "clear",
    },
    {
      label: "Audit-integrity violations",
      value: audit?.violation_count ?? null,
      detail: "Verified hash-chain violations, if any. Investigate with the evidence explorer.",
      href: "/evidence",
      tone: (audit?.violation_count ?? 0) > 0 ? "attention" : "clear",
    },
    {
      label: "Process-local HTTP failures",
      value: runtime?.failed_request_total ?? null,
      detail: "Since this application process started; it resets on restart and is not central monitoring.",
      href: "/evidence",
      tone: (runtime?.failed_request_total ?? 0) > 0 ? "attention" : "clear",
    },
  ];

  return (
    <RegistryShell title="Observability & audit" eyebrow="Governance evidence">
      <p className="mb-6 max-w-3xl text-sm leading-6 text-slate-500">
        Read-only view of what AgentOS recorded: decisions, approvals, sandbox executions, audit events, and tenant posture. Sandbox only — no real money movement.
      </p>
      {error && <StateMessage tone="error">Unable to load observability data. {error}</StateMessage>}
      {!error && !metrics && <StateMessage>Loading observability telemetry…</StateMessage>}
      {metrics && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
            {kpis.map(([label, value, note]) => (
              <div key={label} className="rounded-card border border-hairline bg-surface p-4">
                <p className="text-xs font-medium text-inkSubtle">{label}</p>
                <p className="tnum mt-2 text-3xl font-semibold tracking-tight text-ink">{value}</p>
                <p className="mt-2 text-[11px] text-inkFaint">{note}</p>
              </div>
            ))}
          </div>

          {audit && (
            <div className={`mt-6 rounded-card border p-6 ${audit.violation_count === 0 ? "border-successBorder bg-successBg" : "border-dangerBorder bg-dangerBg"}`}>
              <p className="eyebrow text-inkSubtle">Audit integrity</p>
              <p className={`mt-1 text-2xl font-bold ${audit.violation_count === 0 ? "text-success" : "text-danger"}`}>{audit.audit_integrity_status}</p>
              <p className="mt-2 text-sm text-slate-600">{audit.total_requests_verified} requests verified · {audit.violation_count} violations</p>
              {audit.violations.slice(0, 10).map((v, i) => <p key={i} className="mt-1 text-xs text-red-700">{v.type}</p>)}
            </div>
          )}

          {runtime && (
            <section className="mt-6 border border-hairline bg-surface p-6">
              <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="eyebrow">Runtime operations</p><h2 className="mt-1 font-semibold text-ink">Current application process</h2></div><StatusPill value="PROCESS-LOCAL" /></div>
              <p className="mt-2 text-sm leading-6 text-inkSubtle">Payload-free metrics for this application process only. Central monitoring and alerts remain required before production launch.</p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{[["Requests", runtime.request_total], ["Failed requests", runtime.failed_request_total], ["Average latency", `${runtime.average_latency_ms} ms`], ["Max latency", `${runtime.max_latency_ms} ms`]].map(([label, value]) => <div key={String(label)} className="border border-hairline p-3"><p className="text-xs text-inkFaint">{label}</p><p className="mt-1 text-xl font-semibold text-ink">{value}</p></div>)}</div>
              <p className="mt-4 text-xs text-inkFaint">Started {new Date(runtime.started_at).toLocaleString()} · status responses {Object.entries(runtime.status_counts).map(([status, count]) => `${status}: ${count}`).join(" · ") || "none yet"}</p>
            </section>
          )}

          <section className="mt-6 border border-hairline bg-surface p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="eyebrow">Operational attention</p>
                <h2 className="mt-1 font-semibold text-ink">Evidence-backed attention signals</h2>
              </div>
              <StatusPill value="DERIVED VIEW" />
            </div>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-inkSubtle">
              These are derived from the current tenant’s ledger, audit verification, reconciliation queue, and current process metrics. They are not a paging or alert-delivery system; central alerting remains a launch blocker.
            </p>
            <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {attentionItems.map((item) => (
                <Link key={item.label} href={item.href} className="group border border-hairline p-4 transition hover:border-signal focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs font-medium text-inkSubtle">{item.label}</p>
                    <StatusPill value={item.tone === "attention" ? "ATTENTION" : "CLEAR"} />
                  </div>
                  <p className="tnum mt-3 text-3xl font-semibold tracking-tight text-ink">{item.value ?? "--"}</p>
                  <p className="mt-3 text-xs leading-5 text-inkFaint">{item.detail}</p>
                  <p className="mt-3 text-xs font-semibold text-signal group-hover:underline">Review evidence →</p>
                </Link>
              ))}
            </div>
          </section>

          {posture && (
            <section className="mt-6 border border-slate-200 bg-white p-6">
              <h2 className="font-semibold text-ink">Tenant posture</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-4">
                {[["Active agents", posture.active_agents], ["Active delegations", posture.active_delegations], ["Execution volume", posture.execution_volume], ["Approval volume", posture.approval_volume]].map(([label, value]) => (
                  <div key={label} className="border border-slate-100 p-3"><p className="text-xs text-slate-500">{label}</p><p className="mt-1 text-xl font-semibold text-ink">{value}</p></div>
                ))}
              </div>
            </section>
          )}

          <section className="mt-6 border border-slate-200 bg-white p-6">
            <div className="flex items-end justify-between gap-4">
              <h2 className="font-semibold text-ink">Recent audit events</h2>
              <div className="flex gap-4"><Link href="/evidence" className="text-xs font-semibold text-signal hover:underline">Evidence explorer →</Link><Link href="/action-requests" className="text-xs font-semibold text-signal hover:underline">Action requests →</Link></div>
            </div>
            {events.length === 0 ? <div className="mt-4"><StateMessage>No audit events recorded yet.</StateMessage></div> : (
              <ul className="mt-4 space-y-1">
                {events.slice(0, 25).map((event) => (
                  <li key={event.id} className="flex items-baseline justify-between gap-4 border-b border-slate-100 py-2 text-sm">
                    <span className="flex items-center gap-2"><StatusPill value={event.event_type} /><span className="text-xs text-slate-400">{event.actor_type}</span></span>
                    <span className="text-xs text-slate-400">{event.created_at ? new Date(event.created_at).toLocaleString() : ""}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}

      {securityEvents.length > 0 && (
        <section className="mt-6 border border-red-200 bg-white p-6">
          <h2 className="font-semibold text-ink">Security &amp; blocked events ({securityEvents.length})</h2>
          <ul className="mt-3 space-y-1">
            {securityEvents.slice(0, 20).map((event) => (
              <li key={event.id} className="flex items-baseline justify-between gap-3 border-b border-slate-100 py-1.5 text-sm">
                <span className="font-medium text-ink">{event.event_type}</span>
                {event.action_request_id ? <Link href={`/action-requests/${event.action_request_id}`} className="text-xs font-semibold text-signal hover:underline">Trace action →</Link> : <span className="text-xs text-slate-400">{event.actor_type}</span>}
              </li>
            ))}
          </ul>
        </section>
      )}
    </RegistryShell>
  );
}
