"use client";

import { useEffect, useState } from "react";
import { WhoAmI, api, devTokenFor, getAccessToken, setAccessToken } from "@/lib/api";

const DEMO_IDENTITIES: Array<{ label: string; external_id: string }> = [
  { label: "Alice Smith — Treasury Manager", external_id: "treasury_alice" },
  { label: "Bob Jones — VP Finance", external_id: "treasury_bob" },
  { label: "Demo Admin", external_id: "demo-admin" },
];

/** Compact identity switcher — secondary UI, never the visual focus. */
export function IdentityBar() {
  const [me, setMe] = useState<WhoAmI | null>(null);

  useEffect(() => {
    api.me().then(setMe).catch(() => setMe({ authenticated: false }));
  }, []);

  const currentExternalId = me?.principal?.external_id ?? "";
  const currentLabel = me?.principal?.name ? `Acting as ${me.principal.name}` : "Demo";

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

  const known = DEMO_IDENTITIES.find((d) => d.external_id === currentExternalId);
  const signedOut = !me?.authenticated && !getAccessToken();

  return (
    <div className="flex items-center gap-1.5">
      <span className="relative inline-flex items-center">
        <span className="pointer-events-none absolute left-2.5 grid h-4 w-4 place-items-center rounded-full bg-ink text-[9px] font-semibold text-white">
          {me?.principal ? me.principal.name.charAt(0).toUpperCase() : "•"}
        </span>
        <select
          aria-label="Switch demo identity"
          value={signedOut ? "demo-anon" : currentExternalId}
          onChange={(e) => {
            const value = e.target.value;
            if (value === "__clear") clear();
            else if (value) switchTo(value);
          }}
          className="h-8 appearance-none rounded-control border border-hairline bg-surface pl-8 pr-7 text-[13px] font-medium text-ink shadow-card transition-colors hover:border-hairlineStrong focus-visible:outline-2"
        >
          {signedOut ? (
            <option value="demo-anon">Demo (unsigned)</option>
          ) : (
            known && <option value={known.external_id}>{currentLabel}</option>
          )}
          {!known && currentExternalId && <option value={currentExternalId}>{currentLabel}</option>}
          {DEMO_IDENTITIES.filter((d) => d.external_id !== currentExternalId).map((d) => (
            <option key={d.external_id} value={d.external_id}>
              {d.label}
            </option>
          ))}
          {me?.authenticated && <option value="__clear">Sign out</option>}
        </select>
        <span aria-hidden className="pointer-events-none absolute right-2 text-inkFaint">
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
            <path d="M2.5 3.5 5 6 7.5 3.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
      </span>
      {me?.tenant_name && <span className="hidden text-[11px] font-medium text-inkFaint xl:block">{me.tenant_name}</span>}
    </div>
  );
}
