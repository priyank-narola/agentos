"use client";

import { AppNav } from "@/components/app-nav";
import { IdentityBar } from "@/components/identity-bar";

export function RegistryShell({ children, title, eyebrow }: { children: React.ReactNode; title: string; eyebrow: string }) {
  return (
    <main className="min-h-screen bg-[#f4f6f5] lg:flex">
      <aside className="border-b border-slate-200 bg-ink px-6 py-6 text-slate-300 lg:min-h-screen lg:w-64 lg:border-b-0 lg:border-r">
        <AppNav />
      </aside>
      <section className="min-w-0 flex-1 px-5 py-7 lg:px-10 lg:py-9">
        <header className="mb-8 flex flex-wrap items-end justify-between gap-4 border-b border-slate-200 pb-6">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-signal">{eyebrow}</p>
            <h1 className="text-3xl font-semibold tracking-tight text-ink">{title}</h1>
          </div>
          <div className="flex flex-wrap items-center justify-end gap-3">
            <IdentityBar />
            <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-800">SANDBOX · NO REAL MONEY</span>
          </div>
        </header>
        {children}
      </section>
    </main>
  );
}

export function StateMessage({ children, tone = "muted" }: { children: React.ReactNode; tone?: "muted" | "error" }) {
  return <div className={`border p-6 text-sm ${tone === "error" ? "border-red-200 bg-red-50 text-red-800" : "border-dashed border-slate-300 bg-white text-slate-500"}`}>{children}</div>;
}
export function StatusPill({ value }: { value: string }) {
  return <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-600">{value}</span>;
}
