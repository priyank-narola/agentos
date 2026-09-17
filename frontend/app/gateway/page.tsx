"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Action, GatewayResponse, Resource, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

type RecoveryClass = "REVERSIBLE" | "COMPENSATABLE" | "IRREVERSIBLE";
type ActionContextForm = {
  summary: string;
  targetSystem: string;
  before: string;
  proposedChange: string;
  recoveryClass: RecoveryClass;
  recoveryPlan: string;
};

const emptyContext: ActionContextForm = {
  summary: "", targetSystem: "", before: "{}", proposedChange: "{}", recoveryClass: "COMPENSATABLE", recoveryPlan: "",
};

function jsonObject(value: string, label: string): Record<string, unknown> {
  const parsed: unknown = JSON.parse(value || "{}");
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") throw new Error(`${label} must be a JSON object.`);
  return parsed as Record<string, unknown>;
}

export default function GatewayPage() {
  const [agents, setAgents] = useState<Array<{ id: string; name: string; owner_principal_id: string }>>([]);
  const [actions, setActions] = useState<Action[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [selected, setSelected] = useState({ agent: "", action: "", resource: "", key: crypto.randomUUID() });
  const [context, setContext] = useState<ActionContextForm>(emptyContext);
  const [showContext, setShowContext] = useState(false);
  const [result, setResult] = useState<GatewayResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    Promise.all([
      api.agents(), api.resources(),
      api.tools().then(async (tools) => (await Promise.all(tools.map((tool) => api.toolActions(tool.id)))).flat()),
    ]).then(([agentData, resourceData, actionData]) => {
      setAgents(agentData); setResources(resourceData); setActions(actionData);
      setSelected((current) => ({ ...current, agent: agentData[0]?.id ?? "", action: actionData[0]?.id ?? "", resource: resourceData[0]?.id ?? "" }));
    }).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false));
  }, []);

  const updateContext = <K extends keyof ActionContextForm>(key: K, value: ActionContextForm[K]) => setContext((current) => ({ ...current, [key]: value }));
  const contextStarted = [context.summary, context.targetSystem, context.recoveryPlan].some((value) => value.trim().length > 0);

  const submit = () => {
    setError(null);
    if (contextStarted && [context.summary, context.targetSystem, context.recoveryPlan].some((value) => value.trim().length === 0)) {
      setError("Complete the business intent, target system, and recovery plan, or clear the action context.");
      return;
    }
    try {
      const actionContext = contextStarted ? {
        summary: context.summary.trim(), target_system: context.targetSystem.trim(),
        before: jsonObject(context.before, "Before state"), proposed_change: jsonObject(context.proposedChange, "Proposed change"),
        recovery_class: context.recoveryClass, recovery_plan: context.recoveryPlan.trim(),
      } : undefined;
      setSubmitting(true);
      api.gateway({
        principal_id: agents.find((agent) => agent.id === selected.agent)?.owner_principal_id,
        agent_id: selected.agent, action_id: selected.action, resource_id: selected.resource,
        parameters: {}, action_context: actionContext, idempotency_key: selected.key,
      }).then(setResult).catch((reason: Error) => setError(reason.message)).finally(() => setSubmitting(false));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Action context is invalid.");
    }
  };

  const selectors: Array<[keyof typeof selected, string, Array<{ id: string; name?: string; resource_key?: string }>]> = [
    ["agent", "Agent", agents], ["action", "Action", actions], ["resource", "Resource", resources],
  ];

  return <RegistryShell title="Runtime action gateway" eyebrow="Single interception boundary">
    <p className="mb-6 max-w-2xl text-sm leading-6 text-slate-500">Submit a hypothetical agent action. The gateway resolves context, calculates explainable risk, evaluates policy, and persists evidence. Authorized wires execute inside the sandbox provider only — no real money movement.</p>
    {loading && <StateMessage>Loading gateway references…</StateMessage>}
    {error && <StateMessage tone="error">Gateway request failed. {error}</StateMessage>}
    {!loading && <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
      <section className="border border-slate-200 bg-white p-6">
        <h2 className="font-semibold text-ink">Action request</h2>
        <div className="mt-5 space-y-4">
          {selectors.map(([key, label, values]) => <label key={key} className="block text-sm font-medium text-slate-600">{label}<select className="mt-2 block w-full border border-slate-300 bg-white px-3 py-2.5 text-sm" value={selected[key]} onChange={(event) => setSelected((current) => ({ ...current, [key]: event.target.value }))}><option value="">Select {label.toLowerCase()}</option>{values.map((value) => <option key={value.id} value={value.id}>{value.name ?? value.resource_key}</option>)}</select></label>)}
          <div className="border-y border-slate-100 py-4">
            <button type="button" className="flex w-full items-center justify-between text-left text-sm font-semibold text-ink" onClick={() => setShowContext((value) => !value)}><span>Business intent & recovery</span><span className="text-xs font-medium text-signal">{showContext ? "Hide" : "Add evidence"}</span></button>
            <p className="mt-1 text-xs leading-5 text-slate-500">Optional for the technical gateway. Required for a serious high-impact product action.</p>
            {showContext && <div className="mt-4 space-y-3">
              <label className="block text-sm font-medium text-slate-600">Business intent<textarea className="mt-2 block w-full border border-slate-300 px-3 py-2 text-sm" rows={3} value={context.summary} onChange={(event) => updateContext("summary", event.target.value)} placeholder="What action is proposed and why?" /></label>
              <label className="block text-sm font-medium text-slate-600">Target system<input className="mt-2 block w-full border border-slate-300 px-3 py-2 text-sm" value={context.targetSystem} onChange={(event) => updateContext("targetSystem", event.target.value)} placeholder="e.g. support-platform" /></label>
              <div className="grid gap-3 sm:grid-cols-2"><label className="block text-sm font-medium text-slate-600">Before state<textarea className="mt-2 block w-full border border-slate-300 px-3 py-2 font-mono text-xs" rows={3} value={context.before} onChange={(event) => updateContext("before", event.target.value)} /></label><label className="block text-sm font-medium text-slate-600">Proposed change<textarea className="mt-2 block w-full border border-slate-300 px-3 py-2 font-mono text-xs" rows={3} value={context.proposedChange} onChange={(event) => updateContext("proposedChange", event.target.value)} /></label></div>
              <label className="block text-sm font-medium text-slate-600">Recovery type<select className="mt-2 block w-full border border-slate-300 bg-white px-3 py-2 text-sm" value={context.recoveryClass} onChange={(event) => updateContext("recoveryClass", event.target.value as RecoveryClass)}><option value="REVERSIBLE">Reversible</option><option value="COMPENSATABLE">Compensatable</option><option value="IRREVERSIBLE">Irreversible</option></select></label>
              <label className="block text-sm font-medium text-slate-600">Recovery plan<textarea className="mt-2 block w-full border border-slate-300 px-3 py-2 text-sm" rows={3} value={context.recoveryPlan} onChange={(event) => updateContext("recoveryPlan", event.target.value)} placeholder="What correction path is available if this action is wrong?" /></label>
            </div>}
          </div>
          <label className="block text-sm font-medium text-slate-600">Idempotency key<input className="mt-2 block w-full border border-slate-300 px-3 py-2.5 font-mono text-xs" value={selected.key} onChange={(event) => setSelected((current) => ({ ...current, key: event.target.value }))} /></label>
          <button type="button" disabled={!selected.agent || !selected.action || !selected.resource || submitting} onClick={submit} className="w-full bg-ink px-4 py-3 text-sm font-medium text-white disabled:bg-slate-300">{submitting ? "Intercepting…" : "Submit to gateway"}</button>
        </div>
      </section>
      <section>{!result && <StateMessage>Gateway response will appear here. The client cannot provide risk or override the decision.</StateMessage>}{result && <div className="space-y-6"><div className="border border-slate-200 bg-white p-6"><p className="text-xs uppercase tracking-wide text-slate-400">Gateway status</p><p className="mt-2 text-4xl font-semibold text-ink">{result.gateway_status}</p><div className="mt-4 flex flex-wrap gap-2"><StatusPill value={result.decision} /><StatusPill value={result.reason_code} />{result.risk_classification && <StatusPill value={`${result.risk_classification} · ${result.risk_score}/100`} />}</div><p className="mt-5 text-sm leading-6 text-slate-600">{result.reason}</p>{result.action_context && <div className="mt-5 border-l-2 border-signal bg-slate-50 px-4 py-3"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Bound business intent</p><p className="mt-1 text-sm text-ink">{result.action_context.summary}</p><p className="mt-1 text-xs text-slate-500">{result.action_context.recovery_class} · {result.execution_receipt.recovery_status}</p></div>}<dl className="mt-6 grid gap-4 border-t border-slate-100 pt-5 text-xs sm:grid-cols-2"><div><dt className="text-slate-400">Request ID</dt><dd className="mt-1 break-all font-mono text-slate-600">{result.action_request_id}</dd></div><div><dt className="text-slate-400">Execution status</dt><dd className="mt-1 font-medium text-signal">{result.execution_status}</dd></div><div><dt className="text-slate-400">Provider evidence</dt><dd className="mt-1 text-slate-600">{result.execution_receipt.evidence_status}</dd></div><div><dt className="text-slate-400">Decision time</dt><dd className="mt-1 text-slate-600">{new Date(result.decided_at).toLocaleString()}</dd></div></dl><p className="mt-6 border-t border-amber-100 pt-4 text-xs font-medium text-amber-800">Sandbox execution only — no real money movement.</p><p className="mt-3"><Link href={`/action-requests/${result.action_request_id}`} className="text-xs font-semibold text-signal hover:underline">Open this action&apos;s full governance case file →</Link></p></div><div className="border border-slate-200 bg-white p-6"><h2 className="font-semibold text-ink">Risk factors</h2><div className="mt-4 space-y-3">{result.risk_factors.map((factor) => <div key={factor.code} className="flex justify-between gap-4 border-b border-slate-100 pb-3 text-sm"><div><p className="font-medium text-ink">{factor.code}</p><p className="mt-1 text-xs text-slate-500">{factor.explanation}</p></div><span className="font-mono text-signal">+{factor.contribution}</span></div>)}</div></div></div>}</section>
    </div>}
  </RegistryShell>;
}
