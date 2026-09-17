"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { CustomerRemediationReadiness, ZendeskTicketContext, api, devTokenFor } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function CustomerRemediationPage() {
  const router = useRouter();
  const [readiness, setReadiness] = useState<CustomerRemediationReadiness | null>(null);
  const [ticketId, setTicketId] = useState("");
  const [ticket, setTicket] = useState<ZendeskTicketContext | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [refund, setRefund] = useState({ ticketId: "ZD-10482", paymentReference: "pi_demo_8J4K2", customerAccountId: "cus_demo_customer_0142", amount: "49.00", currency: "USD", reason: "Verified service interruption" });

  useEffect(() => {
    api.customerRemediationReadiness().then(setReadiness).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false));
  }, []);

  async function fetchTicket(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null); setTicket(null); setFetching(true);
    try { setTicket(await api.zendeskTicketContext(Number(ticketId))); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to retrieve ticket context."); }
    finally { setFetching(false); }
  }

  async function submitRefund(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const amount = Number(refund.amount);
    if (!Number.isFinite(amount) || amount <= 0) { setError("Refund amount must be greater than zero."); return; }
    setError(null); setSubmitting(true);
    try {
      const manifest = await api.customerRemediationBootstrap();
      await devTokenFor(manifest.requester.external_id).catch(() => undefined);
      const result = await api.gateway({
        principal_id: manifest.requester.id, agent_id: manifest.agent.id, action_id: manifest.action.id, resource_id: manifest.resource.id,
        idempotency_key: `refund-case-${crypto.randomUUID()}`,
        parameters: { ticket_id: ticket?.ticket_id ? `ZD-${ticket.ticket_id}` : refund.ticketId, payment_reference: refund.paymentReference, customer_account_id: refund.customerAccountId, amount: refund.amount, amount_minor: Math.round(amount * 100), currency: refund.currency, remedy: "refund", reason: refund.reason, transaction_reference: `RFD-${crypto.randomUUID().slice(0, 8).toUpperCase()}` },
        action_context: { summary: `Proposed ${refund.currency} ${refund.amount} customer refund for ${ticket?.ticket_id ? `Zendesk ticket ${ticket.ticket_id}` : refund.ticketId}.`, target_system: "Sandbox billing connector", before: { ticket_status: ticket?.status ?? "synthetic_demo", payment_reference: refund.paymentReference, prior_refund_amount: "0.00" }, proposed_change: { remedy: "refund", amount: refund.amount, currency: refund.currency }, recovery_class: "IRREVERSIBLE", recovery_plan: "No automatic reversal. Escalate an incorrect refund to finance and support for a documented corrective action." },
      });
      router.push(`/action-requests/${result.action_request_id}`);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to create the governed refund case."); }
    finally { setSubmitting(false); }
  }

  return <RegistryShell title="Customer remedies" eyebrow="Zendesk → governed refund → Stripe">
    <p className="max-w-3xl text-sm leading-6 text-inkSubtle">Prepare a customer refund from verified, minimised support context. The control layer does not read ticket conversations or execute a remedy until policy and an independent reviewer allow it.</p>
    {error && <div className="mt-5"><StateMessage tone="error">{error}</StateMessage></div>}
    {loading && <div className="mt-6"><StateMessage>Loading pilot readiness…</StateMessage></div>}
    {readiness && <>
      <section className="mt-6 grid gap-4 md:grid-cols-2">
        <article className="border border-hairline bg-surface p-5"><div className="flex justify-between gap-3"><div><p className="eyebrow">Support context</p><h2 className="mt-1 font-semibold text-ink">Zendesk ticket metadata</h2></div><StatusPill value={readiness.zendesk_ticket_context.configured ? "READY" : readiness.zendesk_ticket_context.enabled ? "CONFIGURATION REQUIRED" : "NOT CONNECTED"} /></div><p className="mt-3 text-sm leading-6 text-inkSubtle">Read-only metadata with {readiness.zendesk_ticket_context.required_scope}. Ticket content, comments, and attachments remain outside this product.</p></article>
        <article className="border border-hairline bg-surface p-5"><div className="flex justify-between gap-3"><div><p className="eyebrow">Billing execution</p><h2 className="mt-1 font-semibold text-ink">Stripe refund adapter</h2></div><StatusPill value={readiness.stripe_refund_execution.configured ? "TEST MODE READY" : readiness.stripe_refund_execution.enabled ? "CONFIGURATION REQUIRED" : "NOT CONNECTED"} /></div><p className="mt-3 text-sm leading-6 text-inkSubtle">Provider idempotency and unknown-outcome reconciliation are required before any refund is treated as complete.</p></article>
      </section>
      {readiness.zendesk_ticket_context.enabled ? <section className="mt-6 border border-hairline bg-surface p-6"><h2 className="font-semibold text-ink">Retrieve ticket context</h2><form onSubmit={fetchTicket} className="mt-4 flex flex-wrap items-end gap-3"><label className="grid gap-1.5 text-sm font-medium text-ink">Zendesk ticket ID<input required min="1" type="number" value={ticketId} onChange={(event) => setTicketId(event.target.value)} placeholder="10482" className="w-48 border border-hairlineStrong px-3 py-2 text-sm" /></label><button disabled={fetching} className="rounded-control bg-signal px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{fetching ? "Retrieving…" : "Retrieve context"}</button></form>{ticket && <dl className="mt-5 grid gap-3 border-t border-hairline pt-5 text-sm sm:grid-cols-2 lg:grid-cols-4"><div><dt className="text-xs text-inkFaint">Status</dt><dd className="mt-1"><StatusPill value={ticket.status} /></dd></div><div><dt className="text-xs text-inkFaint">Type / priority</dt><dd className="mt-1 text-ink">{ticket.type ?? "—"} / {ticket.priority ?? "—"}</dd></div><div><dt className="text-xs text-inkFaint">Tags</dt><dd className="mt-1 text-ink">{ticket.tags.join(", ") || "—"}</dd></div><div><dt className="text-xs text-inkFaint">Updated</dt><dd className="mt-1 text-ink">{ticket.updated_at ?? "—"}</dd></div></dl>}</section> : <section className="mt-6 border border-dashed border-hairlineStrong bg-surface p-6"><h2 className="font-semibold text-ink">Sandbox-first pilot</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-inkSubtle">Zendesk is intentionally disconnected until a design partner approves a least-privilege OAuth test. You can still run the full synthetic refund workflow now.</p><Link href="/demo" className="mt-4 inline-block text-sm font-semibold text-signal hover:underline">Run customer refund control demo →</Link></section>}
      <section className="mt-6 border border-hairline bg-surface p-6"><h2 className="font-semibold text-ink">Create governed refund case</h2><p className="mt-1 text-sm leading-6 text-inkSubtle">This creates a policy-bound action request. It does not execute a refund; the request must be independently approved and revalidated first.</p><form onSubmit={submitRefund} className="mt-5 grid gap-4 md:grid-cols-2"><label className="text-sm font-medium text-ink">Ticket reference<input required value={refund.ticketId} onChange={(event) => setRefund({ ...refund, ticketId: event.target.value })} className="mt-2 w-full border border-hairlineStrong px-3 py-2 text-sm" /></label><label className="text-sm font-medium text-ink">Stripe payment reference<input required value={refund.paymentReference} onChange={(event) => setRefund({ ...refund, paymentReference: event.target.value })} className="mt-2 w-full border border-hairlineStrong px-3 py-2 text-sm" /></label><label className="text-sm font-medium text-ink">Customer billing account<input required value={refund.customerAccountId} onChange={(event) => setRefund({ ...refund, customerAccountId: event.target.value })} className="mt-2 w-full border border-hairlineStrong px-3 py-2 text-sm" /></label><label className="text-sm font-medium text-ink">Refund amount<input required type="number" min="0.01" step="0.01" value={refund.amount} onChange={(event) => setRefund({ ...refund, amount: event.target.value })} className="mt-2 w-full border border-hairlineStrong px-3 py-2 text-sm" /></label><label className="md:col-span-2 text-sm font-medium text-ink">Reason<textarea required rows={3} value={refund.reason} onChange={(event) => setRefund({ ...refund, reason: event.target.value })} className="mt-2 w-full border border-hairlineStrong px-3 py-2 text-sm" /></label><div className="md:col-span-2"><button disabled={submitting} className="rounded-control bg-signal px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{submitting ? "Creating governed case…" : "Create refund case"}</button></div></form></section>
    </>}
  </RegistryShell>;
}
