"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ActionRequest, Approval, CorpusStats, IntelligenceAssessmentResult, api } from "@/lib/api";
import { RegistryShell, StateMessage, StatusPill } from "@/components/registry-shell";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function IntelligencePage() {
  const [requests, setRequests] = useState<ActionRequest[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [assessment, setAssessment] = useState<IntelligenceAssessmentResult | null>(null);
  const [corpus, setCorpus] = useState<CorpusStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [assessing, setAssessing] = useState(false);
  const [modelStatus, setModelStatus] = useState<{
    available: Array<{ name: string }>;
    providers?: Array<{ name: string; configured: boolean; reachable: boolean | null; status: string; error: string | null; latency_ms?: number; model?: string | null; endpoint_host?: string | null }>;
    status?: string;
    summary?: string;
    governance_rule?: string;
    note: string;
  } | null>(null);
  const [benchmark, setBenchmark] = useState<{ rule_engine: { accuracy: number; false_allow_rate: number; false_deny_rate: number; total: number; correct: number }; model_engine: { accuracy: number | null; false_allow_rate: number | null; false_deny_rate: number | null; unavailable: number }; dataset_size: number; model_provider: string; security_guarantee: string } | null>(null);
  const [benchmarking, setBenchmarking] = useState(false);
  const [evalData, setEvalData] = useState<{ total_scenarios: number; recommendation_accuracy: number; false_allow_rate: number } | null>(null);
  const [knowledge, setKnowledge] = useState<{ total: number; sources: Record<string, number>; categories: Record<string, number>; version: string } | null>(null);

  useEffect(() => {
    Promise.all([
      api.actionRequests().catch(() => [] as ActionRequest[]),
      api.approvals().catch(() => [] as Approval[]),
      api.intelligenceCorpusStats().catch(() => null),
      fetch(`${apiBase}/api/v1/intelligence/models`).then(r => r.ok ? r.json() : null).catch(() => null),
      fetch(`${apiBase}/api/v1/intelligence/evaluation`).then(r => r.ok ? r.json() : null).catch(() => null),
      fetch(`${apiBase}/api/v1/intelligence/knowledge/stats`).then(r => r.ok ? r.json() : null).catch(() => null),
    ])
      .then(([reqData, apprData, corpusData, modelData, evalResult, knowledgeData]) => {
        setRequests(reqData); setApprovals(apprData); setCorpus(corpusData); setModelStatus(modelData); setEvalData(evalResult); setKnowledge(knowledgeData);
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

  const runBenchmark = async () => {
    setBenchmarking(true); setError(null);
    try {
      const res = await fetch(`${apiBase}/api/v1/intelligence/benchmark`);
      if (!res.ok) throw new Error(`Benchmark: ${res.status}`);
      setBenchmark(await res.json());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Benchmark failed");
    } finally { setBenchmarking(false); }
  };

  const riskCounts = ["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((level) => ({ level, count: requests.filter((r) => r.risk_classification === level).length }));
  const executed = requests.filter((r) => r.execution_status === "EXECUTED").length;
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
      {/* === ARCHITECTURE BANNER === */}
      <div className="mb-6 rounded border border-ink bg-ink px-5 py-4 text-white">
        <p className="text-sm font-semibold">Three-Layer Intelligence Architecture</p>
        <div className="mt-3 grid gap-3 text-xs sm:grid-cols-3">
          <div className="rounded border border-blue-400/30 bg-blue-900/30 p-3">
            <p className="font-bold text-blue-300">MODEL INTELLIGENCE</p>
            <p className="mt-1 text-slate-300">Real LLM analysis — risk classification, threat detection, intent analysis, anomaly detection</p>
            <p className="mt-1 text-[10px] text-slate-400">Optional · Advisory only · Never authorizes</p>
          </div>
          <div className="rounded border border-emerald-400/30 bg-emerald-900/30 p-3">
            <p className="font-bold text-emerald-300">DETERMINISTIC GOVERNANCE</p>
            <p className="mt-1 text-slate-300">Rule engine — risk scoring, intent analysis, behavioral baseline, threat classification, policy recommendation</p>
            <p className="mt-1 text-[10px] text-slate-400">Always runs · No external calls · Fail-closed</p>
          </div>
          <div className="rounded border border-amber-400/30 bg-amber-900/30 p-3">
            <p className="font-bold text-amber-300">FINAL DECISION</p>
            <p className="mt-1 text-slate-300">Deterministic policy engine — authorization is ALWAYS deterministic, fail-closed, auditable</p>
            <p className="mt-1 text-[10px] text-slate-400">Irrevocable · Audit-logged · Policy engine decides</p>
          </div>
        </div>
        <p className="mt-3 text-xs text-slate-300">AI/Intelligence recommends. The deterministic policy engine decides. <span className="font-semibold text-amber-300">No model output can authorize, bypass policy, or trigger execution.</span></p>
      </div>

      {/* === MODEL STATUS === */}
      {(() => {
        const s = modelStatus?.status ?? "RULES_ONLY";
        const provider = modelStatus?.providers?.find((p) => p.configured) ?? null;
        const isActive = s === "MODEL_ACTIVE";
        const isDegraded = s === "MODEL_CONFIGURED_UNAVAILABLE";
        const tone = isActive
          ? { box: "border-successBorder bg-successBg", label: "text-success", badge: "bg-success/10 text-success", body: "text-ink" }
          : isDegraded
            ? { box: "border-warningBorder bg-warningBg", label: "text-warning", badge: "bg-warning/10 text-warning", body: "text-ink" }
            : { box: "border-hairline bg-surfaceMuted", label: "text-inkSubtle", badge: "bg-neutralBg text-neutral", body: "text-inkMuted" };
        const badge = isActive ? "MODEL ACTIVE" : isDegraded ? "MODEL UNAVAILABLE" : "RULES-ONLY";

        return (
          <div className={`mb-6 rounded-card border p-5 transition-colors duration-standard ease-standard ${tone.box}`}>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="min-w-0">
                <p className={`text-[11px] font-semibold uppercase tracking-[0.08em] ${tone.label}`}>Model Provider Status</p>
                <p className={`mt-1.5 text-[15px] leading-snug ${tone.body}`}>
                  {modelStatus?.summary ?? "No model provider configured. Running on deterministic intelligence."}
                </p>
                {provider && (
                  <dl className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-[12px] text-inkSubtle">
                    <div className="flex gap-1.5"><dt className="text-inkFaint">Provider</dt><dd className="font-medium text-inkMuted">{provider.name}</dd></div>
                    {provider.endpoint_host && <div className="flex gap-1.5"><dt className="text-inkFaint">Endpoint</dt><dd className="font-medium text-inkMuted">{provider.endpoint_host}</dd></div>}
                    {typeof provider.latency_ms === "number" && <div className="flex gap-1.5"><dt className="text-inkFaint">Latency</dt><dd className="font-medium text-inkMuted">{provider.latency_ms} ms</dd></div>}
                    <div className="flex gap-1.5"><dt className="text-inkFaint">Verified</dt><dd className="font-medium text-inkMuted">{provider.reachable === true ? "reachable" : provider.reachable === false ? "not reachable" : "not probed"}</dd></div>
                  </dl>
                )}
                {isDegraded && provider?.error && (
                  <p className="mt-3 max-w-2xl break-words rounded-control border border-warningBorder bg-surface/60 px-3 py-2 font-mono text-[11px] leading-relaxed text-warning">
                    {provider.error}
                  </p>
                )}
              </div>
              <span className={`shrink-0 rounded-control px-2.5 py-1 text-[11px] font-semibold tracking-[0.04em] ${tone.badge}`}>{badge}</span>
            </div>
            <p className="mt-3 border-t border-hairline pt-3 text-[12px] text-inkSubtle">
              {modelStatus?.governance_rule ?? "Model intelligence is advisory only. The deterministic policy engine decides."}{" "}
              {isDegraded && <span className="text-inkMuted">Authorization is unaffected — deterministic governance is the sole authority.</span>}
            </p>
          </div>
        );
      })()}

      {error && <StateMessage tone="error">{error}</StateMessage>}
      {loading && <StateMessage>Loading governance telemetry…</StateMessage>}

      {!loading && (
        <>
          {/* === LIVE INTELLIGENCE ASSESSMENT === */}
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

                {/* Policy Recommendation — FINAL DECISION */}
                {assessment.policy_recommendation && (
                  <div className="border-2 border-amber-400 bg-amber-50 p-5">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-wide text-amber-600">FINAL DECISION — Deterministic Policy Engine</p>
                        <span className={`mt-1 inline-block rounded px-3 py-1 text-sm font-bold ${recoColor(assessment.policy_recommendation.recommendation)}`}>
                          {assessment.policy_recommendation.recommendation}
                        </span>
                      </div>
                      <div className="text-right text-xs text-slate-600">
                        <p>Confidence: {(assessment.policy_recommendation.confidence * 100).toFixed(0)}%</p>
                        <p>Engine: {assessment.engine_version}</p>
                      </div>
                    </div>
                    <p className="mt-3 text-sm text-slate-700">{assessment.policy_recommendation.reasoning}</p>
                    <p className="mt-2 border-t border-amber-200 pt-2 text-xs font-semibold text-amber-700">{assessment.policy_recommendation.disclaimer}</p>
                  </div>
                )}
              </div>
            )}
          </section>

          {/* === BENCHMARK COMPARISON === */}
          <section className="mb-6 border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <h2 className="font-semibold text-ink">Model vs. Rules Benchmark</h2>
                <p className="mt-1 text-xs text-slate-500">Compares deterministic rule engine vs. real model intelligence across the corpus.</p>
              </div>
              <button type="button" disabled={benchmarking} onClick={runBenchmark} className="bg-ink px-4 py-2 text-sm font-medium text-white disabled:bg-slate-300">
                {benchmarking ? "Running…" : "Run Benchmark"}
              </button>
            </div>

            {benchmark && (
              <div className="mt-4 space-y-4">
                {/* Metric cards */}
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <div className="border border-slate-200 p-4">
                    <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Rule Engine Accuracy</p>
                    <p className="mt-1 text-2xl font-bold text-ink">{(benchmark.rule_engine.accuracy * 100).toFixed(1)}%</p>
                  </div>
                  <div className="border border-slate-200 p-4">
                    <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Model Accuracy</p>
                    <p className="mt-1 text-2xl font-bold text-ink">{benchmark.model_engine.accuracy !== null ? `${(benchmark.model_engine.accuracy * 100).toFixed(1)}%` : "N/A"}</p>
                  </div>
                  <div className="border border-red-200 bg-red-50 p-4">
                    <p className="text-[10px] font-bold uppercase tracking-wide text-red-400">Rule False-Allow Rate</p>
                    <p className="mt-1 text-2xl font-bold text-red-700">{(benchmark.rule_engine.false_allow_rate * 100).toFixed(1)}%</p>
                  </div>
                  <div className="border border-red-200 bg-red-50 p-4">
                    <p className="text-[10px] font-bold uppercase tracking-wide text-red-400">Model False-Allow Rate</p>
                    <p className="mt-1 text-2xl font-bold text-red-700">{benchmark.model_engine.false_allow_rate !== null ? `${(benchmark.model_engine.false_allow_rate * 100).toFixed(1)}%` : "N/A"}</p>
                  </div>
                </div>

                {/* Comparison table */}
                <div className="overflow-x-auto">
                  <table className="w-full border border-slate-200 text-xs">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="border-b border-slate-200 px-3 py-2 text-left font-semibold text-slate-600">Metric</th>
                        <th className="border-b border-slate-200 px-3 py-2 text-center font-semibold text-slate-600">Rule Engine</th>
                        <th className="border-b border-slate-200 px-3 py-2 text-center font-semibold text-slate-600">Model Engine</th>
                        <th className="border-b border-slate-200 px-3 py-2 text-center font-semibold text-slate-600">Verdict</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        ["Accuracy", benchmark.rule_engine.accuracy, benchmark.model_engine.accuracy],
                        ["False-Allow Rate", benchmark.rule_engine.false_allow_rate, benchmark.model_engine.false_allow_rate],
                        ["False-Deny Rate", benchmark.rule_engine.false_deny_rate, benchmark.model_engine.false_deny_rate],
                      ].map(([metric, ruleVal, modelVal]) => (
                        <tr key={metric as string}>
                          <td className="border-b border-slate-100 px-3 py-2 font-medium text-ink">{metric}</td>
                          <td className="border-b border-slate-100 px-3 py-2 text-center">{ruleVal !== null ? `${((ruleVal as number) * 100).toFixed(1)}%` : "—"}</td>
                          <td className="border-b border-slate-100 px-3 py-2 text-center">{modelVal !== null ? `${((modelVal as number) * 100).toFixed(1)}%` : "N/A"}</td>
                          <td className="border-b border-slate-100 px-3 py-2 text-center">
                            {modelVal !== null && ruleVal !== null
                              ? ((modelVal as number) >= (ruleVal as number)
                                  ? <span className="text-emerald-600 font-semibold">Model ≥ Rules</span>
                                  : <span className="text-orange-600 font-semibold">Rules &gt; Model</span>)
                              : <span className="text-slate-400">No model</span>}
                          </td>
                        </tr>
                      ))}
                      <tr>
                        <td className="border-b border-slate-100 px-3 py-2 font-medium text-ink">Dataset Size</td>
                        <td className="border-b border-slate-100 px-3 py-2 text-center" colSpan={2}>{benchmark.dataset_size} scenarios</td>
                        <td className="border-b border-slate-100 px-3 py-2 text-center text-slate-400">—</td>
                      </tr>
                      <tr>
                        <td className="border-b border-slate-100 px-3 py-2 font-medium text-ink">Model Provider</td>
                        <td className="border-b border-slate-100 px-3 py-2 text-center" colSpan={2}>{benchmark.model_provider}</td>
                        <td className="border-b border-slate-100 px-3 py-2 text-center text-slate-400">—</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Security guarantee */}
                <div className="rounded border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800">
                  <p className="font-semibold">Security Guarantee: {benchmark.security_guarantee}</p>
                  <p className="mt-1 text-amber-600">The deterministic policy engine always makes the final decision. Intelligence recommendations (rule or model) are advisory only and cannot authorize execution.</p>
                </div>
              </div>
            )}
          </section>

          {/* === CORPUS + KNOWLEDGE STATS === */}
          <section className="mb-6 border border-slate-200 bg-white p-6">
            <h2 className="font-semibold text-ink">Corpus &amp; Knowledge Base</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <div className="border border-slate-200 p-4">
                <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Corpus Scenarios</p>
                <p className="mt-1 text-2xl font-semibold text-ink">{corpus?.total ?? "—"}</p>
                <p className="mt-1 text-[11px] text-slate-400">{corpus?.provenance?.SYNTHETIC ?? "—"} synthetic · {corpus?.provenance?.PUBLIC_SOURCE ?? "—"} public-source</p>
              </div>
              <div className="border border-slate-200 p-4">
                <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Eval Results</p>
                <p className="mt-1 text-2xl font-semibold text-ink">{evalData?.total_scenarios ?? "—"}</p>
                <p className="mt-1 text-[11px] text-slate-400">{evalData?.recommendation_accuracy ? `${(evalData.recommendation_accuracy * 100).toFixed(0)}%` : "—"} accuracy · {evalData?.false_allow_rate ? `${(evalData.false_allow_rate * 100).toFixed(1)}%` : "—"} false-allow</p>
              </div>
              <div className="border border-slate-200 p-4">
                <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Knowledge Base</p>
                <p className="mt-1 text-2xl font-semibold text-ink">{knowledge?.total ?? "—"}</p>
                <p className="mt-1 text-[11px] text-slate-400">{knowledge ? `${Object.keys(knowledge.sources).length} sources · ${Object.keys(knowledge.categories).length} categories` : "authoritative security corpus"}</p>
              </div>
            </div>
          </section>

          {/* === GOVERNANCE SIGNALS === */}
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

          {/* === RISK EXPOSURE === */}
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

          {/* === HIGH-RISK ACTIONS === */}
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
        </>
      )}
    </RegistryShell>
  );
}
