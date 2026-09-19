import Link from "next/link";
import { Eyebrow, PublicShell } from "@/components/public-site";

const features = [
  ["Governed action gateway", "Evaluate intent, policy, risk, approval requirements, and evidence before a consequential action is executed."],
  ["Accountable AI workforce", "Organize goals, projects, and agent work without creating a path around your governance controls."],
  ["Proof, not promises", "Searchable decision trails, approval rationale, execution receipts, and reconciliation workflows in one control plane."],
];

const steps = [
  ["01", "Plan", "Set a mission, goals, projects, and accountable agent ownership."],
  ["02", "Govern", "Policy and risk determine whether an action is allowed, blocked, or routed to a human."],
  ["03", "Prove", "Capture the decision, human approval, execution state, and evidence trail."],
];

export default function HomePage() {
  return (
    <PublicShell>
      <main>
        <section className="overflow-hidden bg-ink text-white">
          <div className="mx-auto grid max-w-7xl gap-12 px-5 pb-20 pt-16 lg:grid-cols-[1.12fr_.88fr] lg:px-8 lg:pb-28 lg:pt-24">
            <div className="max-w-3xl">
              <p className="inline-flex rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1 text-xs font-semibold tracking-wide text-emerald-200">GOVERNED AI OPERATIONS</p>
              <h1 className="mt-6 text-5xl font-semibold leading-[1.03] tracking-[-0.045em] sm:text-6xl lg:text-7xl">Let agents work.<br /><span className="text-emerald-300">Keep humans accountable.</span></h1>
              <p className="mt-7 max-w-xl text-lg leading-8 text-slate-300">AgentOS is the operating layer for teams that need AI agents to plan useful work while every consequential action stays governed, reviewable, and provable.</p>
              <div className="mt-9 flex flex-wrap gap-3">
                <Link href="/signup" className="rounded-lg bg-white px-5 py-3 text-sm font-semibold text-ink transition hover:bg-slate-100">Start in sandbox →</Link>
                <Link href="/product" className="rounded-lg border border-slate-600 px-5 py-3 text-sm font-semibold text-white transition hover:border-slate-400 hover:bg-white/5">Explore the platform</Link>
              </div>
              <p className="mt-4 text-xs text-slate-500">Sandbox-first. No live money movement in this environment.</p>
            </div>
            <div className="relative rounded-2xl border border-slate-700 bg-slate-900/70 p-5 shadow-2xl shadow-black/20 lg:mt-3">
              <div className="flex items-center justify-between border-b border-slate-700 pb-4"><div className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-emerald-400" /><span className="text-sm font-medium">Governed action review</span></div><span className="rounded bg-amber-400/15 px-2 py-1 text-[10px] font-semibold text-amber-200">HUMAN REVIEW</span></div>
              <div className="mt-5 space-y-4"><div className="rounded-xl border border-slate-700 bg-slate-950/60 p-4"><p className="text-xs font-medium text-slate-400">REQUESTED ACTION</p><p className="mt-2 text-base font-semibold">Issue customer account credit</p><p className="mt-1 text-sm text-slate-400">SupportAgent · Billing platform · $250.00</p></div><div className="grid grid-cols-2 gap-3"><Mini label="Policy" value="Approval required" tone="amber" /><Mini label="Risk" value="High · 78" tone="rose" /></div><div className="rounded-xl border border-emerald-400/25 bg-emerald-400/10 p-4"><p className="text-xs font-medium text-emerald-200">SEPARATION OF DUTIES ENFORCED</p><p className="mt-1 text-sm leading-6 text-emerald-50">The requester cannot approve this action. A qualified human approver must record a reason.</p></div></div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28">
          <div className="max-w-2xl"><Eyebrow>One operating model</Eyebrow><h2 className="mt-3 text-3xl font-semibold tracking-tight text-ink sm:text-4xl">From work planning to accountable execution.</h2><p className="mt-4 text-lg leading-8 text-inkSubtle">AgentOS connects the operational context agents need with the controls your organization requires.</p></div>
          <div className="mt-12 grid gap-5 md:grid-cols-3">{features.map(([title, body], index) => <article key={title} className="rounded-xl border border-hairline bg-surface p-6 shadow-card"><span className="grid h-9 w-9 place-items-center rounded-lg bg-signalSoft text-sm font-bold text-signal">0{index + 1}</span><h3 className="mt-6 text-lg font-semibold text-ink">{title}</h3><p className="mt-3 text-sm leading-6 text-inkSubtle">{body}</p><Link href={index === 1 ? "/workforce" : index === 2 ? "/evidence" : "/product"} className="mt-5 inline-block text-sm font-semibold text-signal hover:text-signalHover">Explore →</Link></article>)}</div>
        </section>

        <section className="border-y border-hairline bg-surfaceMuted"><div className="mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-24"><Eyebrow>How it works</Eyebrow><div className="mt-8 grid gap-8 md:grid-cols-3">{steps.map(([number, title, body]) => <div key={number} className="border-t-2 border-ink pt-5"><p className="font-mono text-xs text-signal">{number}</p><h3 className="mt-4 text-xl font-semibold text-ink">{title}</h3><p className="mt-3 text-sm leading-6 text-inkSubtle">{body}</p></div>)}</div></div></section>

        <section className="mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28"><div className="rounded-2xl bg-signal px-7 py-12 text-white sm:px-12"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-100">Designed for consequential work</p><div className="mt-4 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between"><div><h2 className="max-w-2xl text-3xl font-semibold tracking-tight sm:text-4xl">Give your agents a workforce. Keep your organization in control.</h2><p className="mt-4 max-w-xl text-base leading-7 text-emerald-50">Explore the sandbox without connecting a live provider or sending a real transaction.</p></div><Link href="/signup" className="shrink-0 rounded-lg bg-white px-5 py-3 text-center text-sm font-semibold text-ink transition hover:bg-slate-100">Enter sandbox →</Link></div></div></section>
      </main>
    </PublicShell>
  );
}

function Mini({ label, value, tone }: { label: string; value: string; tone: "amber" | "rose" }) {
  return <div className="rounded-lg border border-slate-700 bg-slate-950/60 p-3"><p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className={tone === "amber" ? "mt-1 text-sm font-semibold text-amber-200" : "mt-1 text-sm font-semibold text-rose-200"}>{value}</p></div>;
}
