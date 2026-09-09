"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Policy, PolicyRule, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function PolicyDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    params.then(({ id }) => api.policy(id).then(setPolicy).catch((reason: Error) => setError(reason.message)));
  }, [params]);

  if (!policy && !error) {
    return <RegistryShell title="Policy detail" eyebrow="Authorization rule"><StateMessage>Loading policy…</StateMessage></RegistryShell>;
  }

  const ruleRow = (rule: PolicyRule, index: number) => (
    <li key={rule.id} className="border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Rule {index + 1}</span>
          <StatusPill value={rule.effect === "ALLOW" ? "ALLOW" : "DENY"} />
          <span className="font-mono text-sm text-ink">{rule.action}</span>
          <span className="text-xs text-slate-500">on {rule.resource_type}</span>
        </div>
        <span className="text-xs text-slate-400">priority {rule.priority}</span>
      </div>
      {rule.conditions && Object.keys(rule.conditions).length > 0 && (
        <p className="mt-2 text-xs text-slate-500">Conditions: {JSON.stringify(rule.conditions)}</p>
      )}
    </li>
  );

  return (
    <RegistryShell title={policy?.name ?? "Policy detail"} eyebrow="Policy center">
      {error && <StateMessage tone="error">Unable to load policy. {error}</StateMessage>}
      {policy && (
        <>
          <section className="flex flex-wrap items-start justify-between gap-4 border border-slate-200 bg-white p-6">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-400">Policy</p>
              <p className="mt-1 text-2xl font-semibold text-ink">{policy.name}</p>
              {policy.description && <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">{policy.description}</p>}
            </div>
            <div className="flex flex-wrap gap-2">
              <StatusPill value={policy.status} />
              <StatusPill value={`version ${policy.version}`} />
              <StatusPill value={`priority ${policy.priority}`} />
            </div>
          </section>

          <section className="mt-6">
            <div className="flex items-end justify-between gap-4">
              <h2 className="font-semibold text-ink">Rules ({policy.rules?.length ?? 0})</h2>
              <Link href="/policy-evaluation" className="text-xs font-semibold text-signal hover:underline">Test a request in the evaluator →</Link>
            </div>
            {!policy.rules || policy.rules.length === 0 ? <div className="mt-4"><StateMessage>No rules defined for this policy yet.</StateMessage></div> : <ul className="mt-4 space-y-2">{policy.rules.map(ruleRow)}</ul>}
          </section>

          <section className="mt-6 border border-slate-200 bg-white p-6">
            <h2 className="font-semibold text-ink">How this policy governs</h2>
            <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-600">
              <li>• Rules are evaluated in priority order; an explicit <strong>deny</strong> always wins over allow.</li>
              <li>• If no rule allows the action, AgentOS <strong>blocks by default</strong>.</li>
              <li>• If an allow rule matches a <strong>high-risk action</strong>, AgentOS requires human approval before execution.</li>
              <li>• Every decision records which rule matched and why.</li>
            </ul>
          </section>
        </>
      )}
    </RegistryShell>
  );
}
