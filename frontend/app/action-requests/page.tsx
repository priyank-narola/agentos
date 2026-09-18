"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { ActionRequest, api } from "@/lib/api";
import { RegistryShell, StateMessage } from "@/components/registry-shell";
import { Status } from "@/components/ui/Status";
import { DataTable, type DataColumn } from "@/components/ui/DataTable";
import { formatDateTime, shortId } from "@/lib/format";

export default function ActionRequestsPage() {
  const router = useRouter();
  const [requests, setRequests] = useState<ActionRequest[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [decision, setDecision] = useState("ALL");
  const [risk, setRisk] = useState("ALL");
  const [execution, setExecution] = useState("ALL");

  useEffect(() => {
    api.actionRequests().then(setRequests).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false));
  }, []);

  const visibleRequests = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return requests
      .filter((request) => {
        const matchesText = !normalizedQuery || [request.id, request.agent_name, request.principal_name, request.action_name, request.tool_name, request.resource_key, request.reason, request.reason_code]
          .some((value) => String(value ?? "").toLowerCase().includes(normalizedQuery));
        const matchesDecision = decision === "ALL" || (request.decision ?? request.status) === decision;
        const matchesRisk = risk === "ALL" || (request.risk_classification ?? request.risk_level ?? "LOW") === risk;
        const matchesExecution = execution === "ALL" || (request.execution_status ?? "NOT_EXECUTED") === execution;
        return matchesText && matchesDecision && matchesRisk && matchesExecution;
      })
      .sort((a, b) => new Date(b.requested_at).getTime() - new Date(a.requested_at).getTime());
  }, [decision, execution, query, requests, risk]);

  const summary = useMemo(() => ({
    pending: requests.filter((request) => (request.decision ?? request.status) === "REQUIRE_APPROVAL").length,
    blocked: requests.filter((request) => (request.decision ?? request.status) === "DENY").length,
    flagged: requests.filter((request) => ["HIGH", "CRITICAL"].includes(request.risk_classification ?? request.risk_level ?? "LOW")).length,
  }), [requests]);

  const columns: DataColumn<ActionRequest>[] = [
    {
      key: "who",
      header: "Agent",
      render: (r) => (
        <div className="min-w-0">
          <p className="font-medium text-ink">{r.agent_name}</p>
          <p className="mt-0.5 truncate text-xs text-inkSubtle">Acting for {r.principal_name ?? shortId(r.principal_id)}</p>
        </div>
      ),
    },
    {
      key: "action",
      header: "Action",
      render: (r) => (
        <div className="min-w-0">
          <p className="text-ink">{r.action_name}</p>
          <p className="mt-0.5 truncate text-[11px] text-inkFaint">{r.tool_name}</p>
        </div>
      ),
    },
    { key: "resource", header: "Resource", render: (r) => <span className="font-mono text-xs text-inkSubtle">{r.resource_key}</span> },
    { key: "risk", header: "Risk", render: (r) => <Status value={r.risk_classification ?? "LOW"} /> },
    { key: "decision", header: "Decision", render: (r) => <Status value={r.decision ?? r.status} /> },
    { key: "execution", header: "Execution", render: (r) => <Status value={r.execution_status ?? "NOT_EXECUTED"} /> },
    {
      key: "time",
      header: "Requested",
      headerClassName: "text-right",
      align: "right",
      render: (r) => (
        <span className="text-xs text-inkFaint" title={formatDateTime(r.requested_at)}>
          {new Date(r.requested_at).toLocaleDateString()}
        </span>
      ),
    },
  ];

  return (
    <RegistryShell title="Action requests" eyebrow="Action governance">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          <p className="text-sm leading-6 text-inkSubtle">Every governed action and its decision chain. Open a request to inspect intent, parameters, policy reasoning, risk signals, approval trail, execution receipt, and evidence.</p>
          <p className="mt-2 text-xs text-inkFaint">Sandbox/test-mode records only. No live money movement is active.</p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/policy-evaluation" className="rounded-control border border-hairline px-3 py-2 text-[13px] font-semibold text-ink outline-none hover:bg-surfaceMuted focus-visible:ring-2 focus-visible:ring-focusRing">Preflight an action</Link>
          <Link href="/gateway" className="rounded-control bg-signal px-3 py-2 text-[13px] font-semibold text-white outline-none hover:bg-signalHover focus-visible:ring-2 focus-visible:ring-focusRing focus-visible:ring-offset-2">Request test action</Link>
        </div>
      </div>

      <div className="mb-5 grid gap-3 sm:grid-cols-3">
        <div className="rounded-card border border-hairline bg-surface p-4"><p className="text-[11px] uppercase tracking-wide text-inkFaint">Approval routes</p><p className="mt-1 text-xl font-semibold tnum text-ink">{summary.pending}</p></div>
        <div className="rounded-card border border-hairline bg-surface p-4"><p className="text-[11px] uppercase tracking-wide text-inkFaint">Blocked by policy</p><p className="mt-1 text-xl font-semibold tnum text-ink">{summary.blocked}</p></div>
        <div className="rounded-card border border-hairline bg-surface p-4"><p className="text-[11px] uppercase tracking-wide text-inkFaint">High-risk signals</p><p className="mt-1 text-xl font-semibold tnum text-ink">{summary.flagged}</p></div>
      </div>

      <section aria-label="Action request filters" className="mb-5 rounded-card border border-hairline bg-surface p-4">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_repeat(3,minmax(145px,0.28fr))]">
          <div><label htmlFor="action-search" className="mb-1.5 block text-xs font-medium text-inkMuted">Search evidence fields</label><input id="action-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Action, agent, resource, reason…" className="w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink outline-none placeholder:text-inkFaint focus-visible:ring-2 focus-visible:ring-focusRing" /></div>
          <div><label htmlFor="action-decision" className="mb-1.5 block text-xs font-medium text-inkMuted">Decision</label><select id="action-decision" value={decision} onChange={(event) => setDecision(event.target.value)} className="w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing"><option value="ALL">All decisions</option><option value="ALLOW">Allowed</option><option value="DENY">Blocked</option><option value="REQUIRE_APPROVAL">Approval required</option></select></div>
          <div><label htmlFor="action-risk" className="mb-1.5 block text-xs font-medium text-inkMuted">Risk</label><select id="action-risk" value={risk} onChange={(event) => setRisk(event.target.value)} className="w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing"><option value="ALL">All risk levels</option><option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option><option value="CRITICAL">Critical</option></select></div>
          <div><label htmlFor="action-execution" className="mb-1.5 block text-xs font-medium text-inkMuted">Execution</label><select id="action-execution" value={execution} onChange={(event) => setExecution(event.target.value)} className="w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing"><option value="ALL">All execution states</option><option value="EXECUTED">Executed</option><option value="FAILED">Failed</option><option value="PENDING">Pending</option><option value="NOT_EXECUTED">Not executed</option></select></div>
        </div>
        <p aria-live="polite" className="mt-3 text-xs text-inkFaint">{visibleRequests.length} of {requests.length} action requests shown. Select a row to open its complete case file.</p>
      </section>

      {error && <StateMessage tone="error">Unable to load action requests. {error}</StateMessage>}
      {loading && !error && <StateMessage>Loading governed actions…</StateMessage>}
      {!loading && !error && requests.length === 0 && <StateMessage>No governed actions recorded yet. Run the guided demo to create one.</StateMessage>}
      {requests.length > 0 && (
        <DataTable<ActionRequest>
          columns={columns}
          rows={visibleRequests}
          rowKey={(r) => r.id}
          onRowClick={(r) => router.push(`/action-requests/${r.id}`)}
          caption="Governed action requests. Select a row for its complete case file."
          minWidth={980}
        />
      )}
    </RegistryShell>
  );
}
