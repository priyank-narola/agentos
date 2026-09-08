"use client";

import { useCallback, useEffect, useState } from "react";

import {
  Approval, ApproverCandidate, GatewayResponse, ObservabilityActionDetail, TimelineEvent, TreasuryManifest, api,
} from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

type Phase = "configure" | "evaluated" | "final";

function money(amount: unknown, currency: string) {
  const value = Number(amount ?? 0);
  return new Intl.NumberFormat("en-US", { style: "currency", currency, minimumFractionDigits: 2 }).format(value);
}

export default function DemoPage() {
  const [manifest, setManifest] = useState<TreasuryManifest | null>(null);
  const [amount, setAmount] = useState("25000.00");
  const [currency, setCurrency] = useState("USD");
  const [phase, setPhase] = useState<Phase>("configure");
  const [gateway, setGateway] = useState<GatewayResponse | null>(null);
  const [approval, setApproval] = useState<Approval | null>(null);
  const [observability, setObservability] = useState<ObservabilityActionDetail | null>(null);
  const [audit, setAudit] = useState<TimelineEvent[]>([]);
  const [approvers, setApprovers] = useState<ApproverCandidate[]>([]);
  const [approverId, setApproverId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tamper, setTamper] = useState<Record<string, unknown> | null>(null);
  const [tamperBusy, setTamperBusy] = useState(false);

  useEffect(() => {
    api.treasuryBootstrap()
      .then((manifestData) => {
        setManifest(manifestData);
        setAmount(manifestData.default_amount);
        setCurrency(manifestData.default_currency);
        setApproverId(manifestData.approver.id);
      })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  const startRequest = useCallback(() => {
    if (!manifest) return;
    setError(null);
    setBusy(true);
    const params = {
      source_account_id: manifest.resource.resource_key,
      destination_account_id: "ACC-VENDOR-8888",
      amount,
      currency,
      beneficiary_id: "BEN-ACME-8888",
      transaction_reference: `REF-${crypto.randomUUID().slice(0, 8).toUpperCase()}`,
      purpose: "Quarterly vendor payout (governed demo)",
    };
    api.gateway({
      principal_id: manifest.requester.id,
      agent_id: manifest.agent.id,
      action_id: manifest.action.id,
      resource_id: manifest.resource.id,
      parameters: params,
      idempotency_key: `demo-${crypto.randomUUID()}`,
    })
      .then(async (gatewayResponse) => {
        setGateway(gatewayResponse);
        const approvals = await api.approvals();
        const linked = approvals.find((item) => item.action_request_id === gatewayResponse.action_request_id) ?? null;
        setApproval(linked);
        if (linked) {
          const approverData = await api.approvers(linked.id).catch(() => ({ approvers: [] as ApproverCandidate[] }));
          setApprovers(approverData.approvers);
          if (approverData.approvers.some((candidate) => candidate.id === manifest.approver.id)) {
            setApproverId(manifest.approver.id);
          } else if (approverData.approvers.length > 0) {
            setApproverId(approverData.approvers[0].id);
          }
        }
        setPhase("evaluated");
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setBusy(false));
  }, [manifest, amount, currency]);

  const refreshEvidence = useCallback(async (updated: Approval) => {
    setApproval(updated);
    if (manifest && updated.status === "APPROVED") {
      const detail = await api.observabilityActionRequest(updated.action_request_id, manifest.tenant_id).catch(() => null);
      setObservability(detail);
      const timelineData = await api.timeline(manifest.tenant_id).catch(() => null);
      const events = timelineData ? timelineData.events.filter((event) => event.action_request_id === updated.action_request_id) : [];
      setAudit(events.sort((a, b) => (a.created_at ?? "").localeCompare(b.created_at ?? "")));
    }
  }, [manifest]);

  const decide = useCallback((mode: "approve" | "reject") => {
    if (!approval || !approverId) return;
    setError(null);
    setBusy(true);
    api[mode](approval.id, approverId)
      .then(async (updated) => {
        setPhase("final");
        await refreshEvidence(updated);
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setBusy(false));
  }, [approval, approverId, refreshEvidence]);

  const runTamper = useCallback(() => {
    setTamperBusy(true);
    setTamper(null);
    api.scenarioRun("SCENARIO_D")
      .then(setTamper)
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setTamperBusy(false));
  }, []);

  const executionSucceeded = observability?.execution?.status === "SUCCEEDED";
  const approved = approval?.status === "APPROVED";
  const rejected = approval?.status === "REJECTED";

  const requester = manifest?.requester;
  const approver = manifest?.approver;

  const steps: Array<{ label: string; detail: string; tone: "done" | "active" | "muted" | "bad" }> = [];
  if (!gateway) {
    steps.push({ label: "Agent requests a consequential financial action", detail: "Configure the sandbox wire below.", tone: "active" });
  } else {
    steps.push({ label: "Agent requests $25,000 wire", detail: `${money(amount, currency)} USD wire transfer requested by ${manifest?.agent.name}.`, tone: "done" });
    steps.push({ label: "Identity & delegation resolved", detail: `${manifest?.agent.name} is acting for ${requester?.name} (${requester?.title}).`, tone: "done" });
    steps.push({ label: "Policy evaluation", detail: `${gateway.reason_code ?? gateway.reason ?? "Evaluated"}.`, tone: "done" });
    steps.push({ label: "Risk calculated", detail: `${gateway.risk_score ?? "--"}/100 · ${gateway.risk_classification ?? "--"}`, tone: "done" });
    if (approval?.status === "PENDING") {
      steps.push({ label: "Human approval required", detail: `${requester?.name} requested; ${approver?.name} (${approver?.title}) must decide.`, tone: "active" });
    }
    if (phase === "final") {
      steps.push({ label: "TOCTOU security revalidation", detail: approved ? "Security context re-validated at approval time — passed." : rejected ? "Reviewer rejected before execution." : "Revalidation result unavailable.", tone: approved ? "done" : "muted" });
      steps.push({ label: "Sandbox execution", detail: executionSucceeded ? "Execution succeeded inside the sandbox provider." : rejected ? "Not executed." : "Execution result unavailable.", tone: executionSucceeded ? "done" : rejected ? "muted" : "muted" });
      steps.push({ label: "FinancialExecution ledger", detail: observability?.execution?.status ? `${observability.execution.status} · ${observability.execution.provider_transaction_id ?? ""}` : "No ledger record.", tone: executionSucceeded ? "done" : "muted" });
      steps.push({ label: "Audit trail", detail: `${audit.length} audit events recorded.`, tone: audit.length ? "done" : "muted" });
    }
  }

  const finalLabel = approved && executionSucceeded ? "AUTHORIZED → APPROVED → EXECUTED IN SANDBOX → AUDITED" : approved ? "AUTHORIZED → APPROVED (execution pending/failed)" : rejected ? "BLOCKED — REJECTED BY APPROVER" : "";

  return (
    <RegistryShell title="Flagship demo" eyebrow="Guided customer demonstration">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded border border-amber-300 bg-amber-50 px-5 py-4">
        <p className="text-sm font-semibold text-amber-900">SANDBOX DEMONSTRATION — NO REAL MONEY MOVEMENT</p>
        <p className="text-xs text-amber-800">Every action executes inside the AgentOS sandbox payment provider only.</p>
      </div>

      {error && <StateMessage tone="error">{error}</StateMessage>}
      {!manifest && !error && <StateMessage>Preparing the treasury demonstration environment…</StateMessage>}

      {manifest && (
        <>
          <section className="border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-center gap-8">
              <div className="min-w-[180px]">
                <p className="text-xs uppercase tracking-wide text-slate-400">Agent</p>
                <p className="mt-1 text-xl font-semibold text-ink">{manifest.agent.name}</p>
                <p className="mt-1 text-xs text-slate-500">{manifest.agent.purpose}</p>
              </div>
              <div className="hidden h-10 border-l border-slate-200" />
              <div className="min-w-[180px]">
                <p className="text-xs uppercase tracking-wide text-slate-400">Acting for (requester)</p>
                <p className="mt-1 text-xl font-semibold text-ink">{requester?.name}</p>
                <p className="mt-1 text-xs text-slate-500">{requester?.title}</p>
              </div>
              <div className="hidden h-10 border-l border-slate-200" />
              <div className="min-w-[180px]">
                <p className="text-xs uppercase tracking-wide text-slate-400">Independent approver</p>
                <p className="mt-1 text-xl font-semibold text-ink">{approver?.name}</p>
                <p className="mt-1 text-xs text-slate-500">{approver?.title} · cannot be the requester</p>
              </div>
              <div className="min-w-[140px] rounded border border-slate-200 bg-slate-50 px-4 py-3">
                <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Target</p>
                <p className="mt-1 text-sm font-medium text-ink">{manifest.action.name}</p>
                <p className="text-xs text-slate-500">{manifest.resource.resource_key}</p>
              </div>
            </div>
          </section>

          {phase === "configure" && (
            <section className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
              <div className="border border-slate-200 bg-white p-6">
                <h2 className="font-semibold text-ink">Request the $25,000 USD sandbox wire</h2>
                <p className="mt-2 text-sm text-slate-500">TreasuryBot-v1, acting for {requester?.name}, requests a high-value wire transfer to a vendor account.</p>
                <div className="mt-5 grid gap-4 sm:grid-cols-2">
                  <label className="block text-sm font-medium text-slate-600">Amount<input value={amount} onChange={(event) => setAmount(event.target.value)} className="mt-2 block w-full border border-slate-300 px-3 py-2.5 text-sm tabular-nums" /></label>
                  <label className="block text-sm font-medium text-slate-600">Currency<select value={currency} onChange={(event) => setCurrency(event.target.value)} className="mt-2 block w-full border border-slate-300 bg-white px-3 py-2.5 text-sm"><option value="USD">USD</option><option value="EUR">EUR</option><option value="GBP">GBP</option></select></label>
                </div>
                <dl className="mt-5 space-y-2 text-sm">
                  <div className="flex justify-between border-b border-slate-100 pb-2"><dt className="text-slate-500">Action</dt><dd className="font-medium text-ink">{manifest.action.name} · {manifest.action.risk_level} risk</dd></div>
                  <div className="flex justify-between border-b border-slate-100 pb-2"><dt className="text-slate-500">Resource</dt><dd className="font-medium text-ink">{manifest.resource.resource_type} / {manifest.resource.resource_key}</dd></div>
                  <div className="flex justify-between border-b border-slate-100 pb-2"><dt className="text-slate-500">Policy</dt><dd className="font-medium text-ink">{manifest.policy.name} v{manifest.policy.version}</dd></div>
                </dl>
                <button type="button" disabled={busy} onClick={startRequest} className="mt-6 w-full bg-ink px-4 py-3 text-sm font-medium text-white disabled:bg-slate-300">{busy ? "Intercepting…" : "Request $25,000 wire transfer"}</button>
              </div>
              <div className="border border-slate-200 bg-white p-6">
                <h2 className="font-semibold text-ink">What happens next</h2>
                <ol className="mt-4 space-y-3 text-sm text-slate-600">
                  <li>AgentOS identifies the agent and the human it acts for.</li>
                  <li>Policy is evaluated against the exact action.</li>
                  <li>Risk is calculated (explainable, deterministic).</li>
                  <li>A high-value wire requires a one-time human approval by {approver?.name}.</li>
                  <li>Approval is bound to the exact payload; revalidation happens at approval time.</li>
                  <li>Approval executes inside the sandbox and every step is audited.</li>
                </ol>
              </div>
            </section>
          )}

          {phase !== "configure" && (
            <div className="mt-6 grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
              <section className="border border-slate-200 bg-ink p-6 text-white">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-300">Governance chain</p>
                <div className="mt-6 space-y-1">
                  {steps.map((step, index) => (
                    <div key={step.label} className="relative flex gap-4 pb-5">
                      <div className={`relative z-10 mt-0.5 h-3 w-3 shrink-0 rounded-full border ${step.tone === "done" ? "border-emerald-300 bg-emerald-300" : step.tone === "active" ? "border-amber-300 bg-amber-300" : step.tone === "bad" ? "border-red-400 bg-red-400" : "border-slate-600 bg-ink"}`} />
                      {index < steps.length - 1 && <span className="absolute left-[5px] top-3 h-full w-px bg-white/15" />}
                      <div>
                        <p className={`text-xs font-semibold tracking-wide ${step.tone === "muted" ? "text-slate-500" : "text-white"}`}>{step.label}</p>
                        <p className="mt-1 text-xs leading-5 text-slate-400">{step.detail}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <section className="space-y-6">
                {gateway && (
                  <div className="border border-slate-200 bg-white p-6">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-wide text-slate-400">Gateway decision</p>
                        <p className="mt-1 text-2xl font-semibold text-ink">{gateway.gateway_status}</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <StatusPill value={`RISK ${gateway.risk_score ?? "--"}/100`} />
                        <StatusPill value={gateway.risk_classification ?? "--"} />
                        <StatusPill value={gateway.reason_code ?? "--"} />
                      </div>
                    </div>
                    <div className="mt-5 grid gap-6 sm:grid-cols-2">
                      <div>
                        <p className="text-xs uppercase tracking-wide text-slate-400">Requested amount</p>
                        <p className="mt-1 text-3xl font-semibold text-ink">{money(amount, currency)}</p>
                        <p className="mt-2 text-xs text-slate-500">Action request {gateway.action_request_id}</p>
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-wide text-slate-400">Risk factors</p>
                        <div className="mt-2 space-y-1.5">
                          {gateway.risk_factors.map((factor) => <p key={factor.code} className="flex justify-between border-b border-slate-100 pb-1.5 text-xs"><span className="text-slate-500">{factor.explanation}</span><span className="font-mono text-signal">+{factor.contribution}</span></p>)}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {phase === "evaluated" && approval?.status === "PENDING" && (
                  <div className="border border-amber-200 bg-amber-50/40 p-6">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber-700">Human approval required</p>
                    <div className="mt-4 grid gap-4 md:grid-cols-2">
                      <div className="border border-slate-200 bg-white p-4">
                        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Requester</p>
                        <p className="mt-1 font-semibold text-ink">{requester?.name}</p>
                        <p className="text-xs text-slate-500">{requester?.title}</p>
                      </div>
                      <div className="border border-signal/20 bg-white p-4">
                        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Deciding approver</p>
                        <select value={approverId} onChange={(event) => setApproverId(event.target.value)} disabled={busy} className="mt-1 w-full border border-slate-300 bg-white px-3 py-2 text-sm" aria-label="Select approver">
                          {approvers.length === 0 && <option value={manifest.approver.id}>{approver?.name} ({approver?.title})</option>}
                          {approvers.map((candidate) => <option key={candidate.id} value={candidate.id}>{candidate.name}</option>)}
                        </select>
                      </div>
                    </div>
                    <p className="mt-4 text-sm text-slate-600">Approving authorizes this exact ${money(amount, currency)} payload. The payload is digest-bound — if it changes after approval, AgentOS blocks execution.</p>
                    <div className="mt-5 flex flex-wrap gap-3">
                      <button type="button" disabled={busy || !approverId} onClick={() => decide("approve")} className="bg-signal px-6 py-3 text-sm font-medium text-white disabled:bg-slate-300">{busy ? "Processing…" : "Approve as " + approver?.name}</button>
                      <button type="button" disabled={busy || !approverId} onClick={() => decide("reject")} className="bg-red-700 px-6 py-3 text-sm font-medium text-white disabled:bg-slate-300">Reject</button>
                    </div>
                  </div>
                )}

                {phase === "final" && finalLabel && (
                  <div className={`border p-6 ${approved && executionSucceeded ? "border-emerald-300 bg-emerald-50" : rejected ? "border-red-300 bg-red-50" : "border-slate-300 bg-white"}`}>
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Final result</p>
                    <p className={`mt-2 text-2xl font-bold ${approved && executionSucceeded ? "text-emerald-800" : rejected ? "text-red-800" : "text-ink"}`}>{finalLabel}</p>
                    <p className="mt-2 text-xs text-amber-800">SANDBOX DEMONSTRATION — NO REAL MONEY MOVEMENT.</p>
                  </div>
                )}

                {phase === "final" && audit.length > 0 && (
                  <div className="border border-slate-200 bg-white p-6">
                    <h2 className="font-semibold text-ink">Audit trail ({audit.length} events)</h2>
                    <ol className="mt-4 space-y-2">
                      {audit.map((event) => (
                        <li key={event.id} className="flex items-baseline justify-between gap-4 border-b border-slate-100 pb-2 text-sm">
                          <span className="font-medium text-ink">{event.event_type}</span>
                          <span className="text-xs text-slate-400">{event.created_at ? new Date(event.created_at).toLocaleString() : ""}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
              </section>
            </div>
          )}

          <section className="mt-8 border-t border-slate-200 pt-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-ink">Tamper demonstration</h2>
                <p className="mt-1 max-w-2xl text-sm text-slate-500">Payload integrity is a core AgentOS guarantee. Run the built-in scenario that attempts to modify an approved payload after approval.</p>
              </div>
              <button type="button" disabled={tamperBusy} onClick={runTamper} className="border border-red-300 bg-white px-5 py-3 text-sm font-medium text-red-700 disabled:text-slate-300">{tamperBusy ? "Running…" : "Run tamper scenario"}</button>
            </div>
            {tamper && (
              <div className="mt-4 border border-red-200 bg-red-50 p-5">
                <p className="text-sm font-semibold text-red-800">Result: {String(tamper.final_outcome ?? "")} · {String(tamper.approval_state ?? "")}</p>
                <p className="mt-2 text-xs leading-5 text-slate-600">
                  An approved sandbox wire (USD 50,000) had its payload altered to USD 500,000 after approval. On the approval attempt, AgentOS detected the SHA-256 payload digest mismatch and blocked execution — {String(tamper.execution_state ?? "")}.
                </p>
                <p className="mt-2 text-[11px] text-slate-400">Action request: {String(tamper.action_request_id ?? "")} · Risk classification: {String(tamper.risk_classification ?? "")}</p>
              </div>
            )}
            {!tamper && phase !== "final" && (
              <div className="mt-4 border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-500">Run to show AgentOS detecting a payload modification and blocking execution.</div>
            )}
          </section>
        </>
      )}
    </RegistryShell>
  );
}
