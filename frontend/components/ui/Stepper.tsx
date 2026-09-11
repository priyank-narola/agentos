import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export type StepState = "done" | "active" | "pending" | "bad";

export interface Step {
  label: string;
  caption?: ReactNode;
  state?: StepState;
  /** optional metadata shown at the right edge (vertical only) */
  meta?: ReactNode;
}

const DOT: Record<StepState, string> = {
  done: "border-signal bg-signal",
  active: "border-warning bg-warning ring-4 ring-warning/20",
  bad: "border-danger bg-danger",
  pending: "border-hairlineStrong bg-surface",
};

const CHECK = (
  <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden>
    <path d="M2 5.2 4.2 7.4 8 3" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

/** Ordered governance/process steps — one coherent lifecycle visual. */
export function Stepper({
  items,
  orientation = "vertical",
  className,
}: {
  items: Step[];
  orientation?: "vertical" | "horizontal";
  className?: string;
}) {
  if (orientation === "horizontal") {
    return (
      <ol className={cn("grid gap-2 md:grid-cols-[repeat(auto-fit,minmax(120px,1fr))]", className)}>
        {items.map((step, index) => {
          const state = step.state ?? "pending";
          return (
            <li key={`${step.label}-${index}`} className="relative flex items-center gap-2.5">
              <span aria-hidden className={cn("grid h-5 w-5 shrink-0 place-items-center rounded-full border text-white", DOT[state])}>
                {state === "done" ? CHECK : state === "bad" ? <span aria-hidden>!</span> : <span className="tnum text-[10px] font-semibold text-ink">{index + 1}</span>}
              </span>
              <div className="min-w-0">
                <p className={cn("truncate text-xs font-semibold", state === "pending" ? "text-inkSubtle" : "text-ink")}>{step.label}</p>
                {step.caption && <p className="mt-0.5 line-clamp-2 text-[11px] leading-4 text-inkFaint">{step.caption}</p>}
              </div>
            </li>
          );
        })}
      </ol>
    );
  }

  return (
    <ol className={cn("space-y-0", className)}>
      {items.map((step, index) => {
        const state = step.state ?? "pending";
        const last = index === items.length - 1;
        return (
          <li key={`${step.label}-${index}`} className="relative flex gap-3 pb-5 last:pb-0">
            {!last && <span aria-hidden className="absolute left-[9px] top-5 h-full w-px bg-hairlineStrong" />}
            <span aria-hidden className={cn("relative z-10 mt-0.5 grid h-[19px] w-[19px] shrink-0 place-items-center rounded-full border text-white", DOT[state])}>
              {state === "done" ? CHECK : state === "bad" ? <span aria-hidden className="text-[11px] font-bold">!</span> : <span className="tnum text-[10px] font-semibold text-inkSubtle">{index + 1}</span>}
            </span>
            <div className="flex min-w-0 flex-1 items-baseline justify-between gap-3">
              <div className={cn(state === "pending" && "opacity-70")}>
                <p className={cn("text-sm font-semibold", state === "bad" ? "text-danger" : "text-ink")}>{step.label}</p>
                {step.caption && <p className="mt-0.5 text-xs leading-5 text-inkSubtle">{step.caption}</p>}
              </div>
              {step.meta && <div className="shrink-0 text-xs text-inkFaint">{step.meta}</div>}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
