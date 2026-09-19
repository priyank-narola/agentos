import Link from "next/link";
import { Eyebrow, PublicShell } from "@/components/public-site";

const surfaces = [
  ["Workforce", "Set missions, goals, bounded projects, and accountable agent work. Planning does not bypass governance.", "/workforce"],
  ["Action governance", "Preflight proposed actions, apply deterministic policy, score risk, and route qualified human approvals.", "/action-requests"],
  ["Evidence & operations", "Inspect immutable action evidence, provider outcomes, reconciliation cases, and operational signals.", "/evidence"],
];

export default function ProductPage() {
  return <PublicShell><main><section className="bg-ink px-5 py-20 text-white lg:px-8 lg:py-28"><div className="mx-auto max-w-4xl text-center"><p className="text-xs font-semibold uppercase tracking-[.16em] text-emerald-300">The AgentOS platform</p><h1 className="mt-5 text-4xl font-semibold tracking-tight sm:text-6xl">An operating system for governed AI work.</h1><p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-slate-300">Build an AI workforce that can plan, request, and operate—without losing policy, human judgment, or an audit trail.</p></div></section><section className="mx-auto max-w-6xl px-5 py-20 lg:px-8"><div className="grid gap-5 md:grid-cols-3">{surfaces.map(([title, body, href], index) => <article key={title} className="rounded-xl border border-hairline p-7"><p className="font-mono text-xs text-signal">0{index + 1}</p><h2 className="mt-5 text-2xl font-semibold text-ink">{title}</h2><p className="mt-4 text-sm leading-7 text-inkSubtle">{body}</p><Link href={href} className="mt-7 inline-block text-sm font-semibold text-signal hover:text-signalHover">Open sandbox surface →</Link></article>)}</div><div className="mt-16 rounded-2xl bg-surfaceMuted p-8 lg:p-12"><Eyebrow>Control chain</Eyebrow><h2 className="mt-3 text-3xl font-semibold tracking-tight text-ink">Every action has a readable route.</h2><div className="mt-8 grid gap-4 sm:grid-cols-4">{["Intent", "Policy & risk", "Human decision", "Evidence"].map((label, index) => <div key={label} className="rounded-lg border border-hairline bg-white p-4"><p className="text-xs text-inkFaint">0{index + 1}</p><p className="mt-2 font-semibold text-ink">{label}</p></div>)}</div></div></section></main></PublicShell>;
}
