import Link from "next/link";
import type { ReactNode } from "react";

const nav = [
  { href: "/product", label: "Product" },
  { href: "/security", label: "Security" },
  { href: "/pricing", label: "Pricing" },
];

export function PublicHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-ink/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 lg:px-8">
        <Link href="/" className="flex items-center gap-2.5 text-white" aria-label="AgentOS home">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-signal text-sm font-bold">A</span>
          <span className="font-semibold tracking-tight">AgentOS</span>
        </Link>
        <nav aria-label="Public navigation" className="hidden items-center gap-7 text-sm text-slate-300 md:flex">
          {nav.map((item) => <Link key={item.href} href={item.href} className="transition hover:text-white">{item.label}</Link>)}
        </nav>
        <div className="flex items-center gap-3 text-sm font-medium">
          <Link href="/login" className="hidden text-slate-200 transition hover:text-white sm:inline">Sign in</Link>
          <Link href="/signup" className="rounded-lg bg-white px-3.5 py-2 text-ink transition hover:bg-slate-100">Start in sandbox</Link>
        </div>
      </div>
    </header>
  );
}

export function PublicFooter() {
  return (
    <footer className="border-t border-slate-800 bg-ink text-slate-300">
      <div className="mx-auto grid max-w-7xl gap-10 px-5 py-12 lg:grid-cols-[1.3fr_repeat(3,1fr)] lg:px-8">
        <div>
          <div className="flex items-center gap-2.5 text-white"><span className="grid h-7 w-7 place-items-center rounded-md bg-signal text-xs font-bold">A</span><span className="font-semibold">AgentOS</span></div>
          <p className="mt-4 max-w-xs text-sm leading-6 text-slate-400">A governance control plane for organizations operating AI agents.</p>
        </div>
        <FooterColumn title="Platform" links={[{ href: "/product", label: "Product" }, { href: "/workforce", label: "Workforce" }, { href: "/control-center", label: "Control center" }]} />
        <FooterColumn title="Trust" links={[{ href: "/security", label: "Security" }, { href: "/evidence", label: "Evidence" }, { href: "/policies", label: "Policies" }]} />
        <FooterColumn title="Access" links={[{ href: "/login", label: "Sign in" }, { href: "/signup", label: "Start in sandbox" }, { href: "/demo", label: "Guided demo" }]} />
      </div>
      <div className="mx-auto max-w-7xl border-t border-slate-800 px-5 py-5 text-xs text-slate-500 lg:px-8">AgentOS sandbox demonstration environment. No real money movement.</div>
    </footer>
  );
}

function FooterColumn({ title, links }: { title: string; links: Array<{ href: string; label: string }> }) {
  return <div><p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">{title}</p><div className="mt-4 flex flex-col gap-3 text-sm">{links.map((link) => <Link key={link.href} href={link.href} className="transition hover:text-white">{link.label}</Link>)}</div></div>;
}

export function PublicShell({ children }: { children: ReactNode }) {
  return <div className="min-h-screen bg-white"><PublicHeader />{children}<PublicFooter /></div>;
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return <p className="text-xs font-semibold uppercase tracking-[0.16em] text-signal">{children}</p>;
}
