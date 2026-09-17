"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { Principal, PrincipalRoleAssignment, WhoAmI, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

const roles: Array<{ value: PrincipalRoleAssignment["role"]; label: string; description: string }> = [
  { value: "ADMIN", label: "Admin", description: "Manage tenant access and all operational controls." },
  { value: "POLICY_AUTHOR", label: "Policy author", description: "Create, test, publish, and retire policy versions." },
  { value: "APPROVER", label: "Approver", description: "Approve or reject eligible consequential actions." },
  { value: "OPERATOR", label: "Operator", description: "Reconcile uncertain provider outcomes." },
  { value: "AUDITOR", label: "Auditor", description: "Access governed-action evidence exports." },
];

export default function AccessControlPage() {
  const [principals, setPrincipals] = useState<Principal[]>([]);
  const [assignments, setAssignments] = useState<PrincipalRoleAssignment[]>([]);
  const [identity, setIdentity] = useState<WhoAmI | null>(null);
  const [actorId, setActorId] = useState("");
  const [principalId, setPrincipalId] = useState("");
  const [role, setRole] = useState<PrincipalRoleAssignment["role"]>("POLICY_AUTHOR");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    return Promise.all([api.principals(), api.roleAssignments(), api.me()])
      .then(([nextPrincipals, nextAssignments, who]) => {
        const activeHumans = nextPrincipals.filter((principal) => principal.type === "HUMAN" && principal.status === "ACTIVE");
        setPrincipals(activeHumans);
        setAssignments(nextAssignments);
        setIdentity(who);
        const adminIds = new Set(nextAssignments.filter((assignment) => assignment.role === "ADMIN").map((assignment) => assignment.principal_id));
        const fallbackAdmin = activeHumans.find((principal) => adminIds.has(principal.id))?.id ?? "";
        setActorId(who.principal?.id ?? fallbackAdmin);
        setPrincipalId((current) => current || activeHumans[0]?.id || "");
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { void load(); }, []);

  const principalNames = useMemo(() => new Map(principals.map((principal) => [principal.id, `${principal.name} · ${principal.external_id}`])), [principals]);
  const adminIds = useMemo(() => new Set(assignments.filter((assignment) => assignment.role === "ADMIN").map((assignment) => assignment.principal_id)), [assignments]);

  async function grant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!actorId || !principalId) {
      setError("Choose an active administrator and a tenant member.");
      return;
    }
    setBusy("grant"); setError(null); setMessage(null);
    try {
      await api.grantRole({ actor_principal_id: actorId, principal_id: principalId, role });
      setMessage("Role granted and recorded in the tenant audit trail.");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to grant the role.");
    } finally { setBusy(null); }
  }

  async function revoke(assignment: PrincipalRoleAssignment) {
    if (!actorId) { setError("Choose the administrator performing this change."); return; }
    setBusy(assignment.id); setError(null); setMessage(null);
    try {
      await api.revokeRole(assignment.id, actorId);
      setMessage("Role revoked and recorded in the tenant audit trail.");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to revoke the role.");
    } finally { setBusy(null); }
  }

  return (
    <RegistryShell title="Access control" eyebrow="Tenant roles">
      <p className="max-w-3xl text-sm leading-6 text-inkSubtle">Assign only the authority each person needs. In a production workspace, the authenticated administrator is fixed by their identity token. The local sandbox lets you select a seeded administrator to demonstrate the same controlled operation.</p>
      {error && <div className="mt-5"><StateMessage tone="error">{error}</StateMessage></div>}
      {message && <p className="mt-5 rounded-control border border-successBorder bg-successBg px-3 py-2 text-sm text-success">{message}</p>}
      {loading ? <div className="mt-6"><StateMessage>Loading tenant roles…</StateMessage></div> : <>
        <section className="mt-6 border border-hairline bg-surface p-6">
          <h2 className="text-base font-semibold text-ink">Grant a role</h2>
          <form onSubmit={grant} className="mt-4 grid gap-4 md:grid-cols-3">
            {!identity?.authenticated && <label className="text-sm font-medium text-ink">Acting administrator<select value={actorId} onChange={(event) => setActorId(event.target.value)} className="mt-2 w-full border border-hairlineStrong bg-surface px-3 py-2 text-sm"><option value="">Select admin…</option>{principals.filter((principal) => adminIds.has(principal.id)).map((principal) => <option key={principal.id} value={principal.id}>{principal.name}</option>)}</select></label>}
            <label className="text-sm font-medium text-ink">Tenant member<select value={principalId} onChange={(event) => setPrincipalId(event.target.value)} className="mt-2 w-full border border-hairlineStrong bg-surface px-3 py-2 text-sm">{principals.map((principal) => <option key={principal.id} value={principal.id}>{principalNames.get(principal.id)}</option>)}</select></label>
            <label className="text-sm font-medium text-ink">Role<select value={role} onChange={(event) => setRole(event.target.value as PrincipalRoleAssignment["role"])} className="mt-2 w-full border border-hairlineStrong bg-surface px-3 py-2 text-sm">{roles.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
            <div className="md:col-span-3 flex flex-wrap items-center gap-4"><button disabled={busy !== null} className="rounded-control bg-signal px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{busy === "grant" ? "Granting…" : "Grant role"}</button><p className="text-xs text-inkFaint">Only an existing tenant admin can grant roles. The first production admin is provisioned outside this screen.</p></div>
          </form>
        </section>
        <section className="mt-6"><h2 className="text-base font-semibold text-ink">Current assignments</h2><div className="mt-4 overflow-hidden rounded-card border border-hairline bg-surface"><div className="grid grid-cols-[minmax(0,1fr)_auto_auto] gap-4 border-b border-hairline bg-surfaceMuted px-5 py-3 text-xs font-medium uppercase tracking-wide text-inkFaint"><span>Member</span><span>Role</span><span>Control</span></div>{assignments.length === 0 ? <p className="px-5 py-6 text-sm text-inkSubtle">No roles have been assigned.</p> : assignments.map((assignment) => <div key={assignment.id} className="grid grid-cols-[minmax(0,1fr)_auto_auto] items-center gap-4 border-b border-hairline px-5 py-4 last:border-0"><span className="min-w-0 truncate text-sm text-ink">{principalNames.get(assignment.principal_id) ?? assignment.principal_id}</span><StatusPill value={assignment.role} /><button type="button" disabled={busy !== null} onClick={() => void revoke(assignment)} className="text-xs font-semibold text-rose-700 hover:underline disabled:opacity-50">{busy === assignment.id ? "Revoking…" : "Revoke"}</button></div>)}</div></section>
        <section className="mt-6 grid gap-3 md:grid-cols-2 lg:grid-cols-3">{roles.map((item) => <article key={item.value} className="border border-hairline bg-surface p-4"><StatusPill value={item.value} /><h3 className="mt-3 font-semibold text-ink">{item.label}</h3><p className="mt-1 text-sm leading-6 text-inkSubtle">{item.description}</p></article>)}</section>
      </>}
    </RegistryShell>
  );
}
