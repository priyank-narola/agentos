import Link from "next/link";
import { PublicShell } from "@/components/public-site";

export default function LoginPage() {
  return <PublicShell><main className="grid min-h-[calc(100vh-22rem)] place-items-center px-5 py-16"><section className="w-full max-w-md rounded-xl border border-hairline bg-white p-7 shadow-card"><p className="text-xs font-semibold uppercase tracking-[.16em] text-signal">Sandbox access</p><h1 className="mt-3 text-2xl font-semibold tracking-tight text-ink">Welcome back</h1><p className="mt-2 text-sm leading-6 text-inkSubtle">Authentication integration is not configured in this local demo. Enter with a sandbox identity to explore the product.</p><Link href="/control-center" className="mt-7 block rounded-lg bg-ink px-4 py-3 text-center text-sm font-semibold text-white hover:bg-ink/90">Enter control center</Link><Link href="/signup" className="mt-4 block text-center text-sm font-semibold text-signal hover:text-signalHover">Need sandbox access? Start here →</Link></section></main></PublicShell>;
}
