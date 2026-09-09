"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ActionRequest, Approval, CorpusStats, IntelligenceAssessmentResult, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

export default function IntelligencePage() {
  const [requests, setRequests] = useState<ActionRequest[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [assessment, setAssessment] = useState<IntelligenceAssessmentResult | null>(null);
  const [corpus, setCorpus] = useState<CorpusStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [assessing, setAssessing] = useState(false);

  useEffect(() => {
    Promise.all([
      api.actionRequests().catch(() => [] as ActionRequest[]),
      api.approvals().catch(() => [] as Approval[]),
      api.intelligenceCorpusStats().catch(() => null),
    ])
      .then(([reqData, apprData, corpusData]) => {
        setRequests(reqData); setApprovals(apprData); setCorpus(corpusData);
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, []);

  const runAssessment = async () => {
    setAssessing(true); setError(null);
    try {
      const result = await api.intelligenceAssessDemo();
      setAssessment(result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Assessment failed");
    } finally { setAssessing(false); }
  };

  const riskCounts = ["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((level) => ({ level, count: requests.filter((r) => r.risk_classification === level).length }));
  const executed = requests.filter((r) => (r.reason ?? "").includes("executed via SandboxPaymentProvider")).length;
  const policyDenied = requests.filter((r) => (r.reason_code ?? "").startsWith("POLICY_DENY") || (r.reason_code ?? "").startsWith("DEFAULT_DENY")).length;
  const approvalRequired = requests.filter((r) => r.decision === "REQUIRE_APPROVAL" || (r.reason_code ?? "").startsWith("HIGH_RISK_APPROVAL")).length;
  const pendingApprovals = approvals.filter((a) => a.status === "PENDING").length;
  const tamper = requests.filter((r) => (r.reason_code ?? "").startsWith("SECURITY_PAYLOAD_TAMPERED")).length;
  const toctou = requests.filter((r) => (r.reason_code ?? "").startsWith("SECURITY_TOCTOU_REVALIDATION_FAILED")).length;
  const sod = requests.filter((r) => (r.reason_code ?? "").startsWith("SECURITY_SEPARATION_OF_DUTIES_VIOLATION")).length;

  const signals: Array<[string, number, string]> = [
    ["Executed in sandbox", executed, "successful governed executions"],
    ["Blocked by policy", policyDenied, "actions denied by policy"],
    ["Require approval", approvalRequired, "high-risk actions that needed a human"],
    ["Awaiting approval", pendingApprovals, "open approvals in the queue"],
    ["Tamper attempts", tamper, "payload integrity violations"],
    ["Revoked-delegation blocks", toctou, "TOCTOU revalidation failures"],
    ["SoD violations", sod, "self-approval attempts rejected"],
  ];

  const riskLevelColor = (level: string) => level === "CRITICAL" || level === "HIGH" ? "border-red-200 bg-red-50 text-red-700" : level === "MEDIUM" ? "border-amber-200 bg-amber-50 text-amber-700" : "border-emerald-200 bg-emerald-50 text-emerald-700";
  const threatSevColor = (sev: string) => sev === "CRITICAL" ? "text-red-700" : sev === "HIGH" ? "text-orange-600" : "text-slate-600";
  const recoColor = (reco: string) => reco === "DENY" ? "bg-red-600 text-white" : reco === "REQUIRE_APPROVAL" ? "bg-amber-500 text-white" : reco === "INVESTIGATE" ? "bg-blue-500 text-white" : "bg-emerald-600 text-white";

  return (
    <RegistryShell title="Risk & intelligence" eyebrow="Security & intelligence">
      <div className="mb-6 rounded border border-ink bg-ink px-5 py-4 text-white">
        <p className="text-sm font-semibold">AI/Intelligence recommends. The deterministic policy engine decides.</p>
        <p className="mt-1 text-xs text-slate-300">Intelligence assessments are advisory. Authorization is always deterministic and fail-closed.</p>
      </div>

      {error && <StateMessage tone="error">{error}</StateMessage>}
      {loading && <StateMessage>Loading governance telemetry…</StateMessage>}

      {!loading && (
        <>
          {/* Live Intelligence Assessment */}
          <section className="mb-6 border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-ink">Live Intelligence Assessment</h2>
                <p className="mt-1 text-sm text-slate-500">Runs the full intelligence pipeline (risk → intent → anomaly → threats → recommendation) against the most recent governed action.</p>
              </div>
              <button type="button" disabled={assessing} onClick={runAssessment} className="bg-ink px-5 py-2.5 text-sm font-medium text-white disabled:bg-slate-300">
                {assessing ? "Assessing…" : "Run Assessment"}
              </button>
            </div>

            {assessment?.status === "NO_DATA" && (
              <div className="mt-4"><StateMessage>{assessment.message}</StateMessage></div>
            )}

            {assessment?.risk && (
              <div className="mt-5 space-y-5">
                {/* Risk */}
                <div className={`rounded border p-5 ${riskLevelColor(assessment.risk.level)}`}>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-wide">Risk Assessment</p>
                      <p className="text-3xl font-bold">{assessment.risk.level} — {assessment.risk.score}/100</p>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] uppercase text-slate-500">Recommended control</p>
                      <span className={`rounded px-3 py-1 text-sm font-bold ${recoColor(assessment.risk.recommended_control)}`}>{assessment.risk.recommended_control}</span>
                    </div>
                  </div>
                  {assessment.risk.factors.length > 0 && (
                    <div className="mt-3 space-y-1.5">
                      <p className="text-xs font-semibold">Risk factors:</p>
                      {assessment.risk.factors.map((f) => (
                        <p key={f.code} className="flex justify-between border-b border-white/20 pb-1 text-xs">
                          <span>{f.label}</span>
                          <span className="font-mono font-semibold">+{f.weight}</span>
                        </p>
                      ))}
                    </div>
                  )}
                  <p className="mt-2 text-xs italic opacity-80">{assessment.risk.reasoning}</p>
                </div>

                {/* Intent + Anomaly side by side */}
                <div className="grid gap-4 md:grid-cols-2">
                  {assessment.intent && (
                    <div className="border border-slate-200 p-4">
                      <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Intent Analysis</p>
                      <p className="mt-1 font-medium text-ink">{assessment.intent.normalized_intent}</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        <StatusPill value={`Category: ${assessment.intent.category}`} />
                        <StatusPill value={`Confidence: ${(assessment.intent.confidence * 100).toFixed(0)}%`} />
                        <StatusPill value={`Provider: ${assessment.intent.provider}`} />
                      </div>
                      {assessment.intent.suspicious_indicators.length > 0 && (
                        <div className="mt-2 text-xs text-red-600">
                          <p className="font-semibold">Suspicious:</p>
                          {assessment.intent.suspicious_indicators.map((s, i) => <p key={i}>• {s}</p>)}
                        </div>
                      )}
                    </div>
                  )}
                  {assessment.anomaly && (
                    <div className="border border-slate-200 p-4">
                      <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Anomaly Detection</p>
                      <p className={`mt-1 text-xl font-bold ${assessment.anomaly.level === "CRITICAL" ? "text-red-700" : assessment.anomaly.level === "SUSPICIOUS" ? "text-orange-600" : assessment.anomaly.level === "UNUSUAL" ? "text-amber-600" : "text-emerald-600"}`}>
                        {assessment.anomaly.level}
                      </p>
                      {assessment.anomaly.signals.length > 0 ? (
                        <div className="mt-2 space-y-1 text-xs">
                          {assessment.anomaly.signals.map((s) => <p key={s.code}>• <strong>{s.label}</strong></p>)}
                        </div>
                      ) : (
                        <p className="mt-2 text-xs text-slate-500">Behavior consistent with baseline.</p>
                      )}
                    </div>
                  )}
                </div>

                {/* Threats */}
                {assessment.threats && assessment.threats.threats.length > 0 && (
                  <div className="border border-red-200 bg-red-50/50 p-4">
                    <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Threat Classification ({assessment.threats.threats.length} detected — highest: {assessment.threats.highest_severity})</p>
                    <div className="mt-2 space-y-2">
                      {assessment.threats.threats.map((t, i) => (
                        <div key={i} className="flex flex-wrap items-center justify-between gap-2 border-b border-red-100 pb-2 text-sm">
                          <div>
                            <span className={`font-bold ${threatSevColor(t.severity)}`}>{t.type.toUpperCase()}</span>
                            <span className="ml-2 text-xs text-slate-500">{t.reasoning}</span>
                          </div>
                          <div className="flex gap-2">
                            <StatusPill value={`${t.severity}`} />
                            <StatusPill value={`Rec: ${t.recommended_action}`} />
                            <StatusPill value={`${(t.confidence * 100).toFixed(0)}%`} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Policy Recommendation */}
                {assessment.policy_recommendation && (
                  <div className="border border-ink bg-ink p-5 text-white">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Policy Recommendation (Advisory)</p>
                        <span className={`mt-1 inline-block rounded px-3 py-1 text-sm font-bold ${recoColor(assessment.policy_recommendation.recommendation)}`}>
                          {assessment.policy_recommendation.recommendation}
                        </span>
                      </div>
                      <div className="text-right text-xs text-slate-300">
                        <p>Confidence: {(assessment.policy_recommendation.confidence * 100).toFixed(0)}%</p>
                        <p>Engine: {assessment.engine_version}</p>
                      </div>
                    </div>
                    <p className="mt-3 text-sm text-slate-300">{assessment.policy_recommendation.reasoning}</p>
                    <p className="mt-2 border-t border-white/10 pt-2 text-xs font-semibold text-amber-300">{assessment.policy_recommendation.disclaimer}</p>
                  </div>
                )}
              </div>
            )}
          </section>

          {/* Governance Signals (derived from real requests) */}
          <section className="border border-slate-200 bg-white p-6">
            <h2 className="font-semibold text-ink">Governance signals</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {signals.map(([label, value, note]) => (
                <div key={label} className="border border-slate-100 p-4">
                  <p className="text-sm font-medium text-ink">{label}</p>
                  <p className="mt-1 text-2xl font-semibold text-ink">{value}</p>
                  <p className="mt-1 text-[11px] leading-4 text-slate-400">{note}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Risk exposure */}
          <section className="mt-6 border border-slate-200 bg-white p-6">
            <h2 className="font-semibold text-ink">Risk exposure</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-4">
              {riskCounts.map(({ level, count }) => (
                <div key={level} className={`border p-4 ${level === "HIGH" || level === "CRITICAL" ? "border-red-200 bg-red-50" : "border-slate-200 bg-slate-50"}`}>
                  <p className="text-xs font-semibold text-slate-500">{level}</p>
                  <p className="mt-2 text-3xl font-semibold text-ink">{count}</p>
                </div>
              ))}
            </div>
          </section>

          {/* High-risk actions */}
          <section className="mt-6 border border-slate-200 bg-white p-6">
            <div className="flex items-end justify-between gap-4">
              <h2 className="font-semibold text-ink">High-risk governed actions</h2>
              <Link href="/action-requests" className="text-xs font-semibold text-signal hover:underline">All actions →</Link>
            </div>
            {requests.filter((r) => r.risk_classification === "HIGH" || r.risk_classification === "CRITICAL").length === 0 ? (
              <div className="mt-4"><StateMessage>No high-risk actions recorded.</StateMessage></div>
            ) : (
              <ul className="mt-4 space-y-2">
                {requests.filter((r) => r.risk_classification === "HIGH" || r.risk_classification === "CRITICAL").slice(0, 10).map((req) => (
                  <li key={req.id}>
                    <Link href={`/action-requests/${req.id}`} className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 py-2.5 text-sm hover:bg-slate-50">
                      <span><strong className="text-ink">{req.agent_name}</strong><small className="ml-2 text-slate-400">{req.action_name}</small></span>
                      <span className="flex gap-2"><StatusPill value={`${req.risk_classification} · ${req.risk_score}`} /><StatusPill value={req.decision ?? req.status} /></span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Corpus */}
          {corpus && (
            <section className="mt-6 border border-slate-200 bg-white p-6">
              <h2 className="font-semibold text-ink">Intelligence corpus</h2>
              <div className="mt-3 flex flex-wrap gap-3 text-sm">
                <StatusPill value={`${corpus.total} scenarios`} />
                {Object.entries(corpus.provenance).map(([prov, count]) => (
                  <StatusPill key={prov} value={`${prov}: ${count}`} />
                ))}
                <StatusPill value={`Schema: ${corpus.schema_version}`} />
              </div>
              <p className="mt-2 text-xs text-slate-400">Every scenario is provenance-labeled (SYNTHETIC or PUBLIC_SOURCE). No real customer data.</p>
            </section>
          )}

          {/* Architecture note */}
          <section className="mt-6 border border-slate-200 bg-white p-6">
            <h2 className="font-semibold text-ink">Intelligence architecture</h2>
            <div className="mt-3 flex flex-wrap items-center gap-2 text-sm font-medium">
              {["Action", "Context Builder", "Risk Intelligence", "Intent Analysis", "Anomaly Detection", "Threat Classification", "Policy Recommendation", "Deterministic Policy Engine", "Final Decision"].map((step, i, arr) => (
                <span key={step} className="flex items-center gap-2">
                  <span className={`rounded px-3 py-1.5 ${step === "Deterministic Policy Engine" ? "bg-ink text-white" : "border border-slate-200 bg-slate-50 text-slate-700"}`}>{step}</span>
                  {i < arr.length - 1 && <span className="text-slate-300">→</span>}
                </span>
              ))}
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              The intelligence layer analyzes, classifies, explains, and recommends — but the deterministic policy engine always makes the final authorization decision.
              Model providers (LLMs) are optional pluggable intelligence sources behind the <code className="rounded bg-slate-100 px-1">IntelligenceModelProvider</code> abstraction; the system works fully without any LLM.
            </p>
          </section>
        </>
      )}
    </RegistryShell>
  );
}
