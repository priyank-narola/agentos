/**
 * CANONICAL GOVERNANCE CHAIN + PRODUCT VOCABULARY
 *
 * Single source of truth for the AgentOS governance lifecycle and the
 * product-facing vocabulary. Every screen must consume GOVERNANCE_STAGES
 * rather than defining its own step array. Semantic status presentation is
 * owned by lib/status.ts — never duplicated here or in screens.
 */

export type GovernanceStageId =
  | "request"
  | "identify"
  | "evaluate"
  | "decide"
  | "approve"
  | "revalidate"
  | "execute"
  | "audit";

/** Who/what produces this stage — useful for authority labelling in UIs. */
export type GovernanceMode = "server" | "deterministic" | "human" | "sandbox" | "system";

export interface GovernanceStage {
  id: GovernanceStageId;
  /** Human-readable product label */
  label: string;
  /** One-line meaning */
  short: string;
  /** Longer description used for explanations/education */
  description: string;
  /** Who/what drives the stage */
  mode: GovernanceMode;
}

export const GOVERNANCE_STAGES: readonly GovernanceStage[] = [
  {
    id: "request",
    label: "Request",
    short: "Intent captured",
    description: "The agent submits a concrete action request on behalf of a principal.",
    mode: "server",
  },
  {
    id: "identify",
    label: "Identify",
    short: "Identity resolved",
    description: "Agent, principal, and delegated authority are resolved and verified.",
    mode: "deterministic",
  },
  {
    id: "evaluate",
    label: "Evaluate",
    short: "Risk assessed",
    description: "Risk is scored from the action, resource, context, and history.",
    mode: "deterministic",
  },
  {
    id: "decide",
    label: "Decide",
    short: "Policy decides",
    description: "The deterministic policy engine returns ALLOW, REQUIRE_APPROVAL, or DENY.",
    mode: "deterministic",
  },
  {
    id: "approve",
    label: "Approve",
    short: "Human approval",
    description: "A distinct human authorizes the exact request when approval is required.",
    mode: "human",
  },
  {
    id: "revalidate",
    label: "Revalidate",
    short: "Final check before execution",
    description: "The security context and payload are re-checked immediately before execution.",
    mode: "deterministic",
  },
  {
    id: "execute",
    label: "Execute",
    short: "Authoritative outcome",
    description: "The downstream action is attempted and its outcome is recorded.",
    mode: "sandbox",
  },
  {
    id: "audit",
    label: "Audit",
    short: "Durable evidence",
    description: "Durable evidence of what happened and why is recorded for proof.",
    mode: "system",
  },
];

/** Canonical stage order is the array order. */
export const GOVERNANCE_STAGE_IDS: readonly GovernanceStageId[] = GOVERNANCE_STAGES.map((s) => s.id);

export function stageById(id: GovernanceStageId): GovernanceStage {
  return GOVERNANCE_STAGES.find((s) => s.id === id) as GovernanceStage;
}

export function stageIndex(stage: GovernanceStageId | number): number {
  return typeof stage === "number" ? stage : GOVERNANCE_STAGE_IDS.indexOf(stage);
}

export function stageLabel(id: GovernanceStageId): string {
  return stageById(id).label;
}

/**
 * Determine a governance step's display state.
 * 'done' for everything up to completedThrough, 'active' for current,
 * overridable per-stage (e.g. a rejected approval marks its stage 'bad').
 */
export type GovernanceStepState = "done" | "active" | "pending" | "bad";

export interface GovernanceStateInput {
  /** stage that is currently in progress (index or id); optional */
  current?: GovernanceStageId | number;
  /** last stage already completed (index or id); optional */
  completedThrough?: GovernanceStageId | number;
  /** explicit per-stage overrides, applied last */
  overrides?: Partial<Record<GovernanceStageId, GovernanceStepState>>;
}

export function governanceStageState(stageId: GovernanceStageId, ctx: GovernanceStateInput): GovernanceStepState {
  const override = ctx.overrides?.[stageId];
  if (override) return override;
  const idx = stageIndex(stageId);
  const current = ctx.current !== undefined ? stageIndex(ctx.current) : -1;
  const completed = ctx.completedThrough !== undefined ? stageIndex(ctx.completedThrough) : -1;
  if (completed >= 0 && idx <= completed) return "done";
  if (idx === current) return "active";
  return "pending";
}

/**
 * ── CANONICAL PRODUCT VOCABULARY ────────────────────────────────────────
 * Product-facing meanings of the core concepts. Use these labels/meanings
 * consistently at the UI boundary even where backend field names differ.
 */
export type ConceptKey =
  | "agent"
  | "principal"
  | "intent"
  | "action"
  | "resource"
  | "risk"
  | "policy"
  | "decision"
  | "approval"
  | "revalidation"
  | "execution"
  | "audit"
  | "delegation"
  | "capability"
  | "proof";

export interface Concept {
  label: string;
  meaning: string;
}

export const GOVERNANCE_CONCEPTS: Record<ConceptKey, Concept> = {
  agent: { label: "Agent", meaning: "The AI/software actor attempting the action." },
  principal: { label: "Principal", meaning: "The human or organizational identity the agent is acting for." },
  intent: { label: "Intent", meaning: "What the agent is trying to accomplish." },
  action: { label: "Action", meaning: "The concrete operation requested." },
  resource: { label: "Resource", meaning: "The target data/system/object affected." },
  risk: { label: "Risk", meaning: "The assessed risk of the requested action." },
  policy: { label: "Policy", meaning: "The deterministic governance rules that apply." },
  decision: { label: "Decision", meaning: "The governance result: ALLOW, REQUIRE_APPROVAL, or DENY." },
  approval: { label: "Approval", meaning: "Explicit human authorization when required." },
  revalidation: { label: "Revalidation", meaning: "The final authorization check immediately before execution." },
  execution: { label: "Execution", meaning: "The actual downstream action attempt and its authoritative outcome." },
  audit: { label: "Audit", meaning: "Durable evidence of what happened and why." },
  delegation: { label: "Delegation", meaning: "The authority relationship allowing an agent to act for a principal." },
  capability: { label: "Capability", meaning: "What an agent/tool is technically capable of doing." },
  proof: { label: "Proof", meaning: "Evidence that lets an action and its governance outcome be independently audited." },
};

export function concept(key: ConceptKey): Concept {
  return GOVERNANCE_CONCEPTS[key];
}

/** Canonical phrase for "the agent acting for a principal". */
export function actingFor(agent: string, principal: string): string {
  return `${agent} acting for ${principal}`;
}
