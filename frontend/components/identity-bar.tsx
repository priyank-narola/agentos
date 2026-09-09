"use client";

import { useEffect, useState } from "react";

import { WhoAmI, api, devTokenFor, getAccessToken, setAccessToken } from "@/lib/api";

const DEMO_IDENTITIES: Array<{ label: string; external_id: string }> = [
  { label: "Alice Smith — Treasury Manager", external_id: "treasury_alice" },
  { label: "Bob Jones — VP Finance", external_id: "treasury_bob" },
  { label: "Demo Admin", external_id: "demo-admin" },
];

export function IdentityBar({ compact = false }: { compact?: boolean }) {
  const [me, setMe] = useState<WhoAmI | null>(null);

  useEffect(() => {
    api.me().then(setMe).catch(() => setMe({ authenticated: false }));
  }, []);

  const switchTo = async (externalId: string) => {
    try {
      await devTokenFor(externalId);
      const who = await api.me();
      setMe(who);
    } catch {
      setMe({ authenticated: false, principal: null, tenant_id: null, tenant_name: null });
    }
  };

  const clear = () => {
    setAccessToken(null);
    setMe({ authenticated: false });
  };

  const whoLabel = me?.principal ? `${me.principal.name}` : "Demo (unauthenticated)";

  return (
    <div className={`flex items-center gap-2 ${compact ? "text-xs" : ""}`}>
      <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${me?.authenticated ? "border-emerald-300 bg-emerald-50 text-emerald-800" : "border-slate-300 bg-slate-50 text-slate-600"}`}>
        Acting as {whoLabel}
      </span>
      {me?.tenant_name && <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-500">{me.tenant_name}</span>}
      <select
        aria-label="Switch demo identity"
        onChange={(e) => e.target.value && switchTo(e.target.value)}
        defaultValue=""
        className="border border-slate-300 bg-white px-2 py-1 text-xs"
      >
        <option value="" disabled>
          Switch identity (dev)
        </option>
        {DEMO_IDENTITIES.map((id) => (
          <option key={id.external_id} value={id.external_id}>
            {id.label}
          </option>
        ))}
        {getAccessToken() && <option value="__clear">Sign out</option>}
      </select>
      {me?.authenticated && (
        <button type="button" onClick={clear} className="text-xs font-medium text-slate-400 hover:text-slate-600">
          Sign out
        </button>
      )}
    </div>
  );
}
