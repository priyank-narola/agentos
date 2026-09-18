"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Action, Agent, Policy, PolicyEvaluation, PolicyRule, Resource, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

const emptyRule = { effect: "ALLOW" as const, action: "", resource_type: "", priority: "100", conditions: "" };

export default function PolicyDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [rule, setRule] = useState<{ effect: "ALLOW" | "DENY"; action: string; resource_type: string; priority: string; conditions: string }>(emptyRule);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [actions, setActions] = useState<Action[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [simulation, setSimulation] = useState({ agent: "", action: "", resource: "" });
  const [simulationResult, setSimulationResult] = useState<PolicyEvaluation | null>(null);

  const load = useCallback(async () => {
    try {
      const { id } = await params;
      setPolicy(await api.policy(id));
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load policy.");
    }
  }, [params]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => { api.agents().then(async (agentData) => { const [resourceData, tools] = await Promise.all([api.resources(), api.tools()]); const actionData = (await Promise.all(tools.map((tool) => api.toolActions(tool.id)))).flat(); setAgents(agentData); setActions(actionData); setResources(resourceData); setSimulation({ agent: agentData[0]?.id ?? "", action: actionData[0]?.id ?? "", resource: resourceData[0]?.id ?? "" }); }).catch(() => undefined); }, []);

  async function lifecycle(action: "publish" | "retire" | "version") {
    if (!policy) return;
    setBusy(action);
    setError(null);
    try {
      const result = action === "publish" ? await api.publishPolicy(policy.id) : action === "retire" ? await api.retirePolicy(policy.id) : await api.createPolicyVersion(policy.id);
      if (action === "version") router.push(`/policies/${result.id}`);
      else setPolicy(result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to update the policy.");
    } finally {
      setBusy(null);
    }
  }

  async function addRule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!policy) return;
    setBusy("rule");
    setError(null);
    try {
      let conditions: Record<string, unknown> | undefined;
      if (rule.conditions.trim()) {
        const parsed: unknown = JSON.parse(rule.conditions);
        if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") throw new Error("Conditions must be a JSON object, for example {\"amount\": {\"lte\": 500}}.");
        conditions = parsed as Record<string, unknown>;
      }
      await api.createPolicyRule(policy.id, { effect: rule.effect, action: rule.action.trim(), resource_type: rule.resource_type.trim(), priority: Number(rule.priority), conditions });
      setRule(emptyRule);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to add the rule.");
    } finally {
      setBusy(null);
    }
  }

  async function removeRule(ruleId: string) {
    if (!policy) return;
    setBusy(ruleId);
    setError(null);
    try {
      await api.deletePolicyRule(policy.id, ruleId);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to remove the rule.");
    } finally {
      setBusy(null);
    }
  }

  async function simulateDraft() {
    if (!policy || !simulation.agent || !simulation.action || !simulation.resource) return;
    const agent = agents.find((item) => item.id === simulation.agent);
    const action = actions.find((item) => item.id === simulation.action);
    if (!agent || !action) return;
    setBusy("simulate"); setError(null);
    try { setSimulationResult(await api.simulatePolicyDraft(policy.id, { principal_id: agent.owner_principal_id, agent_id: agent.id, tool_id: action.tool_id, action_id: action.id, resource_id: simulation.resource })); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Draft simulation failed."); }
    finally { setBusy(null); }
  }

  if (!policy && !error) return <RegistryShell title="Policy detail" eyebrow="Authorization rule"><StateMessage>Loading policy…</StateMessage></RegistryShell>;

  const draft = policy?.status === "DRAFT";
  const ruleRow = (item: PolicyRule, index: number) => (
    <li key={item.id} className="border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Rule {index + 1}</span>
          <StatusPill value={item.effect} />
          <span className="font-mono text-sm text-ink">{item.action}</span>
          <span className="text-xs text-slate-500">on {item.resource_type}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400">priority {item.priority}</span>
          {draft && <button disabled={busy === item.id} onClick={() => void removeRule(item.id)} className="text-xs font-semibold text-rose-700 hover:underline disabled:opacity-50">Remove</button>}
        </div>
      </div>
      {item.conditions && Object.keys(item.conditions).length > 0 && <p className="mt-2 break-all font-mono text-xs text-slate-500">Conditions: {JSON.stringify(item.conditions)}</p>}
    </li>
  );

  return (
    <RegistryShell title={policy?.name ?? "Policy detail"} eyebrow="Policy center">
      {error && <div className="mb-6"><StateMessage tone="error">{error}</StateMessage></div>}
      {policy && <>
        <section className="border border-slate-200 bg-white p-6">
          <div className="flex flex-wrap items-start justify-between gap-5">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-400">Policy</p>
              <p className="mt-1 text-2xl font-semibold text-ink">{policy.name}</p>
              {policy.description && <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">{policy.description}</p>}
            </div>
            <div className="flex flex-wrap gap-2"><StatusPill value={policy.status} /><StatusPill value={`version ${policy.version}`} /><StatusPill value={`priority ${policy.priority}`} /></div>
          </div>
          <div className="mt-5 flex flex-wrap gap-2 border-t border-slate-100 pt-5">
            <Link href="/policy-evaluation" className="border border-ink px-3 py-2 text-sm font-medium text-ink hover:bg-ink hover:text-white">Test a request</Link>
            {draft && <button disabled={busy !== null} onClick={() => void lifecycle("publish")} className="bg-ink px-3 py-2 text-sm font-medium text-white disabled:opacity-50">{busy === "publish" ? "Publishing…" : "Publish version"}</button>}
            {policy.status === "ACTIVE" && <button disabled={busy !== null} onClick={() => void lifecycle("version")} className="border border-ink px-3 py-2 text-sm font-medium text-ink disabled:opacity-50">{busy === "version" ? "Creating…" : "Create next draft"}</button>}
            {policy.status !== "RETIRED" && <button disabled={busy !== null} onClick={() => void lifecycle("retire")} className="border border-rose-700 px-3 py-2 text-sm font-medium text-rose-700 disabled:opacity-50">{busy === "retire" ? "Retiring…" : "Retire"}</button>}
          </div>
          <p className="mt-3 text-xs leading-5 text-slate-500">Publishing activates this version and retires the previous active version with the same name. Live versions cannot be edited.</p>
        </section>

        <section className="mt-6">
          <div className="flex items-end justify-between gap-4"><h2 className="font-semibold text-ink">Rules ({policy.rules?.length ?? 0})</h2>{!draft && <p className="text-xs text-slate-500">Create a new draft to change these rules.</p>}</div>
          {!policy.rules || policy.rules.length === 0 ? <div className="mt-4"><StateMessage>No rules defined for this policy yet.</StateMessage></div> : <ul className="mt-4 space-y-2">{policy.rules.map(ruleRow)}</ul>}
        </section>

        {draft && <section className="mt-6 border border-slate-200 bg-white p-6">
          <h2 className="font-semibold text-ink">Add a rule</h2>
          <p className="mt-1 text-sm leading-6 text-slate-500">Use a deny rule for prohibited actions. The policy engine defaults to block when no allow rule matches.</p>
          <form onSubmit={addRule} className="mt-5 grid gap-4 md:grid-cols-2">
            <label className="text-sm font-medium text-ink">Effect<select value={rule.effect} onChange={(event) => setRule({ ...rule, effect: event.target.value as "ALLOW" | "DENY" })} className="mt-2 w-full border border-slate-300 bg-white px-3 py-2 text-sm"><option value="ALLOW">Allow</option><option value="DENY">Deny</option></select></label>
            <label className="text-sm font-medium text-ink">Priority<input required type="number" min="0" value={rule.priority} onChange={(event) => setRule({ ...rule, priority: event.target.value })} className="mt-2 w-full border border-slate-300 px-3 py-2 text-sm" /></label>
            <label className="text-sm font-medium text-ink">Action<input required value={rule.action} onChange={(event) => setRule({ ...rule, action: event.target.value })} placeholder="issue_credit" className="mt-2 w-full border border-slate-300 px-3 py-2 text-sm" /></label>
            <label className="text-sm font-medium text-ink">Resource type<input required value={rule.resource_type} onChange={(event) => setRule({ ...rule, resource_type: event.target.value })} placeholder="customer_account" className="mt-2 w-full border border-slate-300 px-3 py-2 text-sm" /></label>
            <label className="md:col-span-2 text-sm font-medium text-ink">Conditions JSON <span className="font-normal text-slate-400">optional</span><textarea value={rule.conditions} onChange={(event) => setRule({ ...rule, conditions: event.target.value })} rows={3} placeholder='{"amount": {"lte": 500}}' className="mt-2 w-full resize-y border border-slate-300 px-3 py-2 font-mono text-sm" /></label>
            <div className="md:col-span-2"><button disabled={busy !== null} className="bg-ink px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{busy === "rule" ? "Adding…" : "Add draft rule"}</button></div>
          </form>
        </section>}

        {draft && <section className="mt-6 rounded-card border border-hairline bg-surface p-6"><p className="eyebrow text-inkFaint">Draft-only simulation</p><h2 className="mt-1 text-base font-semibold text-ink">Test this draft without publishing</h2><p className="mt-2 text-sm leading-6 text-inkSubtle">This evaluates only this draft against current registered references. It creates no action request and cannot activate the policy.</p><div className="mt-4 grid gap-3 md:grid-cols-3"><label className="text-sm font-medium text-inkMuted">Agent<select value={simulation.agent} onChange={(event) => setSimulation({ ...simulation, agent: event.target.value })} className="mt-1 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink"><option value="">Select agent</option>{agents.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label className="text-sm font-medium text-inkMuted">Action<select value={simulation.action} onChange={(event) => setSimulation({ ...simulation, action: event.target.value })} className="mt-1 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink"><option value="">Select action</option>{actions.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label className="text-sm font-medium text-inkMuted">Resource<select value={simulation.resource} onChange={(event) => setSimulation({ ...simulation, resource: event.target.value })} className="mt-1 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-sm text-ink"><option value="">Select resource</option>{resources.map((item) => <option key={item.id} value={item.id}>{item.resource_key}</option>)}</select></label></div><button type="button" disabled={busy !== null || !simulation.agent || !simulation.action || !simulation.resource} onClick={() => void simulateDraft()} className="mt-4 rounded-control bg-signal px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{busy === "simulate" ? "Simulating…" : "Run draft simulation"}</button>{simulationResult && <div className="mt-4 rounded-card border border-hairline bg-surfaceMuted p-4"><div className="flex items-center justify-between gap-3"><p className="font-semibold text-ink">{simulationResult.decision}</p><StatusPill value={simulationResult.reason_code} /></div><p className="mt-2 text-sm text-inkSubtle">{simulationResult.reason}</p><p className="mt-2 text-xs text-inkFaint">{simulationResult.matched_policies.length} matching draft rule(s) · no policy status changed</p></div>}</section>}

        <section className="mt-6 border border-slate-200 bg-white p-6"><h2 className="font-semibold text-ink">Safe policy workflow</h2><ol className="mt-3 space-y-2 text-sm leading-6 text-slate-600"><li>1. Create a draft and define its rules.</li><li>2. Test representative requests in the evaluator.</li><li>3. Publish when reviewed; the prior live version is retired atomically.</li><li>4. Create the next draft for every later change, preserving a reviewable history.</li></ol></section>
      </>}
    </RegistryShell>
  );
}
