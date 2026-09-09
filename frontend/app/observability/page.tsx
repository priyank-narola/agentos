"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AuditVerify, ObservabilityMetrics, TenantPosture, TimelineEvent, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function ObservabilityPage() {
  const [metrics, setMetrics] = useState<ObservabilityMetrics | null>(null);
  const [posture, setPosture] = useState<TenantPosture | null>(null);
  const [audit, setAudit] = useState<AuditVerify | null>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.metrics(), api.tenantPosture(), api.auditVerify(), api.timeline()])
      .then(([m, p, a, t]) => {
        setMetrics(m); setPosture(p); setAudit(a); setEvents(t.events);
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
              <div key={label} className="border border-slate-200 bg-white p-4">
                <p className="text-xs font-medium text-slate-500">{label}</p>
                <p className="mt-2 text-3xl font-semibold text-ink">{value}</p>
                <p className="mt-2 text-[11px] text-slate-400">{note}</p>
              </div>
            ))}
          </div>

          {audit && (
            <div className={`mt-6 border p-6 ${audit.violation_count === 0 ? "border-emerald-200 bg-emerald-50" : "border-red-300 bg-red-50"}`}>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Audit integrity</p>
              <p className={`mt-1 text-2xl font-bold ${audit.violation_count === 0 ? "text-emerald-800" : "text-red-800"}`}>{audit.audit_integrity_status}</p>
              <p className="mt-2 text-sm text-slate-600">{audit.total_requests_verified} requests verified · {audit.violation_count} violations</p>
              {audit.violations.slice(0, 10).map((v, i) => <p key={i} className="mt-1 text-xs text-red-700">{v.type}</p>)}
            </div>
          )}

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
              <Link href="/action-requests" className="text-xs font-semibold text-signal hover:underline">Action requests →</Link>
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
