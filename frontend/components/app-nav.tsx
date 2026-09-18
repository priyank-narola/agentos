"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";

export type NavItem = { label: string; href: string; hint?: string };

/**
 * Product navigation grouped by the AgentOS governance model.
 *
 * A group either navigates directly (`href`, no children) or opens a menu of
 * related surfaces. The grouping mirrors the governance chain so the shell
 * teaches the product's structure: what is happening now (Control Center),
 * what agents asked to do (Action Governance), who is allowed to act
 * (Agent Governance), what may be acted upon (Catalog), advisory analysis
 * (Intelligence), and the evidence trail (Observability).
 */
export type NavGroup = { label: string; href: string; items?: NavItem[] };

export const NAV_GROUPS: NavGroup[] = [
  { label: "Control center", href: "/" },
  {
    label: "Action governance",
    href: "/action-requests",
    items: [
      { label: "Action requests", href: "/action-requests", hint: "Every governed agent action and its decision" },
      { label: "Approvals", href: "/approvals", hint: "Human authorization queue" },
      { label: "Reconciliation", href: "/reconciliation", hint: "Resolve provider outcomes that remain uncertain" },
      { label: "Customer remedies", href: "/customer-remediation", hint: "Prepare governed refunds from support context" },
    ],
  },
  {
    label: "Agent governance",
    href: "/agents",
    items: [
      { label: "Agents", href: "/agents", hint: "Registered agent identities" },
      { label: "Delegations", href: "/delegations", hint: "Authority granted by principals" },
      { label: "Access control", href: "/access", hint: "Tenant roles for operators and reviewers" },
      { label: "Tenant settings", href: "/settings", hint: "Secret-free identity, connector, and release posture" },
    ],
  },
  {
    label: "Catalog",
    href: "/policies",
    items: [
      { label: "Policies", href: "/policies", hint: "Rules that decide" },
      { label: "Resources", href: "/resources", hint: "What agents may act upon" },
      { label: "Capabilities", href: "/tools", hint: "Tools and their actions" },
    ],
  },
  {
    label: "Prove",
    href: "/evidence",
    items: [
      { label: "Evidence", href: "/evidence", hint: "Searchable action evidence and immutable exports" },
      { label: "Observability", href: "/observability", hint: "Decision, execution, and provider-health signals" },
      { label: "Intelligence", href: "/intelligence", hint: "Advisory risk and policy analysis" },
    ],
  },
];

/** Developer / test surfaces — reachable, but deliberately subordinate. */
export const DEVELOPER_NAV: NavItem[] = [
  { label: "Action preflight", href: "/policy-evaluation" },
  { label: "Request a test action", href: "/gateway" },
];

export const DEMO_NAV: NavItem = { label: "Run governance demo", href: "/demo" };

/**
 * Trailing desktop menu. Developer/test surfaces stay reachable at every
 * breakpoint — subordinate to the governance groups, but never hidden.
 */
const MORE_GROUP: NavGroup = {
  label: "More",
  href: DEMO_NAV.href,
  items: [
    { label: DEMO_NAV.label, href: DEMO_NAV.href, hint: "Guided end-to-end governance walkthrough" },
    { label: "Action preflight", href: "/policy-evaluation", hint: "Preview policy, risk, and next controls without executing" },
    { label: "Launch readiness", href: "/launch-readiness", hint: "Production release gates and remaining work" },
    { label: "Request a test action", href: "/gateway", hint: "Submit an action through the live gateway" },
  ],
};

export function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

function groupActive(pathname: string, group: NavGroup): boolean {
  if (group.items?.length) return group.items.some((i) => isActive(pathname, i.href));
  return isActive(pathname, group.href);
}

/** The wordmark used in the top bar. */
export function Wordmark() {
  return (
    <Link href="/" className="flex items-center gap-2.5" aria-label="AgentOS control center">
      <span className="grid h-7 w-7 place-items-center rounded-[7px] bg-signal text-[13px] font-bold text-white">A</span>
      <span className="flex flex-col leading-none">
        <span className="text-[15px] font-semibold tracking-tight text-ink">AgentOS</span>
        <span className="mt-0.5 hidden text-[10px] font-medium tracking-wide text-inkFaint md:block">AI agent control plane</span>
      </span>
    </Link>
  );
}

