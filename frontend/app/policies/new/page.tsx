"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { RegistryShell, StateMessage } from "@/components/registry-shell";

export default function NewPolicyPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("100");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const policy = await api.createPolicy({
        name: name.trim(),
        description: description.trim() || undefined,
        version: 1,
        priority: Number(priority),
      });
      router.push(`/policies/${policy.id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to create the policy draft.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <RegistryShell title="New draft policy" eyebrow="Policy center">
      <div className="mb-6 flex items-start justify-between gap-4">
        <p className="max-w-2xl text-sm leading-6 text-slate-500">Drafts do not govern any action. Add rules, test representative requests, and publish only when the policy is ready.</p>
        <Link href="/policies" className="text-sm font-semibold text-signal hover:underline">← Policies</Link>
      </div>
      <form onSubmit={submit} className="max-w-2xl space-y-5 border border-slate-200 bg-white p-6">
        {error && <StateMessage tone="error">{error}</StateMessage>}
        <label className="block text-sm font-medium text-ink">Policy name
          <input required value={name} onChange={(event) => setName(event.target.value)} placeholder="Customer credit guardrail" className="mt-2 w-full border border-slate-300 px-3 py-2 text-sm outline-none focus:border-ink" />
        </label>
        <label className="block text-sm font-medium text-ink">Description <span className="font-normal text-slate-400">optional</span>
          <textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={4} placeholder="What business risk this policy controls and why." className="mt-2 w-full resize-y border border-slate-300 px-3 py-2 text-sm outline-none focus:border-ink" />
        </label>
        <label className="block text-sm font-medium text-ink">Policy priority
          <input required type="number" min="0" value={priority} onChange={(event) => setPriority(event.target.value)} className="mt-2 w-40 border border-slate-300 px-3 py-2 text-sm outline-none focus:border-ink" />
          <span className="mt-2 block text-xs font-normal leading-5 text-slate-500">Lower numbers evaluate first. Within a matching policy, explicit deny always wins.</span>
        </label>
        <div className="flex flex-wrap items-center gap-3 border-t border-slate-100 pt-5">
          <button disabled={saving} className="bg-ink px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{saving ? "Creating…" : "Create draft"}</button>
          <p className="text-xs text-slate-500">The first version is 1. Future changes create a new version automatically.</p>
        </div>
      </form>
    </RegistryShell>
  );
}
