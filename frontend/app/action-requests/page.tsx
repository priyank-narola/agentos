"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ActionRequest, api } from "@/lib/api";
import { RegistryShell, StateMessage } from "@/components/registry-shell";
import { Status } from "@/components/ui/Status";
import { DataTable, type DataColumn } from "@/components/ui/DataTable";
import { formatDateTime, shortId } from "@/lib/format";

export default function ActionRequestsPage() {
  const router = useRouter();
  const [requests, setRequests] = useState<ActionRequest[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.actionRequests().then(setRequests).catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false));
  }, []);

  const columns: DataColumn<ActionRequest>[] = [
    {
      key: "who",
      header: "Agent",
      render: (r) => (
        <div className="min-w-0">
          <p className="font-medium text-ink">{r.agent_name}</p>
          <p className="mt-0.5 truncate text-xs text-inkSubtle">Acting for {r.principal_name ?? shortId(r.principal_id)}</p>
        </div>
      ),
    },
    {
      key: "action",
      header: "Action",
      render: (r) => (
        <div className="min-w-0">
          <p className="text-ink">{r.action_name}</p>
          <p className="mt-0.5 truncate text-[11px] text-inkFaint">{r.tool_name}</p>
        </div>
      ),
    },
    { key: "resource", header: "Resource", render: (r) => <span className="font-mono text-xs text-inkSubtle">{r.resource_key}</span> },
    { key: "risk", header: "Risk", render: (r) => <Status value={r.risk_classification ?? "LOW"} /> },
    { key: "decision", header: "Decision", render: (r) => <Status value={r.decision ?? r.status} /> },
    { key: "execution", header: "Execution", render: (r) => <Status value={r.execution_status ?? "NOT_EXECUTED"} /> },
    {
      key: "time",
      header: "Requested",
      headerClassName: "text-right",
      align: "right",
      render: (r) => (
        <span className="text-xs text-inkFaint" title={formatDateTime(r.requested_at)}>
          {new Date(r.requested_at).toLocaleDateString()}
        </span>
      ),
    },
  ];

  return (
    <RegistryShell title="Action requests" eyebrow="Action governance">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-2xl text-sm leading-6 text-inkSubtle">
          Every governed action and its decision chain. Open a request to inspect who acted, why it was allowed or blocked, and the proof.
        </p>
        <div className="flex items-center gap-3">
          <Link href="/gateway" className="text-[13px] font-medium text-inkSubtle hover:text-ink">
            Test a request
          </Link>
          <span className="text-xs text-inkFaint">{requests.length} records</span>
        </div>
      </div>

      {error && <StateMessage tone="error">Unable to load action requests. {error}</StateMessage>}
      {loading && !error && <StateMessage>Loading governed actions…</StateMessage>}
      {!loading && !error && requests.length === 0 && <StateMessage>No governed actions recorded yet. Run the guided demo to create one.</StateMessage>}
      {requests.length > 0 && (
        <DataTable<ActionRequest>
          columns={columns}
          rows={requests}
          rowKey={(r) => r.id}
          onRowClick={(r) => router.push(`/action-requests/${r.id}`)}
          caption="Governed action requests"
          minWidth={980}
        />
      )}
    </RegistryShell>
  );
}
