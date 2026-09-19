import Link from "next/link";
import { PublicShell } from "@/components/public-site";

const controls = [
  ["Policy before execution", "A protected action is evaluated before it can reach an execution connector."],
  ["Separation of duties", "Requesters and AI agents cannot approve their own actions."],
  ["Evidence by default", "Decisions, approval reasons, receipts, and relevant events are recorded for review."],
  ["Sandbox transparency", "This demo environment only uses sandbox/test-mode connectors; no page represents live money movement as active."],
];

export default function SecurityPage() {
  return <PublicShell><main><section className="bg-surfaceMuted px-5 py-20 lg:px-8 lg:py-28"><div className="mx-auto max-w-4xl"><p className="text-xs font-semibold uppercase tracking-[.16em] text-signal">Security & governance</p><h1 className="mt-5 text-4xl font-semibold tracking-tight text-ink sm:text-6xl">Trust is a product feature, not a checkbox.</h1><p className="mt-6 max-w-2xl text-lg leading-8 text-inkSubtle">AgentOS is designed so operational speed does not require an ungoverned path to consequential systems.</p></div></section><section className="mx-auto max-w-6xl px-5 py-20 lg:px-8"><div className="grid gap-px overflow-hidden rounded-xl border border-hairline bg-hairline md:grid-cols-2">{controls.map(([title, body]) => <article key={title} className="bg-white p-7"><span className="text-signal">●</span><h2 className="mt-4 text-xl font-semibold text-ink">{title}</h2><p className="mt-3 text-sm leading-7 text-inkSubtle">{body}</p></article>)}</div><div className="mt-14 flex flex-col justify-between gap-5 rounded-xl bg-ink p-8 text-white sm:flex-row sm:items-center"><div><p className="text-sm font-semibold">See the decision trail in the sandbox.</p><p className="mt-1 text-sm text-slate-400">Evidence and operational views remain part of the governed app.</p></div><Link href="/evidence" className="rounded-lg bg-white px-4 py-2.5 text-center text-sm font-semibold text-ink">Open evidence explorer</Link></div></section></main></PublicShell>;
}
