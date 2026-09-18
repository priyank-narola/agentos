"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { ActionEvidenceBundle, ActionRequest, Approval, TimelineEvent, api } from "@/lib/api";
import { RegistryShell, StateMessage } from "@/components/registry-shell";
import { Breadcrumbs } from "@/components/ui/Breadcrumbs";
import { Status } from "@/components/ui/Status";
import { formatDateTime, shortId } from "@/lib/format";

type EvidenceLoadState = "idle" | "loading" | "ready" | "error";

const eventDate = (event: TimelineEvent) => event.created_at ? new Date(event.created_at).getTime() : 0;

function matchesText(value: unknown, query: string) {
  return String(value ?? "").toLowerCase().includes(query);
}

function formatEventData(data: Record<string, unknown>) {
  const entries = Object.entries(data).slice(0, 4);
  if (!entries.length) return "No additional event attributes were recorded.";
  return entries.map(([key, value]) => `${key}: ${typeof value === "string" ? value : JSON.stringify(value)}`).join(" · ");
}

export default function EvidenceExplorerPage() {
  const [requests, setRequests] = useState<ActionRequest[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [bundle, setBundle] = useState<ActionEvidenceBundle | null>(null);
  const [loadState, setLoadState] = useState<EvidenceLoadState>("loading");
  const [bundleState, setBundleState] = useState<EvidenceLoadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [outcome, setOutcome] = useState("ALL");
  const [risk, setRisk] = useState("ALL");
  const [windowDays, setWindowDays] = useState("ALL");

  useEffect(() => {
    Promise.all([api.actionRequests(), api.approvals(), api.timeline()])
      .then(([requestData, approvalData, timelineData]) => {
        setRequests(requestData);
        setApprovals(approvalData);
        setTimeline(timelineData.events);
        setSelectedId((current) => current ?? requestData[0]?.id ?? null);
        setLoadState("ready");
      })
      .catch((reason: Error) => {
        setError(reason.message);
        setLoadState("error");
      });
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setBundle(null);
      return;
    }
    setBundleState("loading");
    setError(null);
    api.actionEvidence(selectedId)
      .then((data) => {
        setBundle(data);
        setBundleState("ready");
      })
      .catch((reason: Error) => {
        setBundle(null);
        setError(`Unable to load this evidence bundle. ${reason.message}`);
        setBundleState("error");
      });
  }, [selectedId]);

  const approvalByRequest = useMemo(() => new Map(approvals.map((approval) => [approval.action_request_id, approval])), [approvals]);

  const visibleRequests = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    const minTime = windowDays === "ALL" ? 0 : Date.now() - Number(windowDays) * 24 * 60 * 60 * 1000;
    return requests
      .filter((request) => {
        const approval = approvalByRequest.get(request.id);
        const requestMatches = !normalized || [request.id, request.action_name, request.agent_name, request.principal_name, request.resource_key, request.decision, approval?.policy_id, approval?.decided_by]
          .some((value) => matchesText(value, normalized));
        const outcomeMatches = outcome === "ALL" || (request.decision ?? request.status) === outcome || (request.execution_status ?? "NOT_EXECUTED") === outcome;
        const riskMatches = risk === "ALL" || (request.risk_classification ?? request.risk_level ?? "LOW") === risk;
        return requestMatches && outcomeMatches && riskMatches && new Date(request.requested_at).getTime() >= minTime;
      })
      .sort((a, b) => new Date(b.requested_at).getTime() - new Date(a.requested_at).getTime());
  }, [approvalByRequest, outcome, query, requests, risk, windowDays]);

  const selectedRequest = requests.find((request) => request.id === selectedId) ?? null;
  const relatedEvents = useMemo(
    () => timeline.filter((event) => event.action_request_id === selectedId).sort((a, b) => (a.event_sequence ?? Number.MAX_SAFE_INTEGER) - (b.event_sequence ?? Number.MAX_SAFE_INTEGER) || eventDate(a) - eventDate(b)),
    [selectedId, timeline],
  );

  const downloadEvidence = () => {
    if (!bundle || !selectedRequest) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `action-evidence-${selectedRequest.id}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  if (loadState === "loading") return <RegistryShell><StateMessage>Loading the evidence explorer…</StateMessage></RegistryShell>;
  if (loadState === "error") return <RegistryShell><StateMessage>Unable to load evidence explorer data. {error}</StateMessage></RegistryShell>;

  return (
    <RegistryShell>
      <Breadcrumbs items={[{ label: "Control center", href: "/" }, { label: "Evidence" }]} />
      <section className="mt-5 rounded-card border border-hairline bg-surface p-6 lg:p-8">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div className="max-w-3xl">
            <p className="eyebrow text-inkFaint">Evidence / audit explorer</p>
            <h1 className="mt-1.5 text-2xl font-semibold tracking-tight text-ink lg:text-3xl">Trace a governed action from intent to outcome</h1>
            <p className="mt-3 text-[15px] leading-7 text-inkSubtle">Search server-recorded action evidence, inspect the decision chain, and export an immutable evidence bundle. This workspace is scoped to the current tenant.</p>
          </div>
          <div className="rounded-card border border-amber-200 bg-amber-50 px-4 py-3 text-[12px] leading-5 text-amber-950 dark:border-amber-900/70 dark:bg-amber-950/30 dark:text-amber-100">
            <p className="font-semibold">Sandbox/test-mode evidence</p>
            <p className="mt-0.5">No live money movement is active in this environment.</p>
          </div>
        </div>
      </section>

      <section aria-label="Evidence filters" className="mt-5 rounded-card border border-hairline bg-surface p-4">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_repeat(3,minmax(150px,0.25fr))]">
          <div>
            <label htmlFor="evidence-search" className="mb-1.5 block text-xs font-medium text-inkMuted">Search action, agent, resource, policy reference, or approver</label>
            <input id="evidence-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search recorded evidence" className="w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink outline-none placeholder:text-inkFaint focus-visible:ring-2 focus-visible:ring-focusRing" />
          </div>
          <div>
            <label htmlFor="evidence-outcome" className="mb-1.5 block text-xs font-medium text-inkMuted">Outcome</label>
            <select id="evidence-outcome" value={outcome} onChange={(event) => setOutcome(event.target.value)} className="w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing">
              <option value="ALL">All outcomes</option><option value="ALLOW">Allowed</option><option value="DENY">Blocked</option><option value="REQUIRE_APPROVAL">Approval required</option><option value="EXECUTED">Executed</option><option value="FAILED">Failed</option><option value="PENDING">Pending</option>
            </select>
          </div>
          <div>
            <label htmlFor="evidence-risk" className="mb-1.5 block text-xs font-medium text-inkMuted">Risk</label>
            <select id="evidence-risk" value={risk} onChange={(event) => setRisk(event.target.value)} className="w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing">
              <option value="ALL">All risk levels</option><option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option><option value="CRITICAL">Critical</option>
            </select>
          </div>
          <div>
            <label htmlFor="evidence-window" className="mb-1.5 block text-xs font-medium text-inkMuted">Time window</label>
            <select id="evidence-window" value={windowDays} onChange={(event) => setWindowDays(event.target.value)} className="w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing">
              <option value="ALL">All recorded time</option><option value="1">Last 24 hours</option><option value="7">Last 7 days</option><option value="30">Last 30 days</option>
            </select>
          </div>
        </div>
        <p aria-live="polite" className="mt-3 text-xs text-inkFaint">{visibleRequests.length} of {requests.length} recorded actions match. Tenant scope is derived by the server; cross-tenant search is not exposed by the current API.</p>
      </section>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(320px,0.85fr)_minmax(0,1.4fr)]">
        <section aria-label="Recorded actions" className="overflow-hidden rounded-card border border-hairline bg-surface">
          <div className="border-b border-hairline px-5 py-4"><h2 className="text-sm font-semibold text-ink">Recorded actions</h2></div>
          <div className="max-h-[680px] overflow-y-auto p-2">
            {visibleRequests.length ? visibleRequests.map((request) => {
              const active = request.id === selectedId;
              const approval = approvalByRequest.get(request.id);
              return <button key={request.id} type="button" onClick={() => setSelectedId(request.id)} aria-pressed={active} className={`mb-1 w-full rounded-card border p-4 text-left outline-none transition-colors focus-visible:ring-2 focus-visible:ring-focusRing ${active ? "border-signal bg-signalSoft" : "border-transparent hover:border-hairline hover:bg-surfaceMuted"}`}>
                <div className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="truncate text-sm font-semibold text-ink">{request.action_name}</p><p className="mt-1 truncate text-xs text-inkSubtle">{request.agent_name} · {request.resource_key}</p></div><Status value={request.decision ?? request.status} /></div>
                <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-inkFaint"><span>{formatDateTime(request.requested_at)}</span><span className="font-mono">{shortId(request.id, 10)}</span>{approval && <span>Approval: {approval.status}</span>}</div>
              </button>;
            }) : <p className="p-5 text-sm text-inkSubtle">No action records match these filters.</p>}
          </div>
        </section>

        <section aria-live="polite" className="rounded-card border border-hairline bg-surface p-5 lg:p-6">
          {!selectedRequest ? <StateMessage>No recorded action is selected.</StateMessage> : bundleState === "loading" ? <StateMessage>Loading the signed evidence bundle…</StateMessage> : bundleState === "error" ? <StateMessage>{error}</StateMessage> : bundle ? <>
            <div className="flex flex-wrap items-start justify-between gap-4 border-b border-hairline pb-5">
              <div><p className="eyebrow text-inkFaint">Evidence bundle</p><h2 className="mt-1 text-xl font-semibold tracking-tight text-ink">{bundle.action_request.action_name}</h2><p className="mt-2 text-sm text-inkSubtle">Action {shortId(bundle.action_request.id, 12)} · exported {formatDateTime(bundle.exported_at)}</p></div>
              <div className="flex gap-2"><Link href={`/action-requests/${selectedRequest.id}`} className="rounded-control border border-hairline px-3 py-2 text-sm font-semibold text-ink outline-none hover:bg-surfaceMuted focus-visible:ring-2 focus-visible:ring-focusRing">Case file</Link><button type="button" onClick={downloadEvidence} className="rounded-control bg-signal px-3 py-2 text-sm font-semibold text-white outline-none hover:bg-signalHover focus-visible:ring-2 focus-visible:ring-focusRing focus-visible:ring-offset-2">Export JSON</button></div>
            </div>

            <div className="mt-5 grid gap-4 md:grid-cols-3"><div className="rounded-card border border-hairline bg-surfaceMuted p-4"><p className="text-[11px] uppercase tracking-wide text-inkFaint">Decision</p><div className="mt-2"><Status value={bundle.action_request.decision ?? bundle.action_request.status} /></div><p className="mt-2 text-xs leading-5 text-inkSubtle">{bundle.action_request.reason ?? "No decision rationale was recorded."}</p></div><div className="rounded-card border border-hairline bg-surfaceMuted p-4"><p className="text-[11px] uppercase tracking-wide text-inkFaint">Approval trail</p><p className="mt-2 text-sm font-semibold text-ink">{bundle.approval ? bundle.approval.status : "Not required"}</p><p className="mt-2 text-xs leading-5 text-inkSubtle">{bundle.approval?.decided_by ? `Decided by ${shortId(bundle.approval.decided_by, 10)}` : "A requester cannot self-approve an action."}</p></div><div className="rounded-card border border-hairline bg-surfaceMuted p-4"><p className="text-[11px] uppercase tracking-wide text-inkFaint">Execution receipt</p><div className="mt-2"><Status value={bundle.execution_receipt.status} /></div><p className="mt-2 text-xs leading-5 text-inkSubtle">{bundle.execution_receipt.provider_name ? `${bundle.execution_receipt.provider_name} · sandbox/test mode` : "No provider receipt recorded."}</p></div></div>

            {bundle.action_request.action_context && <section className="mt-5 rounded-card border border-hairline p-4"><p className="eyebrow text-inkFaint">Intent, impact & recovery</p><p className="mt-2 text-sm leading-6 text-inkSubtle">{bundle.action_request.action_context.summary}</p><div className="mt-3 grid gap-3 md:grid-cols-2"><p className="rounded-control bg-surfaceMuted px-3 py-2 text-xs text-inkSubtle"><span className="font-semibold text-ink">Target:</span> {bundle.action_request.action_context.target_system}</p><p className="rounded-control bg-surfaceMuted px-3 py-2 text-xs text-inkSubtle"><span className="font-semibold text-ink">Correction plan:</span> {bundle.action_request.action_context.recovery_plan}</p></div></section>}

            <section className="mt-5"><div className="flex items-baseline justify-between gap-4"><div><p className="eyebrow text-inkFaint">Immutable event timeline</p><h3 className="mt-1 text-base font-semibold text-ink">Recorded causal chain</h3></div><span className="text-xs text-inkFaint">{bundle.audit_events.length} bundle events · {relatedEvents.length} timeline events</span></div><ol className="mt-4 space-y-3 border-l border-hairline pl-5">{bundle.audit_events.map((event, index) => <li key={event.id} className="relative"><span className="absolute -left-[25px] top-1.5 h-2.5 w-2.5 rounded-full border-2 border-surface bg-signal" /><div className="rounded-card border border-hairline p-3"><div className="flex flex-wrap justify-between gap-2"><p className="text-sm font-semibold text-ink">{event.event_type}</p><p className="text-xs text-inkFaint">{formatDateTime(event.occurred_at)}</p></div><p className="mt-1 text-xs leading-5 text-inkSubtle">{formatEventData(event.event_data)}</p><p className="mt-1 font-mono text-[10px] text-inkFaint">#{event.sequence ?? index + 1} · {shortId(event.id, 12)}</p></div></li>)}</ol></section>

            <section className="mt-5 rounded-card border border-hairline bg-surfaceMuted p-4"><p className="eyebrow text-inkFaint">Integrity metadata</p><p className="mt-2 break-all font-mono text-xs text-inkSubtle">{bundle.integrity.algorithm} · {bundle.integrity.digest}</p><p className="mt-2 text-xs leading-5 text-inkSubtle">Excluded export fields: {bundle.integrity.excluded_fields.length ? bundle.integrity.excluded_fields.join(", ") : "None"}. The download contains the server-produced evidence bundle.</p></section>
          </> : null}
        </section>
      </div>
    </RegistryShell>
  );
}
