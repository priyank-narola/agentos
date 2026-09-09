"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  Approval, ApproverCandidate, GatewayResponse, ObservabilityActionDetail, TimelineEvent, TreasuryManifest, api, devTokenFor,
} from "@/lib/api";
import { RegistryShell, StateMessage } from "@/components/registry-shell";

type Phase = "idle" | "pending_approval" | "decided" | "blocked";

const SCENARIOS: Array<{ key: string; title: string; what: string; run: string }> = [
  { key: "A", title: "Low-risk action (auto-authorized)", what: "A small, allowed vendor payout is evaluated and auto-authorized.", run: "Run allowed scenario" },
  { key: "C", title: "Unauthorized action", what: "An agent requests a transfer it has no policy allowance for.", run: "Run blocked scenario" },
  { key: "D", title: "Payload tampering", what: "The approved payload is modified after approval.", run: "Run tamper scenario" },
  { key: "E", title: "Revoked delegation", what: "The delegation is revoked while the request awaits approval.", run: "Run revocation scenario" },
  { key: "F", title: "Cross-tenant access", what: "An agent in one tenant targets a resource in another.", run: "Run isolation scenario" },
  { key: "G", title: "Provider timeout", what: "The execution provider times out mid-transfer.", run: "Run timeout scenario" },
  { key: "H", title: "Duplicate execution", what: "The same request is submitted a second time.", run: "Run duplicate scenario" },
];

const SCENARIO_RESULT: Record<string, { outcome: string; why: string; tone: "ok" | "blocked" | "info" }> = {
  SUCCESS: { outcome: "AUTHORIZED & EXECUTED IN SANDBOX", why: "Low-risk action was within policy and executed in the sandbox.", tone: "ok" },
  BLOCKED_BY_POLICY: { outcome: "BLOCKED", why: "The agent is not authorized for this action under policy.", tone: "blocked" },
  TAMPER_BLOCKED: { outcome: "BLOCKED", why: "The approved payload digest does not match the execution payload.", tone: "blocked" },
  TOCTOU_BLOCKED: { outcome: "BLOCKED", why: "The delegation was revoked before execution.", tone: "blocked" },
  CROSS_TENANT_BLOCKED: { outcome: "BLOCKED", why: "The action targeted a resource outside the agent's tenant.", tone: "blocked" },
  DUPLICATE_PREVENTED: { outcome: "DUPLICATE PREVENTED", why: "The idempotency guard blocked a repeated execution.", tone: "info" },
  SAFE_TIMEOUT_HANDLED: { outcome: "TIMEOUT HANDLED", why: "The provider timeout was contained; no false success was recorded.", tone: "info" },
  FAILED: { outcome: "SCENARIO FAILED", why: "The scenario did not reach its expected outcome.", tone: "blocked" },
};

function money(amount: unknown, currency: string) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency, minimumFractionDigits: 2 }).format(Number(amount ?? 0));
}

