"use client";

import { useEffect, useState } from "react";
import { LaunchReadiness, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function LaunchReadinessPage() {
  const [readiness, setReadiness] = useState<LaunchReadiness | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api.launchReadiness().then(setReadiness).catch((reason: Error) => setError(reason.message)); }, []);
  return <RegistryShell title="Launch readiness" eyebrow="Production release gates">
    <p className="max-w-3xl text-sm leading-6 text-inkSubtle">This checklist is intentionally strict. A payment-control product is not launch-ready merely because its interface works; every item below must be resolved before live customer actions are enabled.</p>
    {error && <div className="mt-6"><StateMessage tone="error">{error}</StateMessage></div>}
    {!readiness && !error && <div className="mt-6"><StateMessage>Assessing release posture…</StateMessage></div>}
    {readiness && <><section className="mt-6 flex flex-wrap items-center justify-between gap-4 border border-hairline bg-surface p-5"><div><p className="eyebrow">Current posture</p><h2 className="mt-1 text-xl font-semibold text-ink">{readiness.launch_ready ? "Ready for launch" : "Not ready for live launch"}</h2><p className="mt-1 text-sm text-inkSubtle">Environment: {readiness.environment}</p></div><div className="flex gap-2"><StatusPill value={`${readiness.blockers} BLOCKED`} /><StatusPill value={`${readiness.pending} PENDING`} /></div></section><section className="mt-6 overflow-hidden border border-hairline bg-surface">{readiness.checks.map((check) => <article key={check.id} className="flex flex-wrap items-start justify-between gap-4 border-b border-hairline p-5 last:border-0"><div><h2 className="font-semibold text-ink">{check.label}</h2><p className="mt-1 max-w-2xl text-sm leading-6 text-inkSubtle">{check.detail}</p></div><StatusPill value={check.status} /></article>)}</section></>}
  </RegistryShell>;
}
