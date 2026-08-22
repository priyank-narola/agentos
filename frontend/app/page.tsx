const navigation = ["Overview", "Action requests", "Agents", "Policies", "Audit trail"];

export default function Home() {
  return (
    <main className="min-h-screen lg:flex">
      <aside className="border-b border-slate-200 bg-ink px-6 py-6 text-slate-300 lg:min-h-screen lg:w-64 lg:border-b-0 lg:border-r">
        <div className="mb-12 flex items-center gap-3 text-white">
          <span className="grid h-9 w-9 place-items-center rounded bg-signal text-sm font-bold">A</span>
          <div><p className="font-semibold tracking-wide">AgentOS</p><p className="text-xs text-slate-400">Action Firewall</p></div>
        </div>
        <nav aria-label="Primary navigation" className="space-y-2">
          {navigation.map((item, index) => <div key={item} className={`rounded px-3 py-2.5 text-sm ${index === 0 ? "bg-white/10 text-white" : "text-slate-400"}`}>{item}</div>)}
        </nav>
        <div className="mt-16 border-t border-white/10 pt-5 text-xs leading-5 text-slate-500">Phase 1 foundation<br />Control plane under construction</div>
      </aside>
      <section className="flex-1 px-6 py-8 lg:px-12">
        <header className="mb-10 flex flex-wrap items-end justify-between gap-4 border-b border-slate-200 pb-6">
          <div><p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-signal">Runtime trust infrastructure</p><h1 className="text-3xl font-semibold tracking-tight text-ink">Control plane overview</h1></div>
          <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-800">Foundation mode</span>
        </header>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {["Active agents", "Action requests", "Allowed", "Pending approval"].map((label) => <div key={label} className="border border-slate-200 bg-white p-5"><p className="text-sm text-slate-500">{label}</p><p className="mt-4 text-3xl font-semibold text-slate-300">--</p><p className="mt-2 text-xs text-slate-400">Not connected yet</p></div>)}
        </div>
        <div className="mt-8 grid gap-6 xl:grid-cols-[1.4fr_1fr]">
          <div className="border border-slate-200 bg-white p-6"><h2 className="text-lg font-semibold">Action decision stream</h2><div className="mt-12 border-t border-dashed border-slate-300 pt-5 text-center text-sm text-slate-500">Runtime gateway will appear here in Phase 5.</div></div>
          <div className="border border-slate-200 bg-white p-6"><h2 className="text-lg font-semibold">System readiness</h2><div className="mt-6 space-y-4 text-sm"><p className="flex justify-between border-b border-slate-100 pb-3"><span className="text-slate-500">Frontend shell</span><strong className="font-medium text-signal">Ready</strong></p><p className="flex justify-between border-b border-slate-100 pb-3"><span className="text-slate-500">API foundation</span><strong className="font-medium text-signal">Ready</strong></p><p className="flex justify-between"><span className="text-slate-500">Authorization pipeline</span><strong className="font-medium text-slate-400">Planned</strong></p></div></div>
        </div>
      </section>
    </main>
  );
}