const triggerClass = (active: boolean) =>
  cn(
    "flex items-center gap-1 rounded-control px-2.5 py-1.5 text-[13px] font-medium outline-none transition-colors duration-fast ease-standard",
    "focus-visible:ring-2 focus-visible:ring-focusRing focus-visible:ring-offset-1",
    active ? "bg-signalSoft text-signal" : "text-inkSubtle hover:bg-surfaceMuted hover:text-ink",
  );

function GroupMenu({ group, align = "left" }: { group: NavGroup; align?: "left" | "right" }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);
  const active = groupActive(pathname, group);

  // Close on outside click or Escape — menus must never trap the user.
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  // Route change closes the menu.
  useEffect(() => setOpen(false), [pathname]);

  return (
    <div ref={wrapRef} className="relative">
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className={triggerClass(active)}
      >
        {group.label}
        <svg
          width="10"
          height="10"
          viewBox="0 0 10 10"
          fill="none"
          aria-hidden
          className={cn("mt-px transition-transform duration-fast ease-standard", open && "rotate-180")}
        >
          <path d="m2.5 4 2.5 2.5L7.5 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open && (
        <div
          role="menu"
          aria-label={group.label}
          className={cn(
            "absolute top-[calc(100%+6px)] z-50 w-[272px] overflow-hidden rounded-popover border border-hairline bg-surface p-1.5 shadow-elevated",
            align === "right" ? "right-0" : "left-0",
          )}
        >
          {group.items?.map((item) => {
            const itemActive = isActive(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                role="menuitem"
                aria-current={itemActive ? "page" : undefined}
                className={cn(
                  "block rounded-control px-2.5 py-2 outline-none transition-colors duration-fast ease-standard",
                  "focus-visible:ring-2 focus-visible:ring-focusRing",
                  itemActive ? "bg-signalSoft" : "hover:bg-surfaceMuted",
                )}
              >
                <span className={cn("block text-[13px] font-medium", itemActive ? "text-signal" : "text-ink")}>{item.label}</span>
                {item.hint && <span className="mt-0.5 block text-[11px] leading-4 text-inkFaint">{item.hint}</span>}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

function PrimaryLinks({ className }: { className?: string }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Primary" className={cn("flex items-center gap-0.5", className)}>
      {NAV_GROUPS.map((group) =>
        group.items?.length ? (
          <GroupMenu key={group.label} group={group} />
        ) : (
          <Link
            key={group.href}
            href={group.href}
            aria-current={isActive(pathname, group.href) ? "page" : undefined}
            className={triggerClass(isActive(pathname, group.href))}
          >
            {group.label}
          </Link>
        ),
      )}
      <GroupMenu group={MORE_GROUP} align="right" />
    </nav>
  );
}

export function NavLinksMobile({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  const link = (item: NavItem) => {
    const active = isActive(pathname, item.href);
    return (
      <Link
        key={item.href}
        href={item.href}
        onClick={onNavigate}
        aria-current={active ? "page" : undefined}
        className={cn(
          "rounded-control px-3 py-2.5 text-[15px] font-medium transition-colors duration-fast ease-standard",
          active ? "bg-signalSoft text-signal" : "text-ink hover:bg-surfaceMuted",
        )}
      >
        {item.label}
      </Link>
    );
  };

  return (
    <div className="flex flex-col">
      <Link
        href={DEMO_NAV.href}
        onClick={onNavigate}
        className="rounded-control bg-ink px-4 py-3 text-center text-sm font-semibold text-white transition-colors duration-fast ease-standard hover:bg-ink/90"
      >
        {DEMO_NAV.label}
      </Link>

      {NAV_GROUPS.map((group) => (
        <div key={group.label}>
          {group.items?.length ? (
            <>
              <p className="mb-1.5 mt-5 px-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-inkFaint">{group.label}</p>
              <div className="flex flex-col">{group.items.map(link)}</div>
            </>
          ) : (
            <div className="mt-1.5 flex flex-col">{link({ label: group.label, href: group.href })}</div>
          )}
        </div>
      ))}

      <p className="mb-1.5 mt-5 px-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-inkFaint">Developer</p>
      <div className="flex flex-col">{DEVELOPER_NAV.map(link)}</div>

      <p className="mt-6 px-1 text-[11px] leading-4 text-inkFaint">Sandbox environment · no real money movement</p>
    </div>
  );
}

/** Renders the grouped primary navigation — used in the desktop top bar. */
export function AppNav({ className = "" }: { className?: string }) {
  return <PrimaryLinks className={className} />;
}
