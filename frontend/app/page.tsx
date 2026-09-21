import Link from "next/link";
import { PublicShell } from "@/components/public-site";

const operatingLoops = [
  { number: "01", title: "Organize work", body: "Give AI agents missions, goals, scoped projects, and an accountable owner.", tone: "emerald" },
  { number: "02", title: "Control actions", body: "Evaluate intent, policy, risk, and authority before any consequential action reaches a connector.", tone: "blue" },
  { number: "03", title: "Keep people in the loop", body: "Route the right decisions to qualified humans with complete context and a required reason.", tone: "amber" },
  { number: "04", title: "Prove what happened", body: "Keep a decision trail, execution receipt, and evidence bundle that can be searched later.", tone: "violet" },
];

export default function HomePage() {
  return (
    <PublicShell>
      <main className="marketing-main">
        <section className="agentos-hero">
          <div className="hero-light hero-light-one" aria-hidden />
          <div className="hero-light hero-light-two" aria-hidden />
          <div className="hero-grid-overlay" aria-hidden />
          <div className="relative z-10 mx-auto grid max-w-[1380px] gap-12 px-5 pb-16 pt-14 lg:grid-cols-[.82fr_1.18fr] lg:items-center lg:px-10 lg:pb-24 lg:pt-24">
            <div className="hero-copy max-w-[600px]">
              <p className="motion-reveal motion-delay-1 inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-300/[.08] px-3 py-1.5 text-[10px] font-bold tracking-[.15em] text-emerald-200">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-300 shadow-[0_0_12px_#6ee7b7]" /> GOVERNED AI OPERATIONS
              </p>
              <h1 className="motion-reveal motion-delay-2 mt-7 text-[48px] font-semibold leading-[.98] tracking-[-.06em] text-white sm:text-6xl lg:text-[74px]">
                Give your AI workforce a <span className="hero-gradient-text">clear chain of command.</span>
              </h1>
              <p className="motion-reveal motion-delay-3 mt-7 max-w-[540px] text-[17px] leading-8 text-slate-300 lg:text-lg">
                AgentOS lets teams plan useful work, govern consequential decisions, and retain proof of every outcome—without turning people into approval bottlenecks.
              </p>
              <div className="motion-reveal motion-delay-4 mt-9 flex flex-wrap gap-3">
                <Link href="/signup" className="public-cta rounded-lg bg-white px-5 py-3.5 text-sm font-semibold text-slate-950">Explore the sandbox <span aria-hidden>→</span></Link>
                <Link href="/product" className="public-secondary-cta rounded-lg border border-slate-600 bg-white/[.03] px-5 py-3.5 text-sm font-semibold text-white">See the operating model</Link>
              </div>
              <div className="motion-reveal motion-delay-5 mt-10 flex flex-wrap gap-x-6 gap-y-3 text-xs text-slate-400">
                <span className="flex items-center gap-2"><Check /> Sandbox-only connectors</span>
                <span className="flex items-center gap-2"><Check /> Human authority stays explicit</span>
              </div>
            </div>
            <CommandCenterPreview />
          </div>
          <div className="relative z-10 mx-auto grid max-w-[1380px] border-t border-white/[.09] px-5 lg:grid-cols-3 lg:px-10">
            <ProofItem label="Policy enforced" value="Before execution" />
            <ProofItem label="Human decision" value="Required when risk demands it" />
            <ProofItem label="Evidence retained" value="Across the action lifecycle" />
          </div>
        </section>

        <section className="mx-auto max-w-[1280px] px-5 py-20 lg:px-10 lg:py-28">
          <div className="grid gap-8 lg:grid-cols-[.75fr_1.25fr] lg:items-end">
            <div className="motion-reveal"><p className="section-kicker">THE AGENTOS LOOP</p><h2 className="mt-4 text-4xl font-semibold leading-[1.05] tracking-[-.045em] text-ink lg:text-5xl">AI work moves fast.<br />Control should move with it.</h2></div>
            <p className="motion-reveal motion-delay-2 max-w-xl text-base leading-7 text-inkSubtle lg:justify-self-end">AgentOS is not another agent chat surface. It is the operating layer between a workforce of AI agents and the systems where their decisions have real consequences.</p>
          </div>
          <div className="mt-14 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {operatingLoops.map((loop, index) => <article key={loop.title} className={`operating-loop operating-loop-${loop.tone} motion-reveal motion-delay-${index + 1}`}><div className="flex items-start justify-between"><span className="font-mono text-xs text-inkFaint">{loop.number}</span><span className="loop-dot" /></div><h3 className="mt-16 text-xl font-semibold tracking-tight text-ink">{loop.title}</h3><p className="mt-3 text-sm leading-6 text-inkSubtle">{loop.body}</p><span className="mt-8 inline-flex text-sm font-semibold text-signal">Explore <span className="ml-1">→</span></span></article>)}
          </div>
        </section>

        <section className="border-y border-slate-200 bg-[#f7f8f8] py-20 lg:py-28">
          <div className="mx-auto grid max-w-[1280px] gap-12 px-5 lg:grid-cols-[1fr_.92fr] lg:items-center lg:px-10">
            <WorkflowDiagram />
            <div className="motion-reveal motion-delay-2"><p className="section-kicker">ONE CONNECTED OPERATING MODEL</p><h2 className="mt-4 max-w-xl text-4xl font-semibold leading-[1.06] tracking-[-.045em] text-ink lg:text-5xl">Planning is useful only when it stays connected to control.</h2><p className="mt-6 max-w-lg text-base leading-7 text-inkSubtle">Workforce plans describe what agents are trying to accomplish. AgentOS governance decides whether an action is permitted, routes human judgment when needed, and records the final result.</p><div className="mt-8 space-y-3"><Detail label="No agent self-approval" text="Separation of duties stays enforced." /><Detail label="No silent execution" text="Protected actions pass through policy and risk." /><Detail label="No false reversals" text="Reconciliation uses correction actions and evidence." /></div><Link href="/workforce" className="public-dark-cta mt-9 inline-flex rounded-lg px-5 py-3 text-sm font-semibold text-white">Open Workforce <span className="ml-2">→</span></Link></div>
          </div>
        </section>

        <section className="mx-auto max-w-[1280px] px-5 py-20 lg:px-10 lg:py-28">
          <div className="governance-callout motion-reveal"><div><p className="text-xs font-bold tracking-[.15em] text-emerald-200">BUILT FOR CONSEQUENTIAL WORK</p><h2 className="mt-4 max-w-2xl text-3xl font-semibold leading-tight tracking-[-.04em] text-white lg:text-5xl">The goal is not more agent activity. It is accountable progress.</h2><p className="mt-5 max-w-xl text-base leading-7 text-slate-300">Use the local sandbox to explore the full decision path without connecting a live provider or moving real money.</p></div><div className="mt-8 flex flex-wrap gap-3 lg:mt-0"><Link href="/demo" className="public-cta rounded-lg bg-white px-5 py-3 text-sm font-semibold text-slate-950">Run guided demo →</Link><Link href="/security" className="public-secondary-cta rounded-lg border border-white/20 px-5 py-3 text-sm font-semibold text-white">Read security model</Link></div></div>
        </section>
      </main>
    </PublicShell>
  );
}

function Check() { return <span aria-hidden className="grid h-4 w-4 place-items-center rounded-full border border-emerald-300/30 text-[10px] text-emerald-200">✓</span>; }
function ProofItem({ label, value }: { label: string; value: string }) { return <div className="hero-proof-item"><span>{label}</span><strong>{value}</strong></div>; }
function Detail({ label, text }: { label: string; text: string }) { return <div className="flex gap-3"><span className="mt-1 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-signalSoft text-[11px] font-bold text-signal">✓</span><p className="text-sm leading-6 text-inkSubtle"><strong className="font-semibold text-ink">{label}.</strong> {text}</p></div>; }

function CommandCenterPreview() {
  return <div className="command-preview motion-reveal motion-delay-3" aria-label="Illustration of the AgentOS control center">
    <div className="preview-glow" aria-hidden />
    <div className="preview-topbar"><div className="flex items-center gap-2"><span className="preview-logo">A</span><span className="text-sm font-semibold text-white">acme / operations</span><span className="preview-badge">SANDBOX</span></div><div className="flex items-center gap-3 text-xs text-slate-500"><span className="preview-pulse" /> Control plane healthy</div></div>
    <div className="preview-body"><aside className="preview-sidebar"><p>OPERATE</p><span className="active">◫&nbsp;&nbsp; Control center</span><span>◈&nbsp;&nbsp; Workforce</span><span>↗&nbsp;&nbsp; Action requests</span><p className="mt-7">GOVERN</p><span>✓&nbsp;&nbsp; Approvals <b>2</b></span><span>⌁&nbsp;&nbsp; Evidence</span><div className="sidebar-user"><i>AS</i><div><strong>Alice Smith</strong><small>Treasury Manager</small></div></div></aside><div className="preview-content"><div className="preview-heading"><div><p>CONTROL CENTER</p><h3>Today&apos;s operating picture</h3></div><button type="button">+ New action</button></div><div className="preview-metrics"><PreviewMetric label="Governed actions" value="24" note="+8 this week" /><PreviewMetric label="Needs review" value="02" note="Human decision" warn /><PreviewMetric label="Evidence coverage" value="100%" note="All recorded" /></div><div className="preview-grid"><div className="preview-queue"><div className="queue-header"><div><p>REQUIRES YOUR ATTENTION</p><strong>Approval queue</strong></div><span>View all →</span></div><div className="approval-row"><span className="risk-ring" /><div><strong>Customer account credit</strong><small>SupportAgent · $250.00 · High risk</small></div><em>Review</em></div><div className="approval-row"><span className="risk-ring amber" /><div><strong>Update billing exception</strong><small>FinanceAgent · Requires reason</small></div><em>Review</em></div></div><div className="preview-activity"><p>WORKFORCE STATUS</p><strong>1 project progressing</strong><div className="activity-bar"><i /></div><small>3 work items active · 0 blocked</small></div></div></div></div>
  </div>;
}

function PreviewMetric({ label, value, note, warn }: { label: string; value: string; note: string; warn?: boolean }) { return <div className="preview-metric"><p>{label}</p><strong>{value}</strong><small className={warn ? "warn" : ""}>{warn ? "●" : "↑"} {note}</small></div>; }

function WorkflowDiagram() {
  return <div className="workflow-diagram motion-reveal"><div className="workflow-top"><span className="workflow-title">Workforce plan</span><span className="workflow-live"><i /> LIVE</span></div><div className="workflow-canvas"><div className="workflow-node node-mission"><span className="node-icon">◈</span><div><small>MISSION</small><strong>Reduce approval friction</strong></div></div><div className="workflow-path path-one" /><div className="workflow-path path-two" /><div className="workflow-node node-work"><span className="node-icon">↗</span><div><small>WORK ITEM</small><strong>Map queue patterns</strong></div></div><div className="workflow-node node-control"><span className="node-icon">✓</span><div><small>GOVERNANCE GATE</small><strong>Policy evaluation</strong></div></div><div className="workflow-node node-proof"><span className="node-icon">⌁</span><div><small>EVIDENCE</small><strong>Decision receipt</strong></div></div></div></div>;
}