export default function DemoPage() {
  const [manifest, setManifest] = useState<TreasuryManifest | null>(null);
  const [amount, setAmount] = useState("25000.00");
  const [currency, setCurrency] = useState("USD");
  const [phase, setPhase] = useState<Phase>("idle");
  const [gateway, setGateway] = useState<GatewayResponse | null>(null);
  const [approval, setApproval] = useState<Approval | null>(null);
  const [obs, setObs] = useState<ObservabilityActionDetail | null>(null);
  const [audit, setAudit] = useState<TimelineEvent[]>([]);
  const [approvers, setApprovers] = useState<ApproverCandidate[]>([]);
  const [approverId, setApproverId] = useState("");
  const [scenarioResults, setScenarioResults] = useState<Record<string, Record<string, unknown>>>({});
  const [delegationScopes, setDelegationScopes] = useState<string[]>([]);
  const [busy, setBusy] = useState<"gateway" | "approve" | "reject" | string | null>(null);
  const [runningScenario, setRunningScenario] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api.treasuryBootstrap()
      .then(async (m) => {
        if (!active) return;
        setManifest(m); setAmount(m.default_amount); setCurrency(m.default_currency); setApproverId(m.approver.id);
        const delegations = await api.delegations().catch(() => [] as Array<{ agent_id: string; scope: string }>);
        if (active) setDelegationScopes(delegations.filter((d) => d.agent_id === m.agent.id).map((d) => d.scope).slice(0, 4));
      })
      .catch((reason: Error) => { if (active) setError(reason.message); });
    return () => { active = false; };
  }, []);

  const loadEvidence = useCallback(async (updated: Approval) => {
    setApproval(updated);
    if (!manifest) return;
    if (updated.status === "APPROVED") {
      const detail = await api.observabilityActionRequest(updated.action_request_id, manifest.tenant_id).catch(() => null);
      setObs(detail);
      const t = await api.timeline(manifest.tenant_id).catch(() => null);
      setAudit(t ? t.events.filter((e) => e.action_request_id === updated.action_request_id).sort((a, b) => (a.created_at ?? "").localeCompare(b.created_at ?? "")) : []);
    }
  }, [manifest]);

  const startRequest = useCallback(async () => {
    if (!manifest) return;
    setError(null);
    setBusy("gateway");
    try {
      await devTokenFor(manifest.requester.external_id).catch(() => undefined);
      const params = {
        source_account_id: manifest.resource.resource_key,
        destination_account_id: "ACC-VENDOR-8888",
        amount, currency,
        beneficiary_id: "BEN-ACME-8888",
        transaction_reference: `REF-${crypto.randomUUID().slice(0, 8).toUpperCase()}`,
        purpose: "Quarterly vendor payout (governed demo)",
      };
      const gatewayResponse = await api.gateway({
        principal_id: manifest.requester.id, agent_id: manifest.agent.id,
        action_id: manifest.action.id, resource_id: manifest.resource.id,
        parameters: params, idempotency_key: `demo-${crypto.randomUUID()}`,
      });
      setGateway(gatewayResponse);
      const approvals = await api.approvals();
      const linked = approvals.find((a) => a.action_request_id === gatewayResponse.action_request_id) ?? null;
      setApproval(linked);
      setObs(null); setAudit([]);
      if (linked) {
        const data = await api.approvers(linked.id).catch(() => ({ approvers: [] as ApproverCandidate[] }));
        setApprovers(data.approvers);
        const eligible = data.approvers.some((c) => c.id === manifest.approver.id) ? manifest.approver.id : data.approvers[0]?.id ?? "";
        setApproverId(eligible);
        setPhase("pending_approval");
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Request failed");
    } finally { setBusy(null); }
  }, [manifest, amount, currency]);

  const decide = useCallback(async (mode: "approve" | "reject") => {
    if (!approval || !approverId) return;
    setError(null); setBusy(mode);
    try {
      const candidate = approvers.find((c) => c.id === approverId);
      const externalId = candidate?.external_id ?? manifest?.approver.external_id;
      if (externalId) await devTokenFor(externalId).catch(() => undefined);
      const updated = await api[mode](approval.id, approverId);
      setPhase(mode === "approve" ? "decided" : "blocked");
      await loadEvidence(updated);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : `${mode} failed`);
    } finally { setBusy(null); }
  }, [approval, approverId, approvers, manifest, loadEvidence]);

  const runScenario = useCallback(async (key: string) => {
    setRunningScenario(key); setError(null);
    try {
      const res = await api.scenarioRun(`SCENARIO_${key}`);
      setScenarioResults((prev) => ({ ...prev, [key]: res }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Scenario failed");
    } finally { setRunningScenario(null); }
  }, []);

  const reset = () => {
    setPhase("idle"); setGateway(null); setApproval(null); setObs(null); setAudit([]); setScenarioResults({}); setError(null);
  };

  const executed = obs?.execution?.status === "SUCCEEDED";
  const decidedApproved = phase === "decided";
  const blockedByReviewer = phase === "blocked";
  const requester = manifest?.requester;
  const approver = manifest?.approver;

  const stages: Array<{ label: string; caption: string; state: "done" | "active" | "pending" | "bad" }> = [
    { label: "Request", caption: gateway ? `Agent requested ${money(amount, currency)} ${currency}` : "Agent requests a wire transfer", state: gateway ? "done" : phase === "idle" ? "pending" : "pending" },
    { label: "Identify", caption: gateway ? `${manifest?.agent.name} acting for ${requester?.name}` : "Identity & delegation resolved", state: gateway ? "done" : "pending" },
    { label: "Authorize", caption: gateway ? `Policy: ${gateway.reason_code ?? "evaluated"}` : "Policy evaluation", state: gateway ? "done" : "pending" },
    { label: "Evaluate", caption: gateway ? `Risk ${gateway.risk_score ?? "--"}/100 · ${gateway.risk_classification ?? "--"}` : "Risk analysis", state: gateway ? "done" : "pending" },
    { label: "Approve", caption: approval?.status === "PENDING" ? `Requires ${approver?.name}` : approval ? approval.status : "Human approval", state: approval?.status === "PENDING" ? "active" : approval?.status === "APPROVED" ? "done" : approval?.status === "REJECTED" ? "bad" : "pending" },
    { label: "Revalidate", caption: decidedApproved ? "Security context revalidated before execution" : "TOCTOU / payload revalidation", state: decidedApproved ? "done" : "pending" },
    { label: "Execute", caption: executed ? `Executed in sandbox (${obs?.execution.provider_transaction_id ?? ""})` : blockedByReviewer ? "Not executed" : "Sandbox execution", state: executed ? "done" : blockedByReviewer ? "bad" : "pending" },
    { label: "Audit", caption: audit.length ? `${audit.length} audit events recorded` : "Evidence recorded", state: executed && audit.length ? "done" : "pending" },
  ];

  const stageColor: Record<string, string> = { done: "border-emerald-400 bg-emerald-400", active: "border-amber-300 bg-amber-300", bad: "border-red-500 bg-red-500", pending: "border-slate-400 bg-ink" };

  return (
    <RegistryShell title="Treasury governance demo" eyebrow="Guided demonstration">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded border border-amber-300 bg-amber-50 px-5 py-4">
        <p className="text-sm font-semibold text-amber-900">SANDBOX DEMONSTRATION — NO REAL MONEY MOVEMENT</p>
        <p className="text-xs text-amber-800">Every action executes inside the AgentOS sandbox payment provider only.</p>
      </div>

      {error && <StateMessage tone="error">{error}</StateMessage>}

      {phase === "idle" && manifest && !gateway && (
        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="border border-slate-200 bg-white p-6">
            <h2 className="text-xl font-semibold text-ink">What will happen</h2>
            <ol className="mt-5 space-y-3 text-sm leading-6 text-slate-600">
              <li><strong className="text-ink">Agent requests a financial action.</strong> TreasuryBot-v1, acting for {requester?.name} ({requester?.title}), requests a {money(Number(amount), currency)} USD wire transfer.</li>
              <li><strong className="text-ink">AgentOS governs the request.</strong> Identity and delegation are resolved, policy is evaluated, and risk is calculated.</li>
              <li><strong className="text-ink">A high-value wire requires human approval.</strong> {approver?.name} ({approver?.title}) — an independent human — reviews the exact payload and decides.</li>
              <li><strong className="text-ink">Revalidation, execution, proof.</strong> The request is revalidated, executed in the sandbox, recorded in the execution ledger, and audited.</li>
              <li><strong className="text-ink">See AgentOS block unsafe actions.</strong> Run the unauthorized, tamper, revocation, isolation, timeout, and duplicate scenarios below.</li>
            </ol>
          </div>
          <div className="border border-slate-200 bg-white p-6">
            <h2 className="font-semibold text-ink">Action to demonstrate</h2>
            <div className="mt-4 space-y-4">
              <label className="block text-sm font-medium text-slate-600">Amount
                <input value={amount} onChange={(e) => setAmount(e.target.value)} className="mt-1 block w-full border border-slate-300 px-3 py-2.5 text-sm tabular-nums" />
              </label>
              <label className="block text-sm font-medium text-slate-600">Currency
                <select value={currency} onChange={(e) => setCurrency(e.target.value)} className="mt-1 block w-full border border-slate-300 bg-white px-3 py-2.5 text-sm">
                  <option value="USD">USD</option><option value="EUR">EUR</option><option value="GBP">GBP</option>
                </select>
              </label>
              <button type="button" disabled={busy !== null} onClick={startRequest} className="w-full bg-ink px-4 py-3 text-sm font-medium text-white disabled:bg-slate-300">{busy === "gateway" ? "Evaluating…" : "Run Treasury Governance Demo"}</button>
            </div>
          </div>
        </section>
      )}

      {manifest && (phase !== "idle" || gateway) && (
        <section className="grid gap-6 xl:grid-cols-[0.78fr_1.22fr]">
          <div className="h-fit rounded border border-slate-200 bg-white p-5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">Governance lifecycle</p>
            <div className="mt-4 space-y-1">
              {stages.map((stage, i) => (
                <div key={stage.label} className="relative flex gap-3 pb-3">
                  <div className={`relative z-10 mt-1 h-3 w-3 shrink-0 rounded-full border ${stageColor[stage.state]}`} />
                  {i < stages.length - 1 && <span className="absolute left-[5px] top-4 h-full w-px bg-slate-200" />}
                  <div className={stage.state === "pending" ? "opacity-50" : ""}>
                    <p className="text-sm font-semibold text-ink">{stage.label}</p>
                    <p className="text-xs leading-5 text-slate-500">{stage.caption}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-5">
            <section className="border border-slate-200 bg-white p-6">
              <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-400">Requested action</p>
                  <p className="mt-1 text-3xl font-semibold tabular-nums text-ink">{money(amount, currency)} <span className="text-lg text-slate-400">{currency}</span></p>
                  <p className="text-sm text-slate-500">{manifest.action.name} · {manifest.resource.resource_key}</p>
                </div>
                {gateway && (
                  <div className="flex flex-wrap gap-2">
                    {gateway.gateway_status === "PENDING_APPROVAL" && <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">APPROVAL REQUIRED</span>}
                    {approval?.status && <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">{approval.status}</span>}
                  </div>
                )}
              </div>
              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                <div className="border border-slate-100 bg-slate-50 p-4"><p className="text-[11px] font-semibold uppercase text-slate-400">Agent</p><p className="mt-1 font-medium text-ink">{manifest.agent.name}</p><p className="text-xs text-slate-500">requesting</p></div>
                <div className="border border-slate-100 bg-slate-50 p-4"><p className="text-[11px] font-semibold uppercase text-slate-400">On behalf of</p><p className="mt-1 font-medium text-ink">{requester?.name}</p><p className="text-xs text-slate-500">{requester?.title}</p></div>
                <div className="border border-slate-100 bg-slate-50 p-4"><p className="text-[11px] font-semibold uppercase text-slate-400">Independent approver</p><p className="mt-1 font-medium text-ink">{approver?.name}</p><p className="text-xs text-slate-500">{approver?.title}</p></div>
              </div>
              <div className="mt-3 border border-slate-100 bg-white p-3 text-sm">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Authority (delegation)</p>
                <p className="mt-1 text-slate-700">
                  {requester?.name} delegated scope <span className="font-mono font-semibold text-ink">{delegationScopes.join(", ") || "wire_transfer"}</span> to {manifest.agent.name}; the requested action ({manifest.action.name}) is within that delegated capability.
                </p>
              </div>
            </section>

            {phase === "pending_approval" && approval && (
              <section className="border border-amber-300 bg-amber-50/40 p-6">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber-800">Request requires human approval</p>
                <p className="mt-2 text-sm text-slate-700">A high-value wire is only allowed with a one-time approval by a distinct, eligible human — never the requester.</p>
                <div className="mt-3 flex flex-wrap gap-2 text-xs">
                  <span className="rounded border border-emerald-200 bg-emerald-50 px-2 py-1 font-medium text-emerald-800">Payload digest-bound — any change after approval blocks execution</span>
                  {approval.expires_at && <span className="rounded border border-slate-200 bg-white px-2 py-1 text-slate-600">Approval expires {new Date(approval.expires_at).toLocaleString()}</span>}
                  <span className="rounded border border-slate-200 bg-white px-2 py-1 text-slate-600">Policy: {manifest.policy.name} v{manifest.policy.version} (allow rule; high-risk ⇒ approval)</span>
                </div>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <div className="border border-slate-200 bg-white p-4">
                    <p className="text-[11px] font-semibold uppercase text-slate-400">Why risk is {gateway?.risk_classification ?? "--"}</p>
                    {gateway?.risk_factors.map((f) => <p key={f.code} className="mt-1 flex justify-between border-b border-slate-100 py-1 text-xs"><span>{f.explanation}</span><span className="font-mono text-signal">+{f.contribution}</span></p>)}
                  </div>
                  <div className="border border-slate-200 bg-white p-4">
                    <p className="text-[11px] font-semibold uppercase text-slate-400">Who can approve</p>
                    <select value={approverId} onChange={(e) => setApproverId(e.target.value)} className="mt-1 w-full border border-slate-300 bg-white px-3 py-2 text-sm" aria-label="Select approver">
                      {approvers.length === 0 && <option value={manifest.approver.id}>{approver?.name}</option>}
                      {approvers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                    <p className="mt-2 text-xs text-slate-500">The requester can never approve their own action (separation of duties).</p>
                    <div className="mt-4 flex flex-wrap gap-2">
                      <button type="button" disabled={busy !== null || !approverId} onClick={() => decide("approve")} className="bg-signal px-5 py-2.5 text-sm font-medium text-white disabled:bg-slate-300">{busy === "approve" ? "Approving…" : "Approve as " + approver?.name}</button>
                      <button type="button" disabled={busy !== null} onClick={() => decide("reject")} className="bg-red-700 px-5 py-2.5 text-sm font-medium text-white disabled:bg-slate-300">Reject</button>
                    </div>
                  </div>
                </div>
              </section>
            )}

            {(phase === "decided" || phase === "blocked") && (
              <section className={`border p-6 ${decidedApproved && executed ? "border-emerald-300 bg-emerald-50" : "border-red-300 bg-red-50"}`}>
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Final result</p>
                {decidedApproved && executed && <p className="mt-2 text-2xl font-bold text-emerald-800">ACTION GOVERNED — AUTHORIZED → APPROVED → EXECUTED IN SANDBOX → AUDITED</p>}
                {decidedApproved && !executed && <p className="mt-2 text-2xl font-bold text-ink">APPROVED — awaiting/checking execution evidence</p>}
                {blockedByReviewer && <p className="mt-2 text-2xl font-bold text-red-800">BLOCKED — REJECTED BY APPROVER · NOT EXECUTED</p>}
                <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2 xl:grid-cols-3">
                  {[["Principal", requester?.name], ["Action", `${money(amount, currency)} ${currency} wire`], ["Approver", approver?.name], ["Integrity", "Payload verified unchanged"], ["Revalidation", "TOCTOU security revalidation passed"], ["Execution record", executed ? `Sandbox · ${obs?.execution.provider_transaction_id ?? ""}` : "Not executed"]].map(([label, value]) => (
                    <div key={label} className="border border-slate-200 bg-white/70 p-3"><p className="text-[10px] uppercase tracking-wide text-slate-400">{label}</p><p className="mt-0.5 font-medium text-ink">{value}</p></div>
                  ))}
                </div>
                {executed && (
                  <p className="mt-3 text-xs text-emerald-800">FinancialExecution ledger: {obs?.execution.status} — recorded by {obs?.execution.provider_name} under action request {approval?.action_request_id}</p>
                )}
                {approval && (
                  <div className="mt-4 flex flex-wrap gap-2 text-sm">
                    <span className="self-center text-xs text-slate-400">Continue into the product:</span>
                    <Link href={`/action-requests/${approval.action_request_id}`} className="rounded border border-ink bg-white px-3 py-1 text-xs font-medium text-ink hover:bg-ink hover:text-white">View action case file</Link>
                    <Link href={`/approvals/${approval.id}`} className="rounded border border-ink bg-white px-3 py-1 text-xs font-medium text-ink hover:bg-ink hover:text-white">View approval</Link>
                    <Link href="/observability" className="rounded border border-ink bg-white px-3 py-1 text-xs font-medium text-ink hover:bg-ink hover:text-white">View observability</Link>
                  </div>
                )}
              </section>
            )}

            {audit.length > 0 && (
              <section className="border border-slate-200 bg-white p-6">
                <div className="flex items-end justify-between gap-3">
                  <h2 className="font-semibold text-ink">Audit evidence ({audit.length} events)</h2>
                  <button type="button" onClick={reset} className="text-xs font-semibold text-signal hover:underline">Reset & run again</button>
                </div>
                <ol className="mt-4 space-y-1">
                  {audit.map((event) => (
                    <li key={event.id} className="flex items-baseline justify-between gap-4 border-b border-slate-100 py-1.5 text-sm">
                      <span className="font-medium text-ink">{event.event_type}</span>
                      <span className="text-xs text-slate-400">{event.created_at ? new Date(event.created_at).toLocaleTimeString() : ""}</span>
                    </li>
                  ))}
                </ol>
              </section>
            )}
          </div>
        </section>
      )}

      <section className="mt-10 border-t border-slate-200 pt-7">
        <h2 className="text-xl font-semibold text-ink">AgentOS blocks unsafe actions</h2>
        <p className="mt-1 max-w-3xl text-sm text-slate-500">These scenarios reuse the verified governance engine to show exactly why each unsafe action is stopped. Each run creates an isolated sandbox tenant.</p>
        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {SCENARIOS.map((scenario) => {
            const result = scenarioResults[scenario.key];
            const meta = result ? SCENARIO_RESULT[String(result.final_outcome)] ?? SCENARIO_RESULT.FAILED : null;
            const tone = meta?.tone === "ok" ? "border-emerald-300 bg-emerald-50" : meta?.tone === "blocked" ? "border-red-300 bg-red-50" : "border-slate-200 bg-white";
            return (
              <div key={scenario.key} className={`border p-5 ${result ? tone : "border-slate-200 bg-white"}`}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-ink">{scenario.title}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{scenario.what}</p>
                  </div>
                  <span className="shrink-0 text-xs font-bold text-slate-400">SCENARIO_{scenario.key}</span>
                </div>
                {!result ? (
                  <button type="button" disabled={runningScenario !== null} onClick={() => runScenario(scenario.key)} className="mt-4 border border-ink px-4 py-2 text-xs font-medium text-ink hover:bg-ink hover:text-white disabled:text-slate-300 disabled:border-slate-300">
                    {runningScenario === scenario.key ? "Running…" : scenario.run}
                  </button>
                ) : (
                  <div className="mt-4">
                    <p className={`text-sm font-bold ${meta?.tone === "blocked" ? "text-red-700" : meta?.tone === "ok" ? "text-emerald-700" : "text-ink"}`}>{meta?.outcome}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-600">{meta?.why}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>
    </RegistryShell>
  );
}
