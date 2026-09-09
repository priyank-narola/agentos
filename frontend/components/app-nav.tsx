"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export type NavItem = { label: string; href: string };
export type NavSection = { title?: string; items: NavItem[] };

export const NAV_SECTIONS: NavSection[] = [
  { items: [{ label: "Flagship demo", href: "/demo" }] },
  { title: "Overview", items: [{ label: "Control center", href: "/" }] },
  {
    title: "Action gateway",
    items: [
      { label: "Runtime gateway", href: "/gateway" },
      { label: "Action requests", href: "/action-requests" },
      { label: "Approvals", href: "/approvals" },
    ],
  },
  {
    title: "Agent governance",
    items: [
      { label: "Agents", href: "/agents" },
      { label: "Delegations", href: "/delegations" },
      { label: "Tools", href: "/tools" },
      { label: "Resources", href: "/resources" },
      { label: "Policies", href: "/policies" },
      { label: "Policy evaluation", href: "/policy-evaluation" },
    ],
  },
  { title: "Observability", items: [{ label: "Audit & posture", href: "/observability" }] },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AppNav({ className = "" }: { className?: string }) {
  const pathname = usePathname();
  return (
    <div className={className}>
      <div className="mb-10 flex items-center gap-3 text-white">
        <span className="grid h-9 w-9 place-items-center rounded bg-signal text-sm font-bold">A</span>
        <div>
          <p className="font-semibold tracking-wide">AgentOS</p>
          <p className="text-xs text-slate-400">AI Action Governance</p>
        </div>
      </div>
      <nav aria-label="Product navigation" className="space-y-6">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title ?? section.items[0].href}>
            {section.title && <p className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">{section.title}</p>}
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const active = isActive(pathname, item.href);
                return (
                  <Link key={item.href} href={item.href} aria-current={active ? "page" : undefined} className={`block rounded px-3 py-2 text-sm ${active ? "bg-white/10 font-medium text-white" : "text-slate-400 hover:bg-white/10 hover:text-white"}`}>
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
      <div className="mt-12 border-t border-white/10 pt-5 text-xs leading-5 text-slate-500">
        Control center
        <br />
        Sandbox execution only — no real money movement
      </div>
    </div>
  );
}
