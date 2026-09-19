import Link from "next/link";
import { PublicShell } from "@/components/public-site";

const plans = [
  { name: "Sandbox", description: "Explore the product safely", capabilities: ["Guided governance demo", "Seeded Workforce data", "Sandbox connectors only"], label: "Enter sandbox", href: "/signup" },
  { name: "Team", description: "For teams defining a governed pilot", capabilities: ["Workforce planning", "Policy and approvals", "Evidence and reconciliation"], label: "Talk to us", href: "/signup" },
  { name: "Enterprise", description: "For organization-wide AI operations", capabilities: ["Tenant administration", "Identity and retention controls", "Implementation planning"], label: "Plan deployment", href: "/signup" },
];

export default function PricingPage() {
  return <PublicShell><main><section className="mx-auto max-w-4xl px-5 pb-12 pt-20 text-center lg:px-8 lg:pt-28"><p className="text-xs font-semibold uppercase tracking-[.16em] text-signal">Access & rollout</p><h1 className="mt-5 text-4xl font-semibold tracking-tight text-ink sm:text-6xl">Start governed. Scale deliberately.</h1><p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-inkSubtle">The current environment is a sandbox product demonstration. Production tiers and contracts require explicit founder and customer validation before launch.</p></section><section className="mx-auto grid max-w-6xl gap-5 px-5 pb-20 lg:grid-cols-3 lg:px-8">{plans.map((plan, index) => <article key={plan.name} className={index === 1 ? "rounded-xl border-2 border-signal bg-white p-7 shadow-card" : "rounded-xl border border-hairline bg-white p-7"}><p className="text-xl font-semibold text-ink">{plan.name}</p><p className="mt-2 min-h-12 text-sm leading-6 text-inkSubtle">{plan.description}</p><div className="my-7 border-t border-hairline" /><ul className="space-y-3 text-sm text-inkSubtle">{plan.capabilities.map((capability) => <li key={capability} className="flex gap-2"><span className="font-semibold text-signal">✓</span>{capability}</li>)}</ul><Link href={plan.href} className={index === 1 ? "mt-8 block rounded-lg bg-signal px-4 py-3 text-center text-sm font-semibold text-white hover:bg-signalHover" : "mt-8 block rounded-lg border border-hairlineStrong px-4 py-3 text-center text-sm font-semibold text-ink hover:bg-surfaceMuted"}>{plan.label}</Link></article>)}</section></main></PublicShell>;
}
