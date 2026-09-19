"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ActionRequest, Agent, Approval, api } from "@/lib/api";
import { RegistryShell, StateMessage } from "@/components/registry-shell";
import { Status } from "@/components/ui/Status";
import { DataTable, type DataColumn } from "@/components/ui/DataTable";
import { GovernanceStepper } from "@/components/ui/GovernanceStepper";
import { SandboxBadge } from "@/components/ui/Banner";
import { formatTime, shortId } from "@/lib/format";
import { cn } from "@/lib/cn";

export default function ControlCenterPage() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [requests, setRequests] = useState<ActionRequest[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.agents(), api.actionRequests(), api.approvals()])
      .then(([a, r, ap]) => {
        setAgents(a);
        setRequests(r);
        setApprovals(ap);
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, []);

  const pendingApprovals = approvals.filter((a) => a.status === "PENDING");
  const authorized = requests.filter((r) => r.decision === "ALLOW").length;
  const blocked = requests.filter((r) => r.decision === "DENY").length;
  const awaitingReview = requests.filter((r) => r.decision === "REQUIRE_APPROVAL").length;
  // Canonical product vocabulary emitted by the API (see canonical_execution_status):
  // NOT_EXECUTED | PENDING | EXECUTED | FAILED — never the raw internal enum.
  const executed = requests.filter((r) => r.execution_status === "EXECUTED").length;
  const failed = requests.filter((r) => r.execution_status === "FAILED").length;
  const settling = requests.filter((r) => r.execution_status === "PENDING").length;
  const highRisk = requests.filter((r) => r.risk_classification === "HIGH" || r.risk_classification === "CRITICAL").length;

  const needsAttention = pendingApprovals.length > 0 || failed > 0;
  const principalLabel = (r: ActionRequest) => r.principal_name ?? shortId(r.principal_id);
  const timeTitle = (v: string) => new Date(v).toLocaleString();

  /** Placeholder while loading — a literal 0 would assert a fact we do not yet have. */
  const metric = (value: number) => (loading ? "—" : value);

  const recentColumns: DataColumn<ActionRequest>[] = [
    {
      key: "who",
      header: "Agent",
      render: (r) => (
        <div className="min-w-0">
          <p className="font-medium text-ink">{r.agent_name}</p>
          <p className="mt-0.5 truncate text-xs text-inkSubtle">
            Acting for <span className="text-inkMuted">{principalLabel(r)}</span>
          </p>
        </div>
      ),
    },
    {
      key: "action",
      header: "Action",
      render: (r) => (
        <div className="min-w-0">
          <p className="text-ink">{r.action_name}</p>
          <p className="mt-0.5 truncate font-mono text-[11px] text-inkFaint">{r.tool_name}</p>
        </div>
      ),
    },
    {
      key: "resource",
      header: "Resource",
      render: (r) => (
        <div className="min-w-0">
          <p className="text-ink">{r.resource_type}</p>
          <p className="mt-0.5 truncate font-mono text-[11px] text-inkFaint">{r.resource_key}</p>
        </div>
      ),
    },
    {
      key: "risk",
      header: "Risk",
      render: (r) => <Status value={r.risk_classification ?? "LOW"} />,
    },
    {
      key: "decision",
      header: "Decision",
      render: (r) => <Status value={r.decision ?? r.status} />,
    },
    {
      key: "execution",
      header: "Execution",
      render: (r) => <Status value={r.execution_status ?? "NOT_EXECUTED"} />,
    },
    {
      key: "time",
      header: "Time",
      headerClassName: "text-right",
      align: "right",
      render: (r) => (
        <span className="text-xs text-inkFaint" title={timeTitle(r.requested_at)}>
          {formatTime(r.requested_at)}
        </span>
      ),
    },
  ];

  return (
    <RegistryShell>
      <header className="mb-8 flex flex-wrap items-end justify-between gap-6">
        <div className="max-w-3xl">
          <p className="eyebrow text-signal">Control center</p>
          <h1 className="mt-2 text-[32px] font-semibold leading-tight tracking-tight text-ink lg:text-[40px]">AgentOS governance posture</h1>
          <p className="mt-3 text-[15px] leading-7 text-inkSubtle">
            Every consequential agent action is evaluated before execution — who is acting, for whom, at what risk, under which policy, and with what proof.
          </p>
        </div>
        <div className="flex flex-col items-start gap-2 lg:items-end">
          <SandboxBadge />
          <Link href="/demo" className="text-[13px] font-semibold text-signal hover:text-signalHover">
            Run the guided governance demo →
          </Link>
        </div>
      </header>

      {error && <StateMessage tone="error">Unable to load control-plane data. Confirm the API is running. {error}</StateMessage>}

      {/* Posture strip */}
      <section className="grid gap-px overflow-hidden rounded-card border border-hairline bg-hairline md:grid-cols-[1.35fr_repeat(4,1fr)]">
        <div className="bg-surface p-6 lg:p-7">
          <div className="flex items-center gap-2.5">
            {/* The indicator reports what is true: a failed control-plane read
                must never render as a healthy "governance active" pulse. */}
            <span aria-hidden className="relative flex h-2.5 w-2.5">
              {!error && !loading && (
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal/40" />
              )}
              <span className={cn("relative inline-flex h-2.5 w-2.5 rounded-full", error ? "bg-danger" : loading ? "bg-inkFaint" : "bg-signal")} />
            </span>
            <p className="text-sm font-semibold text-ink">
              {error ? "Control plane unreachable" : loading ? "Reading control plane…" : "Governance active"}
            </p>
          </div>
          <p className="mt-3 max-w-md text-[13px] leading-6 text-inkSubtle">
            {loading
              ? "Reading the decision ledger…"
              : `${requests.length} action request${requests.length === 1 ? "" : "s"} evaluated since startup. All decisions are deterministic and audit-logged.`}
          </p>
        </div>
        {[
          { label: "Authorized", value: authorized, note: "policy allowed" },
          { label: "Blocked", value: blocked, note: "policy denied" },
          { label: "Awaiting review", value: awaitingReview, note: "need human decision" },
          { label: "High-risk", value: highRisk, note: "of all requests" },
        ].map((m) => (
          <div key={m.label} className="flex flex-col justify-center bg-surface px-6 py-5">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-inkFaint">{m.label}</p>
            <p className="tnum mt-2 text-3xl font-semibold tracking-tight text-ink">{metric(m.value)}</p>
            <p className="mt-1 text-[11px] text-inkSubtle">{m.note}</p>
          </div>
        ))}
      </section>

      {/* Attention */}
      {loading ? (
        <div className="mt-6 rounded-card border border-hairline bg-surface p-6">Loading posture…</div>
      ) : needsAttention ? (
        <div className="mt-6 rounded-card border border-hairline bg-surface p-5">
          <div className="flex flex-wrap items-center gap-4">
            <Status value={pendingApprovals.length > 0 ? "PENDING" : "FAILED"} variant="inline" dot />
            <p className="text-[15px] text-ink">
              {pendingApprovals.length > 0 ? (
                <>
                  <span className="font-semibold">{pendingApprovals.length}</span> action{pendingApprovals.length === 1 ? "" : "s"} await{pendingApprovals.length === 1 ? "s" : ""} human approval
                </>
              ) : (
                <span className="font-semibold">{failed}</span>
              )}{" "}
              {failed > 0 && <span className="text-inkSubtle">· {failed} execution failure{failed === 1 ? "" : "s"}</span>}
            </p>
            <Link href="/approvals" className="ml-auto text-[13px] font-semibold text-signal hover:text-signalHover">
              Review approval queue →
            </Link>
          </div>
          {pendingApprovals.length > 0 && (
            <div className="mt-4 grid gap-px overflow-hidden rounded-card border border-hairline bg-hairline lg:grid-cols-3">
              {pendingApprovals.slice(0, 3).map((approval) => (
                <Link key={approval.id} href={`/approvals/${approval.id}`} className="group bg-surface p-4 transition-colors hover:bg-surfaceMuted">
                  <p className="truncate text-sm font-medium text-ink">
                    {approval.agent_name} <span className="font-normal text-inkFaint">for</span> {approval.principal_name ?? shortId(approval.principal_id)}
                  </p>
                  <p className="mt-1 truncate text-[13px] text-inkSubtle">{approval.action_name}</p>
                  <div className="mt-3 flex items-center justify-between gap-2">
                    <span className="text-xs font-medium text-warning">Review required</span>
                    <span className="text-[11px] text-inkFaint">expires {formatTime(approval.expires_at)}</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="mt-6 flex items-center gap-2.5 rounded-card border border-hairline bg-surface px-5 py-4">
          <Status value="EXECUTED" variant="inline" dot />
          <p className="text-[15px] text-ink">No actions require attention right now. <span className="text-inkSubtle">Authorized {authorized} · executed {executed}.</span></p>
        </div>
      )}

      {/* Lifecycle + signals */}
      <div className="mt-8 grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <section className="rounded-card border border-hairline bg-surface p-6 lg:p-7">
          <div className="flex items-baseline justify-between gap-4">
            <div>
              <p className="eyebrow text-inkFaint">Governance chain</p>
              <h2 className="mt-1 text-lg font-semibold tracking-tight text-ink">How every action is governed</h2>
            </div>
            <span className="hidden text-xs text-inkSubtle sm:block">Request → proof</span>
          </div>
          <p className="mt-2 max-w-xl text-[13px] leading-6 text-inkSubtle">
            Each step is recorded and can be re-opened as evidence. The model advises. The deterministic policy engine decides.
          </p>
          <div className="mt-7">
            <GovernanceStepper orientation="vertical" />
          </div>
        </section>

        <section className="flex flex-col gap-6">
          <div className="rounded-card border border-hairline bg-surface p-6">
            <p className="eyebrow text-inkFaint">System signals</p>
            <h2 className="mt-1 text-lg font-semibold tracking-tight text-ink">What the system is seeing</h2>
            <dl className="mt-4 divide-y divide-hairline">
              {[
                ["Approval queue", pendingApprovals.length],
                ["Blocked by policy", blocked],
                ["Executed in sandbox", executed],
                ["Settling", settling],
                ["Execution failures", failed],
                ["Registered agents", agents.length],
              ].map(([label, value]) => (
                <div key={label as string} className="flex items-center justify-between py-3">
                  <dt className="text-[13px] text-inkSubtle">{label}</dt>
                  <dd className="tnum text-sm font-semibold text-ink">{metric(value as number)}</dd>
                </div>
              ))}
            </dl>
          </div>
          {pendingApprovals.length === 0 && blocked > 0 && (
            <div className="rounded-card border border-hairline bg-surface p-6">
              <p className="eyebrow text-inkFaint">Security</p>
              <p className="mt-2 text-sm leading-6 text-inkSubtle">
                <span className="font-medium text-ink">{blocked}</span> attempt{blocked === 1 ? "" : "s"} were denied by policy. Open the action requests list to inspect the reasons.
              </p>
              <Link href="/action-requests" className="mt-3 inline-block text-[13px] font-semibold text-signal hover:text-signalHover">
                Inspect decisions →
              </Link>
            </div>
          )}
        </section>
      </div>

      {/* Recent actions */}
      <section className="mt-8">
        <div className="mb-4 flex items-end justify-between gap-4">
          <div>
            <p className="eyebrow text-inkFaint">Recent governed actions</p>
            <h2 className="mt-1 text-lg font-semibold tracking-tight text-ink">Latest decisions</h2>
          </div>
          <Link href="/action-requests" className="text-[13px] font-semibold text-signal hover:text-signalHover">
            View all →
          </Link>
        </div>
        {loading ? (
          <StateMessage>Loading governed actions…</StateMessage>
        ) : requests.length === 0 ? (
          <div className="rounded-card border border-dashed border-hairlineStrong bg-surface px-6 py-12 text-center">
            <p className="text-sm font-medium text-ink">No governed actions yet</p>
            <p className="mx-auto mt-1 max-w-sm text-[13px] text-inkSubtle">Run the guided governance demo to see a real decision, approval, and proof.</p>
            <Link href="/demo" className="mt-4 inline-flex items-center gap-2 rounded-control bg-ink px-4 py-2 text-sm font-medium text-white hover:bg-ink/90">
              Run the demo
            </Link>
          </div>
        ) : (
          <DataTable<ActionRequest>
            columns={recentColumns}
            rows={requests.slice(0, 8)}
            rowKey={(r) => r.id}
            onRowClick={(r) => router.push(`/action-requests/${r.id}`)}
            caption="Recent governed actions"
            minWidth={980}
          />
        )}
      </section>
    </RegistryShell>
  );
}
