"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Approval, api } from "@/lib/api";
import { RegistryShell, StateMessage } from "@/components/registry-shell";
import { Status } from "@/components/ui/Status";
import { DataTable, type DataColumn } from "@/components/ui/DataTable";
import { formatDateTime, shortId } from "@/lib/format";

export default function ApprovalsPage() {
  const router = useRouter();
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.approvals().then(setApprovals).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false));
  }, []);

  const pending = approvals.filter((a) => a.status === "PENDING").length;

  const columns: DataColumn<Approval>[] = [
    {
      key: "who",
      header: "Requested by",
      render: (a) => (
        <div className="min-w-0">
          <p className="font-medium text-ink">{a.agent_name}</p>
          <p className="mt-0.5 truncate text-xs text-inkSubtle">Acting for {a.principal_name ?? shortId(a.principal_id)}</p>
        </div>
      ),
    },
    { key: "action", header: "Action", render: (a) => <span className="text-ink">{a.action_name}</span> },
    { key: "resource", header: "Resource", render: (a) => <span className="font-mono text-xs text-inkSubtle">{a.resource_key}</span> },
    { key: "risk", header: "Risk", render: (a) => <Status value={a.risk_classification ?? "LOW"} /> },
    { key: "status", header: "Status", render: (a) => <Status value={a.status} /> },
    {
      key: "expiry",
      header: "Expires",
      headerClassName: "text-right",
      align: "right",
      render: (a) => <span className="text-xs text-inkSubtle">{a.status === "PENDING" ? formatDateTime(a.expires_at) : "—"}</span>,
    },
  ];

  return (
    <RegistryShell title="Approvals" eyebrow="Human review boundary">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-2xl text-sm leading-6 text-inkSubtle">
          High-risk actions that a distinct human must authorize before execution. Approving executes in the sandbox only.
        </p>
        <span className="text-xs text-inkFaint">
          {approvals.length} total · <span className="font-medium text-warning">{pending} pending review</span>
        </span>
      </div>

      {error && <StateMessage tone="error">Unable to load approvals. {error}</StateMessage>}
      {loading && !error && <StateMessage>Loading the approval queue…</StateMessage>}
      {!loading && !error && approvals.length === 0 && (
        <div className="rounded-card border border-dashed border-hairlineStrong bg-surface px-6 py-12 text-center">
          <p className="text-sm font-medium text-ink">No approvals in the queue</p>
          <p className="mx-auto mt-1 max-w-sm text-[13px] text-inkSubtle">When a high-risk action requires a human, it will appear here for review.</p>
          <Link href="/action-requests" className="mt-4 inline-block text-[13px] font-semibold text-signal hover:text-signalHover">
            Browse governed actions →
          </Link>
        </div>
      )}
      {approvals.length > 0 && (
        <DataTable<Approval>
          columns={columns}
          rows={approvals}
          rowKey={(a) => a.id}
          onRowClick={(a) => router.push(`/approvals/${a.id}`)}
          caption="Approval requests"
          minWidth={860}
        />
      )}
    </RegistryShell>
  );
}
