"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { api, Principal, PrincipalRoleAssignment, ReconciliationCase } from "@/lib/api";
import { formatDateTime, shortId } from "@/lib/format";
import { RegistryShell, StateMessage } from "@/components/registry-shell";
import { Status } from "@/components/ui/Status";

export default function ReconciliationPage() {
  const [cases, setCases] = useState<ReconciliationCase[]>([]);
  const [principals, setPrincipals] = useState<Principal[]>([]);
  const [roleAssignments, setRoleAssignments] = useState<PrincipalRoleAssignment[]>([]);
  const [selectedOperator, setSelectedOperator] = useState<Record<string, string>>({});
  const [checking, setChecking] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    return Promise.all([api.reconciliationCases(), api.principals(), api.roleAssignments()])
      .then(([nextCases, nextPrincipals, nextRoles]) => {
        setCases(nextCases);
        setPrincipals(nextPrincipals.filter((principal) => principal.type === "HUMAN" && principal.status === "ACTIVE"));
        setRoleAssignments(nextRoles);
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { void load(); }, []);

  const operatorOptions = useMemo(() => {
    const operatorIds = new Set(
      roleAssignments
        .filter((assignment) => assignment.role === "OPERATOR" || assignment.role === "ADMIN")
        .map((assignment) => assignment.principal_id),
    );
    return principals
      .filter((principal) => operatorIds.has(principal.id))
      .map((principal) => ({ id: principal.id, label: `${principal.name} · ${principal.external_id}` }));
  }, [principals, roleAssignments]);

  const reconcile = async (item: ReconciliationCase) => {
    const operatorId = selectedOperator[item.action_request_id];
    if (!operatorId) {
      setError("Choose an independent active human operator before checking the provider outcome.");
      return;
    }
    setChecking(item.action_request_id);
    setError(null);
    setMessage(null);
    try {
      const result = await api.reconcile(item.action_request_id, operatorId);
      setMessage(
        result.execution_state === "RECONCILIATION_REQUIRED"
          ? "The provider still cannot confirm an outcome. The action remains in the reconciliation queue; no retry was sent."
          : `Provider readback confirmed ${result.execution_state}. The case file and audit trail were updated.`,
      );
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The reconciliation check could not be completed.");
    } finally {
      setChecking(null);
    }
  };

  return (
    <RegistryShell title="Reconciliation" eyebrow="Uncertain execution outcomes">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <p className="max-w-3xl text-sm leading-6 text-inkSubtle">
          When a provider timeout or unclear response leaves an action uncertain, check its durable provider reference. This screen never retries the original action. An independent human records the readback, and an unresolved result stays visible for follow-up.
        </p>
        <span className="rounded-full border border-warningBorder bg-warningBg px-3 py-1 text-xs font-medium text-warning">
          {cases.length} open {cases.length === 1 ? "case" : "cases"}
        </span>
      </div>

      {error && <StateMessage tone="error">{error}</StateMessage>}
      {message && <p className="mb-4 rounded-control border border-successBorder bg-successBg px-3 py-2 text-sm text-success">{message}</p>}
      {loading && !error && <StateMessage>Loading uncertain execution outcomes…</StateMessage>}

      {!loading && !error && cases.length === 0 && (
        <div className="rounded-card border border-dashed border-hairlineStrong bg-surface px-6 py-12 text-center">
          <p className="text-sm font-medium text-ink">No executions need reconciliation</p>
          <p className="mx-auto mt-1 max-w-md text-[13px] leading-5 text-inkSubtle">Provider outcomes are either definitive or no action has been submitted. If an execution becomes unknown, it will appear here rather than being assumed successful.</p>
          <Link href="/action-requests" className="mt-4 inline-block text-[13px] font-semibold text-signal hover:text-signalHover">Browse governed actions →</Link>
        </div>
      )}

      <div className="space-y-4">
        {cases.map((item) => {
          const allowedOperators = operatorOptions.filter((operator) => operator.id !== item.requester_principal_id);
          return (
            <article key={item.action_request_id} className="rounded-card border border-hairline bg-surface p-5 shadow-card">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="eyebrow">Action case</p>
                  <h2 className="mt-1 text-base font-semibold text-ink">{item.action_name} <span className="font-mono text-sm font-normal text-inkSubtle">{item.resource_key}</span></h2>
                  <p className="mt-1 text-xs text-inkFaint">Requested {formatDateTime(item.requested_at)} · Case {shortId(item.action_request_id)}</p>
                </div>
                <Status value={item.execution_state} dot />
              </div>

              <dl className="mt-4 grid gap-3 border-y border-hairline py-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
                <div><dt className="text-xs text-inkFaint">Provider</dt><dd className="mt-1 font-medium text-ink">{item.provider_name}</dd></div>
                <div><dt className="text-xs text-inkFaint">Provider reference</dt><dd className="mt-1 font-mono text-xs text-inkSubtle">{item.provider_reference}</dd></div>
                <div><dt className="text-xs text-inkFaint">Provider request</dt><dd className="mt-1 font-mono text-xs text-inkSubtle">{shortId(item.provider_request_id)}</dd></div>
                <div><dt className="text-xs text-inkFaint">Last update</dt><dd className="mt-1 text-inkSubtle">{formatDateTime(item.updated_at)}</dd></div>
              </dl>

              {item.error_message && <p className="mt-3 rounded-control border border-warningBorder bg-warningBg px-3 py-2 text-xs leading-5 text-warning">{item.error_message}</p>}

              <div className="mt-4 flex flex-wrap items-end justify-between gap-3">
                <label className="grid min-w-[260px] gap-1.5 text-xs font-medium text-inkSubtle">
                  Independent operator
                  <select
                    value={selectedOperator[item.action_request_id] ?? ""}
                    onChange={(event) => setSelectedOperator((current) => ({ ...current, [item.action_request_id]: event.target.value }))}
                    className="rounded-control border border-hairlineStrong bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-signal focus:ring-2 focus:ring-focusRing"
                  >
                    <option value="">Select an active human…</option>
                    {allowedOperators.map((operator) => <option key={operator.id} value={operator.id}>{operator.label}</option>)}
                  </select>
                </label>
                <div className="flex items-center gap-4">
                  <Link href={`/action-requests/${item.action_request_id}`} className="text-[13px] font-medium text-inkSubtle hover:text-ink">Open case file</Link>
                  <button
                    type="button"
                    onClick={() => void reconcile(item)}
                    disabled={checking === item.action_request_id}
                    className="rounded-control bg-signal px-3.5 py-2 text-[13px] font-semibold text-white transition hover:bg-signalHover disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {checking === item.action_request_id ? "Checking provider…" : "Check provider outcome"}
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </RegistryShell>
  );
}
