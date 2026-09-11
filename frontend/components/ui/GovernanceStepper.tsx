import type { ReactNode } from "react";
import {
  GOVERNANCE_STAGES,
  governanceStageState,
  type GovernanceStageId,
  type GovernanceStateInput,
} from "@/lib/governance";
import { Stepper, type Step } from "@/components/ui/Stepper";

export interface GovernanceStepperProps extends GovernanceStateInput {
  orientation?: "vertical" | "horizontal";
  /** per-stage caption overrides by stage id */
  captions?: Partial<Record<GovernanceStageId, ReactNode>>;
  /** per-stage right-edge metadata (vertical layout) */
  meta?: Partial<Record<GovernanceStageId, ReactNode>>;
  className?: string;
}

/**
 * AgentOS-specific stepper. Owns no stage definitions — it consumes
 * GOVERNANCE_STAGES and derives states from the shared model. The generic
 * Stepper remains a pure visual primitive.
 */
export function GovernanceStepper({
  current,
  completedThrough,
  overrides,
  orientation = "vertical",
  captions,
  meta,
  className,
}: GovernanceStepperProps) {
  const steps: Step[] = GOVERNANCE_STAGES.map((stage) => ({
    label: stage.label,
    caption: captions?.[stage.id] ?? stage.short,
    state: governanceStageState(stage.id, { current, completedThrough, overrides }),
    meta: meta?.[stage.id],
  }));

  return <Stepper items={steps} orientation={orientation} className={className} />;
}

export { GOVERNANCE_STAGES };
export type { GovernanceStageId };
