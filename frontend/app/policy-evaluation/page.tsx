"use client";

import { useCallback, useEffect, useState } from "react";

import { Action, ActionPreflight, Agent, Resource, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

type RecoveryClass = "REVERSIBLE" | "COMPENSATABLE" | "IRREVERSIBLE";

function parseObject(value: string, label: string): Record<string, unknown> {
  const parsed: unknown = JSON.parse(value || "{}");
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") throw new Error(`${label} must be a JSON object.`);
  return parsed as Record<string, unknown>;
}

export default function ActionPreflightPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [actions, setActions] = useState<Action[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [selected, setSelected] = useState({ agent: "", action: "", resource: "" });
  const [parameters, setParameters] = useState("{}");
  const [includeContext, setIncludeContext] = useState(false);
  const [context, setContext] = useState({ summary: "", targetSystem: "", before: "{}", proposedChange: "{}", recoveryClass: "COMPENSATABLE" as RecoveryClass, recoveryPlan: "" });
  const [result, setResult] = useState<ActionPreflight | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    Promise.all([
      api.agents(),
      api.resources(),
      api.tools().then(async (tools) => (await Promise.all(tools.map((tool) => api.toolActions(tool.id)))).flat()),
    ])
      .then(([agentData, resourceData, actionData]) => {
        setAgents(agentData); setResources(resourceData); setActions(actionData);
        setSelected({ agent: agentData[0]?.id ?? "", action: actionData[0]?.id ?? "", resource: resourceData[0]?.id ?? "" });
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, []);

  const update = (key: keyof typeof selected, value: string) => setSelected((current) => ({ ...current, [key]: value }));
  const updateContext = <K extends keyof typeof context>(key: K, value: typeof context[K]) => setContext((current) => ({ ...current, [key]: value }));

  const buildPayload = () => {
    const agent = agents.find((item) => item.id === selected.agent);
    if (!agent || !selected.action || !selected.resource) return null;
    if (includeContext && [context.summary, context.targetSystem, context.recoveryPlan].some((value) => !value.trim())) {
      throw new Error("Complete business intent, target system, and recovery plan before preflighting this context.");
    }
    const parsedParameters = parseObject(parameters, "Parameters");
    const actionContext = includeContext ? {
      summary: context.summary.trim(), target_system: context.targetSystem.trim(),
      before: parseObject(context.before, "Before state"), proposed_change: parseObject(context.proposedChange, "Proposed change"),
      recovery_class: context.recoveryClass, recovery_plan: context.recoveryPlan.trim(),
    } : undefined;
    return { principal_id: agent.owner_principal_id, agent_id: selected.agent, action_id: selected.action, resource_id: selected.resource, parameters: parsedParameters, action_context: actionContext };
  };

  const runPreflight = useCallback(() => {
    let payload;
    try {
      payload = buildPayload();
      if (!payload) return;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Preflight input is invalid.");
      return;
    }
    setRunning(true); setError(null); setResult(null);
    api.preflight(payload).then(setResult).catch((reason: Error) => setError(reason.message)).finally(() => setRunning(false));
  // buildPayload depends on every form value; using it directly would make this
  // callback unstable without adding value in every dependency position.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agents, selected, parameters, includeContext, context]);

  useEffect(() => {
    if (loading || !selected.agent || !selected.action || !selected.resource) return;
    let payload;
    try {
      payload = buildPayload();
    } catch {
      return;
    }
    if (!payload) return;
    let active = true;
    const timer = window.setTimeout(() => {
      setRunning(true);
      api.preflight(payload)
        .then((next) => { if (active) { setResult(next); setError(null); } })
        .catch((reason: Error) => { if (active) setError(reason.message); })
        .finally(() => { if (active) setRunning(false); });
    }, 450);
    return () => { active = false; window.clearTimeout(timer); };
  // The live preview intentionally reacts to every editable action field.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, agents, selected, parameters, includeContext, context]);

  const selectors: Array<[keyof typeof selected, string, Array<{ id: string; name?: string; resource_key?: string }>]> = [
    ["agent", "Agent", agents], ["action", "Action", actions], ["resource", "Resource", resources],
  ];

  return <RegistryShell title="Action preflight" eyebrow="Safe decision preview">
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4"><p className="max-w-3xl text-sm leading-6 text-inkSubtle">Preview the controls that would apply to an agent action before submitting it. The decision preview updates as valid fields change, but never creates an action, audit record, approval, or execution.</p><span className="rounded-full border border-warningBorder bg-warningBg px-3 py-1 text-xs font-semibold text-warning">Sandbox/test-mode only</span></div>
    {loading && <StateMessage>Loading registered agents, actions, and resources…</StateMessage>}
    {error && <StateMessage tone="error">Preflight unavailable. {error}</StateMessage>}
    {!loading && <div className="grid gap-6 xl:grid-cols-[360px_1fr]">
      <section className="rounded-card border border-hairline bg-surface p-6">
        <h2 className="text-base font-semibold text-ink">Proposed action</h2>
        <div className="mt-5 space-y-4">
          {selectors.map(([key, label, values]) => <label key={key} className="block text-sm font-medium text-inkMuted">{label}<select className="mt-2 block w-full rounded-control border border-hairline bg-surface px-3 py-2.5 text-sm text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing" value={selected[key]} onChange={(event) => update(key, event.target.value)}><option value="">Select {label.toLowerCase()}</option>{values.map((value) => <option key={value.id} value={value.id}>{value.name ?? value.resource_key}</option>)}</select></label>)}
          <label className="block text-sm font-medium text-inkMuted">Executable parameters (JSON)<textarea aria-label="Executable parameters JSON" className="mt-2 block w-full rounded-control border border-hairline bg-surface px-3 py-2 font-mono text-xs text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing" rows={4} value={parameters} onChange={(event) => setParameters(event.target.value)} placeholder='{"field":"value"}' /></label>
          <div className="border-y border-hairline py-4"><button type="button" aria-expanded={includeContext} className="flex w-full items-center justify-between text-left text-sm font-semibold text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing" onClick={() => setIncludeContext((value) => !value)}><span>Business intent & recovery</span><span className="text-xs font-medium text-signal">{includeContext ? "Hide" : "Add context"}</span></button><p className="mt-1 text-xs leading-5 text-inkSubtle">Include the proposed change and correction plan to preview the exact governed payload.</p>{includeContext && <div className="mt-4 space-y-3"><label className="block text-sm font-medium text-inkMuted">Business intent<textarea className="mt-2 block w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing" rows={2} value={context.summary} onChange={(event) => updateContext("summary", event.target.value)} /></label><label className="block text-sm font-medium text-inkMuted">Target system<input className="mt-2 block w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing" value={context.targetSystem} onChange={(event) => updateContext("targetSystem", event.target.value)} /></label><div className="grid gap-3 sm:grid-cols-2"><label className="block text-sm font-medium text-inkMuted">Before state<textarea className="mt-2 block w-full rounded-control border border-hairline bg-surface px-3 py-2 font-mono text-xs text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing" rows={3} value={context.before} onChange={(event) => updateContext("before", event.target.value)} /></label><label className="block text-sm font-medium text-inkMuted">Proposed change<textarea className="mt-2 block w-full rounded-control border border-hairline bg-surface px-3 py-2 font-mono text-xs text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing" rows={3} value={context.proposedChange} onChange={(event) => updateContext("proposedChange", event.target.value)} /></label></div><label className="block text-sm font-medium text-inkMuted">Recovery type<select className="mt-2 block w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing" value={context.recoveryClass} onChange={(event) => updateContext("recoveryClass", event.target.value as RecoveryClass)}><option value="REVERSIBLE">Reversible</option><option value="COMPENSATABLE">Compensatable</option><option value="IRREVERSIBLE">Irreversible</option></select></label><label className="block text-sm font-medium text-inkMuted">Correction plan<textarea className="mt-2 block w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:ring-2 focus-visible:ring-focusRing" rows={2} value={context.recoveryPlan} onChange={(event) => updateContext("recoveryPlan", event.target.value)} /></label></div>}</div>
          <button type="button" disabled={!selected.agent || !selected.action || !selected.resource || running} onClick={runPreflight} className="w-full rounded-control bg-signal px-4 py-3 text-sm font-semibold text-white outline-none hover:bg-signalHover focus-visible:ring-2 focus-visible:ring-focusRing focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60">{running ? "Updating preview…" : "Refresh safe preview"}</button>
        </div>
      </section>
      <section>
        {!result && <StateMessage>Select a proposed action. A valid configuration is previewed automatically; nothing is submitted to the execution path.</StateMessage>}
        {result && <div className="space-y-6">
          <div className="border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs uppercase tracking-wide text-slate-400">Decision preview</p><p className="mt-2 text-3xl font-semibold text-ink">{result.decision}</p></div><div className="flex flex-wrap gap-2"><StatusPill value={result.execution_plan} />{result.risk_classification && <StatusPill value={`${result.risk_classification} · ${result.risk_score}/100`} />}</div></div>
            <p className="mt-5 text-sm leading-6 text-slate-600">{result.reason}</p>
            <dl className="mt-6 grid gap-4 border-t border-slate-100 pt-5 text-xs sm:grid-cols-2"><div><dt className="text-slate-400">Next control</dt><dd className="mt-1 font-medium text-ink">{result.approval_required ? "Human approval and revalidation" : "Submit through the gateway"}</dd></div><div><dt className="text-slate-400">Planned connector</dt><dd className="mt-1 font-medium text-ink">{result.connector_provider}</dd></div><div><dt className="text-slate-400">Policy reason</dt><dd className="mt-1 font-mono text-slate-600">{result.reason_code}</dd></div><div><dt className="text-slate-400">Payload digest</dt><dd className="mt-1 break-all font-mono text-slate-600">{result.payload_digest}</dd></div></dl>
          </div>
          <div className="border border-slate-200 bg-white p-6"><h2 className="font-semibold text-ink">Risk factors</h2><div className="mt-4 space-y-3">{result.risk_factors.map((factor) => <div key={factor.code} className="flex justify-between gap-4 border-b border-slate-100 pb-3 text-sm"><div><p className="font-medium text-ink">{factor.code}</p><p className="mt-1 text-xs text-slate-500">{factor.explanation}</p></div><span className="font-mono text-signal">+{factor.contribution}</span></div>)}</div></div>
          <div className="border border-slate-200 bg-white p-6"><h2 className="font-semibold text-ink">Matched policies</h2>{result.matched_policies.length === 0 ? <p className="mt-3 text-sm text-slate-500">No matching policy rules.</p> : <div className="mt-4 space-y-3">{result.matched_policies.map((match) => <div key={match.rule_id} className="flex justify-between gap-4 border-b border-slate-100 pb-3 text-sm"><span>{match.policy_name} v{match.policy_version}</span><StatusPill value={match.rule_effect} /></div>)}</div>}</div>
          <div className="border-l-2 border-amber-300 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-900">{result.warnings.map((warning) => <p key={warning}>{warning}</p>)}</div>
        </div>}
      </section>
    </div>}
  </RegistryShell>;
}
