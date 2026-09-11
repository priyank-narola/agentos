"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { ActionRequest, Approval, ObservabilityActionDetail, Principal, TimelineEvent, api } from "@/lib/api";
import { RegistryShell, StateMessage } from "@/components/registry-shell";
import { Breadcrumbs } from "@/components/ui/Breadcrumbs";
import { Status } from "@/components/ui/Status";
import { Disclosure } from "@/components/ui/Disclosure";
import { GovernanceStepper } from "@/components/ui/GovernanceStepper";
import { KeyValueList } from "@/components/ui/KeyValue";
import { formatDateTime, formatMoney, shortId } from "@/lib/format";

type StepState = "done" | "active" | "pending" | "bad";

export default function ActionCaseFile({ params }: { params: Promise<{ id: string }> }) {
  const [request, setRequest] = useState<ActionRequest | null>(null);
  const [approval, setApproval] = useState<Approval | null>(null);
  const [obs, setObs] = useState<ObservabilityActionDetail | null>(null);
  const [audit, setAudit] = useState<TimelineEvent[]>([]);
  const [principals, setPrincipals] = useState<Principal[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    params.then(({ id }) => {
      api
        .actionRequest(id)
        .then(async (requestData) => {
          setRequest(requestData);
          const [approvals, principalsData] = await Promise.all([
            api.approvals().catch(() => [] as Approval[]),
            api.principals().catch(() => [] as Principal[]),
          ]);
          setApproval(approvals.find((item) => item.action_request_id === id) ?? null);
          setPrincipals(principalsData);
          if (requestData.tenant_id) {
            const detail = await api.observabilityActionRequest(id, requestData.tenant_id).catch(() => null);
            setObs(detail);
            const t = await api.timeline(requestData.tenant_id).catch(() => null);
            setAudit(t ? t.events.filter((e) => e.action_request_id === id).sort((a, b) => (a.created_at ?? "").localeCompare(b.created_at ?? "")) : []);
          }
        })
        .catch((reason: Error) => setError(reason.message));
    });
  }, [params]);

  const principalName = useMemo(() => {
    const map = new Map(principals.map((p) => [p.id, p.name]));
    return (id?: string | null, name?: string | null) => name ?? (id ? (map.get(id) ?? shortId(id)) : "Unavailable");
  }, [principals]);

  if (!request) {
    return (
      <RegistryShell>
        <StateMessage>{error ? `Unable to load action case file. ${error}` : "Loading case file…"}</StateMessage>
      </RegistryShell>
    );
  }

  const decision = request.decision ?? request.status ?? "UNKNOWN";
  const executionStatus = request.execution_status ?? "NOT_EXECUTED";
  const decidedBy = obs?.approval?.decided_by;
  const executionReason =
    executionStatus === "EXECUTED"
      ? `Executed in the sandbox provider${obs?.execution.provider_transaction_id ? ` · ${obs.execution.provider_transaction_id}` : ""}.`
      : executionStatus === "FAILED"
        ? "Execution was attempted but failed in the sandbox provider."
        : executionStatus === "PENDING"
          ? "Execution is pending a definitive outcome."
          : "No execution was recorded for this action.";

  const amount = request.parameters?.amount;
  const amountLine = typeof amount === "number" || typeof amount === "string" ? `${formatMoney(amount, String(request.parameters?.currency ?? "USD"))}` : null;

  const overrides = {
    approve: (approval ? (approval.status === "PENDING" ? ("active" as StepState) : approval.status === "APPROVED" ? ("done" as StepState) : ("bad" as StepState)) : ("pending" as StepState)),
    revalidate: (approval?.status === "APPROVED" ? ("done" as StepState) : ("pending" as StepState)),
    execute:
      executionStatus === "EXECUTED"
        ? ("done" as StepState)
        : executionStatus === "FAILED"
          ? ("bad" as StepState)
          : executionStatus === "PENDING"
            ? ("active" as StepState)
            : ("pending" as StepState),
    audit: audit.length > 0 ? ("done" as StepState) : ("pending" as StepState),
  };

  const decisionMeta: Record<string, { label: string; note: string }> = {
    ALLOW: { label: "Allow", note: "The policy engine authorized this action." },
    REQUIRE_APPROVAL: { label: "Approval required", note: "The policy engine requires a distinct human to approve this action." },
    DENY: { label: "Deny", note: "The policy engine denied this action." },
  };
  const decisionText = decisionMeta[decision] ?? { label: decision, note: "This request did not reach a policy decision." };

  return (
    <RegistryShell>
      <div className="mb-6">
        <Breadcrumbs
          items={[
            { label: "Control center", href: "/" },
            { label: "Actions", href: "/action-requests" },
            { label: request.action_name },
          ]}
        />
      </div>

      {/* Decision / outcome header */}
      <section className="rounded-card border border-hairline bg-surface p-6 lg:p-8">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="min-w-0 max-w-2xl">
            <p className="eyebrow text-inkFaint">Decision case file</p>
            <h1 className="mt-1.5 text-2xl font-semibold tracking-tight text-ink lg:text-3xl">{request.action_name}</h1>
            <div className="mt-4 flex flex-wrap items-center gap-2.5">
              <span className="text-sm font-medium text-inkSubtle">Decision</span>
              <Status value={decision} />
              <span className="mx-1 text-inkFaint">·</span>
              <span className="text-sm font-medium text-inkSubtle">Execution</span>
              <Status value={executionStatus} />
            </div>
            <p className="mt-3 text-[15px] leading-7 text-inkSubtle">{request.reason ?? decisionText.note}</p>
            {request.reason_code && <p className="mt-2 inline-block rounded-control border border-hairline bg-surfaceMuted px-2 py-0.5 font-mono text-[11px] text-inkSubtle">{request.reason_code}</p>}
          </div>
          <dl className="grid shrink-0 grid-cols-2 gap-x-8 gap-y-2 text-[13px] sm:grid-cols-2">
            <div className="col-span-2">
              <dt className="text-[11px] uppercase tracking-wide text-inkFaint">Requested</dt>
              <dd className="mt-0.5 text-inkMuted">{formatDateTime(request.requested_at)}</dd>
            </div>
            <div>
              <dt className="text-[11px] uppercase tracking-wide text-inkFaint">Decided</dt>
              <dd className="mt-0.5 text-inkMuted">{formatDateTime(request.decided_at)}</dd>
            </div>
            <div>
              <dt className="text-[11px] uppercase tracking-wide text-inkFaint">Reference</dt>
              <dd className="mt-0.5 font-mono text-xs text-inkSubtle">{shortId(request.id, 10)}</dd>
            </div>
          </dl>
        </div>
      </section>

      {/* WHO / WHAT / WHY / RISK */}
      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <section className="rounded-card border border-hairline bg-surface p-5">
          <p className="eyebrow text-inkFaint">Who is acting</p>
          <p className="mt-3 text-[15px] font-semibold text-ink">{request.agent_name}</p>
          <p className="mt-1 text-[13px] leading-5 text-inkSubtle">
            Acting for <span className="font-medium text-inkMuted">{principalName(request.principal_id, request.principal_name)}</span>
          </p>
        </section>
        <section className="rounded-card border border-hairline bg-surface p-5">
          <p className="eyebrow text-inkFaint">What</p>
          <p className="mt-3 text-[15px] font-semibold text-ink">{amountLine ?? request.action_name}</p>
          <p className="mt-1 text-[13px] leading-5 text-inkSubtle">
            {request.action_name} <span className="text-inkFaint">via</span> {request.tool_name}
          </p>
        </section>
        <section className="rounded-card border border-hairline bg-surface p-5">
          <p className="eyebrow text-inkFaint">Resource</p>
          <p className="mt-3 break-all text-[15px] font-semibold text-ink">{request.resource_type}</p>
          <p className="mt-1 break-all font-mono text-xs text-inkSubtle">{request.resource_key}</p>
        </section>
        <section className="rounded-card border border-hairline bg-surface p-5">
          <p className="eyebrow text-inkFaint">Risk</p>
          <div className="mt-3 flex items-center gap-2">
            <Status value={request.risk_classification ?? "LOW"} />
            {request.risk_score !== null && request.risk_score !== undefined && <span className="tnum text-[13px] font-medium text-inkMuted">{request.risk_score}/100</span>}
          </div>
        </section>
      </div>

      {/* Governance chain + evidence */}
      <div className="mt-6 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <section className="h-fit rounded-card border border-hairline bg-surface p-6">
          <div className="flex items-baseline justify-between gap-4">
            <div>
              <p className="eyebrow text-inkFaint">Governance chain</p>
              <h2 className="mt-1 text-base font-semibold tracking-tight text-ink">Where this action stands</h2>
            </div>
            <span className="text-xs text-inkFaint">{audit.length} events</span>
          </div>
          <div className="mt-5">
            <GovernanceStepper completedThrough="decide" overrides={overrides} />
          </div>
          <div className="mt-4 rounded-card border border-hairline bg-surfaceMuted px-4 py-3 text-[13px] leading-6 text-inkSubtle">
            <span className="font-medium text-ink">Execution outcome:</span> {executionReason}
          </div>
        </section>

        <div className="space-y-4">
          {/* Approval / execution */}
          <section className="rounded-card border border-hairline bg-surface p-6">
            <p className="eyebrow text-inkFaint">Approval & execution</p>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-xs text-inkFaint">Approval</p>
                <p className="mt-1 text-[15px] font-semibold text-ink">{approval ? <Status value={approval.status} /> : "Not required"}</p>
                {approval?.status === "PENDING" && approval.id && (
                  <Link href={`/approvals/${approval.id}`} className="mt-2 inline-block text-[13px] font-semibold text-signal hover:text-signalHover">
                    Review approval →
                  </Link>
                )}
                {approval && approval.decided_at && (
                  <p className="mt-2 text-xs text-inkSubtle">
                    Decided by {principalName(decidedBy)} · {formatDateTime(approval.decided_at)}
                  </p>
                )}
              </div>
              <div>
                <p className="text-xs text-inkFaint">Execution</p>
                <p className="mt-1 text-[15px] font-semibold text-ink">{executionStatus}</p>
                {obs?.execution?.provider_transaction_id && (
                  <p className="mt-2 font-mono text-[11px] text-inkSubtle">{obs.execution.provider_transaction_id}</p>
                )}
              </div>
            </div>
          </section>

          {/* Evidence disclosures */}
          <Disclosure title="Risk evidence & factors">
            {request.risk_factors.length === 0 ? (
              <p className="text-inkSubtle">No risk factors were recorded.</p>
            ) : (
              <ul className="divide-y divide-hairline">
                {request.risk_factors.map((factor) => (
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

          <Disclosure title="Request payload & parameters">
            <div className="overflow-x-auto rounded-card border border-hairline bg-surfaceSunken p-3">
              <pre className="text-xs leading-5 text-inkMuted">{JSON.stringify(request.parameters, null, 2)}</pre>
            </div>
          </Disclosure>

          <Disclosure title="Policy decision">
            <KeyValueList
              items={[
                { label: "Decision", value: <Status value={decision} /> },
                { label: "Reason code", value: request.reason_code ?? "—", mono: true },
                { label: "Reason", value: request.reason ?? decisionText.note },
                { label: "Matched on", value: `${request.decision ?? request.status}`, muted: true },
              ]}
            />
          </Disclosure>

          <Disclosure title={`Audit & proof (${audit.length} events)`}>
            {audit.length === 0 ? (
              <p className="text-inkSubtle">No audit events are available for this request.</p>
            ) : (
              <ol className="space-y-0.5">
                {audit.map((event) => (
                  <li key={event.id} className="flex flex-wrap items-baseline justify-between gap-3 border-b border-hairline py-2 text-sm last:border-0">
                    <span className="font-medium text-ink">{event.event_type}</span>
                    <span className="text-xs text-inkFaint">{formatDateTime(event.created_at)}</span>
                  </li>
                ))}
              </ol>
            )}
          </Disclosure>

          <div className="flex flex-wrap gap-2">
            <Link href={`/agents/${request.agent_id}`} className="rounded-control border border-hairline bg-surface px-3 py-1.5 text-[13px] font-medium text-inkMuted hover:bg-surfaceMuted">
              Open agent file
            </Link>
            <Link href={`/resources/${request.resource_id}`} className="rounded-control border border-hairline bg-surface px-3 py-1.5 text-[13px] font-medium text-inkMuted hover:bg-surfaceMuted">
              Open resource
            </Link>
            {approval && (
              <Link href={`/approvals/${approval.id}`} className="rounded-control border border-hairline bg-surface px-3 py-1.5 text-[13px] font-medium text-inkMuted hover:bg-surfaceMuted">
                Open approval
              </Link>
            )}
            {request.tenant_id && (
              <Link href={`/observability?request=${request.id}`} className="ml-auto text-[13px] font-semibold text-signal hover:text-signalHover">
                Open in observability →
              </Link>
            )}
          </div>
        </div>
      </div>
    </RegistryShell>
  );
}
