/**
 * Canonical status language — ONE source of truth for semantic presentation.
 *
 * Concepts are intentionally kept separate so decision, outcome, and risk are
 * never visually conflated:
 *   DECISION  = the policy engine's verdict        (ALLOW | REQUIRE_APPROVAL | DENY)
 *   OUTCOME   = the effective product result       (AUTHORIZED | BLOCKED | PENDING | EXECUTED | FAILED | …)
 *   RISK      = assessed risk severity             (LOW | MEDIUM | HIGH | CRITICAL)
 *   TONE      = the shared visual vocabulary any label renders with
 *
 * Every future screen must consume this mapping rather than inventing colors.
 */

export type StatusTone = "neutral" | "success" | "warning" | "danger" | "info";

export interface ToneStyle {
  /** background + text + border classes for a chip/pill */
  chip: string;
  /** text-only color (used inline, e.g. value readouts) */
  text: string;
  /** dot indicator fill */
  dot: string;
}

export const TONE_STYLES: Record<StatusTone, ToneStyle> = {
  neutral: { chip: "border-neutralBorder bg-neutralBg text-inkMuted", text: "text-inkMuted", dot: "bg-inkFaint" },
  success: { chip: "border-successBorder bg-successBg text-success", text: "text-success", dot: "bg-success" },
  warning: { chip: "border-warningBorder bg-warningBg text-warning", text: "text-warning", dot: "bg-warning" },
  danger: { chip: "border-dangerBorder bg-dangerBg text-danger", text: "text-danger", dot: "bg-danger" },
  info: { chip: "border-infoBorder bg-infoBg text-info", text: "text-info", dot: "bg-info" },
};

export const TONE_LABEL: Record<StatusTone, string> = {
  neutral: "Neutral",
  success: "Allowed",
  warning: "Pending / review",
  danger: "Blocked / critical",
  info: "Informational",
};

/** ── DECISION — policy engine verdict ─────────────────────────────────── */
export const DECISION = {
  ALLOW: { tone: "success" as StatusTone },
  REQUIRE_APPROVAL: { tone: "warning" as StatusTone },
  DENY: { tone: "danger" as StatusTone },
} as const;
export type DecisionValue = keyof typeof DECISION;
export const DECISION_LABEL: Record<DecisionValue, string> = {
  ALLOW: "Allow",
  REQUIRE_APPROVAL: "Approval required",
  DENY: "Deny",
};

/** ── OUTCOME — effective product result ───────────────────────────────── */
export const OUTCOME = {
  AUTHORIZED: { tone: "success" as StatusTone },
  EXECUTED: { tone: "success" as StatusTone },
  PENDING_APPROVAL: { tone: "warning" as StatusTone },
  PENDING: { tone: "warning" as StatusTone },
  BLOCKED: { tone: "danger" as StatusTone },
  FAILED: { tone: "danger" as StatusTone },
  NOT_EXECUTED: { tone: "neutral" as StatusTone },
} as const;
export type OutcomeValue = keyof typeof OUTCOME;
export const OUTCOME_LABEL: Record<OutcomeValue, string> = {
  AUTHORIZED: "Authorized",
  EXECUTED: "Executed",
  PENDING_APPROVAL: "Pending approval",
  PENDING: "Pending",
  BLOCKED: "Blocked",
  FAILED: "Failed",
  NOT_EXECUTED: "Not executed",
};

/** ── RISK — assessed severity ─────────────────────────────────────────── */
export const RISK = {
  LOW: { tone: "success" as StatusTone },
  MEDIUM: { tone: "warning" as StatusTone },
  HIGH: { tone: "danger" as StatusTone },
  CRITICAL: { tone: "danger" as StatusTone },
} as const;
export type RiskValue = keyof typeof RISK;

/** ── Approval / lifecycle statuses (entities) ────────────────────────── */
export const APPROVAL_STATUS = {
  PENDING: { tone: "warning" as StatusTone },
  APPROVED: { tone: "success" as StatusTone },
  REJECTED: { tone: "danger" as StatusTone },
  EXPIRED: { tone: "danger" as StatusTone },
  CANCELLED: { tone: "neutral" as StatusTone },
} as const;

export const ENTITY_STATUS = {
  ACTIVE: { tone: "success" as StatusTone },
  SUSPENDED: { tone: "danger" as StatusTone },
  RETIRED: { tone: "neutral" as StatusTone },
  REVOKED: { tone: "danger" as StatusTone },
  DISABLED: { tone: "warning" as StatusTone },
  RESTRICTED: { tone: "warning" as StatusTone },
  DRAFT: { tone: "neutral" as StatusTone },
} as const;

/** Entity statuses that imply an authorization problem for tone heuristics. */
const DANGEROUS_ENTITY = new Set<string>(["SUSPENDED", "REVOKED"]);
const WARNING_ENTITY = new Set<string>(["DISABLED", "RESTRICTED", "EXPIRED"]);

export type StatusCategory = "decision" | "outcome" | "risk" | "approval" | "entity";

export interface ResolvedStatus {
  label: string;
  tone: StatusTone;
  category?: StatusCategory;
}

/**
 * Resolve a raw backend string to a canonical tone + friendly label.
 * Exact-match only; unknown values resolve neutral so no color is ever guessed.
 */
export function resolveStatus(value: string | null | undefined): ResolvedStatus {
  const v = (value ?? "").trim().toUpperCase();
  if (!v) return { label: "—", tone: "neutral" };

  const decision = DECISION[v as DecisionValue];
  if (decision) return { label: v, tone: decision.tone, category: "decision" };

  const outcome = OUTCOME[v as OutcomeValue];
  if (outcome) return { label: v, tone: outcome.tone, category: "outcome" };

  const risk = RISK[v as RiskValue];
  if (risk) return { label: v, tone: risk.tone, category: "risk" };

  const approval = APPROVAL_STATUS[v as keyof typeof APPROVAL_STATUS];
  if (approval) return { label: v, tone: approval.tone, category: "approval" };

  const entity = ENTITY_STATUS[v as keyof typeof ENTITY_STATUS];
  if (entity) return { label: v, tone: entity.tone, category: "entity" };

  if (DANGEROUS_ENTITY.has(v)) return { label: v, tone: "danger" };
  if (WARNING_ENTITY.has(v)) return { label: v, tone: "warning" };

  return { label: v, tone: "neutral" };
}
