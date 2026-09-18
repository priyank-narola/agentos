"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CustomerRemediationReadiness, LaunchReadiness, PrincipalRoleAssignment, WhoAmI, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function TenantSettingsPage() {
  const [identity, setIdentity] = useState<WhoAmI | null>(null);
  const [readiness, setReadiness] = useState<LaunchReadiness | null>(null);
  const [roles, setRoles] = useState<PrincipalRoleAssignment[]>([]);
  const [connectors, setConnectors] = useState<CustomerRemediationReadiness | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { Promise.all([api.me(), api.launchReadiness(), api.roleAssignments(), api.customerRemediationReadiness()]).then(([me, launch, assignments, connectorData]) => { setIdentity(me); setReadiness(launch); setRoles(assignments); setConnectors(connectorData); }).catch((reason: Error) => setError(reason.message)); }, []);
  return <RegistryShell title="Tenant settings" eyebrow="Administration">
    <p className="max-w-3xl text-sm leading-6 text-inkSubtle">Secret-free tenant posture. This workspace reports server-derived configuration without displaying or accepting identity keys, API keys, or connector credentials.</p>
    {error && <div className="mt-5"><StateMessage tone="error">Unable to load tenant settings. {error}</StateMessage></div>}
    {!identity && !error && <div className="mt-6"><StateMessage>Loading tenant configuration posture…</StateMessage></div>}
    {identity && <div className="mt-6 space-y-5">
      <section className="grid gap-4 md:grid-cols-3"><article className="rounded-card border border-hairline bg-surface p-5"><p className="eyebrow text-inkFaint">Tenant</p><p className="mt-2 text-base font-semibold text-ink">{identity.tenant_name ?? "Server-derived tenant"}</p><p className="mt-1 text-xs text-inkSubtle">{identity.tenant_id ?? "No tenant context"}</p></article><article className="rounded-card border border-hairline bg-surface p-5"><p className="eyebrow text-inkFaint">Authenticated identity</p><p className="mt-2 text-base font-semibold text-ink">{identity.principal?.name ?? "Unavailable"}</p><p className="mt-1 text-xs text-inkSubtle">Identity is resolved server-side.</p></article><article className="rounded-card border border-hairline bg-surface p-5"><p className="eyebrow text-inkFaint">Roles</p><p className="mt-2 text-2xl font-semibold tnum text-ink">{roles.length}</p><Link href="/access" className="mt-2 inline-block text-xs font-semibold text-signal">Manage tenant roles →</Link></article></section>
      <section className="rounded-card border border-hairline bg-surface p-6"><p className="eyebrow text-inkFaint">Identity, credentials & break-glass</p><h2 className="mt-1 text-base font-semibold text-ink">Controlled outside the browser</h2><p className="mt-3 text-sm leading-6 text-inkSubtle">Identity provider configuration, API/MCP credentials, retention rules, and emergency break-glass access do not have a mutable tenant API in this sandbox. They are intentionally not editable here, preventing secrets from being stored or exposed by the UI.</p></section>
      {readiness && <section className="rounded-card border border-hairline bg-surface p-6"><div className="flex justify-between gap-4"><div><p className="eyebrow text-inkFaint">Launch readiness</p><h2 className="mt-1 text-base font-semibold text-ink">Server-derived release gates</h2></div><StatusPill value={readiness.launch_ready ? "READY" : "NOT READY"} /></div><div className="mt-4 space-y-2">{readiness.checks.map((check) => <div key={check.id} className="flex flex-wrap items-center justify-between gap-3 rounded-control border border-hairline bg-surfaceMuted px-3 py-2"><span className="text-sm text-ink">{check.label}<span className="ml-2 text-xs text-inkSubtle">{check.detail}</span></span><StatusPill value={check.status} /></div>)}</div></section>}
      {connectors && <section className="rounded-card border border-hairline bg-surface p-6"><p className="eyebrow text-inkFaint">Connector state</p><p className="mt-2 text-sm text-inkSubtle">Zendesk context: {connectors.zendesk_ticket_context.configured ? "configured" : "not configured"} · Stripe refund: {connectors.stripe_refund_execution.configured ? "configured" : "not configured"}. Any configured connector remains sandbox/test-mode only.</p></section>}
    </div>}
  </RegistryShell>;
}
